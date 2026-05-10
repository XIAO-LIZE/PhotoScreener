# scorer/scorer.py - Photo quality assessment engine
import os
import sys
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import numpy as np
import torch
from PIL import Image
import cv2
from tqdm import tqdm

# Frozen (PyInstaller) or development mode
if getattr(sys, "frozen", False):
    _base = Path(sys._MEIPASS)
else:
    _base = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_base))

import config


class PhotoScorer:
    """Photo quality scorer using SigLIP 2 for content understanding
    and aesthetic evaluation, with OpenCV for sharpness detection."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.MODEL_CONFIG["name"]
        self.device = self._detect_device()
        self.dtype = getattr(torch, config.MODEL_CONFIG["dtype"])
        self.model = None
        self.processor = None

    # ================================================================
    # 设备检测
    # ================================================================

    @staticmethod
    def _detect_device() -> torch.device:
        if config.MODEL_CONFIG["use_gpu"] and torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"[GPU] {gpu_name} ({vram:.1f} GB)")
            return torch.device("cuda")
        print("[CPU] 使用 CPU 推理（较慢，建议安装 CUDA 版 PyTorch）")
        return torch.device("cpu")

    # ================================================================
    # 模型加载（自动下载）
    # ================================================================

    def load(self):
        """加载模型，首次运行自动下载"""
        print(f"[Model] 加载 {self.model_name} ...")
        print(f"[Device] 当前设备: {self.device}")
        try:
            self._load_model(self.model_name)
        except Exception as e:
            print(f"[Warn] 主模型加载失败: {e}")
            fallback = config.MODEL_CONFIG["fallback_name"]
            print(f"[Model] 回退到 {fallback}")
            self._load_model(fallback)

        # 确保模型在正确设备上
        self.model = self.model.to(self.device)

        # FP16 优化（仅 GPU）
        if self.dtype == torch.float16 and self.device.type == "cuda":
            self.model = self.model.half()
            print(f"[GPU] FP16 模式")

        # CPU 模式自动降低 batch_size
        if self.device.type == "cpu":
            config.BATCH_SIZE = 4
            print("[Warn] CPU 模式，batch_size 已调整为 4，速度较慢")
        else:
            print(f"[GPU] batch_size={config.BATCH_SIZE}, 显存={torch.cuda.memory_allocated()/1024**3:.1f}GB/{torch.cuda.get_device_properties(0).total_memory/1024**3:.1f}GB")

        self.model.eval()
        
        # 启动自检：跑一张假图片确认模型正常
        print("[Check] 模型自检 ...")
        import numpy as np
        dummy = Image.fromarray(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
        s = self._encode_images([dummy])
        if s.shape[1] > 0:
            print(f"[Check] ✓ 模型正常, 特征维度={s.shape[1]}")
        
        print("[Model] 加载完成 ✓")

    def _load_model(self, name: str):
        """加载 SigLIP 2（从本地缓存，不下载）"""
        from transformers import AutoProcessor, AutoModel

        # 模型已在启动时预下载，直接用 local_files_only
        self.processor = AutoProcessor.from_pretrained(
            name,
            local_files_only=True,
        )
        self.model = AutoModel.from_pretrained(
            name,
            local_files_only=True,
        )

    # ================================================================
    # 图片加载（多线程）
    # ================================================================

    @staticmethod
    def _load_single_image(path: str) -> Optional[Image.Image]:
        """加载单张图片，返回 RGB PIL Image 或 None"""
        try:
            img = Image.open(path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            # 缩放到最大边长（加速后续处理）
            img.thumbnail((config.MAX_IMAGE_SIZE, config.MAX_IMAGE_SIZE))
            return img
        except Exception:
            return None

    def load_images(self, paths: list[str]) -> tuple[list[str], list[Image.Image]]:
        """Load images in parallel / 多线程批量加载"""
        total = len(paths)
        print(f"[IO] Loading {total} images / 加载 {total} 张图片 ...")

        with ThreadPoolExecutor(max_workers=config.NUM_WORKERS) as pool:
            images = list(tqdm(
                pool.map(self._load_single_image, paths),
                total=total,
                desc="Reading / 读取图片",
                unit="img",
            ))

        valid_paths, valid_images = [], []
        for p, img in zip(paths, images):
            if img is not None:
                valid_paths.append(p)
                valid_images.append(img)

        skipped = len(paths) - len(valid_paths)
        if skipped:
            print(f"[IO] 跳过 {skipped} 张无法读取的图片")
        return valid_paths, valid_images

    # ================================================================
    # 批量评分（所有文本 prompt 一次性过模型，不再循环多次）
    # ================================================================

    @torch.no_grad()
    def _encode_images(self, images: list[Image.Image]) -> np.ndarray:
        """批量编码图片特征（每张只过一遍视觉模型）"""
        all_embeds = []
        for i in range(0, len(images), config.BATCH_SIZE):
            batch = images[i:i + config.BATCH_SIZE]
            inputs = self.processor(
                images=batch,
                return_tensors="pt",
            ).to(self.device)
            outputs = self.model.get_image_features(**inputs)
            # SigLIP 返回 BaseModelOutputWithPooling，取 pooler_output
            embeds = outputs if isinstance(outputs, torch.Tensor) else outputs.pooler_output
            embeds = embeds / embeds.norm(dim=-1, keepdim=True)
            all_embeds.append(embeds.cpu().numpy())
        return np.vstack(all_embeds)  # (N, dim)

    @torch.no_grad()
    def _encode_texts(self, prompts: list[str]) -> np.ndarray:
        """编码文本特征（只过一遍文本模型）"""
        inputs = self.processor(
            text=prompts,
            return_tensors="pt",
            padding=True,
        ).to(self.device)
        outputs = self.model.get_text_features(**inputs)
        embeds = outputs if isinstance(outputs, torch.Tensor) else outputs.pooler_output
        embeds = embeds / embeds.norm(dim=-1, keepdim=True)
        return embeds.cpu().numpy()  # (P, dim)

    @torch.no_grad()
    def _score_multiple_prompts(
        self, images: list[Image.Image], prompts: list[str]
    ) -> np.ndarray:
        """高效批量评分：图片编码一次 + 文本编码一次 = O(N+P) 而非 O(N×P)
        
        Returns:
            np.ndarray shape (N_images, N_prompts), 范围 0-100
        """
        if not prompts:
            return np.full((len(images), 1), 50.0)

        img_embeds = self._encode_images(images)     # (N, dim)
        txt_embeds = self._encode_texts(prompts)     # (P, dim)
        
        # 余弦相似度 → sigmoid → 0-100
        sim = img_embeds @ txt_embeds.T               # (N, P)
        scores = (1.0 / (1.0 + np.exp(-sim))) * 100   # sigmoid
        return scores

    # ================================================================
    # 内容匹配评分
    # ================================================================

    @torch.no_grad()
    def score_content(self, images: list[Image.Image], prompt: str) -> np.ndarray:
        """计算图片与文本描述的匹配度，返回 0-100 分数数组

        Args:
            images: PIL 图片列表
            prompt: 文本描述，如 "a beautiful landscape"

        Returns:
            np.ndarray, shape (N,), 范围 0-100
        """
        if not prompt.strip():
            return np.full(len(images), 50.0)  # 无描述给中性分

        scores = []
        for i in range(0, len(images), config.BATCH_SIZE):
            batch = images[i:i + config.BATCH_SIZE]
            inputs = self.processor(
                text=[prompt],
                images=batch,
                return_tensors="pt",
                padding=True,
            ).to(self.device)

            outputs = self.model(**inputs)
            # SigLIP 2 logits_per_image: (batch_size, 1)
            logits = outputs.logits_per_image.squeeze(-1)
            # sigmoid → 0~1 → 乘 100
            batch_scores = torch.sigmoid(logits).cpu().numpy() * 100
            scores.extend(batch_scores.tolist())

        return np.array(scores)

    # ================================================================
    # 美学评分（批量模式，一步完成）
    # ================================================================

    @torch.no_grad()
    def score_aesthetic(self, images: list[Image.Image]) -> np.ndarray:
        """美学评分：多prompt一次性批量评分取平均，不再循环多次"""
        prompts = config.AESTHETIC_PROMPTS
        scores = self._score_multiple_prompts(images, prompts)  # (N, 5)
        return scores.mean(axis=1)

    # ================================================================
    # 清晰度评分（OpenCV Laplacian）
    # ================================================================

    @staticmethod
    def _sharpness_single(img: Image.Image) -> float:
        """单张图片清晰度评分"""
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        # 映射到 0-100：经验值，variance=500 以上算非常清晰
        score = min(100.0, (variance / 500.0) * 100.0)
        return score

    def score_sharpness(self, images: list[Image.Image]) -> np.ndarray:
        """批量清晰度评分"""
        scores = [self._sharpness_single(img) for img in images]
        return np.array(scores)

    # ================================================================
    # 综合评分
    # ================================================================

    def score_all(
        self,
        paths: list[str],
        prompt: str = "",
        weights: Optional[dict] = None,
    ) -> list[dict]:
        """Full scoring pipeline / 完整评分流程"""
        import time
        t_start = time.time()
        
        if weights is None:
            weights = config.DEFAULT_WEIGHTS

        # 1. Load images / 加载图片
        t_load = time.time()
        valid_paths, images = self.load_images(paths)
        t_load = time.time() - t_load
        if not images:
            print("[Warn] No valid images / 没有有效图片")
            return []
        print(f"[Timer] IO: {t_load:.1f}s ({len(images)} images)")

        # 2. Model scoring / 模型评分
        t_score = time.time()
        all_prompts = []
        content_idx = None
        if prompt.strip():
            all_prompts.append(prompt)
            content_idx = 0
        aesthetic_prompts = config.AESTHETIC_PROMPTS
        total_prompts = len(all_prompts) + len(aesthetic_prompts)

        print(f"[Timer] Model scoring... ({total_prompts} prompts) / 模型评分...")
        
        # 一次前向传播：图片 × (内容prompt + 美学prompts)
        all_scores = self._score_multiple_prompts(
            images, all_prompts + aesthetic_prompts
        )  # shape: (N, total_prompts)

        # 拆分：内容分 + 美学分
        if content_idx is not None:
            content_scores = all_scores[:, content_idx]
        else:
            content_scores = np.full(len(images), 50.0)
        
        # 美学分 = 剩余prompt的平均
        aesthetic_scores = all_scores[:, len(all_prompts):].mean(axis=1)

        # Sharpness analysis / 清晰度分析
        sharpness_scores = self.score_sharpness(images)
        t_score = time.time() - t_score
        print(f"[Timer] Scoring: {t_score:.1f}s (model + sharpness) / 评分耗时")

        total = (
            weights["content"] * content_scores
            + weights["aesthetic"] * aesthetic_scores
            + weights["sharpness"] * sharpness_scores
        )

        # 6. 组装结果
        results = []
        for i, path in enumerate(valid_paths):
            results.append({
                "path": path,
                "name": os.path.basename(path),
                "content": round(float(content_scores[i]), 1),
                "aesthetic": round(float(aesthetic_scores[i]), 1),
                "sharpness": round(float(sharpness_scores[i]), 1),
                "total": round(float(total[i]), 1),
            })

        # 按总分降序
        results.sort(key=lambda x: x["total"], reverse=True)
        print(f"[Timer] 总耗时: {time.time()-t_start:.1f}s")
        return results
