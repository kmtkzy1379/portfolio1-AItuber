"""
screen-capture.py

使い方: このスクリプトは画面をキャプチャして連番PNGまたは表示を行います。
できるだけ既存のコードを変えず、単独で使えるように簡潔かつ可読性を保って追加します。

依存:
  - mss (pip install mss)
  - numpy (pip install numpy)
  - opencv-python (任意, 表示する場合のみ必要: pip install opencv-python)

基本動作:
  - 指定したFPSで画面全体または矩形領域をキャプチャ
  - フレームを output/frames に連番PNGで保存
  - --show を付けるとウィンドウ表示 (cv2 が必要)

注: ライブ配信や他プロセスへのパイプを行う用途がある場合は、このスクリプトを起点に拡張してください。
"""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime

try:
    import mss
    import numpy as np
except Exception as e:
    raise SystemExit(
        "Missing dependency: please install required packages: pip install mss numpy (optional: opencv-python)\n" + str(e)
    )

# 表示オプションは OpenCV を使う。無ければ --show はエラーメッセージを表示して終了する。
try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Capture the screen to numbered PNG frames. Kept small and readable for inclusion in the project."
    )
    p.add_argument("--fps", type=float, default=5.0, help="Frames per second to capture (default: 5)")
    p.add_argument(
        "--region",
        type=str,
        default="",
        help=(
            "Region to capture as left,top,width,height (e.g. 100,100,800,600). "
            "Empty string means full screen."
        ),
    )
    p.add_argument("--out", type=str, default="output/frames", help="Output directory for frames")
    p.add_argument(
        "--show", action="store_true", help="Show captured frames in a window (requires opencv)")
    p.add_argument("--max-frames", type=int, default=0, help="Stop after this many frames (0 = unlimited)")
    return p.parse_args()

def ensure_outdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def parse_region(region: str) -> dict | None:
    if not region:
        return None
    parts = [int(x) for x in region.split(",")]
    if len(parts) != 4:
        raise ValueError("region must be left,top,width,height")
    left, top, width, height = parts
    return {"left": left, "top": top, "width": width, "height": height}

def frame_filename(outdir: str, index: int) -> str:
    # 6桁の連番とタイムスタンプ
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return os.path.join(outdir, f"frame_{index:06d}_{ts}.png")

def main() -> int:
    args = parse_args()

    if args.show and not _HAS_CV2:
        print("--show を使うには opencv-python が必要です。インストール: pip install opencv-python")
        return 2

    region = parse_region(args.region)
    ensure_outdir(args.out)

    sct = mss.mss()

    interval = 1.0 / max(0.1, args.fps)
    frame_idx = 0
    print(f"Starting screen capture at {args.fps} FPS -> {args.out}")
    try:
        while True:
            start = time.time()

            if region is None:
                monitor = sct.monitors[0]  # 全画面
            else:
                monitor = region

            img = np.asarray(sct.grab(monitor))
            # mss returns BGRA, opencv expects BGR for display; for saving we keep BGRA -> PNG supports alpha
            # Convert to BGRA if needed (mss already provides 4 channels)

            filename = frame_filename(args.out, frame_idx)
            # cv2.imwrite は BGR/BGRA を受け取るがここでは Pillow を入れず cv2 が有れば使用、無ければ mss.image.save
            if _HAS_CV2:
                # cv2.imwrite handles BGRA as well
                cv2.imwrite(filename, img)
            else:
                # mss.tools.to_png を使って保存
                from mss.tools import to_png

                to_png(img.tobytes(), img.size, output=filename)

            if args.show and _HAS_CV2:
                bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) if img.shape[2] == 4 else img
                cv2.imshow("screen-capture", bgr)
                # waitKey を短くしてウィンドウが応答するようにする
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("User requested quit (q).")
                    break

            frame_idx += 1
            if args.max_frames > 0 and frame_idx >= args.max_frames:
                print(f"Captured {frame_idx} frames. Stopping because --max-frames was set.")
                break

            elapsed = time.time() - start
            sleep_for = interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        if _HAS_CV2:
            cv2.destroyAllWindows()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
