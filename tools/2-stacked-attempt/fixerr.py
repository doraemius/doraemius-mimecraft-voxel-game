import json,time,urllib.request,pathlib
KEY=open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src=pathlib.Path("/tmp/voxel6.html").read_text()
P=("""This page throws immediately and renders a black screen:

Uncaught TypeError: Cannot read properties of undefined (reading 'color')  at line 291

Line 291 is:  material = materials[blockTypes[blockType].color];

blockTypes[blockType] is undefined, so the block-type lookup and the materials table disagree. Fix the data model so every terrain column resolves to a real block type and a real material: make blockTypes a plain array indexed 0..n-1, make materials keyed the same way, and clamp or map any computed biome value into that range. Make sure water, sand, grass, stone and snow all resolve.

Return the COMPLETE corrected HTML only."""+"\n\n"+src)
body={"model":"x","messages":[{"role":"user","content":P}],"temperature":0.2,"max_tokens":14000}
req=urllib.request.Request("http://localhost:8080/v1/chat/completions",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
t0=time.time(); r=json.load(urllib.request.urlopen(req,timeout=3600)); dt=time.time()-t0
out=r["choices"][0]["message"]["content"]
if "```" in out:
    out=out.split("```")[1]; out=out.split("\n",1)[1] if out.split("\n",1)[0].strip() in ("html","") else out
pathlib.Path("/tmp/voxel7.html").write_text(out)
u=r.get("usage",{}); print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
