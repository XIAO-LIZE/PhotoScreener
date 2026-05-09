# Photo Screener / 照片筛选器

A desktop photo analysis tool that scores and ranks images by content relevance, visual quality, and sharpness — helping you pick the best shots from large photo collections.

基于视觉模型的内容理解与质量评估桌面工具，支持内容匹配、美学评分和清晰度检测三维加权打分。

## Features

- **Content Match** — Describe what you're looking for in natural language, scores images by semantic similarity
- **Visual Quality** — Multi-prompt aesthetic evaluation covering composition, color, and exposure
- **Sharpness Detection** — Laplacian variance analysis to flag blurry photos
- **GPU Accelerated** — Automatic CUDA detection with FP16 inference
- **Bilingual UI** — Chinese / English toggle built in
- **Local Only** — All processing runs on-device, no network required after model download

## Quick Start

### Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA (optional, CPU fallback available)
- 4 GB free disk space (model download, ~300 MB for default config)

### Installation

```bash
# Windows (PowerShell)
.\setup.ps1

# macOS / Linux
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The setup script will guide you through mirror selection and PyTorch installation.

### Usage

```bash
python main.py
```

Browser opens at `http://127.0.0.1:7860`.

1. Paste your image folder path
2. Optionally enter a text description (e.g., "sunset beach", "portrait")
3. Adjust scoring weights if needed
4. Click Scan
5. Export top results to a folder of your choice

## Scoring

| Dimension | Method | Default Weight |
|-----------|--------|----------------|
| Content Match | SigLIP 2 vision-language embedding similarity | 0.4 |
| Aesthetic | Multi-prompt text-image alignment | 0.4 |
| Sharpness | OpenCV Laplacian variance | 0.2 |

All weights are adjustable in the UI.

## Model Configuration

Edit `config.py` to switch models:

```python
AVAILABLE_MODELS = [
    {"id": "google/siglip2-base-patch16-256",   "size": "~0.3GB"},
    {"id": "google/siglip2-base-patch16-384",   "size": "~0.5GB"},
    {"id": "google/siglip2-large-patch16-384",  "size": "~1.5GB"},
    {"id": "google/siglip2-so400m-patch16-384", "size": "~2.5GB"},
]
```

The application prompts for model selection on first launch.

### Recommended Configurations

| GPU | Model | VRAM | ~1000 images |
|-----|-------|------|--------------|
| 8 GB | so400m-384 | ~3 GB | ~30s |
| 6 GB | large-384  | ~2 GB | ~40s |
| 4 GB | base-256   | ~0.5 GB | ~50s |
| CPU  | base-256   | RAM ~1 GB | ~3 min |

## Project Structure

```
.
├── main.py              # Gradio web UI
├── config.py            # Model and scoring configuration
├── i18n.py              # Chinese / English translations
├── requirements.txt     # Python dependencies
├── README.md
├── LICENSE
├── setup.ps1            # Windows one-click install
├── run.ps1              # Windows quick launch
└── scorer/
    ├── __init__.py
    └── scorer.py        # Core scoring engine
```

## Mirror Configuration

A HuggingFace mirror is pre-configured for users in regions with limited access to huggingface.co:

```python
# config.py
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
```

Model files are cached locally after first download — no further network access required.

## Dependencies

- [SigLIP 2](https://huggingface.co/docs/transformers/model_doc/siglip2) — Vision-language model
- [OpenCV](https://opencv.org/) — Image analysis
- [PyTorch](https://pytorch.org/) — Inference runtime
- [Transformers](https://huggingface.co/docs/transformers) — Model loading
- [Gradio](https://www.gradio.app/) — Web interface

## License

[MIT](LICENSE)
