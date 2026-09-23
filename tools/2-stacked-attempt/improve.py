import json,time,urllib.request,pathlib
KEY=open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src=pathlib.Path("/tmp/voxel5.html").read_text()
P=("""This voxel game works but the world looks plain and it does not read as a playable game. Improve it. Keep it ONE self-contained HTML file and keep every existing control.

1. TERRAIN VARIETY. Make the world 40x40 and add biomes driven by a second low-frequency noise value: sand near low ground, grass in the middle, bare stone on high ground, and snow on the highest peaks. Add a water level: any column below the water height gets translucent blue water blocks on top.
2. MORE BLOCK COLOURS. Use distinct colours for grass, dirt, sand, stone, snow, water and wood. Keep the darker side faces.
3. IT MUST LOOK PLAYABLE. Add a block-selection outline: a thin black wireframe box drawn on whatever block the crosshair is pointing at, updated every frame with the Raycaster.
4. ADD A HELD BLOCK. Draw a small cube in the bottom-right of the view, fixed to the camera, showing the block type that will be placed. Number keys 1-5 switch the selected block type and the held cube updates.
5. TREES: place trees ONLY on grass columns, and anchor the trunk base exactly on the surface height of that column. Some trees are currently floating in the air with no ground beneath them - fix that.

Return the COMPLETE HTML only.

"""+src)
body={"model":"x","messages":[{"role":"user","content":P}],"temperature":0.25,"max_tokens":12000}
req=urllib.request.Request("http://localhost:8080/v1/chat/completions",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
t0=time.time(); r=json.load(urllib.request.urlopen(req,timeout=3600)); dt=time.time()-t0
out=r["choices"][0]["message"]["content"]
if "```" in out:
    out=out.split("```")[1]; out=out.split("\n",1)[1] if out.split("\n",1)[0].strip() in ("html","") else out
pathlib.Path("/tmp/voxel6.html").write_text(out)
u=r.get("usage",{}); print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s | {len(out)} chars")
for k in ("snow","sand","stone","water","wireframe","LineSegments","EdgesGeometry"):
    print(f"  {'ok ' if k.lower() in out.lower() else 'MISSING'} {k}")
