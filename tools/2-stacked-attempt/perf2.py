#!/usr/bin/env python3
"""Round 12: the InstancedMesh rewrite broke the world with a hallucinated API. Feed it back."""
import json, time, urllib.request, pathlib

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src = pathlib.Path("/tmp/voxel11.html").read_text()
P = """Your InstancedMesh rewrite BROKE the world. Its own metrics now report:

METRICS {"fps":11,"blocks":0,"blocksDrawn":0,"biomes":{"grass":0,"sand":0,"stone":0,"snow":0,"water":0},"treesPlaced":0,"errors":["Uncaught TypeError: matrix.setScale is not a function"]}

Two things are wrong and the first causes the second:

1. `matrix.setScale` DOES NOT EXIST in three.js. THREE.Matrix4 has no setScale method. To hide an instance, compose the matrix properly, for example:
     const m = new THREE.Matrix4();
     m.compose(position, new THREE.Quaternion(), new THREE.Vector3(0,0,0));   // zero scale hides it
     mesh.setMatrixAt(i, m);
     mesh.instanceMatrix.needsUpdate = true;
   and to show a block use scale (1,1,1) with its world position. Use only real three.js APIs: Matrix4.compose, Matrix4.makeTranslation, Object3D.matrix + updateMatrix, InstancedMesh.setMatrixAt, InstancedMesh.count.

2. Because that threw during world generation, zero blocks were ever created: blocks, blocksDrawn and every biome count are 0. After fixing the API, the world must generate again - blocks and blocksDrawn must be non-zero, and the biome counts must be non-zero for grass, sand, stone, water AND snow.

Note that fps "improved" from 6 to 11 only because nothing is being drawn. Do not treat that as success. The target is a world that actually renders AND a higher frame rate, achieved by:
  - one InstancedMesh per block type, sharing one BoxGeometry
  - skipping blocks whose six neighbours are all solid (they are never visible)
  - reporting blocksDrawn as the number of instances actually created

Keep every feature: biomes, trees, NPCs, enemies, combat, guard, dodge, sprint, day/night, clouds, demo mode, METRICS. Return the COMPLETE HTML only.

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
pathlib.Path("/tmp/voxel12.html").write_text(out)
u = r.get("usage", {})
print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
print("  setScale still present:", "setscale" in out.lower())
print("  uses compose:", "compose(" in out)
