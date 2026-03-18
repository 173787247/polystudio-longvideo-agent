from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from ..tools.paths import resolve_project_paths
from ..tools.video_concatenation import (
    VideoConcatenationRequest,
    concatenate_videos_tool,
)
from ..tools.volcano_image_generation import (
    VolcanoImageEditRequest,
    VolcanoImageRequest,
    edit_volcano_image_tool,
    generate_volcano_image_tool,
)
from ..tools.volcano_video_generation import VolcanoVideoRequest, generate_volcano_video_tool


@dataclass(frozen=True)
class Character:
    """
    角色定义（用于多角色一致性）。

    - reference_image_path: 该角色的“统一参考图”。后续所有包含该角色的镜头优先用 edit 来保持一致性。
    """

    character_id: str
    name: str
    reference_image_path: Optional[Path] = None
    description: str = ""


@dataclass(frozen=True)
class ShotSpec:
    shot_id: str
    description: str
    duration_s: float
    character_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Storyboard:
    shots: List[ShotSpec]

    @property
    def total_duration_s(self) -> float:
        return float(sum(s.duration_s for s in self.shots))


@dataclass(frozen=True)
class LongVideoRequest:
    """
    输入：
    - storyboard: 分镜与每镜头时长（可由用户给，也可由 agent 生成后让用户确认）
    - characters: 角色表（角色 id -> 角色信息）
    - style_prompt: 全片统一风格（用于减少镜头间漂移）
    """

    storyboard: Storyboard
    characters: Dict[str, Character] = field(default_factory=dict)
    style_prompt: str = "cinematic, consistent character design, high quality"
    negative_prompt: str = "low quality, blurry, deformed, extra limbs, mixed identity, face swap"
    fps: int = 12
    target_total_duration_s: Optional[float] = None
    duration_tolerance_s: float = 0.25


@dataclass(frozen=True)
class LongVideoResult:
    final_video_path: Path
    clip_video_paths: List[Path]
    shot_image_paths: List[Path]
    storyboard: Storyboard
    duration_before_s: float
    duration_after_s: float


def _normalize_durations(
    storyboard: Storyboard,
    *,
    target_total_s: float,
    tolerance_s: float,
) -> Storyboard:
    cur = storyboard.total_duration_s
    if math.isclose(cur, target_total_s, abs_tol=tolerance_s) or cur <= 0:
        return storyboard

    ratio = target_total_s / cur
    shots = []
    for s in storyboard.shots:
        # 避免出现 0 秒镜头
        dur = max(0.5, float(s.duration_s) * ratio)
        shots.append(ShotSpec(**{**s.__dict__, "duration_s": dur}))
    return Storyboard(shots=shots)


def _build_shot_prompt(
    *,
    shot: ShotSpec,
    characters: Dict[str, Character],
    style_prompt: str,
) -> str:
    char_desc = []
    for cid in shot.character_ids:
        c = characters.get(cid)
        if not c:
            continue
        one = f"{c.name}"
        if c.description:
            one += f" ({c.description})"
        char_desc.append(one)

    chars = "; ".join(char_desc) if char_desc else "no specific character"
    return (
        f"{style_prompt}\n"
        f"SHOT: {shot.description}\n"
        f"CHARACTERS: {chars}\n"
        f"RULES: keep identities consistent; do not mix characters; maintain same face/hair/outfit for each character."
    )


def _composite_multi_role_images(image_paths: List[Path]) -> Path:
    if not image_paths:
        raise ValueError("image_paths 不能为空")

    base = Image.open(image_paths[0]).convert("RGB")
    for p in image_paths[1:]:
        img = Image.open(p).convert("RGB").resize(base.size)
        base = Image.blend(base, img, alpha=0.5)

    paths = resolve_project_paths()
    out_dir = paths.ensure_outputs_dir() / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / ("composite_" + image_paths[0].stem + ".png")
    base.save(out_path)
    return out_path


class LongVideoAgentService:
    """
    长视频生成流程（Agent 驱动）：
    分镜确认 -> 每镜头生图（generate/edit）-> 图生视频 -> 拼接 -> 时长校验/修正（可选）
    """

    def run(self, req: LongVideoRequest) -> LongVideoResult:
        duration_before = req.storyboard.total_duration_s

        storyboard = req.storyboard
        if req.target_total_duration_s is not None:
            storyboard = _normalize_durations(
                storyboard,
                target_total_s=req.target_total_duration_s,
                tolerance_s=req.duration_tolerance_s,
            )

        # 角色表可变副本：用于在首次出现时生成 reference 图并回填
        characters: Dict[str, Character] = dict(req.characters)

        shot_image_paths: List[Path] = []
        clip_video_paths: List[Path] = []

        for shot in storyboard.shots:
            prompt = _build_shot_prompt(
                shot=shot,
                characters=characters,
                style_prompt=req.style_prompt,
            )

            # --- 生图策略 ---
            # 若镜头包含角色：优先对每个角色用其 reference 图 edit 以保一致性。
            # 若角色没有 reference：先 generate 该角色 reference，再用于本镜头 edit。
            image_path: Optional[Path] = None
            if shot.character_ids:
                # 先确保所有角色都有 reference
                for cid in shot.character_ids:
                    c = characters.get(cid)
                    if not c:
                        # 未注册的角色：直接跳过一致性（也可视作错误）
                        continue
                    if c.reference_image_path is None:
                        ref_prompt = (
                            f"{req.style_prompt}\n"
                            f"CHARACTER SHEET: {c.name}\n"
                            f"{c.description}\n"
                            f"RULES: single character, neutral background, front view."
                        ).strip()
                        ref_img = generate_volcano_image_tool(
                            VolcanoImageRequest(
                                prompt=ref_prompt,
                                negative_prompt=req.negative_prompt,
                            )
                        )
                        characters[cid] = Character(
                            character_id=c.character_id,
                            name=c.name,
                            description=c.description,
                            reference_image_path=ref_img,
                        )

                # 多角色一致性：对每个角色分别基于其 reference 做一次 edit，再做合成（降低串脸/互相污染）
                per_role_images: List[Path] = []
                for cid in shot.character_ids:
                    c = characters.get(cid)
                    if not c or not c.reference_image_path:
                        continue
                    role_prompt = f"{prompt}\nFOCUS_CHARACTER: {c.name}"
                    per_role_images.append(
                        edit_volcano_image_tool(
                            VolcanoImageEditRequest(
                                prompt=role_prompt,
                                reference_image_path=c.reference_image_path,
                                negative_prompt=req.negative_prompt,
                            )
                        )
                    )

                if per_role_images:
                    image_path = (
                        per_role_images[0]
                        if len(per_role_images) == 1
                        else _composite_multi_role_images(per_role_images)
                    )

            if image_path is None:
                image_path = generate_volcano_image_tool(
                    VolcanoImageRequest(
                        prompt=prompt,
                        negative_prompt=req.negative_prompt,
                    )
                )

            shot_image_paths.append(image_path)

            # --- 图生视频 ---
            clip_path = generate_volcano_video_tool(
                VolcanoVideoRequest(
                    image_path=image_path,
                    duration_s=float(shot.duration_s),
                    fps=req.fps,
                )
            )
            clip_video_paths.append(clip_path)

        final_path = concatenate_videos_tool(
            VideoConcatenationRequest(
                video_paths=clip_video_paths,
                fps=req.fps,
            )
        )

        duration_after = storyboard.total_duration_s
        return LongVideoResult(
            final_video_path=final_path,
            clip_video_paths=clip_video_paths,
            shot_image_paths=shot_image_paths,
            storyboard=storyboard,
            duration_before_s=duration_before,
            duration_after_s=duration_after,
        )

