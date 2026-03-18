from __future__ import annotations

import textwrap
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ImageDraw, ImageFont

from .paths import resolve_project_paths


@dataclass(frozen=True)
class VolcanoImageRequest:
    prompt: str
    width: int = 1024
    height: int = 1024
    negative_prompt: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class VolcanoImageEditRequest:
    prompt: str
    reference_image_path: Path
    width: int = 1024
    height: int = 1024
    negative_prompt: str = ""
    seed: Optional[int] = None


def _load_font(size: int = 28) -> ImageFont.ImageFont:
    # Pillow on Windows usually ships with a default bitmap font fallback.
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _wrap_lines(s: str, width: int) -> Iterable[str]:
    for line in s.splitlines() or [""]:
        for wrapped in textwrap.wrap(line, width=width) or [""]:
            yield wrapped


def _render_card(
    *,
    title: str,
    prompt: str,
    subtitle: str = "",
    width: int,
    height: int,
) -> Image.Image:
    img = Image.new("RGB", (width, height), color=(20, 24, 33))
    draw = ImageDraw.Draw(img)
    font_title = _load_font(42)
    font_body = _load_font(26)

    pad = 48
    y = pad
    draw.text((pad, y), title, fill=(240, 240, 240), font=font_title)
    y += 70
    if subtitle:
        draw.text((pad, y), subtitle, fill=(180, 190, 210), font=font_body)
        y += 52

    body = "\n".join(_wrap_lines(prompt, width=46))
    draw.multiline_text((pad, y), body, fill=(210, 220, 240), font=font_body, spacing=10)
    return img


def generate_volcano_image_tool(req: VolcanoImageRequest) -> Path:
    """
    产图工具（mock 版）：把 prompt 渲染成一张卡片图，模拟“生图”输出。

    真实接入时：把这里替换为火山/其它图片生成 API 调用即可；接口形状不变。
    """
    paths = resolve_project_paths()
    out_dir = paths.ensure_outputs_dir() / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    image_id = uuid.uuid4().hex[:10]
    out_path = out_dir / f"gen_{image_id}.png"
    img = _render_card(
        title="generate_volcano_image_tool",
        subtitle=f"{req.width}x{req.height}",
        prompt=req.prompt,
        width=req.width,
        height=req.height,
    )
    img.save(out_path)
    return out_path


def edit_volcano_image_tool(req: VolcanoImageEditRequest) -> Path:
    """
    图像编辑工具（mock 版）：读取 reference_image 并叠加当前 prompt，模拟“基于参考图做 edit”。

    多角色一致性的关键：reference_image_path 通常为该角色的 reference 图。
    """
    paths = resolve_project_paths()
    out_dir = paths.ensure_outputs_dir() / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    image_id = uuid.uuid4().hex[:10]
    out_path = out_dir / f"edit_{image_id}.png"

    base = Image.open(req.reference_image_path).convert("RGB")
    base = base.resize((req.width, req.height))
    overlay = _render_card(
        title="edit_volcano_image_tool",
        subtitle=f"ref={Path(req.reference_image_path).name}",
        prompt=req.prompt,
        width=req.width,
        height=req.height,
    )

    # 简单混合，让“参考图”痕迹保留（模拟一致性）
    out = Image.blend(base, overlay, alpha=0.55)
    out.save(out_path)
    return out_path

