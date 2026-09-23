import json,time,urllib.request,pathlib
KEY=open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src=pathlib.Path("/tmp/voxel4.html").read_text()
P=("This voxel game works. Now make it LOOK good. Keep every feature and keep it one self-contained file.\n"
   "1. Sky: a vertical gradient from deep blue at the top to pale near the horizon, using a large inverted sphere with a ShaderMaterial. Keep fog matching the horizon colour.\n"
   "2. Blocks: give grass a slightly varied green per block (small deterministic jitter from its x,z) so the ground is not one flat colour, and darken the side faces relative to the top.\n"
   "3. Lighting: a warm directional light low in the sky plus cool ambient, so hills cast visible shading.\n"
   "4. Add simple distance fog and a subtle vignette overlay in CSS.\n"
   "5. Trees: place a few simple trunk+leaves block trees on high ground.\n"
   "Return the COMPLETE HTML only.\n\n"+src)
body={"model":"x","messages":[{"role":"user","content":P}],"temperature":0.3,"max_tokens":8000}
req=urllib.request.Request("http://localhost:8080/v1/chat/completions",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
t0=time.time(); r=json.load(urllib.request.urlopen(req,timeout=2400)); dt=time.time()-t0
out=r["choices"][0]["message"]["content"]
if "```" in out:
    out=out.split("```")[1]; out=out.split("\n",1)[1] if out.split("\n",1)[0].strip() in ("html","") else out
pathlib.Path("/tmp/voxel5.html").write_text(out)
u=r.get("usage",{}); print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
