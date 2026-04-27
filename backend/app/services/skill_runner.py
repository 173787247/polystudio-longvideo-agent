from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from ..skills.loader import SkillsLoader
from .video_remix_service import VideoRemixRequest, VideoRemixResult, VideoRemixService


@dataclass(frozen=True)
class SkillRunRequest:
    skill_name: str
    inputs: Dict[str, Any]


class SkillRunner:
    """
    最小 Skill 执行入口：
    - 负责发现技能（供“progressive loading”展示摘要）
    - 负责把 skill_name 路由到对应的强约束工作流（确保工具顺序）
    """

    def __init__(self, project_root: Path):
        self.loader = SkillsLoader(project_root=project_root)

    def skills_summary(self) -> str:
        return self.loader.build_skills_summary_xml()

    def run(self, req: SkillRunRequest) -> Any:
        # 这里的“按需加载”体现在：运行前只需要 summary；真正执行时才会读取完整 SKILL.md（可用于审计/调试）
        _skill_md = self.loader.load_skill_body(req.skill_name)  # noqa: F841

        if req.skill_name in ("video-remix", "video_remix"):
            video_path = Path(req.inputs["video_path"])
            target_style = str(req.inputs.get("target_style", "news_anchor"))
            out_duration_s = float(req.inputs.get("out_duration_s", 8.0))
            fps = int(req.inputs.get("fps", 12))
            return VideoRemixService().run(
                VideoRemixRequest(
                    video_path=video_path,
                    target_style=target_style,
                    out_duration_s=out_duration_s,
                    fps=fps,
                )
            )

        raise ValueError(f"未知 skill: {req.skill_name}")

