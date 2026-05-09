# i18n.py - 中英双语翻译
"""所有 UI 文本集中管理，通过 gr.Dropdown 切换语言"""

ZH = {
    # 标题
    "title": "照片筛选器",
    "subtitle": "基于 SigLIP 2 视觉模型的内容理解与质量评估工具",
    "subtitle_p1": "**内容匹配** — 用文字描述筛选符合主题的照片",
    "subtitle_p2": "**美学评分** — 多维度评估构图、色彩、曝光",
    "subtitle_p3": "**清晰度** — 自动检测模糊照片",

    # 控制面板
    "folder_label": "📁 图片文件夹路径",
    "folder_placeholder": "在文件管理器复制路径后粘贴到这里",
    "folder_info": "右键文件夹 → 复制文件地址 或 Ctrl+L 选中路径后 Ctrl+C",
    "folder_note": "💡 图片保留在原位置，不会被上传。筛选结果通过导出按钮复制到指定目录。",
    "prompt_label": "🔍 内容描述（可选）",
    "prompt_placeholder": "如: 海边日落、城市夜景、人像特写 ...",

    "weights_title": "⚙️ 评分权重",
    "w_content": "内容匹配",
    "w_aesthetic": "美学评分",
    "w_sharpness": "清晰度",

    "top_n_label": "🏆 显示 Top N",
    "scan_btn": "🚀 开始扫描",
    "scan_waiting": "等待扫描 ...",

    "export_title": "📤 导出",
    "export_dir_label": "导出目录（留空则在原文件夹创建 筛选结果/）",
    "export_dir_placeholder": "C:\\Photos\\精选",
    "export_btn": "📦 导出筛选结果",

    # 结果
    "gallery_label": "🏆 筛选结果",
    "table_label": "📊 详细评分",
    "table_headers": ["排名", "文件名", "总分", "匹配", "美学", "清晰度", "路径"],

    # 语言
    "lang_label": "🌐 Language / 语言",

    # 消息
    "no_valid_folder": "请选择有效的图片文件夹",
    "no_images": "文件夹中没有找到图片文件",
    "scan_found": "找到 {n} 张图片，开始评分 ...",
    "scan_fail": "评分失败，请检查图片文件",
    "scan_done": "📊 扫描完成",
    "scan_summary": "---" * 12,
    "scan_total_img": "📁 总图片: {n} 张",
    "scan_top_n": "🏆 展示 Top {n}",
    "scan_best": "最高分: {score} ({name})",
    "scan_worst": "最低分: {score} ({name})",
    "scan_avg": "平均分: {score:.1f}",
    "export_done": "✅ 已导出 {n} 张照片到: {path}",
    "export_nothing": "没有可导出的结果",
    "gallery_label_fmt": "#{idx} | {score}分",
}

EN = {
    # 标题
    "title": "Photo Screener",
    "subtitle": "Content-aware photo quality assessment with SigLIP 2",
    "subtitle_p1": "**Content Match** — Filter by theme with text descriptions",
    "subtitle_p2": "**Aesthetic Score** — Multi-dimensional composition, color, exposure",
    "subtitle_p3": "**Sharpness** — Auto-detect blurry photos",

    # 控制面板
    "folder_label": "📁 Image Folder Path",
    "folder_placeholder": "Copy path from file manager and paste here",
    "folder_info": "Right-click folder → Copy address, or Ctrl+L select path then Ctrl+C",
    "folder_note": "💡 Images stay where they are. Export copies filtered results to your chosen folder.",
    "prompt_label": "🔍 Description (optional)",
    "prompt_placeholder": "e.g. sunset beach, city night, portrait ...",

    "weights_title": "⚙️ Scoring Weights",
    "w_content": "Content Match",
    "w_aesthetic": "Aesthetic",
    "w_sharpness": "Sharpness",

    "top_n_label": "🏆 Show Top N",
    "scan_btn": "🚀 Start Scan",
    "scan_waiting": "Waiting for scan ...",

    "export_title": "📤 Export",
    "export_dir_label": "Export folder (leave empty to use Selected/ in source)",
    "export_dir_placeholder": "C:\\Photos\\Selected",
    "export_btn": "📦 Export Results",

    # 结果
    "gallery_label": "🏆 Results",
    "table_label": "📊 Detailed Scores",
    "table_headers": ["Rank", "Filename", "Total", "Content", "Aesthetic", "Sharpness", "Path"],

    # 语言
    "lang_label": "🌐 Language / 语言",

    # 消息
    "no_valid_folder": "Please select a valid image folder",
    "no_images": "No image files found in folder",
    "scan_found": "Found {n} images, scoring ...",
    "scan_fail": "Scoring failed, check image files",
    "scan_done": "📊 Scan Complete",
    "scan_summary": "---" * 12,
    "scan_total_img": "📁 Total: {n} images",
    "scan_top_n": "🏆 Showing Top {n}",
    "scan_best": "Best: {score} ({name})",
    "scan_worst": "Worst: {score} ({name})",
    "scan_avg": "Average: {score:.1f}",
    "export_done": "✅ Exported {n} photos to: {path}",
    "export_nothing": "No results to export",
    "gallery_label_fmt": "#{idx} | {score}",
}


def t(key: str, lang: str = "zh", **fmt) -> str:
    """获取翻译文本，支持 format 参数"""
    d = ZH if lang == "zh" else EN
    text = d.get(key, key)
    if fmt:
        text = text.format(**fmt)
    return text
