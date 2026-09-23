#!/usr/bin/env python3
"""Ask the model to REMOVE the self-eval/metrics code it wrote, which is buggy.

Hypothesis worth testing: that instrumentation may also be what stopped the world
rendering from round 6 onward. Stripping it is both what the operator asked for and the
cheapest way to find out.
"""
import json, time, urllib.request, pathlib

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src = pathlib.Path("/tmp/voxel10.html").read_text()
P = """Remove ALL of the self-evaluation and metrics code from this game. It is buggy and it is not wanted.

Specifically delete:
- the window.__metrics object and everything that maintains it
- the METRICS console.log line and its timers
- every counter that exists only to feed those metrics (treesFloating, blocksDrawn, cameraInsideBlock, skyPixelsVisible, fps sampling, biome tallies, and the demo counters jumpsDone / swordSwings / enemiesKilled / blocksBroken / blocksPlaced)
- any window.onerror handler that exists only to collect errors for metrics

Keep EVERYTHING that is actual gameplay: the terrain and biomes, trees, day/night, clouds, NPCs, enemies, combat with sword and guard and dodge and sprint, health, block placing and removing, the HUD text, and the demo mode that plays the game by itself.

Important: the world is currently NOT VISIBLE when the page runs - the screen is flat grey and no terrain appears, even though the code believes it created thousands of blocks. While you remove the metrics code, also make sure the terrain meshes are actually added to the scene and that the camera starts above the ground looking out at the horizon so the landscape and sky are on screen.

Return the COMPLETE HTML only.

""" + src

body = {"model": "x", "messages": [{"role": "user", "content": P}],
        "temperature": 0.2, "max_tokens": 16000}
req = urllib.request.Request("http://localhost:8080/v1/chat/completions",
                             data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + KEY})
t0 = time.time()
r = json.load(urllib.request.urlopen(req, timeout=5400))
dt = time.time() - t0
out = r["choices"][0]["message"]["content"]
if "```" in out:
    out = out.split("```")[1]
    out = out.split("\n", 1)[1] if out.split("\n", 1)[0].strip() in ("html", "") else out
pathlib.Path("/tmp/voxel13.html").write_text(out)
u = r.get("usage", {})
print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
print("  METRICS gone:", "METRICS" not in out, "| demo kept:", "demoMode" in out,
      "| combat kept:", "enem" in out.lower())
