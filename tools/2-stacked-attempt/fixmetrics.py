import json,time,urllib.request,pathlib
KEY=open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src=pathlib.Path("/tmp/voxel8.html").read_text()
P = """Your game now reports its own metrics. Here is the first real report from a running session:

METRICS {"fps":18,"blocks":23673,"biomes":{"grass":1349,"sand":294,"stone":187,"snow":0,"water":1307},"treesPlaced":9,"treesFloating":513,"cameraInsideBlock":false,"skyPixelsVisible":false,"npcCount":4,"enemyCount":3,"playerHp":20,"enemyHpTotal":30,"errors":[]}

Three of those numbers are wrong. Fix the CAUSES, not the numbers:

1. treesFloating is 513 while treesPlaced is 9. A count of floating trees can never exceed the number of trees. Your check is counting the wrong thing - probably every leaf block, or every block with air beneath it anywhere in the world. Rewrite it so it evaluates exactly one thing per tree: does the trunk's base block have a solid block directly below it. Then make the number actually be 0 by anchoring every trunk base to that column's surface height.

2. snow is 0. The snow biome never generates. Your height thresholds must leave a real band of columns above the stone threshold. Print nothing - just make the terrain actually produce snow columns, and keep sand, grass, stone and water too.

3. skyPixelsVisible is false. The player spawns without the horizon in view. The camera must start above the surface looking OUT across the world, not down at it. Remember: setting camera.lookAt to a point directly below the camera fills the screen with one block face.

Also raise fps if you can do it cheaply: only build meshes for block faces that are exposed to air, and reuse one geometry and one material per block type across all instances.

Keep every feature: biomes, NPCs, enemies, combat, guard, dodge, sprint, day/night, clouds, and the METRICS line. Return the COMPLETE HTML only.

""" + src
body={"model":"x","messages":[{"role":"user","content":P}],"temperature":0.2,"max_tokens":16000}
req=urllib.request.Request("http://localhost:8080/v1/chat/completions",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
t0=time.time(); r=json.load(urllib.request.urlopen(req,timeout=5400)); dt=time.time()-t0
out=r["choices"][0]["message"]["content"]
if "```" in out:
    out=out.split("```")[1]; out=out.split("\n",1)[1] if out.split("\n",1)[0].strip() in ("html","") else out
pathlib.Path("/tmp/voxel9.html").write_text(out)
u=r.get("usage",{}); print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
