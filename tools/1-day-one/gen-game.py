#!/usr/bin/env python3
"""EP007 demo gate: can the local coder build a playable voxel game in one file?

One prompt, no hand-editing. Whatever comes out is what gets filmed.
"""
import json, sys, time, urllib.request, pathlib

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
PROMPT = """Write a COMPLETE single-file HTML page: a Minecraft-style voxel world using Three.js from a CDN.

Requirements:
- <!DOCTYPE html> with everything inline. No build step, no local files, no imports besides the Three.js CDN script tag.
- A 24x24 world of 1x1x1 blocks with hills from a simple noise function (write your own, do not import noise libraries). Grass blocks on top, dirt below.
- Colours: grass green top blocks, brown dirt, a sky-blue background, and a directional light plus ambient light so faces are shaded differently.
- Pointer-lock first-person controls: WASD to move, mouse to look, Space to jump with simple gravity.
- Left click removes the block you are looking at, right click places one. Use a Raycaster.
- A crosshair in the centre and a small instructions overlay in the corner.
- Must run by opening the file directly in a browser.

Output ONLY the HTML, no explanation."""

def main() -> None:
    body = {"model": "x", "messages": [{"role": "user", "content": PROMPT}],
            "temperature": 0.2, "max_tokens": 6000}
    req = urllib.request.Request("http://localhost:8080/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=1800))
    dt = time.time() - t0
    out = r["choices"][0]["message"]["content"]
    if "```" in out:
        out = out.split("```")[1]
        out = out.split("\n", 1)[1] if out.split("\n", 1)[0].strip() in ("html", "") else out
    p = pathlib.Path("/tmp/voxel.html"); p.write_text(out)
    u = r.get("usage", {})
    tok = u.get("completion_tokens", 0)
    print(f"{tok} tokens in {dt:.0f}s = {tok/dt:.1f} tok/s | {len(out)} chars")
    # cheap structural checks before anyone opens a browser
    for need in ("<!DOCTYPE", "three", "Raycaster", "pointerlock", "keydown"):
        print(f"  {'ok ' if need.lower() in out.lower() else 'MISSING'} {need}")

if __name__ == "__main__":
    main()
