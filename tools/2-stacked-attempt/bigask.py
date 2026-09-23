import json,time,urllib.request,pathlib
KEY=open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src=pathlib.Path("/tmp/voxel7.html").read_text()
P = """Extend this voxel game. Keep ONE self-contained HTML file, keep every existing control, and keep it runnable by opening the file.

A. SELF-REPORTING METRICS (do this first, it is the most important part).
Maintain a global `window.__metrics` object and console.log it as ONE line of JSON, prefixed exactly with `METRICS ` , once 3 seconds after load and then every 5 seconds. It must contain:
  fps                  measured frames per second over the last second
  blocks               total blocks in the world
  biomes               {grass, sand, stone, snow, water} counts of surface columns
  treesPlaced          number of trees created
  treesFloating        number of trees whose trunk base has NO solid block directly beneath it (compute this, do not assume 0)
  cameraInsideBlock    true if the camera position is inside a solid block
  skyPixelsVisible     true if the camera is looking above the horizon at spawn
  npcCount             number of living NPCs
  enemyCount           number of living enemies
  playerHp, enemyHpTotal
  errors               array of any caught error messages
Also add window.onerror to push messages into metrics.errors. These metrics are how a human verifies the game without watching it, so they must be computed from real state, never hardcoded.

B. BIGGER WORLD. 64x64 columns with the existing biomes, and keep the frame rate playable by only creating block meshes for surfaces that are actually exposed.

C. MOVING PARTS. Day/night: rotate the directional light over a 2-minute cycle and shift the sky colour with it. A few animated clouds as flat translucent boxes drifting across the sky.

D. NPCs. 4 passive NPCs: simple 2-block-tall humanoid figures of coloured boxes that wander slowly on the surface and never walk through solid blocks.

E. WEAPONS AND COMBAT. The player has a sword: left click swings it (a short animation on a small cube held bottom-right of the screen). 3 hostile enemies, visibly different colour, that path toward the player when within 20 blocks and deal damage on contact. Player has 20 HP and a health bar. Right-click RAISES A GUARD which halves incoming damage while held. Shift = sprint, double-tap a direction = dodge roll with brief invulnerability. A hit enemy flashes and loses HP; at 0 HP it is removed and enemyCount drops.

F. Keep block placing/removing on the number keys plus a modifier so combat and building do not conflict, and show the current mode on screen.

Return the COMPLETE HTML only.

""" + src
body={"model":"x","messages":[{"role":"user","content":P}],"temperature":0.25,"max_tokens":16000}
req=urllib.request.Request("http://localhost:8080/v1/chat/completions",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
t0=time.time(); r=json.load(urllib.request.urlopen(req,timeout=5400)); dt=time.time()-t0
out=r["choices"][0]["message"]["content"]
if "```" in out:
    out=out.split("```")[1]; out=out.split("\n",1)[1] if out.split("\n",1)[0].strip() in ("html","") else out
pathlib.Path("/tmp/voxel8.html").write_text(out)
u=r.get("usage",{})
print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s | {len(out)} chars")
for k in ("METRICS","treesFloating","cameraInsideBlock","npc","enemy","guard","dodge","sprint","cloud"):
    print(f"  {'ok ' if k.lower() in out.lower() else 'MISSING'} {k}")
