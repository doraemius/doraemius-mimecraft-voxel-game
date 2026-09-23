#!/usr/bin/env python3
"""Draw calls for good13 vs good14, and does a left click on good14 change the PIXELS."""
import pathlib, subprocess, re
from PIL import Image, ImageChops
D = pathlib.Path("/tmp/vox")
CH = ["/usr/bin/google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--use-gl=swiftshader",
      "--enable-unsafe-swiftshader", "--window-size=1280,720", "--virtual-time-budget=6000"]
INFO = ('<script>setTimeout(function(){document.title="CALLS "+renderer.info.render.calls+" TRIS "+'
        'renderer.info.render.triangles+" CHILDREN "+scene.children.length;},3000);</script></body>')
CLICK = ('<script>setTimeout(function(){mouseLocked=true;var n=world.size;'
         'document.dispatchEvent(new MouseEvent("mousedown",{button:%d,clientX:640,clientY:360}));'
         'document.title="WORLD "+n+"->"+world.size;},%s);</script></body>')
def run(name, html, shot=None):
    f = D / name; f.write_text(html)
    args = CH + ([f"--screenshot={shot}"] if shot else ["--dump-dom"]) + [f"file://{f}"]
    out = subprocess.run(args, capture_output=True, text=True).stdout
    m = re.search(r"<title>([^<]*)</title>", out); return m.group(1) if m else ""
for g in ("good13", "good14"):
    print(g, run(f"p_{g}.html", (D / f"{g}.html").read_text().replace("</body>", INFO)))
src = (D / "good14.html").read_text()
for btn, label in ((0, "break"), (2, "place")):
    print(label, run(f"p_{label}.html", src.replace("</body>", CLICK % (btn, 2000))))
    run(f"p_{label}s.html", src.replace("</body>", CLICK % (btn, 2000)), D / f"after_{label}.png")
run("p_none.html", src, D / "before.png")
a = Image.open(D / "before.png").convert("RGB")
for label in ("break", "place"):
    b = Image.open(D / f"after_{label}.png").convert("RGB")
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 20 else 0)
    print(label, "changed px:", sum(1 for v in diff.getdata() if v), "bbox", diff.getbbox())
b2 = Image.open(D / "before.png").convert("RGB")  # negative control: two renders with no click
run("p_none2.html", src, D / "before2.png")
d0 = ImageChops.difference(b2, Image.open(D / "before2.png").convert("RGB")).convert("L").point(lambda v: 255 if v > 20 else 0)
print("no-click control changed px:", sum(1 for v in d0.getdata() if v))
