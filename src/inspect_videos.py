from __future__ import annotations

import sys
from pathlib import Path

import imageio.v3 as iio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    video_dir = PROJECT_ROOT / "outputs" / "videos"
    out_dir = PROJECT_ROOT / "outputs" / "inspect"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(video_dir.glob("*.mp4"))
    print("video_dir:", video_dir)
    print("count:", len(files))

    for p in files:
        print("\n==", p.name, "==")
        try:
            meta = iio.immeta(p)
            if isinstance(meta, dict):
                for k in ("codec", "fps", "duration", "size", "nframes", "plugin"):
                    if k in meta:
                        print(f"{k}:", meta[k])
            else:
                print(meta)
        except Exception as e:
            print("meta_error:", repr(e))

        # 导出首帧截图，便于肉眼核对内容
        try:
            frame0 = iio.imread(p, index=0)
            out_path = out_dir / (p.stem + "_frame0.png")
            iio.imwrite(out_path, frame0)
            print("frame0_png:", out_path)
        except Exception as e:
            print("frame0_error:", repr(e))


if __name__ == "__main__":
    main()

