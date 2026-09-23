#!/usr/bin/env python3
"""Rebuild the voxel game one feature per round, gating each on PIXELS before promoting it.

    python3 rounds.py 1          run round 1 (from scratch)
    python3 rounds.py 5          run round 5 on top of the last PASSING file

State: /tmp/vox/goodN.html is the last build that passed the gate. A round that fails is
kept as /tmp/vox/failN.html and the good file is NOT advanced, so the next round always
builds on something known to render.

Why this exists: a previous attempt stacked six features into one round and then spent
seven rounds unable to tell which one made the world invisible.
"""
import json, pathlib, subprocess, sys, time, urllib.request

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
URL = "http://localhost:8080/v1/chat/completions"
D = pathlib.Path("/tmp/vox"); D.mkdir(exist_ok=True)
GATE = "/tmp/game-gate-linux.py"

BASE_RULES = (
    "Return the COMPLETE single-file HTML only, no explanation. Everything inline, "
    "three.js from a CDN script tag, runs by opening the file directly. "
    "Do NOT add any self-evaluation, metrics or telemetry code.\n"
    "STANDING RULE - do not regress this: the player must spawn standing on OPEN GRASS "
    "with the horizon and sky clearly visible ahead, never inside a block, never pressed "
    "against a block face, and never looking straight down or straight up. If terrain "
    "changes, recompute the spawn: pick a grass column whose immediate neighbours are not "
    "taller than it, place the camera on its surface plus eye height, and face it toward "
    "the middle of the map horizontally.")

ROUNDS = {
 1: ("one green cube on a sky-blue background, with a PerspectiveCamera 10 units back looking "
     "straight at it, an ambient light and a directional light. Nothing else.", ""),
 2: ("Extend it: replace the single cube with a FLAT 32x32 floor of 1x1x1 green grass blocks "
     "centred on the origin. Put the camera 12 units above the floor near one corner, looking "
     "ACROSS the floor toward the opposite corner and slightly down, so both the ground and the "
     "sky are visible in the frame.", "demo"),
 3: ("Extend it: give the floor height variation using a simple deterministic noise function you "
     "write yourself (no libraries), heights 0 to 8. Grass on the top block of each column, "
     "brown dirt blocks below it. Keep the camera above the highest terrain looking out at the "
     "horizon.", ""),
 4: ("Extend it: add first-person controls. Pointer lock on click, mouse look, WASD movement "
     "relative to facing, gravity, and Space to jump. The player must stand ON the terrain "
     "surface and never fall through it. Keep the spawn view looking at the horizon.", ""),
 5: ("Extend it: add a Raycaster so left click removes the block under the crosshair and right "
     "click places one against the face you are pointing at. Draw a small crosshair in the centre "
     "of the screen.", ""),
 6: ("Extend it: add biomes by height using a second noise value - sand at low elevations, grass "
     "in the middle, bare stone high up, snow on the highest peaks, and blue water blocks filling "
     "any column below a fixed sea level. Each type gets its own distinct colour.", ""),
 7: ("Extend it: place about 12 trees - a brown trunk 4 blocks tall with a green leaf canopy - "
     "ONLY on grass columns, with the base of each trunk exactly on that column's surface height "
     "so no tree floats in the air.", ""),
 8: ("Extend it: improve the lighting. A warm directional light low in the sky plus a cooler "
     "ambient light, and make the side faces of every block visibly darker than the top faces so "
     "the terrain reads as three-dimensional.", ""),
 9: ("Extend it: add a vertical sky gradient (deep blue overhead fading to pale at the horizon), "
     "distance fog matching the horizon colour, and a subtle CSS vignette over the canvas.", ""),
 10: ("Optimise the rendering WITHOUT changing how it looks: use one THREE.InstancedMesh per block "
      "type sharing a single BoxGeometry instead of one Mesh per block, and skip blocks whose six "
      "neighbours are all solid. Block removal and placement must still work, and the Raycaster "
      "must still select blocks (it reports instanceId on instanced meshes).", ""),
 11: ("Extend it: add 4 passive NPCs - two-block-tall figures built from coloured boxes - that "
      "wander slowly across the surface, stay on top of the terrain and never walk through solid "
      "blocks.", ""),
 12: ("Extend it: give the player 20 HP with a health bar, a sword held in the lower right of the "
      "view that swings on left click, and 3 hostile enemies of a distinct colour that move toward "
      "the player when close and deal damage on contact. A hit enemy flashes and loses HP and is "
      "removed at zero.", ""),
 13: ("Extend it: hold right mouse button to RAISE GUARD, which halves incoming damage; hold Shift "
      "to SPRINT; double-tap a movement key to DODGE ROLL with brief invulnerability.", ""),
 14: ("Extend it: if the URL contains ?demo=1, the game plays ITSELF starting 1 second after load, "
      "with no human input and no pointer lock: walk across the terrain with a gentle head-bob, "
      "jump twice, sprint briefly, swing the sword at an enemy, raise guard, dodge once, and break "
      "and place one block. Drive it from a FRAME COUNTER, not wall-clock time or randomness, so "
      "the same run is reproducible. About 35 seconds.", "demo"),
}


def ask(prompt: str, base: str) -> tuple[str, float, int]:
    content = prompt + "\n\n" + BASE_RULES + (("\n\nHere is the current file:\n\n" + base) if base else "")
    body = {"model": "x", "messages": [{"role": "user", "content": content}],
            "temperature": 0.2, "max_tokens": 16000}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + KEY})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=5400))
    out = r["choices"][0]["message"]["content"]
    if "```" in out:
        out = out.split("```")[1]
        out = out.split("\n", 1)[1] if out.split("\n", 1)[0].strip() in ("html", "") else out
    return out, time.time() - t0, r.get("usage", {}).get("completion_tokens", 0)


def main() -> None:
    n = int(sys.argv[1])
    prompt, query = ROUNDS[n]
    prev = D / f"good{n-1}.html"
    base = prev.read_text() if n > 1 and prev.exists() else ""
    if n > 1 and not base:
        sys.exit(f"no passing round {n-1} to build on")

    html, dt, tok = ask(prompt, base)
    cand = D / f"cand{n}.html"; cand.write_text(html)
    print(f"round {n}: {tok} tok in {dt:.0f}s = {tok/dt:.1f} tok/s, {len(html)} chars", flush=True)

    cmd = ["python3", GATE, str(cand), "--budget", "13000", "--no-telemetry",
           "--shot", str(D / f"r{n}.png")]
    if query:
        cmd += ["--query", "demo=1"]
    g = subprocess.run(cmd, capture_output=True, text=True)
    print(g.stdout.strip())
    if g.returncode == 0:
        (D / f"good{n}.html").write_text(html)
        print(f"PROMOTED -> good{n}.html")
    else:
        (D / f"fail{n}.html").write_text(html)
        print(f"NOT promoted; good{n-1}.html still stands")
    sys.exit(g.returncode)


if __name__ == "__main__":
    main()
