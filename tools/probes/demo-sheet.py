#!/usr/bin/env python3
"""Screenshot the ?demo=1 run at chosen demo frames (rAF shimmed to 16 ms, so frame ~= t/16),
stamp each with its frame number and state, and tile them into one sheet."""
import pathlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
D = pathlib.Path("/tmp/vox"); name = sys.argv[1]
FRAMES = [30, 130, 200, 360, 470, 545, 560, 700, 830, 965, 1030, 1400, 1800, 2150]
SHIM = "<head><script>window.requestAnimationFrame=function(cb){return setTimeout(function(){cb(performance.now())},16)};</script>"
src = (D / name).read_text().replace("<head>", SHIM, 1)
def shot(f):
    # freeze exactly at demo frame f so the screenshot shows that frame, then print state into the page
    js = ("<script>(function w(){if(typeof demoFrame!=='undefined'&&demoFrame>=%d){var d=document.createElement('div');"
          "d.style.cssText='position:absolute;top:4px;left:4px;z-index:999;color:#fff;background:#000a;font:14px monospace';"
          "d.textContent='f'+demoFrame+' hp'+playerHP+' en'+enemies.length+' y'+player.position.y.toFixed(1)+' g'+(+guarding)+' s'+(+sprinting)+' dg'+dodgeFrames;"
          "document.body.appendChild(d);window.requestAnimationFrame=function(){};return;}setTimeout(w,4);})();</script></body>") % f
    p = D / f"demo_{f}.html"; p.write_text(src.replace("</body>", js))
    out = D / f"demo_{f}.png"
    subprocess.run(["/usr/bin/google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--use-gl=swiftshader",
        "--enable-unsafe-swiftshader", "--window-size=1280,720", f"--virtual-time-budget={f*16+4000}",
        f"--user-data-dir=/tmp/vox/prof_{f}", f"--screenshot={out}", f"file://{p}?demo=1"], capture_output=True, timeout=900)
    return out
with ThreadPoolExecutor(4) as ex:
    outs = list(ex.map(shot, FRAMES))
tiles = [Image.open(o).convert("RGB").resize((426, 240)) for o in outs if o.exists()]
sheet = Image.new("RGB", (426 * 4, 240 * ((len(tiles) + 3) // 4)))
for k, t in enumerate(tiles):
    sheet.paste(t, ((k % 4) * 426, (k // 4) * 240))
sheet.save(D / "demo_sheet.png"); print(len(tiles), "of", len(FRAMES), "frames")
