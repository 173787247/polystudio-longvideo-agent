from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.video_remix_service import VideoRemixRequest, VideoRemixService


def main() -> None:
    """
    用法：
      1) 先跑 python src/demo.py 生成一个 final_*.mp4
      2) 再跑 python src/remix_demo.py [path/to/video.mp4]
    """
    default_video = _pick_latest_final_video(PROJECT_ROOT / "outputs" / "videos")
    video_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_video
    if not video_path:
        raise SystemExit("未找到输入视频。请先运行 python src/demo.py 或传入 mp4 路径。")

    svc = VideoRemixService()
    result = svc.run(VideoRemixRequest(video_path=video_path, target_style="news_anchor"))

    print("=== VIDEO REMIX DONE ===")
    print("input_video:", video_path)
    print("poster_image_path:", result.poster_image_path)
    print("final_video_path:", result.final_video_path)
    print("\n--- script_text ---\n")
    print(result.script_text)


def _pick_latest_final_video(video_dir: Path) -> Path | None:
    if not video_dir.exists():
        return None
    finals = sorted(video_dir.glob("final_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return finals[0] if finals else None


if __name__ == "__main__":
    main()

