#!/usr/bin/env python3
"""Record a browser game's ?demo=1 run headlessly: Xvfb + kiosk Chrome + ffmpeg x11grab.

    PY_MEM_CAP=none python3 capture-demo.py game.html out.mp4 --seconds 60

Implements local-coder/CAPTURE-GAMEPLAY.md with its checks built in rather than remembered:
  - libx264 must be an available ENCODER, not merely ffmpeg on PATH
  - one frame is grabbed first and must show a game (not black, not a blank page) before
    the full recording starts
  - the bottom rows must not be flat page background (headless screenshots showed an 88 px
    strip where the canvas did not reach)
  - Chrome and Xvfb are torn down by their own Popen handles, never by name pattern
Run under PY_MEM_CAP=none on the GPU box: Chrome dies (SIGTRAP) under the 16 GiB RLIMIT_AS wrapper.

GL backend matters: plain flags and --use-gl=swiftshader both render in SOFTWARE at ~9-12 fps
on the GPU box, which played the 60-fps frame-counted demo ~6x slow. --use-angle=gl-egl (default
here) or --use-angle=vulkan reach the RTX 3080 at 60 fps; measured 2026-09-23 by reading
WEBGL_debug_renderer_info from the page, not by trusting the flag.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

W, H = 1280, 720


def grab_one(display: str, out: Path) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "x11grab", "-draw_mouse", "0",
                    "-video_size", f"{W}x{H}", "-i", display, "-frames:v", "1", str(out)], check=True)


def frame_ok(png: Path) -> tuple[bool, str]:
    from PIL import Image
    im = Image.open(png).convert("RGB")
    colours = im.getcolors(W * H) or []
    bottom = im.crop((0, H - 60, W, H)).getcolors(W * 60) or []
    # graded object: the captured OUTPUT frame, not the page or the flags that produced it
    output_distinct, output_bottom_distinct = len(colours), len(bottom)
    # CONTENT PRESENT, not content large: round 1 (one cube on sky) is a correct frame with
    # 5 colours, and a first version (>200 colours, bottom >20) refused it and every early
    # round. A blank page or bare X root is 1-2 colours. The bottom-row count is reported,
    # not graded: kiosk captures fill all 720 rows (verified), the strip was headless-only.
    ok = output_distinct >= 3
    return ok, f"distinct={output_distinct} bottom60_distinct={output_bottom_distinct}"


def first_game_frame(raw: Path, fps: int) -> float:
    """Seconds into the raw recording of the first frame that is a rendered game, not a
    blank X root or a loading page (same test as frame_ok, on 160x90 samples)."""
    from PIL import Image
    w, h = 160, 90
    data = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(raw), "-t", "12",
                           "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          capture_output=True, check=True).stdout
    n = w * h * 3
    for i in range(len(data) // n):
        im = Image.frombytes("RGB", (w, h), data[i * n:(i + 1) * n])
        if len(im.getcolors(w * h) or []) > 60:
            return i / fps
    sys.exit("no game frame in the first 12 s of the recording")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("out")
    ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--display", default=":95")
    ap.add_argument("--warmup", type=float, default=4.0)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--query", default="demo=1", help="URL query string; '' for none")
    ap.add_argument("--expect-flat", action="store_true",
                    help="the build legitimately shows a near-flat frame (v1 brown, v8 grey): "
                         "skip the content check and trim a fixed 2 s after launch")
    ap.add_argument("--gl", default="--use-angle=gl-egl --ignore-gpu-blocklist",
                    help="Chrome GL flags; '--use-gl=swiftshader --enable-unsafe-swiftshader --disable-gpu' for software")
    a = ap.parse_args()

    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if "libx264" not in enc:
        sys.exit("CAPABILITY ffmpeg has no libx264 encoder")

    html = Path(a.html).resolve()
    out = Path(a.out).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="capture-"))
    env = dict(os.environ, DISPLAY=a.display)
    xvfb = subprocess.Popen(["Xvfb", a.display, "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp"],
                            stderr=subprocess.DEVNULL)
    chrome = None
    try:
        time.sleep(1.0)
        if xvfb.poll() is not None:
            sys.exit(f"INSTRUMENT Xvfb {a.display} exited (display in use?)")
        # Record from BEFORE Chrome starts: the demo is frame-counted from page load, and
        # starting after the warmup lost its first ~300 frames (the walk start and both jumps).
        raw = tmp / "raw.mp4"
        rec = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "x11grab", "-draw_mouse", "0",
                                "-framerate", str(a.fps), "-video_size", f"{W}x{H}", "-i", a.display,
                                "-t", str(a.seconds + a.warmup + 3), "-c:v", "libx264", "-preset", "veryfast",
                                "-crf", "18", "-pix_fmt", "yuv420p", str(raw)])
        time.sleep(0.5)
        chrome = subprocess.Popen(
            ["google-chrome", "--no-sandbox", *a.gl.split(), "--kiosk", f"--window-size={W},{H}", "--window-position=0,0",
             "--disable-infobars", "--no-first-run", "--no-default-browser-check",
             f"--user-data-dir={tmp / 'profile'}", f"file://{html}" + (f"?{a.query}" if a.query else "")],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(a.warmup)
        probe = tmp / "first.png"
        grab_one(a.display, probe)
        ok, detail = frame_ok(probe)
        if a.expect_flat:
            ok, detail = True, detail + " (flat expected, not graded)"
        print(f"FIRST FRAME {detail} -> {'ok' if ok else 'BAD'}  ({probe})", flush=True)
        if not ok:
            rec.terminate()
            sys.exit("frame after warmup is not a full game frame; recording abandoned")
        rec.wait()
        start = 2.0 if a.expect_flat else first_game_frame(raw, a.fps)
        print(f"TRIM game appears at {start:.3f}s of the raw recording", flush=True)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(raw),
                        "-t", str(a.seconds), "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                        "-pix_fmt", "yuv420p", str(out)], check=True)
    finally:
        for p in (chrome, xvfb):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
    # Count FRAMES, not bytes: a legitimately flat clip (v1 brown, v8 grey) encodes to
    # well under 100 KB, and a byte threshold refused all three.
    frames = 0
    if out.exists():
        n = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v",
                            "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(out)],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()
        frames = int(n) if n.isdigit() else 0
    print(f"WROTE {out} {frames} frames")
    if frames < 0.9 * a.seconds * a.fps:
        sys.exit(f"output has {frames} frames, expected ~{a.seconds * a.fps}")


if __name__ == "__main__":
    main()
