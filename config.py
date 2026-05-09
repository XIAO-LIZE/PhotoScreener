# config.py - 全局配置
import os

# ============================================================
# HuggingFace endpoint（国内用户使用镜像加速）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_ENDPOINT"] = "https://hf-mirror.com"

def _force_mirror():
    """Ensure huggingface_hub uses mirror endpoint"""
    try:
        from huggingface_hub import get_session
        get_session()  # 触发 session 初始化，用当前 env var
    except Exception:
        pass

_force_mirror()
print(f"[Config] HF_ENDPOINT={os.environ.get('HF_ENDPOINT','not set')}")

# ============================================================
# 模型配置（可插拔）
# ============================================================

# 可选模型列表（启动时选择）
AVAILABLE_MODELS = [
    {"id": "google/siglip2-base-patch16-256",  "label": "base-256",  "size": "~0.3GB", "desc": "Light & fast, recommended / 轻量极速，推荐日常用"},
    {"id": "google/siglip2-base-patch16-384",  "label": "base-384",  "size": "~0.5GB", "desc": "Balanced / 均衡之选"},
    {"id": "google/siglip2-large-patch16-384", "label": "large-384", "size": "~1.5GB", "desc": "High quality / 高质量"},
    {"id": "google/siglip2-so400m-patch16-384","label": "SO400M",    "size": "~2.5GB", "desc": "Best accuracy / 最强精度"},
]

MODEL_CONFIG = {
    "name": "google/siglip2-base-patch16-256",
    # 备选模型（下载失败时回退）
    "fallback_name": "google/siglip-base-patch16-384",

    # 推理精度："float16" 省显存，"float32" 最高精度
    "dtype": "float16",

    # 使用 GPU（有 CUDA 时自动 True）
    "use_gpu": True,
}

# ============================================================
# 美学评分 Prompt（用 SigLIP 2 对图片匹配这些描述，取平均）
# ============================================================
AESTHETIC_PROMPTS = [
    "a beautiful, high-quality photograph",
    "stunning composition and lighting",
    "professional photography, sharp and vivid",
    "award-winning photo with perfect exposure",
    "aesthetically pleasing image with great detail",
]

# ============================================================
# 评分权重（三项加权 → 总分，可 UI 调整）
# ============================================================
DEFAULT_WEIGHTS = {
    "content": 0.4,    # 内容匹配
    "aesthetic": 0.4,  # 美学评分
    "sharpness": 0.2,  # 清晰度
}

# ============================================================
# 支持的图片格式
# ============================================================
SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp",
    ".webp", ".tiff", ".tif", ".gif",
}

# ============================================================
# 性能
# ============================================================
BATCH_SIZE = 64          # base256 模型轻量，8GB 显存可以开大
MAX_IMAGE_SIZE = 512     # 预处理缩放最大边长（加速 IO）
NUM_WORKERS = 4          # 图片加载线程数
