# Photo Screener / 照片筛选器

A desktop photo analysis tool that scores and ranks images by content relevance, visual quality, and sharpness — helping you pick the best shots from large photo collections.

基于视觉模型的内容理解与质量评估桌面工具，支持内容匹配、美学评分和清晰度检测三维加权打分。

## Features / 功能

- **Content Match / 内容匹配** — Describe what you're looking for in natural language, scores images by semantic similarity / 用自然语言描述你想要的画面，通过语义相似度评估
- **Visual Quality / 视觉质量** — Multi-dimensional aesthetic evaluation covering composition, color, and exposure / 多维度美学评估，包括构图、色彩、曝光
- **Sharpness Detection / 清晰度检测** — Laplacian variance analysis to flag blurry photos / 拉普拉斯方差分析，筛选模糊照片
- **GPU Accelerated / GPU 加速** — Automatic CUDA detection with FP16 inference / 自动检测 CUDA，启用 FP16 推理
- **Bilingual UI / 双语界面** — Chinese / English toggle built in / 内置中英文切换
- **Local Only / 纯本地** — All processing runs on-device, no network required after model download / 模型下载后全程本地运行，无需联网

## Quick Start / 快速开始

### Prerequisites / 环境要求

- Python 3.10+
- NVIDIA GPU with CUDA (optional, CPU fallback available) / NVIDIA 显卡 (可选，支持 CPU 回退)
- 4 GB free disk space / 4 GB 可用空间 (default model ~300 MB / 默认模型 ~300 MB)

### One-Click Launch (EXE) / 一键启动

A pre-built launcher EXE is in the project root / 预编译启动器在项目根目录:

```bash
PhotoScreener.exe
```

On first launch it will / 首次运行会自动:
1. Auto-create a Python virtual environment / 创建虚拟环境
2. Install all dependencies (Tsinghua mirror for users in China) / 安装依赖 (国内用户走清华镜像)
3. Prompt for model selection and download / 选择并下载模型
4. Open the browser at `http://127.0.0.1:7860` / 打开浏览器

Subsequent launches skip straight to the app — no setup required. / 之后秒开，无需重复安装。

### Manual Install / 手动安装

```bash
# Windows (PowerShell)
.\setup.ps1

# macOS / Linux
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Usage / 使用

```bash
python main.py
```

Browser opens at / 浏览器打开 `http://127.0.0.1:7860`.

1. Paste your image folder path / 输入图片文件夹路径
2. Optionally enter a text description (e.g. / 如 "sunset beach", "portrait") / 可选输入描述文字
3. Adjust scoring weights if needed / 按需调整评分权重
4. Click Scan / 点击扫描
5. Export top results to a folder of your choice / 导出最佳结果到指定文件夹

## Scoring / 评分体系

| Dimension / 维度 | Method / 方法 | Default Weight / 默认权重 |
|-----------|--------|----------------|
| Content Match / 内容匹配 | SigLIP 2 vision-language embedding similarity / 视觉-语言嵌入相似度 | 0.4 |
| Aesthetic / 美学 | Multi-prompt text-image alignment / 多提示图文对齐 | 0.4 |
| Sharpness / 清晰度 | OpenCV Laplacian variance / Laplacian 方差 | 0.2 |

All weights are adjustable in the UI. / 所有权重可在界面调整。

## Model Configuration / 模型配置

Edit `config.py` to switch models / 编辑 `config.py` 切换模型:

```python
AVAILABLE_MODELS = [
    {"id": "google/siglip2-base-patch16-256",   "size": "~0.3GB"},
    {"id": "google/siglip2-base-patch16-384",   "size": "~0.5GB"},
    {"id": "google/siglip2-large-patch16-384",  "size": "~1.5GB"},
    {"id": "google/siglip2-so400m-patch16-384", "size": "~2.5GB"},
]
```

The application prompts for model selection on first launch. / 首次启动时在终端选择模型。

### Recommended Configurations / 推荐配置

| GPU | Model | VRAM | ~1000 images |
|-----|-------|------|--------------|
| 8 GB | so400m-384 | ~3 GB | ~30s |
| 6 GB | large-384  | ~2 GB | ~40s |
| 4 GB | base-256   | ~0.5 GB | ~50s |
| CPU  | base-256   | RAM ~1 GB | ~3 min |

## Project Structure / 项目结构

```
.
├── PhotoScreener.exe   # One-click launcher / 一键启动器
├── main.py              # Gradio web UI / 界面主程序
├── config.py            # Model and scoring configuration / 模型与评分配置
├── i18n.py              # Chinese / English translations / 中英文翻译
├── requirements.txt     # Python dependencies / Python 依赖
├── README.md
├── LICENSE
├── setup.ps1            # Windows one-click install / Windows 一键安装
├── run.ps1              # Windows quick launch / Windows 快速启动
└── scorer/
    ├── __init__.py
    └── scorer.py        # Core scoring engine / 核心评分引擎
```

## Mirror Configuration / 镜像配置

A HuggingFace mirror is pre-configured for users in regions with limited access to huggingface.co / 预配置镜像，方便无法访问 huggingface.co 的用户:

```python
# config.py
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
```

Model files are cached locally after first download — no further network access required. / 模型文件首次下载后缓存本地，之后无需联网。

## Dependencies / 依赖

- [SigLIP 2](https://huggingface.co/docs/transformers/model_doc/siglip2) — Vision-language model / 视觉语言模型
- [OpenCV](https://opencv.org/) — Image analysis / 图像分析
- [PyTorch](https://pytorch.org/) — Inference runtime / 推理运行时
- [Transformers](https://huggingface.co/docs/transformers) — Model loading / 模型加载
- [Gradio](https://www.gradio.app/) — Web interface / 网页界面

## License / 许可证

[MIT](LICENSE) © XIAO-LIZE
