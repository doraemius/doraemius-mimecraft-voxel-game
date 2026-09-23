# Every prompt, in order

Every prompt that produced a build in this repo, copied verbatim from the script that sent it
(`tools/`). Unless noted, each prompt was followed by the current HTML file. Model:
Qwen3-Coder-30B-A3B-Instruct (Q4_K_XL) on llama-server, one RTX 3080, temperature 0.2.

**Count:** 4 prompts on day one, 9 in the stacked attempt, and 22 rounds plus at least 10
retries in the rebuild. Only v1 came from a single prompt.

## Phase 1: day one (`iterations/1-day-one/`)

### v1: one prompt for the whole game

Source: `tools/1-day-one/gen-game.py`

```text
EP007 demo gate: can the local coder build a playable voxel game in one file?

One prompt, no hand-editing. Whatever comes out is what gets filmed.
```

```text
Write a COMPLETE single-file HTML page: a Minecraft-style voxel world using Three.js from a CDN.

Requirements:
- <!DOCTYPE html> with everything inline. No build step, no local files, no imports besides the Three.js CDN script tag.
- A 24x24 world of 1x1x1 blocks with hills from a simple noise function (write your own, do not import noise libraries). Grass blocks on top, dirt below.
- Colours: grass green top blocks, brown dirt, a sky-blue background, and a directional light plus ambient light so faces are shaded differently.
- Pointer-lock first-person controls: WASD to move, mouse to look, Space to jump with simple gravity.
- Left click removes the block you are looking at, right click places one. Use a Raycaster.
- A crosshair in the centre and a small instructions overlay in the corner.
- Must run by opening the file directly in a browser.

Output ONLY the HTML, no explanation.
```

**Result:** Spawned inside the ground: a brown screen.

### v2: the bug described in plain English

Source: `tools/1-day-one/fix-game.py`

```text
This page runs, but the camera spawns INSIDE the terrain: the whole screen is solid brown dirt and you cannot see the world.

Fix these, and return the COMPLETE corrected HTML file only:
1. Spawn the camera above the highest block at the centre of the world, looking out across it, so the player starts standing on the surface with sky visible.
2. Make sure gravity puts the player ON TOP of the ground rather than falling through or starting buried.
3. Keep the sky visible: the background should be sky blue and the horizon should be in view at spawn.
4. Keep every existing feature: WASD, mouse look, jump, block remove/place, crosshair, overlay.

Here is the current file:
```

**Result:** Still buried. Green instead of brown.

### v3: a vision model's bug report, plus instructions

Source: `tools/1-day-one/fix3.py`

```text
The game's rendering engine has failed to load any terrain or environment assets, resulting in an entirely blank green screen instead of the expected landscape and sky. The cursor and on-screen controls remain visible, indicating that the game is running but unable to render the world properly.
```

```text
"

The screen is filled edge to edge with one flat green colour, the same green as the grass blocks, with no sky and no block edges. The most likely cause is that the camera is positioned INSIDE a block, so the near face of that block fills the frame.

Fix it so the player spawns clearly ABOVE the terrain with sky visible and the landscape in view. Verify your own logic: compute the maximum terrain height at the spawn column and place the camera above it plus player eye height. Return the COMPLETE corrected HTML only.
```

**Result:** Unchanged. The vision model's report (first block) was wrong: the terrain had loaded.

### v4: not a prompt

I changed one line by hand: `camera.lookAt(0, maxHeight, 0)` to `camera.lookAt(10, maxHeight + 1, 10)`. The world had been there all along.

### v5: make it look good

Source: `tools/1-day-one/polish.py`

```text
This voxel game works. Now make it LOOK good. Keep every feature and keep it one self-contained file.
1. Sky: a vertical gradient from deep blue at the top to pale near the horizon, using a large inverted sphere with a ShaderMaterial. Keep fog matching the horizon colour.
2. Blocks: give grass a slightly varied green per block (small deterministic jitter from its x,z) so the ground is not one flat colour, and darken the side faces relative to the top.
3. Lighting: a warm directional light low in the sky plus cool ambient, so hills cast visible shading.
4. Add simple distance fog and a subtle vignette overlay in CSS.
5. Trees: place a few simple trunk+leaves block trees on high ground.
Return the COMPLETE HTML only.
```

**Result:** Sky, vignette and shading land. Some trees float.

## Phase 2: the stacked attempt (`iterations/2-stacked-attempt/`)

Several features per prompt, verified from a METRICS line the game printed about itself. From v6 on, the screen showed no world at all while the numbers looked fine.

### v6: biomes, a held block, fix floating trees

Source: `tools/2-stacked-attempt/improve.py`

```text
This voxel game works but the world looks plain and it does not read as a playable game. Improve it. Keep it ONE self-contained HTML file and keep every existing control.

1. TERRAIN VARIETY. Make the world 40x40 and add biomes driven by a second low-frequency noise value: sand near low ground, grass in the middle, bare stone on high ground, and snow on the highest peaks. Add a water level: any column below the water height gets translucent blue water blocks on top.
2. MORE BLOCK COLOURS. Use distinct colours for grass, dirt, sand, stone, snow, water and wood. Keep the darker side faces.
3. IT MUST LOOK PLAYABLE. Add a block-selection outline: a thin black wireframe box drawn on whatever block the crosshair is pointing at, updated every frame with the Raycaster.
4. ADD A HELD BLOCK. Draw a small cube in the bottom-right of the view, fixed to the camera, showing the block type that will be placed. Number keys 1-5 switch the selected block type and the held cube updates.
5. TREES: place trees ONLY on grass columns, and anchor the trunk base exactly on the surface height of that column. Some trees are currently floating in the air with no ground beneath them - fix that.

Return the COMPLETE HTML only.
```

### v7: a pasted TypeError

Source: `tools/2-stacked-attempt/fixerr.py`

```text
This page throws immediately and renders a black screen:

Uncaught TypeError: Cannot read properties of undefined (reading 'color')  at line 291

Line 291 is:  material = materials[blockTypes[blockType].color];

blockTypes[blockType] is undefined, so the block-type lookup and the materials table disagree. Fix the data model so every terrain column resolves to a real block type and a real material: make blockTypes a plain array indexed 0..n-1, make materials keyed the same way, and clamp or map any computed biome value into that range. Make sure water, sand, grass, stone and snow all resolve.

Return the COMPLETE corrected HTML only.
```

### v8: everything at once, plus self-reporting metrics

Source: `tools/2-stacked-attempt/bigask.py`

```text
Extend this voxel game. Keep ONE self-contained HTML file, keep every existing control, and keep it runnable by opening the file.

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
```

### v9: the three wrong metrics

Source: `tools/2-stacked-attempt/fixmetrics.py`

```text
Your game now reports its own metrics. Here is the first real report from a running session:

METRICS {"fps":18,"blocks":23673,"biomes":{"grass":1349,"sand":294,"stone":187,"snow":0,"water":1307},"treesPlaced":9,"treesFloating":513,"cameraInsideBlock":false,"skyPixelsVisible":false,"npcCount":4,"enemyCount":3,"playerHp":20,"enemyHpTotal":30,"errors":[]}

Three of those numbers are wrong. Fix the CAUSES, not the numbers:

1. treesFloating is 513 while treesPlaced is 9. A count of floating trees can never exceed the number of trees. Your check is counting the wrong thing - probably every leaf block, or every block with air beneath it anywhere in the world. Rewrite it so it evaluates exactly one thing per tree: does the trunk's base block have a solid block directly below it. Then make the number actually be 0 by anchoring every trunk base to that column's surface height.

2. snow is 0. The snow biome never generates. Your height thresholds must leave a real band of columns above the stone threshold. Print nothing - just make the terrain actually produce snow columns, and keep sand, grass, stone and water too.

3. skyPixelsVisible is false. The player spawns without the horizon in view. The camera must start above the surface looking OUT across the world, not down at it. Remember: setting camera.lookAt to a point directly below the camera fills the screen with one block face.

Also raise fps if you can do it cheaply: only build meshes for block faces that are exposed to air, and reuse one geometry and one material per block type across all instances.

Keep every feature: biomes, NPCs, enemies, combat, guard, dodge, sprint, day/night, clouds, and the METRICS line. Return the COMPLETE HTML only.
```

### v10: a self-playing demo mode

Source: `tools/2-stacked-attempt/autoplay.py`

```text
Add a DEMO MODE to this game so it can play itself for a video recording. Keep everything else working.

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
```

### v11: InstancedMesh for performance

Source: `tools/2-stacked-attempt/perf.py`

```text
This game runs at 6 frames per second. Its own metrics report blocks:23675, and it creates one THREE.Mesh per block. That is the bottleneck: 23,675 draw calls per frame.

Fix the rendering, changing nothing about gameplay:

1. Use THREE.InstancedMesh - ONE InstancedMesh per block type (grass, dirt, sand, stone, snow, water, wood, leaves). Each block becomes an instance matrix on the right mesh, not its own Mesh object. Share one BoxGeometry across all of them.
2. Do not create instances for blocks that are completely buried: a block with solid neighbours on all six sides is never visible, so skip it. Report the number actually drawn as a new metric blocksDrawn.
3. Block removal and placement must still work: keep a map from world coordinate to (instancedMesh, instanceIndex) so a removed block can be hidden by writing a zero-scale matrix and setting instanceMatrix.needsUpdate = true.
4. Keep the raycaster working for block selection against the instanced meshes (Raycaster reports instanceId on intersections - use it).

Keep every other feature exactly as it is: biomes, trees, NPCs, enemies, combat, guard, dodge, sprint, day/night, clouds, demo mode and the METRICS line. Add blocksDrawn to METRICS.

Return the COMPLETE HTML only.
```

### v12: the hallucinated setScale API

Source: `tools/2-stacked-attempt/perf2.py`

```text
Your InstancedMesh rewrite BROKE the world. Its own metrics now report:

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
```

### (lost): a self-evaluation system designed by the model

Source: `tools/2-stacked-attempt/roundA.py`

```text
This voxel game renders correctly. Before adding any features, give it a way to prove it is still working.

Design and add a SELF-EVALUATION system. You decide what to check and what to call things. The requirements are only these:

- It must run periodically WHILE the game is playing (not once at startup), at an interval you choose.
- Each run must decide, from the real state of the scene, whether the game is actually working, and emit ONE line to the console beginning with the word EVAL followed by JSON.
- That JSON must include an overall verdict field whose value is "ok" or "bad", and a list of individual named checks with their pass/fail and the measured value that decided it.
- The single most important check: the player can actually SEE the world. A count of blocks in a data structure does not prove anything is on screen - a previous version reported thousands of blocks while rendering a blank grey screen. Find a way to verify that geometry is genuinely being rendered and visible from the current camera, and report the number actually drawn.
- Other checks are your choice. Think about what could silently break in a voxel game: the camera ending up inside geometry or aimed at nothing, terrain failing to generate, objects placed with nothing beneath them, the frame rate collapsing, an exception swallowed somewhere.
- If any check fails, the verdict is "bad" and the failing check must say why in plain words.

Do not change how the game looks or plays. Return the COMPLETE HTML only.
```

**Result:** the output file was not kept.

### v13: remove all the metrics code

Source: `tools/2-stacked-attempt/strip.py`

```text
Remove ALL of the self-evaluation and metrics code from this game. It is buggy and it is not wanted.

Specifically delete:
- the window.__metrics object and everything that maintains it
- the METRICS console.log line and its timers
- every counter that exists only to feed those metrics (treesFloating, blocksDrawn, cameraInsideBlock, skyPixelsVisible, fps sampling, biome tallies, and the demo counters jumpsDone / swordSwings / enemiesKilled / blocksBroken / blocksPlaced)
- any window.onerror handler that exists only to collect errors for metrics

Keep EVERYTHING that is actual gameplay: the terrain and biomes, trees, day/night, clouds, NPCs, enemies, combat with sword and guard and dodge and sprint, health, block placing and removing, the HUD text, and the demo mode that plays the game by itself.

Important: the world is currently NOT VISIBLE when the page runs - the screen is flat grey and no terrain appears, even though the code believes it created thousands of blocks. While you remove the metrics code, also make sure the terrain meshes are actually added to the scene and that the camera starts above the ground looking out at the horizon so the landscape and sky are on screen.

Return the COMPLETE HTML only.
```

## Phase 3: the rebuild, one feature per round (`iterations/3-rebuild/`)

Every round was gated on the RENDERED FRAME before it was promoted. Rounds 1-13 appended these standing rules to each prompt:

```text
Return the COMPLETE single-file HTML only, no explanation. Everything inline, three.js from a CDN script tag, runs by opening the file directly. Do NOT add any self-evaluation, metrics or telemetry code.
STANDING RULE - do not regress this: the player must spawn standing on OPEN GRASS with the horizon and sky clearly visible ahead, never inside a block, never pressed against a block face, and never looking straight down or straight up. If terrain changes, recompute the spawn: pick a grass column whose immediate neighbours are not taller than it, place the camera on its surface plus eye height, and face it toward the middle of the map horizontally.
```

### Round 1

```text
one green cube on a sky-blue background, with a PerspectiveCamera 10 units back looking straight at it, an ambient light and a directional light. Nothing else.
```

### Round 2

```text
Extend it: replace the single cube with a FLAT 32x32 floor of 1x1x1 green grass blocks centred on the origin. Put the camera 12 units above the floor near one corner, looking ACROSS the floor toward the opposite corner and slightly down, so both the ground and the sky are visible in the frame.
```

### Round 3

```text
Extend it: give the floor height variation using a simple deterministic noise function you write yourself (no libraries), heights 0 to 8. Grass on the top block of each column, brown dirt blocks below it. Keep the camera above the highest terrain looking out at the horizon.
```

### Round 4

```text
Extend it: add first-person controls. Pointer lock on click, mouse look, WASD movement relative to facing, gravity, and Space to jump. The player must stand ON the terrain surface and never fall through it. Keep the spawn view looking at the horizon.
```

**Retry 4b** (`tools/3-rebuild/retry4.py`), after the player fell through the floor:

```text
Add first-person controls to this terrain. Your previous attempt failed: the player fell THROUGH the terrain and ended up below the world, looking up at the unlit undersides of the blocks.

Requirements, in this order of importance:

1. COLLISION FIRST. Before applying gravity, work out the surface height of the column the player is standing over: scan that column's blocks and take the highest solid y. The player's feet must never go below that surface. Clamp the camera's y to (surfaceHeight + 1 + eyeHeight) whenever it would fall below it, and zero the downward velocity when that happens.
2. SPAWN standing on the surface at the centre of the map, with the camera looking horizontally out across the terrain - not down, not up.
3. Then add: pointer lock on click, mouse look (yaw on the mouse X, pitch on mouse Y, clamped to just under +/- 90 degrees), WASD movement relative to the direction faced, and Space to jump, which sets an upward velocity that gravity brings back down to the surface.
4. The player must also not walk off the edge of the world into the void: clamp x and z to the map bounds.

Keep the terrain generation, colours and sky exactly as they are.

Return the COMPLETE single-file HTML only, no explanation. Do NOT add any self-evaluation, metrics or telemetry code.

Here is the current file:
```

### Round 5

```text
Extend it: add a Raycaster so left click removes the block under the crosshair and right click places one against the face you are pointing at. Draw a small crosshair in the centre of the screen.
```

### Round 6

```text
Extend it: add biomes by height using a second noise value - sand at low elevations, grass in the middle, bare stone high up, snow on the highest peaks, and blue water blocks filling any column below a fixed sea level. Each type gets its own distinct colour.
```

### Round 7

```text
Extend it: place about 12 trees - a brown trunk 4 blocks tall with a green leaf canopy - ONLY on grass columns, with the base of each trunk exactly on that column's surface height so no tree floats in the air.
```

### Round 8

```text
Extend it: improve the lighting. A warm directional light low in the sky plus a cooler ambient light, and make the side faces of every block visibly darker than the top faces so the terrain reads as three-dimensional.
```

### Round 9

```text
Extend it: add a vertical sky gradient (deep blue overhead fading to pale at the horizon), distance fog matching the horizon colour, and a subtle CSS vignette over the canvas.
```

### Rounds 6b, 9b, 10-13: retry notes not preserved

These retries passed a short note on the command line to `game-round-retry.py`, and the notes were not saved. What they asked for is described in `notes/REBUILD-LOG.md`: round 10 sky gradient and fog; round 11 spawn framing (three described attempts failed, then an explicit `camera.position.set(...)` plus `lookAt(...)` formula passed); round 12 terrain coherence (described, failed into stripes); round 13 the literal two-octave `hash2`/`valueNoise` formula, visible as comments in `round-13.html`.

From round 14 the standing rules changed to:

```text
Return the COMPLETE single-file HTML only, no explanation. Everything inline, three.js from a CDN script tag, runs by opening the file directly. Do NOT add any self-evaluation, metrics or telemetry code.
STANDING RULE - do not regress this: leave initPlayer() and the camera spawn formula exactly as they are; the spawn must still show terrain and sky. Keep everything the request does not mention unchanged.
```

### Round 14

```text
Optimise the rendering WITHOUT changing how it looks. Do exactly this:
1. Add at top level: `const world = new Map();` keyed by the string `ix+','+iy+','+iz` (integer cell coords, cell centre = (ix+0.5, iy+0.5, iz+0.5)) with a block type string as the value, and `function setBlock(ix,iy,iz,type){ world.set(ix+','+iy+','+iz, type); }`.
2. In the terrain loop, DELETE every `new THREE.Mesh(...)` and `scene.add(block)`. Instead call setBlock(x - terrainSize/2, y, z - terrainSize/2, type) with type one of 'water','sand','grass','stone','snow' chosen by the existing rules. The water loop also calls setBlock (duplicates simply overwrite).
3. In createTree, DELETE the Mesh creation. Trunk: setBlock(x, surfaceHeight+i, z, 'trunk') for i=0..3. Canopy: setBlock(x+dx, surfaceHeight+4+dy, z+dz, 'leaf') for the same loops.
4. `const MATERIALS = {water: waterMaterial, sand: sandMaterial, grass: grassMaterial, stone: stoneMaterial, snow: snowMaterial, trunk: trunkMaterial, leaf: leafMaterial};` with trunkMaterial (0x8B4513) and leafMaterial (0x228B22) created ONCE at top level.
5. `function covers(k){ const t = world.get(k); return t !== undefined && t !== 'water' && t !== 'leaf'; }` A block is HIDDEN when covers() is true for all six neighbour keys (ix±1, iy±1, iz±1).
6. `let instancedMeshes = [];` and `function rebuildMeshes()`: remove every mesh in instancedMeshes from the scene and call its .dispose(); group the keys of NON-hidden blocks by type; for each type create `new THREE.InstancedMesh(blockGeometry, MATERIALS[type], keys.length)`, and for instance i parse keys[i] to ix,iy,iz, set a reusable `const dummy = new THREE.Object3D()` position to (ix+0.5, iy+0.5, iz+0.5), call dummy.updateMatrix() and mesh.setMatrixAt(i, dummy.matrix); then mesh.instanceMatrix.needsUpdate = true; mesh.userData.keys = keys; scene.add(mesh); instancedMeshes.push(mesh). Call rebuildMeshes() once after terrain and trees are generated.
7. In the mousedown handler use `raycaster.intersectObjects(instancedMeshes)`. With hit = intersects[0], key = hit.object.userData.keys[hit.instanceId]. Left click: world.delete(key); rebuildMeshes(). Right click: parse key to ix,iy,iz, add Math.round of hit.face.normal.x/y/z to it, setBlock(that, 'sand'); rebuildMeshes().
Keep terrain[][], getSurfaceHeight, getCeilingHeight, sky, fog, lights and initPlayer unchanged.
```

**Targeted retry 14b**, on the round's first candidate (`attempts/round-14-a.html`):

```text
Two exact changes to rebuildMeshes(), nothing else:
1. DELETE the line `if (type === 'water' || type === 'leaf') continue;`. It stops every water and leaf block from being drawn, so the lake and every tree canopy are currently invisible. Water and leaf blocks MUST be drawn like any other block; covers() only decides whether they hide their NEIGHBOURS.
2. Replace the 3x3x3 dx/dy/dz loop with a check of exactly the SIX face neighbours: const n = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]]; hidden = n.every(([a,b,c]) => covers((ix+a)+','+(iy+b)+','+(iz+c)));
```

### Round 15

```text
Add 4 wandering NPCs. Do exactly this, and change nothing else:
1. `const npcs = [];` and `function makeNPC(color)` returning a THREE.Group with a body BoxGeometry(0.6, 1.0, 0.4) in MeshPhongMaterial({color}) at y=0.5 and a head BoxGeometry(0.5, 0.5, 0.5) in MeshPhongMaterial({color: 0xFFCC99}) at y=1.25. The group origin is at the feet.
2. After rebuildMeshes() is first called, spawn them: colours [0xE53935, 0x1E88E5, 0xFDD835, 0x8E24AA]; `for (let i = 0; i < terrainSize*terrainSize && npcs.length < 4; i += 37) { const gx = i % terrainSize, gz = Math.floor(i / terrainSize), h = terrain[gx][gz]; if (h >= waterLevel+1 && h < waterLevel+3) { ... } }` where ... makes an NPC, sets group.position to (gx - terrainSize/2 + 0.5, h, gz - terrainSize/2 + 0.5), adds it to the scene and pushes `{group, heading: 0, frame: 0, idx: npcs.length}`.
3. `function isFree(wx, wy, wz)` returns !world.has(Math.floor(wx)+','+Math.floor(wy)+','+Math.floor(wz)).
4. `function updateNPCs()`, called EVERY frame in animate() OUTSIDE the `if (mouseLocked)` block: for each npc: npc.frame++; if (npc.frame % 120 === 1) npc.heading = hash2(npc.idx * 7 + 1, Math.floor(npc.frame / 120)) * Math.PI * 2; const p = npc.group.position, nx = p.x + Math.cos(npc.heading) * 0.03, nz = p.z + Math.sin(npc.heading) * 0.03; const th = getSurfaceHeight(nx, nz); const ok = Math.abs(nx) < terrainSize/2 - 1 && Math.abs(nz) < terrainSize/2 - 1 && th >= waterLevel + 1 && th - p.y <= 1 && isFree(nx, th + 0.5, nz) && isFree(nx, th + 1.5, nz); if (ok) { p.x = nx; p.z = nz; p.y = th; npc.group.rotation.y = Math.atan2(Math.cos(npc.heading), Math.sin(npc.heading)); } else { npc.heading += Math.PI / 2; }
Keep terrain, world, rebuildMeshes, the raycaster, sky, fog, lights and initPlayer unchanged.
```

### Round 16

```text
Add a player health bar and a held sword that swings. Do exactly this, change nothing else:
1. HTML: `<div id="hp"><div id="hpfill"></div></div>` in body. CSS: #hp {position:absolute; left:20px; bottom:20px; width:200px; height:16px; border:2px solid #000; background:#400; z-index:101;} #hpfill {height:100%; width:100%; background:#e33;}
2. JS: `const PLAYER_MAX_HP = 20; let playerHP = 20; function updateHPBar(){ document.getElementById('hpfill').style.width = (playerHP / PLAYER_MAX_HP * 100) + '%'; }` and call updateHPBar() once at startup.
3. Sword: `const sword = new THREE.Group();` with a blade BoxGeometry(0.06, 0.6, 0.02) color 0xDDDDDD at y=0.32, a crossguard BoxGeometry(0.22, 0.05, 0.06) color 0x8B4513 at y=0, a grip BoxGeometry(0.05, 0.16, 0.05) color 0x5A3A1A at y=-0.1, all MeshPhongMaterial. `sword.position.set(0.38, -0.32, -0.7); sword.rotation.z = -0.35; camera.add(sword); scene.add(camera);` (a camera's children are only rendered when the camera itself is in the scene).
4. Swing: `let swingFrame = 0; function swingSword(){ if (swingFrame === 0) swingFrame = 1; }`. In the mousedown handler, when event.button === 0, call swingSword() in addition to the existing block removal. In animate(), OUTSIDE the `if (mouseLocked)` block: `if (swingFrame > 0) { sword.rotation.x = -Math.sin(swingFrame / 15 * Math.PI) * 1.2; swingFrame++; if (swingFrame > 15) { swingFrame = 0; sword.rotation.x = 0; } }`.
Keep terrain, world, rebuildMeshes, NPCs, sky, fog, lights and initPlayer unchanged.
```

### Round 17

```text
Add 3 hostile enemies. Do exactly this, change nothing else:
1. `const enemies = []; let damageCooldown = 0;` and `function makeEnemy()` returning {group, body}: a THREE.Group with a body BoxGeometry(0.7, 1.1, 0.5) MeshPhongMaterial color 0x333333 at y=0.55 and a head BoxGeometry(0.55, 0.55, 0.55) color 0x7CB342 at y=1.38.
2. Spawn right after the NPCs, with the SAME scan as spawnNPCs but starting at i = 11 and stepping i += 53, until enemies.length === 3. Same position formula. Push `{group, body, hp: 3, flash: 0}`.
3. `function updateEnemies()`, called every frame in animate() OUTSIDE the `if (mouseLocked)` block, right after updateNPCs(): `if (damageCooldown > 0) damageCooldown--;` then for each enemy e with p = e.group.position: `const dx = player.position.x - p.x, dz = player.position.z - p.z, dist = Math.hypot(dx, dz);` if (dist < 10 && dist > 0.8) { const nx = p.x + dx / dist * 0.025, nz = p.z + dz / dist * 0.025, th = getSurfaceHeight(nx, nz); if (th >= waterLevel + 1 && th - p.y <= 1 && isFree(nx, th + 0.5, nz) && isFree(nx, th + 1.5, nz)) { p.x = nx; p.z = nz; p.y = th; } } e.group.rotation.y = Math.atan2(dx, dz); if (dist < 1.0 && Math.abs(player.position.y - player.eyeHeight - p.y) < 1.5 && damageCooldown === 0) { playerHP = Math.max(0, playerHP - 2); updateHPBar(); damageCooldown = 60; } e.body.material.emissive.setHex(e.flash > 0 ? 0xff0000 : 0x000000); if (e.flash > 0) e.flash--;
4. Hitting: `function hitEnemies()`: `const f = new THREE.Vector3(); camera.getWorldDirection(f); f.y = 0; f.normalize();` then iterate enemies BACKWARDS (for i = enemies.length-1 down to 0): dx, dz from player to enemy as above, dist = Math.hypot(dx, dz); if (dist < 2.5 && (dx * f.x + dz * f.z) / dist > 0.5) { e.hp--; e.flash = 10; if (e.hp <= 0) { scene.remove(e.group); enemies.splice(i, 1); } }. In swingSword(), call hitEnemies() only when a new swing starts, i.e. inside the `if (swingFrame === 0)` branch.
Keep terrain, world, rebuildMeshes, NPCs, sword, health bar, sky, fog, lights and initPlayer unchanged.
```

**Targeted retry 17b**, on the round's first candidate (`attempts/round-17-a.html`):

```text
One exact change, nothing else: hitEnemies() is defined but never called, so the sword can never damage an enemy. Replace swingSword() with exactly:
function swingSword(){
    if (swingFrame === 0) {
        swingFrame = 1;
        hitEnemies();
    }
}
```

### Round 18

```text
Fix two movement bugs. Exactly these changes, nothing else:
1. W currently moves the player BACKWARD: a three.js camera looks down its local -Z axis, but the movement code uses `new THREE.Vector3(0, 0, 1)` as forward. Change that forward vector to `new THREE.Vector3(0, 0, -1)`. Leave the right vector `(1, 0, 0)` as it is.
2. Mouse look uses the default 'XYZ' Euler order, which skews yaw once the view is pitched. Immediately after the camera is created add `camera.rotation.order = 'YXZ';` and in the player object set `rotation: new THREE.Euler(0, 0, 0, 'YXZ')`.
Keep everything else, including initPlayer, unchanged.
```

### Round 19

```text
Add guard, sprint and dodge. Exactly these changes, nothing else:
1. Globals: `let guarding = false, sprinting = false, dodgeFrames = 0, invulnFrames = 0, frameCount = 0; const dodgeVec = new THREE.Vector3(); const lastTap = {w: -100, a: -100, s: -100, d: -100};`
2. `function setGuard(on){ guarding = on; sword.position.x = on ? 0.1 : 0.38; sword.rotation.z = on ? -1.3 : -0.35; }` `function setSprint(on){ sprinting = on; }` `function startDodge(k){ if (dodgeFrames > 0) return; const f = new THREE.Vector3(0, 0, -1).applyEuler(player.rotation); f.y = 0; f.normalize(); const r = new THREE.Vector3(1, 0, 0).applyEuler(player.rotation); r.y = 0; r.normalize(); if (k === 'w') dodgeVec.copy(f); else if (k === 's') dodgeVec.copy(f).negate(); else if (k === 'd') dodgeVec.copy(r); else dodgeVec.copy(r).negate(); dodgeFrames = 12; invulnFrames = 18; }`
3. keydown handler, after the mouseLocked check and before the switch: `const k = event.key.toLowerCase(); if (k.length === 1 && 'wasd'.includes(k) && !event.repeat) { if (frameCount - lastTap[k] < 15) startDodge(k); lastTap[k] = frameCount; }` and add cases `case 'f': setGuard(true); break;` and `case 'shift': setSprint(true); break;`. keyup handler: add `case 'f': setGuard(false); break;` and `case 'shift': setSprint(false); break;`.
4. animate(): first line `frameCount++;`. Outside the `if (mouseLocked)` block: `if (invulnFrames > 0) invulnFrames--;`. Inside it, change `moveVector.multiplyScalar(moveSpeed * 0.016)` to `moveVector.multiplyScalar(moveSpeed * (sprinting ? 1.8 : 1) * (guarding ? 0.5 : 1) * 0.016)`, and right after `player.position.z += moveVector.z;` add `if (dodgeFrames > 0) { player.position.x += dodgeVec.x * 0.35; player.position.z += dodgeVec.z * 0.35; dodgeFrames--; }`.
5. In updateEnemies() replace `playerHP = Math.max(0, playerHP - 2); updateHPBar();` with `if (invulnFrames === 0) { playerHP = Math.max(0, playerHP - (guarding ? 1 : 2)); updateHPBar(); }` and keep `damageCooldown = 60;`.
Keep everything else unchanged.
```

**Targeted retry 19b**, on the round's first candidate (`attempts/round-19-a.html`):

```text
One exact change, nothing else: the line requestAnimationFrame(animate); was deleted from the top of animate(), so the game renders ONE frame and then freezes. The top of animate() must be exactly:
        function animate() {
            requestAnimationFrame(animate);
            frameCount++;
```

### Round 20

```text
Add a self-playing demo mode for ?demo=1. Exactly these changes, nothing else:
1. Near the top of the script: `const DEMO = new URLSearchParams(location.search).get('demo') === '1'; let demoFrame = 0;`
2. At the very end of the script, after animate() is first called, add: `if (DEMO) { mouseLocked = true; const s = enemies[0].group.position; player.position.set(s.x, s.y + player.eyeHeight + 2, s.z + 7); player.velocity.set(0, 0, 0); player.rotation.set(-0.12, 0, 0, 'YXZ'); }` (mouseLocked only enables physics; never call requestPointerLock in demo).
3. `function demoTurnTo(yaw, pitch){ player.rotation.y += (yaw - player.rotation.y) * 0.08; player.rotation.x += (pitch - player.rotation.x) * 0.08; }` and `function demoYawTo(x, z){ return Math.atan2(-(x - player.position.x), -(z - player.position.z)); }`
4. `function demoStep(){` with `const f = ++demoFrame;` then exactly this timeline (f is a frame number):
   f === 60: moveState.forward = true;
   f === 150 || f === 240: if (player.onGround) { player.velocity.y = jumpForce; player.onGround = false; }
   f === 300: setSprint(true);   f === 420: setSprint(false);
   f === 480: moveState.forward = false;
   f >= 480 && f < 540 && enemies.length: demoTurnTo(demoYawTo(enemies[0].group.position.x, enemies[0].group.position.z), -0.15);
   f === 540 || f === 575 || f === 610: swingSword();
   f === 660: setGuard(true);   f === 780: setGuard(false);
   f === 820: startDodge('a');
   f >= 900 && f < 960: demoTurnTo(player.rotation.y, -0.7);
   f === 960: document.dispatchEvent(new MouseEvent('mousedown', {button: 0, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));
   f === 1020: document.dispatchEvent(new MouseEvent('mousedown', {button: 2, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));
   f >= 1080 && f < 1140: demoTurnTo(player.rotation.y, -0.1);
   f === 1140: moveState.forward = true;
   f >= 1140 && f < 2100: player.rotation.y += 0.004;
   f === 2100: moveState.forward = false;
   `}`
5. In animate(), right after `frameCount++;` add `if (DEMO) demoStep();`. After the line that copies player.position into camera.position add `if (DEMO && (moveState.forward) && player.onGround) camera.position.y += Math.sin(demoFrame * 0.25) * 0.05;` (head-bob).
Keep everything else unchanged.
```

### Round 21

```text
Replace the demo choreography. The current one walks the player into the world edge, where all three enemies pin them to 0 HP. Exactly these changes, nothing else:
1. In the `if (DEMO) { ... }` block at the end, replace the three player lines with: `player.position.set(11.5, getSurfaceHeight(11.5, 5.5) + player.eyeHeight + 0.5, 5.5); player.velocity.set(0, 0, 0); player.rotation.set(-0.12, demoYawTo(11.5, -8), 0, 'YXZ');` (keep `mouseLocked = true;`).
2. Add `const DEMO_PATHS = [[[11.5, -8], [4, -11], [-2, -9.5]], [[-8, -1], [-7, 7], [3, 7.5], [10, 6]]]; let demoPath = null, demoWp = 0;` and
`function demoWalk(){ if (!demoPath) return; const t = demoPath[demoWp]; if (Math.hypot(t[0] - player.position.x, t[1] - player.position.z) < 0.8) { demoWp++; if (demoWp >= demoPath.length) { demoPath = null; moveState.forward = false; return; } } const w = demoPath[demoWp]; demoTurnTo(demoYawTo(w[0], w[1]), -0.12); moveState.forward = true; }`
`function demoNearest(){ let best = null, bd = 1e9; for (const e of enemies) { const d = Math.hypot(e.group.position.x - player.position.x, e.group.position.z - player.position.z); if (d < bd) { bd = d; best = e; } } return best; }`
3. Replace the whole body of demoStep() after `const f = ++demoFrame;` with exactly:
   demoWalk();
   if (f === 60) { demoPath = DEMO_PATHS[0]; demoWp = 0; }
   if ((f === 150 || f === 230) && player.onGround) { player.velocity.y = jumpForce; player.onGround = false; }
   if (f === 260) setSprint(true);   if (f === 380) setSprint(false);
   if (f >= 480 && f < 940) { demoPath = null; moveState.forward = false; const e = demoNearest(); if (e) demoTurnTo(demoYawTo(e.group.position.x, e.group.position.z), -0.2); }
   if (f === 520 || f === 560 || f === 720 || f === 760 || f === 860 || f === 900) swingSword();
   if (f === 600) setGuard(true);   if (f === 700) setGuard(false);
   if (f === 800) startDodge('a');
   if (f === 960) { demoPath = [DEMO_PATHS[1][0]]; demoWp = 0; }
   if (f >= 1150 && f < 1210) { demoPath = null; moveState.forward = false; demoTurnTo(player.rotation.y, -0.75); }
   if (f === 1210) document.dispatchEvent(new MouseEvent('mousedown', {button: 0, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));
   if (f === 1290) document.dispatchEvent(new MouseEvent('mousedown', {button: 2, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));
   if (f >= 1350 && f < 1400) demoTurnTo(player.rotation.y, -0.12);
   if (f === 1400) { demoPath = DEMO_PATHS[1].slice(1); demoWp = 0; }
Keep demoTurnTo, demoYawTo, the head-bob line and everything else unchanged.
```

**Targeted retry 21b**, on the round's first candidate (`attempts/round-21-a.html`):

```text
Two exact changes, nothing else:
1. demoTurnTo does not wrap angles, so near yaw = +/-PI it turns the long way and walks the wrong direction. Replace its first line with exactly:
            let d = yaw - player.rotation.y; d = Math.atan2(Math.sin(d), Math.cos(d)); player.rotation.y += d * 0.08;
   (keep the pitch line unchanged).
2. In demoStep replace   if (f === 800) startDodge('a');   with   if (f === 920) startDodge('s');
```

### Round 22

```text
Enemies stop so close that on screen their body fills the whole view. Exactly these changes in updateEnemies(), nothing else: change `dist > 0.8` to `dist > 1.6`, and change `dist < 1.0` (the contact-damage test) to `dist < 1.8`.
```
