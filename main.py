# main.py - Photo Screener / 照片筛选器
import os
import sys
import shutil
from pathlib import Path

import gradio as gr
import numpy as np
from PIL import Image

# Frozen (PyInstaller) or development mode
if getattr(sys, "frozen", False):
    _base = Path(sys._MEIPASS)
else:
    _base = Path(__file__).resolve().parent
sys.path.insert(0, str(_base))

from scorer import PhotoScorer
import config
from i18n import t

# ================================================================
# 全局评分器（懒加载，首次使用时初始化）
# ================================================================
_scorer: PhotoScorer | None = None


def select_and_download_model():
    """Select model in terminal + pre-download before browser opens"""
    from huggingface_hub import snapshot_download
    import time

    mirror = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")

    print("\n" + "=" * 50)
    print("  Photo Screener - Model Selection / 模型选择")
    print("=" * 50)
    for i, m in enumerate(config.AVAILABLE_MODELS):
        print(f"  [{i+1}] {m['label']:12s} {m['size']:>6s}  {m['desc']}")
    print("=" * 50)

    while True:
        try:
            choice = input("Select model / 选择模型 [1-4, Enter=1]: ").strip()
            if not choice:
                idx = 0
            else:
                idx = int(choice) - 1
            if 0 <= idx < len(config.AVAILABLE_MODELS):
                break
        except ValueError:
            pass
        print("  Enter 1-4 / 输入 1-4")

    selected = config.AVAILABLE_MODELS[idx]
    model_name = selected["id"]
    config.MODEL_CONFIG["name"] = model_name

    print(f"\n[Download / 下载] {selected['label']} ({selected['size']}) ...")
    t0 = time.time()
    try:
        cache_dir = snapshot_download(
            model_name,
            endpoint=mirror,
            resume_download=True,
        )
        print(f"[Download / 下载] OK ({time.time()-t0:.0f}s)")
        print(f"[Cache / 缓存] {cache_dir}")
    except Exception as e:
        print(f"[Download / 下载] FAILED: {e}")
        sys.exit(1)

    print("\n[Loading / 加载] Loading model...")


def get_scorer() -> PhotoScorer:
    global _scorer
    if _scorer is None:
        _scorer = PhotoScorer()
        _scorer.load()
    return _scorer


# ================================================================
# Scan folder
# ================================================================

def scan_folder(folder: str) -> list[str]:
    if not folder or not os.path.isdir(folder):
        return []
    paths = []
    for f in sorted(os.listdir(folder)):
        ext = os.path.splitext(f)[1].lower()
        if ext in config.SUPPORTED_EXTENSIONS:
            paths.append(os.path.join(folder, f))
    return paths


# ================================================================
# 回调（所有用户可见文本通过 i18n.t() 获取）
# ================================================================

def run_scan(
    folder: str,
    prompt: str,
    content_weight: float,
    aesthetic_weight: float,
    sharpness_weight: float,
    top_n: int,
    lang: str,
    progress=gr.Progress(track_tqdm=True),
):
    if not folder or not os.path.isdir(folder):
        msg = t("no_valid_folder", lang)
        gr.Warning(msg)
        return [], None, msg

    paths = scan_folder(folder)
    if not paths:
        msg = t("no_images", lang)
        gr.Warning(msg)
        return [], None, msg

    gr.Info(t("scan_found", lang, n=len(paths)))

    scorer = get_scorer()
    results = scorer.score_all(paths, prompt=prompt, weights={
        "content": content_weight,
        "aesthetic": aesthetic_weight,
        "sharpness": sharpness_weight,
    })

    if not results:
        msg = t("scan_fail", lang)
        return [], None, msg

    top_results = results[:top_n]

    # Thumbnails
    thumb_size = (300, 300)
    gallery_items = []
    for r in top_results:
        try:
            img = Image.open(r["path"])
            img.thumbnail(thumb_size)
            label = t("gallery_label_fmt", lang, idx=top_results.index(r)+1, score=r["total"])
            gallery_items.append((img, label))
        except Exception:
            continue

    # Summary
    summary = (
        f"{t('scan_done', lang)}\n"
        f"{t('scan_summary', lang)}\n"
        f"{t('scan_total_img', lang, n=len(paths))}\n"
        f"{t('scan_top_n', lang, n=len(top_results))}\n"
        f"{t('scan_summary', lang)}\n"
        f"{t('scan_best', lang, score=results[0]['total'], name=results[0]['name'])}\n"
        f"{t('scan_worst', lang, score=results[-1]['total'], name=results[-1]['name'])}\n"
        f"{t('scan_avg', lang, score=np.mean([r['total'] for r in results]))}\n"
    )

    # Table
    table_data = [
        [i+1, r["name"], r["total"], r["content"], r["aesthetic"], r["sharpness"], r["path"]]
        for i, r in enumerate(top_results)
    ]

    return gallery_items, table_data, summary


def export_selected(table_data, folder: str, export_dir: str, lang: str):
    if table_data is None or (hasattr(table_data, 'empty') and table_data.empty) or len(table_data) == 0:
        msg = t("export_nothing", lang)
        gr.Warning(msg)
        return msg

    # Gradio may pass pandas DataFrame — convert to list
    if hasattr(table_data, 'values'):
        table_data = table_data.values.tolist()

    if not export_dir or not export_dir.strip():
        if lang == "zh":
            export_dir = os.path.join(folder, "筛选结果")
        else:
            export_dir = os.path.join(folder, "Selected")

    os.makedirs(export_dir, exist_ok=True)
    count = 0
    skipped = 0
    for row in table_data:
        src = str(row[6]) if row[6] is not None else ""
        if src and os.path.exists(src):
            dst = os.path.join(export_dir, os.path.basename(src))
            shutil.copy2(src, dst)
            count += 1
        else:
            skipped += 1

    if count == 0:
        return t("export_nothing", lang) + f"\n(src not found: {skipped} files / 源文件未找到: {skipped} 个)"
    return t("export_done", lang, n=count, path=export_dir)


def update_ui_text(lang: str):
    """When language changes, update markdowns"""
    title_md = (
        f"# 🖼️ {t('title', lang)}\n"
        f"{t('subtitle', lang)}\n"
        f"- {t('subtitle_p1', lang)}\n"
        f"- {t('subtitle_p2', lang)}\n"
        f"- {t('subtitle_p3', lang)}"
    )
    return title_md


# ================================================================
# UI
# ================================================================

def build_ui():
    default_lang = "zh"

    css = """
    footer { display: none !important; }
    #gallery { min-height: 400px; }
    * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif !important; }
    .card-box {
        background: var(--background-fill-secondary);
        border: 1px solid var(--border-color-primary);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    #scan-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 14px 32px !important;
        transition: transform 0.15s;
    }
    #scan-btn:hover {
        transform: scale(1.02);
    }
    .progress-container { margin: 12px 0; }
    """

    with gr.Blocks(
        title="Photo Screener / 照片筛选器",
        theme=gr.themes.Soft(),
        css=css,
    ) as demo:
        lang_state = gr.State(default_lang)

        # ── Header ──
        with gr.Row():
            with gr.Column(scale=8):
                header_md = gr.Markdown(
                    "# 🖼️ " + t("title", default_lang) + "\n"
                    + t("subtitle", default_lang) + "\n"
                    "- " + t("subtitle_p1", default_lang) + "\n"
                    "- " + t("subtitle_p2", default_lang) + "\n"
                    "- " + t("subtitle_p3", default_lang)
                )
            with gr.Column(scale=1, min_width=140):
                lang_dropdown = gr.Dropdown(
                    choices=[("中文", "zh"), ("English", "en")],
                    value=default_lang,
                    label="🌐 Language / 语言",
                    interactive=True,
                )

        # ── Main: Left controls / Right results ──
        with gr.Row():
            # ── LEFT ──
            with gr.Column(scale=4, min_width=340):
                # Folder
                with gr.Group(elem_classes="card-box"):
                    gr.Markdown("### 📁 图片文件夹 / Image Folder")
                    folder_input = gr.Textbox(
                        label="文件夹路径 / Folder Path",
                        placeholder="粘贴路径 / Paste path here",
                        info="右键文件夹→复制地址 / Right-click folder→Copy address",
                        container=True,
                    )
                    gr.Markdown("> 💡 图片保留在原位置，不会上传 / Images stay local")

                # Prompt
                with gr.Group(elem_classes="card-box"):
                    gr.Markdown("### 🔍 内容描述 / Description")
                    prompt_input = gr.Textbox(
                        label="描述你想找的画面 (可选)",
                        placeholder="海边日落、城市夜景 / sunset beach, portrait, night city...",
                        lines=2,
                        container=True,
                    )

                # Weights
                with gr.Group(elem_classes="card-box"):
                    gr.Markdown("### ⚙️ 评分权重 / Scoring Weights")
                    with gr.Row():
                        w_content = gr.Slider(0, 1, value=0.4, step=0.05, label="内容匹配 / Match")
                        w_aesthetic = gr.Slider(0, 1, value=0.4, step=0.05, label="美学评分 / Aesthetic")
                        w_sharpness = gr.Slider(0, 1, value=0.2, step=0.05, label="清晰度 / Sharpness")

                    top_n = gr.Slider(1, 200, value=20, step=1, label="🏆 " + t("top_n_label", default_lang))

                # Scan button
                scan_btn = gr.Button(
                    "🔍 开始扫描 / Start Scan",
                    variant="primary",
                    size="lg",
                    elem_id="scan-btn",
                )

                # Summary
                with gr.Group(elem_classes="card-box"):
                    gr.Markdown("### 📊 扫描结果 / Scan Summary")
                    summary_output = gr.Markdown("等待扫描 / Waiting for scan ...")

                # Export
                with gr.Group(elem_classes="card-box"):
                    gr.Markdown("### 📤 导出 / Export")
                    export_dir = gr.Textbox(
                        label="导出目录 / Export Folder（留空→筛选结果/）",
                        placeholder="C:\\Photos\\Selected",
                        container=True,
                    )
                    export_btn = gr.Button("📦 导出筛选结果 / Export", variant="secondary")
                    export_status = gr.Markdown("")

            # ── RIGHT ──
            with gr.Column(scale=5):
                gallery = gr.Gallery(
                    label="🏆 筛选结果 / Results",
                    columns=3, height=480,
                    object_fit="contain",
                    show_label=True,
                    elem_id="gallery",
                )

                table = gr.Dataframe(
                    headers=["排名/Rank", "文件名/Name", "总分/Total", "匹配/Match", "美学/Aesthetic", "清晰度/Sharp", "路径/Path"],
                    label="📊 详细评分 / Scores",
                    interactive=False,
                    wrap=True,
                    type="array",
                )

        # ── Events ──
        lang_dropdown.change(
            fn=update_ui_text,
            inputs=[lang_dropdown],
            outputs=[header_md],
        ).then(
            fn=lambda lang: lang,
            inputs=[lang_dropdown],
            outputs=[lang_state],
        )

        scan_btn.click(
            fn=run_scan,
            inputs=[folder_input, prompt_input, w_content, w_aesthetic, w_sharpness, top_n, lang_state],
            outputs=[gallery, table, summary_output],
        )

        export_btn.click(
            fn=export_selected,
            inputs=[table, folder_input, export_dir, lang_state],
            outputs=[export_status],
        )

    return demo


# ================================================================
# Entry
# ================================================================

if __name__ == "__main__":
    select_and_download_model()

    print("\n" + "=" * 50)
    print("  Photo Screener / 照片筛选器")
    print("  Browser / 浏览器: http://127.0.0.1:7860")
    print("  Ctrl+C to stop / 按 Ctrl+C 停止")
    print("=" * 50 + "\n")

    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        share=False,
    )
