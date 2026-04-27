from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import imageio.v3 as iio

from .paths import resolve_project_paths


@dataclass(frozen=True)
class VideoUnderstandingRequest:
    video_path: Path
    max_keyframes: int = 3


def analyze_video_tool(req: VideoUnderstandingRequest) -> Dict[str, Any]:
    """
    多模态理解（视频侧）- 轻量 mock：
    - 读取元信息（fps/duration/size/codec 等）
    - 导出少量关键帧（frame0 + 均匀抽样）

    返回结构化 JSON（dict），便于后续“脚本生成/媒体生成”消费。
    """
    p = Path(req.video_path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    meta = iio.immeta(p)
    meta_dict: Dict[str, Any] = meta if isinstance(meta, dict) else {"raw": str(meta)}

    fps = _to_float(meta_dict.get("fps"))
    duration_s = _to_float(meta_dict.get("duration"))
    size = meta_dict.get("size")

    keyframe_paths = _export_keyframes(p, max_keyframes=max(1, int(req.max_keyframes)))

    return {
        "video_path": str(p),
        "duration_s": duration_s,
        "fps": fps,
        "size": size,
        "codec": meta_dict.get("codec"),
        "nframes": meta_dict.get("nframes"),
        "keyframes": [str(x) for x in keyframe_paths],
        "meta": meta_dict,
    }


def dumps_analysis_json(analysis: Dict[str, Any]) -> str:
    return json.dumps(analysis, ensure_ascii=False, indent=2)


def _export_keyframes(video_path: Path, *, max_keyframes: int) -> List[Path]:
    paths = resolve_project_paths()
    out_dir = paths.ensure_outputs_dir() / "understanding"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 读取总帧数（若无则退化为只取第 0 帧）
    meta = iio.immeta(video_path)
    nframes = None
    if isinstance(meta, dict):
        nframes = meta.get("nframes")
    n = None
    if isinstance(nframes, (int, float)) and nframes:
        nf = float(nframes)
        if math.isfinite(nf) and nf > 0:
            n = int(nf)

    indices = _pick_indices(n, max_keyframes=max_keyframes)
    out: List[Path] = []
    for idx in indices:
        frame = iio.imread(video_path, index=idx)
        out_path = out_dir / f"{video_path.stem}_frame{idx}.png"
        iio.imwrite(out_path, frame)
        out.append(out_path)
    return out


def _pick_indices(nframes: int | None, *, max_keyframes: int) -> List[int]:
    if not nframes or nframes <= 1:
        return [0]
    if max_keyframes <= 1:
        return [0]

    # 0 + 均匀抽样（不包含最后一帧，避免某些编码尾帧读失败）
    step = max(1, nframes // max_keyframes)
    idxs = list(range(0, nframes, step))[:max_keyframes]
    return sorted(set([0, *idxs]))[:max_keyframes]


def _to_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

