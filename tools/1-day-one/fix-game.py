#!/usr/bin/env python3
"""Round 2: describe the visual bug, send the file back, ask for a fix. No hand-editing."""
import json, time, urllib.request, pathlib, sys

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src = pathlib.Path("/tmp/voxel.html").read_text()
BUG = """This page runs, but the camera spawns INSIDE the terrain: the whole screen is solid brown dirt and you cannot see the world.

Fix these, and return the COMPLETE corrected HTML file only:
1. Spawn the camera above the highest block at the centre of the world, looking out across it, so the player starts standing on the surface with sky visible.
2. Make sure gravity puts the player ON TOP of the ground rather than falling through or starting buried.
3. Keep the sky visible: the background should be sky blue and the horizon should be in view at spawn.
4. Keep every existing feature: WASD, mouse look, jump, block remove/place, crosshair, overlay.

Here is the current file:

""" + src

def main() -> None:
    body = {"model": "x", "messages": [{"role": "user", "content": BUG}],
            "temperature": 0.2, "max_tokens": 7000}
    req = urllib.request.Request("http://localhost:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=2400))
    dt = time.time() - t0
    out = r["choices"][0]["message"]["content"]
    if "```" in out:
        out = out.split("```")[1]
        out = out.split("\n", 1)[1] if out.split("\n", 1)[0].strip() in ("html", "") else out
    pathlib.Path("/tmp/voxel2.html").write_text(out)
    u = r.get("usage", {})
    print(f"in {u.get('prompt_tokens',0)} tok -> out {u.get('completion_tokens',0)} tok "
          f"in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s | {len(out)} chars")

if __name__ == "__main__":
    main()
