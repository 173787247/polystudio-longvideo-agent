from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.skill_runner import SkillRunRequest, SkillRunner


def main() -> None:
    runner = SkillRunner(project_root=PROJECT_ROOT)
    print("=== SKILLS SUMMARY (for progressive loading) ===")
    print(runner.skills_summary() or "(no skills found)")

    # 默认复用 outputs/videos 下最新的 final_*.mp4
    video_path = _pick_latest_final_video(PROJECT_ROOT / "outputs" / "videos")
    if not video_path:
        raise SystemExit("未找到输入视频。请先运行 python src/demo.py 生成 final_*.mp4")

    result = runner.run(
        SkillRunRequest(
            skill_name="video-remix",
            inputs={"video_path": str(video_path), "target_style": "news_anchor"},
        )
    )

    print("\n=== SKILL RUN DONE ===")
    print("input_video:", video_path)
    print("final_video_path:", result.final_video_path)


def _pick_latest_final_video(video_dir: Path) -> Path | None:
    if not video_dir.exists():
        return None
    finals = sorted(video_dir.glob("final_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return finals[0] if finals else None


if __name__ == "__main__":
    main()

