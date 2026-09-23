#!/usr/bin/env python3
"""Round 11: ask the model to fix its own rendering bottleneck (one Mesh per block)."""
import json, time, urllib.request, pathlib

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
src = pathlib.Path("/tmp/voxel10.html").read_text()
P = """This game runs at 6 frames per second. Its own metrics report blocks:23675, and it creates one THREE.Mesh per block. That is the bottleneck: 23,675 draw calls per frame.

Fix the rendering, changing nothing about gameplay:

1. Use THREE.InstancedMesh - ONE InstancedMesh per block type (grass, dirt, sand, stone, snow, water, wood, leaves). Each block becomes an instance matrix on the right mesh, not its own Mesh object. Share one BoxGeometry across all of them.
2. Do not create instances for blocks that are completely buried: a block with solid neighbours on all six sides is never visible, so skip it. Report the number actually drawn as a new metric blocksDrawn.
3. Block removal and placement must still work: keep a map from world coordinate to (instancedMesh, instanceIndex) so a removed block can be hidden by writing a zero-scale matrix and setting instanceMatrix.needsUpdate = true.
4. Keep the raycaster working for block selection against the instanced meshes (Raycaster reports instanceId on intersections - use it).

Keep every other feature exactly as it is: biomes, trees, NPCs, enemies, combat, guard, dodge, sprint, day/night, clouds, demo mode and the METRICS line. Add blocksDrawn to METRICS.

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
pathlib.Path("/tmp/voxel11.html").write_text(out)
u = r.get("usage", {})
print(f"{u.get('completion_tokens',0)} tok in {dt:.0f}s = {u.get('completion_tokens',0)/dt:.1f} tok/s")
print("  InstancedMesh:", "instancedmesh" in out.lower(),
      "| blocksDrawn:", "blocksdrawn" in out.lower())
