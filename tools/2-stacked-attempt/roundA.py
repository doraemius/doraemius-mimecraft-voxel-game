#!/usr/bin/env python3
"""Restart from v5 (the last version with a VERIFIED visible world).

The operator's instruction: let the model design the gameplay, the demo and the eval.
So this prompt states goals and constraints, and deliberately does NOT prescribe the
telemetry field names or the check list - that is the model's design problem.
"""
import json, time, urllib.request, pathlib

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src = pathlib.Path("/tmp/voxel4.html").read_text()   # v5 base is voxel5; voxel4 = working fixed
P = """This voxel game renders correctly. Before adding any features, give it a way to prove it is still working.

Design and add a SELF-EVALUATION system. You decide what to check and what to call things. The requirements are only these:

- It must run periodically WHILE the game is playing (not once at startup), at an interval you choose.
- Each run must decide, from the real state of the scene, whether the game is actually working, and emit ONE line to the console beginning with the word EVAL followed by JSON.
- That JSON must include an overall verdict field whose value is "ok" or "bad", and a list of individual named checks with their pass/fail and the measured value that decided it.
- The single most important check: the player can actually SEE the world. A count of blocks in a data structure does not prove anything is on screen - a previous version reported thousands of blocks while rendering a blank grey screen. Find a way to verify that geometry is genuinely being rendered and visible from the current camera, and report the number actually drawn.
- Other checks are your choice. Think about what could silently break in a voxel game: the camera ending up inside geometry or aimed at nothing, terrain failing to generate, objects placed with nothing beneath them, the frame rate collapsing, an exception swallowed somewhere.
- If any check fails, the verdict is "bad" and the failing check must say why in plain words.

Do not change how the game looks or plays. Return the COMPLETE HTML only.

""" + src

body = {"model": "x", "messages": [{"role": "user", "content": P}],
        "temperature": 0.25, "max_tokens": 14000}
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
pathlib.Path("/tmp/vA.html").write_text(out)
u = r.get("usage", {})
print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
print("  emits EVAL:", "EVAL" in out, "| has verdict:", "verdict" in out.lower())
