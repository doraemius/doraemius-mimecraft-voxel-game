#!/usr/bin/env python3
"""Make a PRESENTATION copy of a model-written build with a slow orbit camera, for B-roll.

    python3 presentation-camera.py good13.html out.html --radius 26 --height 18 --look-y 3

The build's code is untouched. One clearly labelled block is inserted right after the
three.js <script> tag. It wraps the THREE.WebGLRenderer constructor so every renderer's
render() call gets a camera orbiting the origin, whatever the model named its variables.
(A prototype hook does NOT work on r128: render is an instance property. The first test
rendered the game's own static view.)

Honesty rule: use this only where the world IS what the viewer should see (the rebuild
rounds). Never on builds whose point is what the PLAYER saw (v1 inside the ground, v3 the
floor close-up, v8 grey): an orbit would reveal a world the player could not see. Those are
captured unmodified.

The orbit is driven by a frame counter, not the clock, so the path is repeatable.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATCH = """<script>
/* PRESENTATION CAMERA - NOT MODEL CODE. Inserted by presentation-camera.py for B-roll. */
(function () {
  /* r128 assigns render() on each INSTANCE in the constructor, so a prototype hook is
     shadowed and silently never runs. Wrap the constructor and patch each instance. */
  var Base = THREE.WebGLRenderer, f = 0;
  THREE.WebGLRenderer = function (params) {
    Base.call(this, params);
    var render = this.render;
    this.render = function (scene, camera) {
      var a = %(start)s + (f++) * %(speed)s;
      camera.position.set(Math.cos(a) * %(radius)s, %(height)s, Math.sin(a) * %(radius)s);
      camera.lookAt(0, %(look_y)s, 0);
      camera.updateMatrixWorld();
      return render.call(this, scene, camera);
    };
  };
  THREE.WebGLRenderer.prototype = Base.prototype;
})();
</script>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("out")
    ap.add_argument("--radius", type=float, required=True)
    ap.add_argument("--height", type=float, required=True)
    ap.add_argument("--look-y", type=float, default=0.0)
    ap.add_argument("--speed", type=float, default=0.004, help="radians per frame")
    ap.add_argument("--start", type=float, default=0.8, help="starting angle, radians")
    a = ap.parse_args()
    src = Path(a.html).read_text()
    m = re.search(r'<script[^>]*three[^>]*\.js"[^>]*>\s*</script>', src)
    if not m:
        sys.exit("no three.js <script> tag found; refusing to guess where to hook")
    patch = PATCH % {"start": a.start, "speed": a.speed, "radius": a.radius,
                     "height": a.height, "look_y": a.look_y}
    Path(a.out).write_text(src[:m.end()] + "\n" + patch + src[m.end():])
    print(f"wrote {a.out}: orbit r={a.radius} h={a.height} lookY={a.look_y}")


if __name__ == "__main__":
    main()
