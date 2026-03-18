from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List

import imageio.v3 as iio
import numpy as np

from .paths import resolve_project_paths


@dataclass(frozen=True)
class VideoConcatenationRequest:
    video_paths: List[Path]
    fps: int = 12


def concatenate_videos_tool(req: VideoConcatenationRequest) -> Path:
    """
    拼接工具（mock 版）：逐段读取视频帧并顺序写入一个新 mp4。

    注：该实现为了“可运行+无外部依赖”而简化，适合作业演示与单元测试。
    """
    if not req.video_paths:
        raise ValueError("video_paths 不能为空")

    paths = resolve_project_paths()
    out_dir = paths.ensure_outputs_dir() / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"final_{uuid.uuid4().hex[:10]}.mp4"
    fps = int(req.fps) if req.fps else 12

    all_frames = []
    for vp in req.video_paths:
        for frame in iio.imiter(vp):
            all_frames.append(frame)

    if not all_frames:
        raise ValueError("读取到的帧为空，无法拼接")

    frames = np.stack(all_frames, axis=0)
    iio.imwrite(out_path, frames, fps=fps)
    return out_path

