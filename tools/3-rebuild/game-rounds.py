#!/usr/bin/env python3
"""Rebuild the voxel game one feature per round, gating each on PIXELS before promoting it.

    python3 rounds.py 1          run round 1 (from scratch)
    python3 rounds.py 5          run round 5 on top of the last PASSING file

State: /tmp/vox/goodN.html is the last build that passed the gate. A round that fails is
kept as /tmp/vox/failN.html and the good file is NOT advanced, so the next round always
builds on something known to render.

Why this exists: a previous attempt stacked six features into one round and then spent
seven rounds unable to tell which one made the world invisible.
"""
import json, pathlib, subprocess, sys, time, urllib.request

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
URL = "http://localhost:8080/v1/chat/completions"
D = pathlib.Path("/tmp/vox"); D.mkdir(exist_ok=True)
GATE = "/tmp/game-gate-linux.py"

BASE_RULES = (
    "Return the COMPLETE single-file HTML only, no explanation. Everything inline, "
    "three.js from a CDN script tag, runs by opening the file directly. "
    "Do NOT add any self-evaluation, metrics or telemetry code.\n"
    "STANDING RULE - do not regress this: leave initPlayer() and the camera spawn formula "
    "exactly as they are; the spawn must still show terrain and sky. Keep everything the "
    "request does not mention unchanged.")

ROUNDS = {
 1: ("one green cube on a sky-blue background, with a PerspectiveCamera 10 units back looking "
     "straight at it, an ambient light and a directional light. Nothing else.", ""),
 2: ("Extend it: replace the single cube with a FLAT 32x32 floor of 1x1x1 green grass blocks "
     "centred on the origin. Put the camera 12 units above the floor near one corner, looking "
     "ACROSS the floor toward the opposite corner and slightly down, so both the ground and the "
     "sky are visible in the frame.", "demo"),
 3: ("Extend it: give the floor height variation using a simple deterministic noise function you "
     "write yourself (no libraries), heights 0 to 8. Grass on the top block of each column, "
     "brown dirt blocks below it. Keep the camera above the highest terrain looking out at the "
     "horizon.", ""),
 4: ("Extend it: add first-person controls. Pointer lock on click, mouse look, WASD movement "
     "relative to facing, gravity, and Space to jump. The player must stand ON the terrain "
     "surface and never fall through it. Keep the spawn view looking at the horizon.", ""),
 5: ("Extend it: add a Raycaster so left click removes the block under the crosshair and right "
     "click places one against the face you are pointing at. Draw a small crosshair in the centre "
     "of the screen.", ""),
 6: ("Extend it: add biomes by height using a second noise value - sand at low elevations, grass "
     "in the middle, bare stone high up, snow on the highest peaks, and blue water blocks filling "
     "any column below a fixed sea level. Each type gets its own distinct colour.", ""),
 7: ("Extend it: place about 12 trees - a brown trunk 4 blocks tall with a green leaf canopy - "
     "ONLY on grass columns, with the base of each trunk exactly on that column's surface height "
     "so no tree floats in the air.", ""),
 8: ("Extend it: improve the lighting. A warm directional light low in the sky plus a cooler "
     "ambient light, and make the side faces of every block visibly darker than the top faces so "
     "the terrain reads as three-dimensional.", ""),
 9: ("Extend it: add a vertical sky gradient (deep blue overhead fading to pale at the horizon), "
     "distance fog matching the horizon colour, and a subtle CSS vignette over the canvas.", ""),
 # Rounds 10-13 were spent on fixes (sky/fog relit, spawn formula, terrain formula) via
 # game-round-retry.py with notes; see local-coder/REBUILD-LOG.md. good13 is the base.
 14: ("Optimise the rendering WITHOUT changing how it looks. Do exactly this:\n"
      "1. Add at top level: `const world = new Map();` keyed by the string `ix+','+iy+','+iz` "
      "(integer cell coords, cell centre = (ix+0.5, iy+0.5, iz+0.5)) with a block type string "
      "as the value, and `function setBlock(ix,iy,iz,type){ world.set(ix+','+iy+','+iz, type); }`.\n"
      "2. In the terrain loop, DELETE every `new THREE.Mesh(...)` and `scene.add(block)`. Instead "
      "call setBlock(x - terrainSize/2, y, z - terrainSize/2, type) with type one of "
      "'water','sand','grass','stone','snow' chosen by the existing rules. The water loop also "
      "calls setBlock (duplicates simply overwrite).\n"
      "3. In createTree, DELETE the Mesh creation. Trunk: setBlock(x, surfaceHeight+i, z, 'trunk') "
      "for i=0..3. Canopy: setBlock(x+dx, surfaceHeight+4+dy, z+dz, 'leaf') for the same loops.\n"
      "4. `const MATERIALS = {water: waterMaterial, sand: sandMaterial, grass: grassMaterial, "
      "stone: stoneMaterial, snow: snowMaterial, trunk: trunkMaterial, leaf: leafMaterial};` "
      "with trunkMaterial (0x8B4513) and leafMaterial (0x228B22) created ONCE at top level.\n"
      "5. `function covers(k){ const t = world.get(k); return t !== undefined && t !== 'water' && t !== 'leaf'; }` "
      "A block is HIDDEN when covers() is true for all six neighbour keys (ix±1, iy±1, iz±1).\n"
      "6. `let instancedMeshes = [];` and `function rebuildMeshes()`: remove every mesh in "
      "instancedMeshes from the scene and call its .dispose(); group the keys of NON-hidden blocks "
      "by type; for each type create `new THREE.InstancedMesh(blockGeometry, MATERIALS[type], keys.length)`, "
      "and for instance i parse keys[i] to ix,iy,iz, set a reusable `const dummy = new THREE.Object3D()` "
      "position to (ix+0.5, iy+0.5, iz+0.5), call dummy.updateMatrix() and mesh.setMatrixAt(i, dummy.matrix); "
      "then mesh.instanceMatrix.needsUpdate = true; mesh.userData.keys = keys; scene.add(mesh); "
      "instancedMeshes.push(mesh). Call rebuildMeshes() once after terrain and trees are generated.\n"
      "7. In the mousedown handler use `raycaster.intersectObjects(instancedMeshes)`. With hit = intersects[0], "
      "key = hit.object.userData.keys[hit.instanceId]. Left click: world.delete(key); rebuildMeshes(). "
      "Right click: parse key to ix,iy,iz, add Math.round of hit.face.normal.x/y/z to it, "
      "setBlock(that, 'sand'); rebuildMeshes().\n"
      "Keep terrain[][], getSurfaceHeight, getCeilingHeight, sky, fog, lights and initPlayer unchanged.", ""),
 15: ("Add 4 wandering NPCs. Do exactly this, and change nothing else:\n"
      "1. `const npcs = [];` and `function makeNPC(color)` returning a THREE.Group with a body "
      "BoxGeometry(0.6, 1.0, 0.4) in MeshPhongMaterial({color}) at y=0.5 and a head BoxGeometry(0.5, 0.5, 0.5) "
      "in MeshPhongMaterial({color: 0xFFCC99}) at y=1.25. The group origin is at the feet.\n"
      "2. After rebuildMeshes() is first called, spawn them: colours [0xE53935, 0x1E88E5, 0xFDD835, 0x8E24AA]; "
      "`for (let i = 0; i < terrainSize*terrainSize && npcs.length < 4; i += 37) { const gx = i % terrainSize, "
      "gz = Math.floor(i / terrainSize), h = terrain[gx][gz]; if (h >= waterLevel+1 && h < waterLevel+3) { ... } }` "
      "where ... makes an NPC, sets group.position to (gx - terrainSize/2 + 0.5, h, gz - terrainSize/2 + 0.5), "
      "adds it to the scene and pushes `{group, heading: 0, frame: 0, idx: npcs.length}`.\n"
      "3. `function isFree(wx, wy, wz)` returns !world.has(Math.floor(wx)+','+Math.floor(wy)+','+Math.floor(wz)).\n"
      "4. `function updateNPCs()`, called EVERY frame in animate() OUTSIDE the `if (mouseLocked)` block: for each npc: "
      "npc.frame++; if (npc.frame % 120 === 1) npc.heading = hash2(npc.idx * 7 + 1, Math.floor(npc.frame / 120)) * Math.PI * 2; "
      "const p = npc.group.position, nx = p.x + Math.cos(npc.heading) * 0.03, nz = p.z + Math.sin(npc.heading) * 0.03; "
      "const th = getSurfaceHeight(nx, nz); const ok = Math.abs(nx) < terrainSize/2 - 1 && Math.abs(nz) < terrainSize/2 - 1 "
      "&& th >= waterLevel + 1 && th - p.y <= 1 && isFree(nx, th + 0.5, nz) && isFree(nx, th + 1.5, nz); "
      "if (ok) { p.x = nx; p.z = nz; p.y = th; npc.group.rotation.y = Math.atan2(Math.cos(npc.heading), Math.sin(npc.heading)); } "
      "else { npc.heading += Math.PI / 2; }\n"
      "Keep terrain, world, rebuildMeshes, the raycaster, sky, fog, lights and initPlayer unchanged.", ""),
 16: ("Add a player health bar and a held sword that swings. Do exactly this, change nothing else:\n"
      "1. HTML: `<div id=\"hp\"><div id=\"hpfill\"></div></div>` in body. CSS: #hp {position:absolute; left:20px; "
      "bottom:20px; width:200px; height:16px; border:2px solid #000; background:#400; z-index:101;} "
      "#hpfill {height:100%; width:100%; background:#e33;}\n"
      "2. JS: `const PLAYER_MAX_HP = 20; let playerHP = 20; function updateHPBar(){ "
      "document.getElementById('hpfill').style.width = (playerHP / PLAYER_MAX_HP * 100) + '%'; }` and call updateHPBar() once at startup.\n"
      "3. Sword: `const sword = new THREE.Group();` with a blade BoxGeometry(0.06, 0.6, 0.02) color 0xDDDDDD at y=0.32, "
      "a crossguard BoxGeometry(0.22, 0.05, 0.06) color 0x8B4513 at y=0, a grip BoxGeometry(0.05, 0.16, 0.05) color 0x5A3A1A at y=-0.1, "
      "all MeshPhongMaterial. `sword.position.set(0.38, -0.32, -0.7); sword.rotation.z = -0.35; camera.add(sword); scene.add(camera);` "
      "(a camera's children are only rendered when the camera itself is in the scene).\n"
      "4. Swing: `let swingFrame = 0; function swingSword(){ if (swingFrame === 0) swingFrame = 1; }`. In the mousedown handler, "
      "when event.button === 0, call swingSword() in addition to the existing block removal. In animate(), OUTSIDE the "
      "`if (mouseLocked)` block: `if (swingFrame > 0) { sword.rotation.x = -Math.sin(swingFrame / 15 * Math.PI) * 1.2; "
      "swingFrame++; if (swingFrame > 15) { swingFrame = 0; sword.rotation.x = 0; } }`.\n"
      "Keep terrain, world, rebuildMeshes, NPCs, sky, fog, lights and initPlayer unchanged.", ""),
 17: ("Add 3 hostile enemies. Do exactly this, change nothing else:\n"
      "1. `const enemies = []; let damageCooldown = 0;` and `function makeEnemy()` returning {group, body}: a THREE.Group with a body "
      "BoxGeometry(0.7, 1.1, 0.5) MeshPhongMaterial color 0x333333 at y=0.55 and a head BoxGeometry(0.55, 0.55, 0.55) color 0x7CB342 at y=1.38.\n"
      "2. Spawn right after the NPCs, with the SAME scan as spawnNPCs but starting at i = 11 and stepping i += 53, until enemies.length === 3. "
      "Same position formula. Push `{group, body, hp: 3, flash: 0}`.\n"
      "3. `function updateEnemies()`, called every frame in animate() OUTSIDE the `if (mouseLocked)` block, right after updateNPCs(): "
      "`if (damageCooldown > 0) damageCooldown--;` then for each enemy e with p = e.group.position: "
      "`const dx = player.position.x - p.x, dz = player.position.z - p.z, dist = Math.hypot(dx, dz);` "
      "if (dist < 10 && dist > 0.8) { const nx = p.x + dx / dist * 0.025, nz = p.z + dz / dist * 0.025, th = getSurfaceHeight(nx, nz); "
      "if (th >= waterLevel + 1 && th - p.y <= 1 && isFree(nx, th + 0.5, nz) && isFree(nx, th + 1.5, nz)) { p.x = nx; p.z = nz; p.y = th; } } "
      "e.group.rotation.y = Math.atan2(dx, dz); "
      "if (dist < 1.0 && Math.abs(player.position.y - player.eyeHeight - p.y) < 1.5 && damageCooldown === 0) { "
      "playerHP = Math.max(0, playerHP - 2); updateHPBar(); damageCooldown = 60; } "
      "e.body.material.emissive.setHex(e.flash > 0 ? 0xff0000 : 0x000000); if (e.flash > 0) e.flash--;\n"
      "4. Hitting: `function hitEnemies()`: `const f = new THREE.Vector3(); camera.getWorldDirection(f); f.y = 0; f.normalize();` "
      "then iterate enemies BACKWARDS (for i = enemies.length-1 down to 0): dx, dz from player to enemy as above, dist = Math.hypot(dx, dz); "
      "if (dist < 2.5 && (dx * f.x + dz * f.z) / dist > 0.5) { e.hp--; e.flash = 10; if (e.hp <= 0) { scene.remove(e.group); enemies.splice(i, 1); } }. "
      "In swingSword(), call hitEnemies() only when a new swing starts, i.e. inside the `if (swingFrame === 0)` branch.\n"
      "Keep terrain, world, rebuildMeshes, NPCs, sword, health bar, sky, fog, lights and initPlayer unchanged.", ""),
 18: ("Fix two movement bugs. Exactly these changes, nothing else:\n"
      "1. W currently moves the player BACKWARD: a three.js camera looks down its local -Z axis, but the movement code uses "
      "`new THREE.Vector3(0, 0, 1)` as forward. Change that forward vector to `new THREE.Vector3(0, 0, -1)`. Leave the right vector "
      "`(1, 0, 0)` as it is.\n"
      "2. Mouse look uses the default 'XYZ' Euler order, which skews yaw once the view is pitched. Immediately after the camera is "
      "created add `camera.rotation.order = 'YXZ';` and in the player object set `rotation: new THREE.Euler(0, 0, 0, 'YXZ')`.\n"
      "Keep everything else, including initPlayer, unchanged.", ""),
 19: ("Add guard, sprint and dodge. Exactly these changes, nothing else:\n"
      "1. Globals: `let guarding = false, sprinting = false, dodgeFrames = 0, invulnFrames = 0, frameCount = 0; "
      "const dodgeVec = new THREE.Vector3(); const lastTap = {w: -100, a: -100, s: -100, d: -100};`\n"
      "2. `function setGuard(on){ guarding = on; sword.position.x = on ? 0.1 : 0.38; sword.rotation.z = on ? -1.3 : -0.35; }` "
      "`function setSprint(on){ sprinting = on; }` "
      "`function startDodge(k){ if (dodgeFrames > 0) return; const f = new THREE.Vector3(0, 0, -1).applyEuler(player.rotation); f.y = 0; f.normalize(); "
      "const r = new THREE.Vector3(1, 0, 0).applyEuler(player.rotation); r.y = 0; r.normalize(); "
      "if (k === 'w') dodgeVec.copy(f); else if (k === 's') dodgeVec.copy(f).negate(); else if (k === 'd') dodgeVec.copy(r); else dodgeVec.copy(r).negate(); "
      "dodgeFrames = 12; invulnFrames = 18; }`\n"
      "3. keydown handler, after the mouseLocked check and before the switch: `const k = event.key.toLowerCase(); "
      "if (k.length === 1 && 'wasd'.includes(k) && !event.repeat) { if (frameCount - lastTap[k] < 15) startDodge(k); lastTap[k] = frameCount; }` "
      "and add cases `case 'f': setGuard(true); break;` and `case 'shift': setSprint(true); break;`. keyup handler: add "
      "`case 'f': setGuard(false); break;` and `case 'shift': setSprint(false); break;`.\n"
      "4. animate(): first line `frameCount++;`. Outside the `if (mouseLocked)` block: `if (invulnFrames > 0) invulnFrames--;`. "
      "Inside it, change `moveVector.multiplyScalar(moveSpeed * 0.016)` to "
      "`moveVector.multiplyScalar(moveSpeed * (sprinting ? 1.8 : 1) * (guarding ? 0.5 : 1) * 0.016)`, and right after "
      "`player.position.z += moveVector.z;` add `if (dodgeFrames > 0) { player.position.x += dodgeVec.x * 0.35; player.position.z += dodgeVec.z * 0.35; dodgeFrames--; }`.\n"
      "5. In updateEnemies() replace `playerHP = Math.max(0, playerHP - 2); updateHPBar();` with "
      "`if (invulnFrames === 0) { playerHP = Math.max(0, playerHP - (guarding ? 1 : 2)); updateHPBar(); }` and keep `damageCooldown = 60;`.\n"
      "Keep everything else unchanged.", ""),
 20: ("Add a self-playing demo mode for ?demo=1. Exactly these changes, nothing else:\n"
      "1. Near the top of the script: `const DEMO = new URLSearchParams(location.search).get('demo') === '1'; let demoFrame = 0;`\n"
      "2. At the very end of the script, after animate() is first called, add: `if (DEMO) { mouseLocked = true; "
      "const s = enemies[0].group.position; player.position.set(s.x, s.y + player.eyeHeight + 2, s.z + 7); "
      "player.velocity.set(0, 0, 0); player.rotation.set(-0.12, 0, 0, 'YXZ'); }` (mouseLocked only enables physics; never call requestPointerLock in demo).\n"
      "3. `function demoTurnTo(yaw, pitch){ player.rotation.y += (yaw - player.rotation.y) * 0.08; player.rotation.x += (pitch - player.rotation.x) * 0.08; }` and "
      "`function demoYawTo(x, z){ return Math.atan2(-(x - player.position.x), -(z - player.position.z)); }`\n"
      "4. `function demoStep(){` with `const f = ++demoFrame;` then exactly this timeline (f is a frame number):\n"
      "   f === 60: moveState.forward = true;\n"
      "   f === 150 || f === 240: if (player.onGround) { player.velocity.y = jumpForce; player.onGround = false; }\n"
      "   f === 300: setSprint(true);   f === 420: setSprint(false);\n"
      "   f === 480: moveState.forward = false;\n"
      "   f >= 480 && f < 540 && enemies.length: demoTurnTo(demoYawTo(enemies[0].group.position.x, enemies[0].group.position.z), -0.15);\n"
      "   f === 540 || f === 575 || f === 610: swingSword();\n"
      "   f === 660: setGuard(true);   f === 780: setGuard(false);\n"
      "   f === 820: startDodge('a');\n"
      "   f >= 900 && f < 960: demoTurnTo(player.rotation.y, -0.7);\n"
      "   f === 960: document.dispatchEvent(new MouseEvent('mousedown', {button: 0, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));\n"
      "   f === 1020: document.dispatchEvent(new MouseEvent('mousedown', {button: 2, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));\n"
      "   f >= 1080 && f < 1140: demoTurnTo(player.rotation.y, -0.1);\n"
      "   f === 1140: moveState.forward = true;\n"
      "   f >= 1140 && f < 2100: player.rotation.y += 0.004;\n"
      "   f === 2100: moveState.forward = false;\n"
      "   `}`\n"
      "5. In animate(), right after `frameCount++;` add `if (DEMO) demoStep();`. After the line that copies player.position into camera.position add "
      "`if (DEMO && (moveState.forward) && player.onGround) camera.position.y += Math.sin(demoFrame * 0.25) * 0.05;` (head-bob).\n"
      "Keep everything else unchanged.", "demo"),
 21: ("Replace the demo choreography. The current one walks the player into the world edge, where all three enemies pin "
      "them to 0 HP. Exactly these changes, nothing else:\n"
      "1. In the `if (DEMO) { ... }` block at the end, replace the three player lines with: "
      "`player.position.set(11.5, getSurfaceHeight(11.5, 5.5) + player.eyeHeight + 0.5, 5.5); player.velocity.set(0, 0, 0); "
      "player.rotation.set(-0.12, demoYawTo(11.5, -8), 0, 'YXZ');` (keep `mouseLocked = true;`).\n"
      "2. Add `const DEMO_PATHS = [[[11.5, -8], [4, -11], [-2, -9.5]], [[-8, -1], [-7, 7], [3, 7.5], [10, 6]]]; let demoPath = null, demoWp = 0;` and\n"
      "`function demoWalk(){ if (!demoPath) return; const t = demoPath[demoWp]; if (Math.hypot(t[0] - player.position.x, t[1] - player.position.z) < 0.8) { "
      "demoWp++; if (demoWp >= demoPath.length) { demoPath = null; moveState.forward = false; return; } } "
      "const w = demoPath[demoWp]; demoTurnTo(demoYawTo(w[0], w[1]), -0.12); moveState.forward = true; }`\n"
      "`function demoNearest(){ let best = null, bd = 1e9; for (const e of enemies) { const d = Math.hypot(e.group.position.x - player.position.x, "
      "e.group.position.z - player.position.z); if (d < bd) { bd = d; best = e; } } return best; }`\n"
      "3. Replace the whole body of demoStep() after `const f = ++demoFrame;` with exactly:\n"
      "   demoWalk();\n"
      "   if (f === 60) { demoPath = DEMO_PATHS[0]; demoWp = 0; }\n"
      "   if ((f === 150 || f === 230) && player.onGround) { player.velocity.y = jumpForce; player.onGround = false; }\n"
      "   if (f === 260) setSprint(true);   if (f === 380) setSprint(false);\n"
      "   if (f >= 480 && f < 940) { demoPath = null; moveState.forward = false; const e = demoNearest(); if (e) demoTurnTo(demoYawTo(e.group.position.x, e.group.position.z), -0.2); }\n"
      "   if (f === 520 || f === 560 || f === 720 || f === 760 || f === 860 || f === 900) swingSword();\n"
      "   if (f === 600) setGuard(true);   if (f === 700) setGuard(false);\n"
      "   if (f === 800) startDodge('a');\n"
      "   if (f === 960) { demoPath = [DEMO_PATHS[1][0]]; demoWp = 0; }\n"
      "   if (f >= 1150 && f < 1210) { demoPath = null; moveState.forward = false; demoTurnTo(player.rotation.y, -0.75); }\n"
      "   if (f === 1210) document.dispatchEvent(new MouseEvent('mousedown', {button: 0, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));\n"
      "   if (f === 1290) document.dispatchEvent(new MouseEvent('mousedown', {button: 2, clientX: window.innerWidth / 2, clientY: window.innerHeight / 2}));\n"
      "   if (f >= 1350 && f < 1400) demoTurnTo(player.rotation.y, -0.12);\n"
      "   if (f === 1400) { demoPath = DEMO_PATHS[1].slice(1); demoWp = 0; }\n"
      "Keep demoTurnTo, demoYawTo, the head-bob line and everything else unchanged.", "demo"),
 22: ("Enemies stop so close that on screen their body fills the whole view. Exactly these changes in updateEnemies(), "
      "nothing else: change `dist > 0.8` to `dist > 1.6`, and change `dist < 1.0` (the contact-damage test) to `dist < 1.8`.", "demo"),
}


def ask(prompt: str, base: str) -> tuple[str, float, int]:
    content = prompt + "\n\n" + BASE_RULES + (("\n\nHere is the current file:\n\n" + base) if base else "")
    body = {"model": "x", "messages": [{"role": "user", "content": content}],
            "temperature": 0.2, "max_tokens": 16000}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + KEY})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=5400))
    out = r["choices"][0]["message"]["content"]
    if "```" in out:
        out = out.split("```")[1]
        out = out.split("\n", 1)[1] if out.split("\n", 1)[0].strip() in ("html", "") else out
    return out, time.time() - t0, r.get("usage", {}).get("completion_tokens", 0)


def main() -> None:
    n = int(sys.argv[1])
    prompt, query = ROUNDS[n]
    prev = D / f"good{n-1}.html"
    base = prev.read_text() if n > 1 and prev.exists() else ""
    if n > 1 and not base:
        sys.exit(f"no passing round {n-1} to build on")

    html, dt, tok = ask(prompt, base)
    cand = D / f"cand{n}.html"; cand.write_text(html)
    print(f"round {n}: {tok} tok in {dt:.0f}s = {tok/dt:.1f} tok/s, {len(html)} chars", flush=True)

    cmd = ["python3", GATE, str(cand), "--budget", "13000", "--no-telemetry",
           "--shot", str(D / f"r{n}.png")]
    if query:
        cmd += ["--query", "demo=1"]
    g = subprocess.run(cmd, capture_output=True, text=True)
    print(g.stdout.strip())
    if g.returncode == 0:
        (D / f"good{n}.html").write_text(html)
        print(f"PROMOTED -> good{n}.html")
    else:
        (D / f"fail{n}.html").write_text(html)
        print(f"NOT promoted; good{n-1}.html still stands")
    sys.exit(g.returncode)


if __name__ == "__main__":
    main()
