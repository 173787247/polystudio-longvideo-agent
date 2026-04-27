from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..tools.remix_script_generation import RemixScriptRequest, generate_remix_script_tool
from ..tools.video_understanding import VideoUnderstandingRequest, analyze_video_tool
from ..tools.volcano_image_generation import VolcanoImageRequest, generate_volcano_image_tool
from ..tools.volcano_video_generation import VolcanoVideoRequest, generate_volcano_video_tool


@dataclass(frozen=True)
class VideoRemixRequest:
    """
    一键式二创输入：
    - video_path: 用户上传原始视频
    - target_style: 默认新闻播报风格
    - out_duration_s: 输出短视频时长（mock：用单图重复帧）
    """

    video_path: Path
    target_style: str = "news_anchor"
    out_duration_s: float = 8.0
    fps: int = 12


@dataclass(frozen=True)
class VideoRemixResult:
    analysis: Dict[str, Any]
    script_text: str
    poster_image_path: Path
    final_video_path: Path


class VideoRemixService:
    """
    Skill 专属工作流支持（严格顺序）：
    1) 多模态理解 -> 2) 脚本生成 -> 3) 媒体生成（新闻播报短视频 mock）
    """

    def run(self, req: VideoRemixRequest) -> VideoRemixResult:
        # 1) 多模态理解
        analysis = analyze_video_tool(VideoUnderstandingRequest(video_path=req.video_path))

        # 2) 脚本生成
        script_text = generate_remix_script_tool(
            RemixScriptRequest(analysis=analysis, target_style=req.target_style)
        )

        # 3) 媒体生成（mock：用脚本生成一张“主播海报”，再图生视频）
        keyframes = analysis.get("keyframes") or []
        visual_hint = keyframes[0] if keyframes else None
        poster_prompt = _build_poster_prompt(script_text=script_text, visual_hint=visual_hint)

        poster_image_path = generate_volcano_image_tool(
            VolcanoImageRequest(
                prompt=poster_prompt,
                negative_prompt="low quality, blurry, deformed, extra limbs, text artifacts",
            )
        )

        final_video_path = generate_volcano_video_tool(
            VolcanoVideoRequest(
                image_path=poster_image_path,
                duration_s=float(req.out_duration_s),
                fps=int(req.fps),
            )
        )

        return VideoRemixResult(
            analysis=analysis,
            script_text=script_text,
            poster_image_path=poster_image_path,
            final_video_path=final_video_path,
        )


def _build_poster_prompt(*, script_text: str, visual_hint: Optional[str]) -> str:
    # 让生成工具可复用：把“关键帧路径”作为提示词文本（真实系统可改为图像参考输入）
    hint = f"\nVISUAL_HINT_KEYFRAME_PATH: {visual_hint}" if visual_hint else ""
    return (
        "news anchor studio, clean composition, cinematic, high quality\n"
        "Create a single poster image for a news brief video.\n"
        "Constraints: no readable text, no logos.\n"
        f"SCRIPT_SUMMARY:\n{script_text}\n"
        f"{hint}\n"
    ).strip()

