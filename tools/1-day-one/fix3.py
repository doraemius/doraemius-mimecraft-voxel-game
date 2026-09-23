#!/usr/bin/env python3
"""Round 3: the CODER gets the VISION model's bug report, written from the pixels."""
import json, time, urllib.request, pathlib
KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src = pathlib.Path("/tmp/voxel2.html").read_text()
VL_REPORT = ("The game's rendering engine has failed to load any terrain or environment assets, "
             "resulting in an entirely blank green screen instead of the expected landscape and "
             "sky. The cursor and on-screen controls remain visible, indicating that the game is "
             "running but unable to render the world properly.")
PROMPT = f"""A vision model looked at a screenshot of this running page and reported:

"{VL_REPORT}"

The screen is filled edge to edge with one flat green colour, the same green as the grass blocks, with no sky and no block edges. The most likely cause is that the camera is positioned INSIDE a block, so the near face of that block fills the frame.

Fix it so the player spawns clearly ABOVE the terrain with sky visible and the landscape in view. Verify your own logic: compute the maximum terrain height at the spawn column and place the camera above it plus player eye height. Return the COMPLETE corrected HTML only.

{src}"""
body={"model":"x","messages":[{"role":"user","content":PROMPT}],"temperature":0.2,"max_tokens":7000}
req=urllib.request.Request("http://localhost:8080/v1/chat/completions",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
t0=time.time(); r=json.load(urllib.request.urlopen(req,timeout=2400)); dt=time.time()-t0
out=r["choices"][0]["message"]["content"]
if "```" in out:
    out=out.split("```")[1]
    out=out.split("\n",1)[1] if out.split("\n",1)[0].strip() in ("html","") else out
pathlib.Path("/tmp/voxel3.html").write_text(out)
u=r.get("usage",{})
print(f"out {u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
