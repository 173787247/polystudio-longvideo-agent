from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image

from .paths import resolve_project_paths


@dataclass(frozen=True)
class VolcanoVideoRequest:
    image_path: Path
    duration_s: float
    fps: int = 12


def generate_volcano_video_tool(req: VolcanoVideoRequest) -> Path:
    """
    图生视频工具（mock 版）：把单张图片重复写入帧，得到一个短 mp4。

    真实接入时：替换为火山/其它视频生成 API 调用即可；接口形状不变。
    """
    paths = resolve_project_paths()
    out_dir = paths.ensure_outputs_dir() / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    video_id = uuid.uuid4().hex[:10]
    out_path = out_dir / f"clip_{video_id}.mp4"

    img = Image.open(req.image_path).convert("RGB")
    frame = np.array(img)
    total_frames = max(1, int(round(req.duration_s * req.fps)))

    # imageio v3 期望写入 (T, H, W, C) 的数组（或可迭代帧序列，但不同后端行为不一致）
    frames = np.repeat(frame[None, ...], repeats=total_frames, axis=0)
    iio.imwrite(out_path, frames, fps=req.fps)
    return out_path

