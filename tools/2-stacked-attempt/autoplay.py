import json,time,urllib.request,pathlib
KEY=open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src=pathlib.Path("/tmp/voxel8.html").read_text()
P = """Add a DEMO MODE to this game so it can play itself for a video recording. Keep everything else working.

If the page URL contains ?demo=1, then 1 second after load the game starts playing itself, with no human input and no pointer lock required:

1. The player WALKS across the terrain with realistic first-person motion: a gentle head-bob synchronised to walking speed, and the camera looking slightly left and right as it goes. It must look like someone is walking, not like a camera sliding on rails.
2. It JUMPS twice during the run, with the existing gravity, so the view rises and falls.
3. It SPRINTS for a few seconds (visibly faster, wider bob).
4. It walks up to an enemy, SWINGS THE SWORD several times until that enemy dies, and the enemy visibly flashes and loses HP.
5. It RAISES GUARD for about two seconds while an enemy attacks.
6. It performs one DODGE ROLL.
7. It BREAKS one block and PLACES one block.
8. The whole demo lasts about 35 seconds, is deterministic (drive it from a frame counter, NOT from wall-clock time or Math.random, so the same recording is produced every run), and it must never walk through solid blocks or fall out of the world.

Keep the METRICS console line, and add to it: demoMode (bool), demoStep (string naming the current action), jumpsDone, swordSwings, enemiesKilled, blocksBroken, blocksPlaced. These let a recording be verified from the log without watching it.

Return the COMPLETE HTML only.

""" + src
body={"model":"x","messages":[{"role":"user","content":P}],"temperature":0.25,"max_tokens":16000}
req=urllib.request.Request("http://localhost:8080/v1/chat/completions",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
t0=time.time(); r=json.load(urllib.request.urlopen(req,timeout=5400)); dt=time.time()-t0
out=r["choices"][0]["message"]["content"]
if "```" in out:
    out=out.split("```")[1]; out=out.split("\n",1)[1] if out.split("\n",1)[0].strip() in ("html","") else out
pathlib.Path("/tmp/voxel10.html").write_text(out)
u=r.get("usage",{}); print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
for k in ("demo=1","demoStep","headBob","swordSwings","enemiesKilled","dodge"):
    print(f"  {'ok ' if k.lower() in out.lower() else 'MISSING'} {k}")
