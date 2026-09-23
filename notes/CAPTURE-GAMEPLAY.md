# Capturing gameplay footage headlessly

How EP007's game footage was made, 2026-09-22. Reusable for any browser-based demo.

## The problem with screenshots

A still from `chrome --headless --screenshot` is taken at one fixed virtual time and can
catch a scene **before it has finished initialising**. It produced a black, apparently unlit
tree in this episode and nearly put a non-existent lighting bug in the script. **A single
headless frame is not evidence about a running scene.** Capture video, or at minimum several
frames at different times.

## The setup

1. **Script the camera, do not drive it by hand.** `voxel-demo.html` is the model's own
   output plus one appended block that moves the camera along keyframed waypoints. Time
   comes from a **frame counter, not the wall clock**, so a slow renderer produces the same
   path rather than a faster one — the capture is repeatable. The block is clearly marked as
   not model-generated, because the episode's claim is about what the model wrote.
2. **Use a dedicated virtual display**, not the operator's desktop and not a display another
   job already owns:
   ```bash
   Xvfb :95 -screen 0 1280x720x24 -nolisten tcp &
   DISPLAY=:95 google-chrome --no-sandbox --disable-gpu --use-gl=swiftshader \
       --enable-unsafe-swiftshader --kiosk --window-size=1280,720 \
       --window-position=0,0 --disable-infobars "file:///tmp/voxel-demo.html" &
   ```
   `--kiosk` removes browser chrome so the frame is all game. Software GL is fine for
   flat-shaded voxels.
3. **Capture with x11grab** at the display's exact size:
   ```bash
   DISPLAY=:95 ffmpeg -f x11grab -framerate 30 -video_size 1280x720 -i :95 -t 25 \
       -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p gameplay.mp4
   ```
4. **Tear down** Chrome and Xvfb when done; check `pgrep` rather than assuming.

## Checks before using the footage

- Sample frames across the clip (not just one) and look at them.
- Confirm the window is the game and not a blank page or an error interstitial.
- Confirm the mouse cursor position is acceptable — x11grab records it.

**Known cosmetic issue in this capture:** the X cursor is visible mid-frame because nothing
moves it. Either move it off-screen before capturing (`xdotool mousemove 1279 719`) or pass
`-draw_mouse 0` to x11grab.

## 2026-09-23: the scripted version, and the GPU

`../scripts/capture-demo.py` now does all of the above, with the checks built in:

```bash
PY_MEM_CAP=none python3 capture-demo.py good21.html out.mp4 --seconds 32
```

- **Software GL played the demo ~6x slow.** With `--use-gl=swiftshader` or plain flags, the
  page renders at 9-12 fps in Xvfb. The demo is frame-counted, so its path stays correct but
  runs ~6x slower. The first 90 s capture ended mid-fight and looked like a *different* run.
  `--use-angle=gl-egl` (the default now) or `--use-angle=vulkan` reach the RTX 3080 at 60 fps.
  This was checked by the page reporting `WEBGL_debug_renderer_info` to an in-process HTTP
  beacon, not assumed from the flag.
- **Record from before Chrome starts**, then trim to the first rendered frame. Starting after
  the warmup lost the demo's first ~300 frames.
- `-draw_mouse 0` hides the cursor (`xdotool` is not installed on the GPU box).
- In kiosk mode the canvas fills all 720 rows. The ~88 px strip seen in headless
  screenshots is a headless-only artifact.

Result: `~/yt-local-coder/EP007-gameplay-demo21-60fps.mp4` (local only), 32.0 s, 1,920
frames at 60 fps.
