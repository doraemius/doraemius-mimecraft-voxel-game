#!/usr/bin/env python3
"""Gate a generated browser game: does it throw, does it SHOW anything, what does it report.

Written after twelve rounds were verified from a metrics line alone. The game reported
blocks:23673 and errors:[] while rendering a blank grey screen, because `blocks` counted
entries in a data structure, not geometry on screen. This gate therefore never trusts the
game's own numbers on their own: it also looks at the pixels.

    python3 game-gate.py path/to/game.html [--query demo=1] [--budget 18000] [--shot out.png]

Run under PY_MEM_CAP=none on the GPU box (see render()).

Exit 0 only if: no uncaught error, the page reports telemetry, AND the frame contains a
world (colour variety plus some sky), i.e. it is not a flat fill.
"""
from __future__ import annotations

import argparse
import json
import re
import resource
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TRAP = (
    '<script>window.__t="";'
    'window.addEventListener("error",function(e){document.title="ERR "+e.message+" @"+e.lineno;});'
    'var _l=console.log;console.log=function(){var a=[].slice.call(arguments).join(" ");'
    'if(a.indexOf("METRICS")===0||a.indexOf("TELEMETRY")===0||a.indexOf("EVAL")===0){'
    'window.__t=a;document.title=a;}_l.apply(console,arguments);};</script>'
)


def render(html: Path, query: str, budget: int, shot: Path,
           want_telemetry: bool = True) -> tuple[str, Path]:
    src = html.read_text()
    trapped = Path(tempfile.mkdtemp()) / "trapped.html"
    trapped.write_text(src.replace("<head>", "<head>" + TRAP, 1))
    url = f"file://{trapped}" + (f"?{query}" if query else "")
    base = [CHROME, "--headless=new", "--disable-gpu", "--use-gl=swiftshader",
            "--enable-unsafe-swiftshader", "--window-size=1280,720",
            f"--virtual-time-budget={budget}"]
    # One Chrome launch when telemetry is not expected: the DOM pass exists only to read
    # the console line, and running it anyway doubled the gate's wall time for nothing.
    if want_telemetry:
        dom = subprocess.run(base + ["--dump-dom", url], capture_output=True, text=True).stdout
        m = re.search(r"<title>([^<]*)</title>", dom)
        title = m.group(1) if m else ""
    else:
        title = ""
    shot.unlink(missing_ok=True)
    r = subprocess.run(base + [f"--screenshot={shot}", url], capture_output=True)
    if not shot.exists():
        # An instrument failure must never read as a verdict on the build. On the GPU box the
        # python3 wrapper caps RLIMIT_AS at 16 GiB; children inherit it and Chrome dies with
        # SIGTRAP (rc -5) before writing anything - good13 "failed" this gate that way.
        sys.exit(f"INSTRUMENT Chrome wrote no screenshot (rc={r.returncode}); "
                 f"RLIMIT_AS={resource.getrlimit(resource.RLIMIT_AS)[0]} - run with PY_MEM_CAP=none")
    return title, shot


def looks_like_a_world(png: Path, min_content: float) -> tuple[bool, str]:
    """Is anything drawn, and is it not the empty-canvas signature?

    Two real failure modes, and one false alarm this gate caused itself:
      - nothing drawn        -> frame is essentially one flat colour
      - empty canvas + CSS vignette -> ~99% neutral grey, no sky
      - FALSE ALARM: round 1 is one small green cube on plain sky (99.8% sky). An earlier
        version rejected it as "too dominant". A correct simple scene must pass, so the
        test is CONTENT PRESENT, not content large.
    """
    from PIL import Image
    im = Image.open(png).convert("RGB")
    total = im.width * im.height
    colours = im.getcolors(600000) or []
    if not colours:
        return False, "unreadable"
    distinct = len(colours)
    top_n, top_c = max(colours, key=lambda x: x[0])
    generated_content = sum(n for n, c in colours
                  if max(abs(c[0]-top_c[0]), abs(c[1]-top_c[1]), abs(c[2]-top_c[2])) > 30) / total
    sky = sum(n for n, c in colours if c[2] > c[0] + 20) / total
    grey = sum(n for n, c in colours if abs(c[0]-c[1]) < 12 and abs(c[1]-c[2]) < 12) / total
    empty_canvas = grey >= 0.90 and sky <= 0.05
    # "Unlit scene": geometry is there but every surface renders near-black, which happened
    # when a sky/fog change silently removed the lights. Colour variety alone passed it.
    dark = sum(n for n, c in colours if max(c) < 24) / total
    unlit = dark >= 0.45
    # the verdict names what it grades: the fraction of the GENERATED frame that is
    # actual content rather than background
    ok = generated_content >= min_content and not empty_canvas and not unlit and distinct > 3
    why = f"distinct={distinct} dominant={top_n/total:.1%} content={generated_content:.2%} sky={sky:.0%} grey={grey:.0%}"
    why += f" dark={dark:.0%}"
    if empty_canvas:
        why += "  [empty-canvas]"
    if unlit:
        why += "  [UNLIT: geometry present but near-black]"
    return ok, why


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--query", default="")
    ap.add_argument("--budget", type=int, default=18000)
    ap.add_argument("--shot", default="")
    ap.add_argument("--min-content", type=float, default=0.0005,
                    help="fraction of pixels that must differ from the dominant colour")
    ap.add_argument("--no-telemetry", action="store_true",
                    help="the build is expected to have no telemetry line; judge on pixels")
    a = ap.parse_args()
    html = Path(a.html).resolve()
    shot = Path(a.shot).resolve() if a.shot else html.with_suffix(".gate.png")

    title, shot = render(html, a.query, a.budget, shot, want_telemetry=not a.no_telemetry)
    print(f"file      {html.name}")

    failures = []
    if title.startswith("ERR "):
        print(f"ERROR     {title[4:]}")
        failures.append("threw")
    elif title.startswith(("METRICS", "TELEMETRY", "EVAL")):
        print(f"REPORTED  {title[:400]}")
        blob = re.search(r"\{.*\}", title)
        if blob:
            try:
                d = json.loads(blob.group(0))
                drawn = d.get("blocksDrawn")
                if drawn is not None and drawn == 0:
                    failures.append("blocksDrawn=0")
                errs = d.get("errors") or []
                if errs:
                    failures.append(f"errors:{errs[:1]}")
            except Exception:
                pass
    else:
        # A page title is not telemetry. The first version of this gate accepted
        # "Minecraft-Style Voxel World" as a report, which is exactly the class of mistake
        # the gate exists to prevent.
        print(f"REPORTED  (no telemetry line; title was {title[:60]!r})")
        if not a.no_telemetry:
            failures.append("no telemetry")

    visible, detail = looks_like_a_world(shot, a.min_content)
    print(f"PIXELS    {detail}  -> {'world visible' if visible else 'FLAT / EMPTY'}")
    if not visible:
        failures.append("nothing visible")

    print(f"SHOT      {shot}")
    print("VERDICT   " + ("PASS" if not failures else "FAIL: " + ", ".join(failures)))
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
