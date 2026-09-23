#!/usr/bin/env python3
"""Retry round 4 with the failure described as STATE, not appearance."""
import json, pathlib, subprocess, sys, time, urllib.request

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
D = pathlib.Path("/tmp/vox")
base = (D / "good3.html").read_text()

P = """Add first-person controls to this terrain. Your previous attempt failed: the player fell THROUGH the terrain and ended up below the world, looking up at the unlit undersides of the blocks.

Requirements, in this order of importance:

1. COLLISION FIRST. Before applying gravity, work out the surface height of the column the player is standing over: scan that column's blocks and take the highest solid y. The player's feet must never go below that surface. Clamp the camera's y to (surfaceHeight + 1 + eyeHeight) whenever it would fall below it, and zero the downward velocity when that happens.
2. SPAWN standing on the surface at the centre of the map, with the camera looking horizontally out across the terrain - not down, not up.
3. Then add: pointer lock on click, mouse look (yaw on the mouse X, pitch on mouse Y, clamped to just under +/- 90 degrees), WASD movement relative to the direction faced, and Space to jump, which sets an upward velocity that gravity brings back down to the surface.
4. The player must also not walk off the edge of the world into the void: clamp x and z to the map bounds.

Keep the terrain generation, colours and sky exactly as they are.

Return the COMPLETE single-file HTML only, no explanation. Do NOT add any self-evaluation, metrics or telemetry code.

Here is the current file:

""" + base

body = {"model": "x", "messages": [{"role": "user", "content": P}],
        "temperature": 0.2, "max_tokens": 16000}
req = urllib.request.Request("http://localhost:8080/v1/chat/completions",
                             data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + KEY})
t0 = time.time()
r = json.load(urllib.request.urlopen(req, timeout=5400))
out = r["choices"][0]["message"]["content"]
if "```" in out:
    out = out.split("```")[1]
    out = out.split("\n", 1)[1] if out.split("\n", 1)[0].strip() in ("html", "") else out
dt = time.time() - t0
tok = r.get("usage", {}).get("completion_tokens", 0)
cand = D / "cand4b.html"; cand.write_text(out)
print(f"retry 4: {tok} tok in {dt:.0f}s = {tok/dt:.1f} tok/s")

g = subprocess.run(["python3", "/tmp/game-gate-linux.py", str(cand), "--budget", "10000",
                    "--no-telemetry", "--shot", str(D / "r4.png")],
                   capture_output=True, text=True)
print(g.stdout.strip())
if g.returncode == 0:
    (D / "good4.html").write_text(out)
    print("PROMOTED -> good4.html")
sys.exit(g.returncode)
