from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.agent_service import (
    Character,
    LongVideoAgentService,
    LongVideoRequest,
    ShotSpec,
    Storyboard,
)


def main() -> None:
    # 两个角色：A、B（reference 不提供，Agent 会自动生成角色卡并回填）
    characters = {
        "A": Character(character_id="A", name="角色A", description="短发，红色外套"),
        "B": Character(character_id="B", name="角色B", description="长发，蓝色连衣裙"),
    }

    storyboard = Storyboard(
        shots=[
            ShotSpec(
                shot_id="s1",
                description="城市街头，角色A走向镜头，表情坚定",
                duration_s=2.0,
                character_ids=["A"],
            ),
            ShotSpec(
                shot_id="s2",
                description="咖啡馆内，角色A与角色B同框对话，氛围温暖",
                duration_s=3.0,
                character_ids=["A", "B"],
            ),
            ShotSpec(
                shot_id="s3",
                description="夜景天桥，角色B独自望向远处霓虹",
                duration_s=2.5,
                character_ids=["B"],
            ),
        ]
    )

    req = LongVideoRequest(
        storyboard=storyboard,
        characters=characters,
        style_prompt="cinematic, consistent character design, soft light, high quality",
        fps=12,
        target_total_duration_s=8.0,
    )

    service = LongVideoAgentService()
    result = service.run(req)

    print("=== DONE ===")
    print("final_video_path:", result.final_video_path)
    print("clips:", *result.clip_video_paths, sep="\n- ")
    print("images:", *result.shot_image_paths, sep="\n- ")
    print("duration_before_s:", result.duration_before_s)
    print("duration_after_s:", result.duration_after_s)

    # 方便用户快速找到输出
    root = Path(__file__).resolve().parents[1]
    print("outputs_dir:", root / "outputs")


if __name__ == "__main__":
    main()

