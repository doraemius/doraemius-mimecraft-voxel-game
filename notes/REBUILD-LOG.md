# Rebuilding the voxel game one round at a time

After twelve rounds stacked on an unverified base produced a game whose world was never
visible, the build was restarted from scratch with one rule: **one feature per round, and a
gate on the PIXELS between every round.** Driver `../scripts/game-rounds.py`, retry
`../scripts/game-round-retry.py`, gate `../scripts/game-gate.py`. Builds in `rebuild/`,
screenshots local-only in `~/yt-qwenvl/rounds/`.

Model: `Qwen3-Coder-30B-A3B-Instruct` Q4_K_XL via llama-server on an RTX 3080, 8,077 MiB
VRAM, 37-55 tok/s throughout.

## What each round cost

| # | feature | first try | notes |
|---|---|---|---|
| 1 | one cube on sky | PASS | 422 tok |
| 2 | 32x32 grass floor | PASS | |
| 3 | height variation | PASS | the noise was broken here and nobody could see it for 8 rounds |
| 4 | first-person controls | **FAIL** | player fell through the floor |
| 5 | break/place blocks | PASS | |
| 6 | biomes | passed the gate, **unusable view** | camera against a stone face |
| 7 | trees | PASS | |
| 8 | lighting | PASS | |
| 9 | collision correctness | **3 review defects** | see below |
| 10 | sky gradient + fog | **FAIL** | killed the lighting, terrain rendered black |
| 11 | spawn framing | **FAIL x3** | fixed only when given an explicit formula |
| 12 | terrain coherence | **FAIL** | over-corrected into flat stripes |
| 13 | two-octave noise formula | PASS | a real landscape: lake, shoreline, slopes, ridges |
| 14 | InstancedMesh + hidden-face culling | passed the gate, **lake and every canopy gone** | fixed by a two-line targeted retry; draw calls 7,912 -> 9 |
| 15 | 4 wandering NPCs | PASS | code matched the spec line for line |
| 16 | HP bar + held sword swing | PASS | spec-exact; rest pose large but readable |
| 17 | 3 enemies: chase, contact damage, sword hits | passed the gate, **sword could never hit** | `hitEnemies()` written but never called; one-line targeted retry |
| 18 | fix: W walked BACKWARD, Euler order | PASS | 3-line diff; W dot view went -4.95 -> +6.48 |
| 19 | guard (hold F), sprint, double-tap dodge | passed the gate, **game frozen after frame 1** | "first line `frameCount++`" was read as *replace* `requestAnimationFrame`; targeted retry |
| 20 | self-playing `?demo=1`, frame-counted timeline | PASS, code exact | **my** choreography walked into the world edge; enemies pinned the player to 0 HP |
| 21 | waypoint route planned from the heightmap | PASS, code exact | my yaw lerp didn't wrap at +/-PI and my dodge went into the lake; targeted retry |
| 22 | enemies hold at 1.6 units, not 0.8 | PASS, 2-number diff | on video a body no longer fills the frame; HP ends 10 |

## The finding that repeated every time

**Describe the outcome and it improvises badly. Give it the exact computation and it
implements it correctly.** Three examples, all in this run:

- *Spawn.* "Pick a column whose neighbours are not taller" failed three times. An explicit
  `camera.position.set(-size/2+4, maxH+14, -size/2+4)` plus `lookAt(0, maxH*0.35, 0)`
  worked first try.
- *Ceiling collision.* "Add a head check" produced a function that re-used the floor height
  and made jumping impossible. Specifying the signature `getCeilingHeight(x, z, headY)` and
  the call-site contract ("check the sentinel FIRST") worked first try.
- *Terrain.* Two rounds of describing hills produced confetti, then stripes. The literal
  `hash2`/`valueNoise` two-octave formula produced a landscape.

## Round 9: what a code review caught that the gate could not

Asked to fix three collision bugs, it returned a build that PASSED the gate and was worse:

1. **Wrong sign.** Asked for an out-of-range value "nothing can fall below", it returned
   `-Infinity` - ground infinitely *low*. Strictly worse than the `return 0` it replaced.
2. **A renamed variable, not a fix.** The "ceiling check" called `getSurfaceHeight` and
   snapped the player back to the ground whenever their head rose above it, making jumping
   impossible.
3. **O(scene.children) per call**, twice per body per frame.

Re-asked with the sign and the distinction spelled out, all three were fixed properly, with
a named `NO_CEILING` constant it invented itself.

Then, asked to *generalise* - "audit for this class of defect, find the instances yourself" -
it fixed the class it could patch locally and **silently deleted the function** whose fix
needed a signature change threaded through call sites. Only the diff caught that.

## The gate

`game-gate.py` decides PASS from the rendered frame, never from the game's own numbers,
because the previous attempt reported `blocks:23673, errors:[]` while rendering nothing.

It caught three real failure classes: nothing drawn, empty canvas plus vignette, and
**unlit** (geometry present, every surface near-black - the round 10 failure).

It also produced three false alarms that had to be corrected, each the same mistake:
tuned on the case that motivated it, not on normal operation.

- Rejected round 1's single small cube for being "too dominated by one colour". A correct
  simple scene must pass, so the test became *content present*, not content large.
- Accepted a page title as a telemetry line.
- Passed two builds whose framing was useless. **The gate answers "is anything rendered,
  lit and not blank". It cannot answer "is this worth looking at"** - that needs eyes, which
  is why every round's screenshot was pulled and viewed.

## Round 14: the gate passed a build that had deleted the lake

The prompt spelled out every step, including `covers(k)`, which says water and leaves do not
hide their *neighbours*. The model turned that into `if (type === 'water' || type === 'leaf')
continue;` in the render loop, so no water and no leaves were drawn at all. The gate passed
it at content 65% because the island was still there. Side by side with round 13 it was
obvious: a green floor where the lake had been, and bare trunks.

A retry that named the exact line and the exact six-neighbour array (`game-round-retry.py 14
"<note>" cand14.html`, a targeted fix on the candidate instead of a rebuild from good13)
produced a diff of exactly those two changes. Measured on the result:

| | good13 | good14 |
|---|---|---|
| draw calls | 7,912 | 9 |
| triangles | 98,940 | 61,620 |
| scene children | 8,252 | 11 |

Break and place were verified by pixels, not by `world.size`: a left click at the crosshair
changes 1,017 pixels and opens a visible hole, a right click 812, and two renders with no
click differ by 0. The lake is now a lighter teal. That is a correction: good13 stacked two
transparent water blocks in every water cell.

## Round 15: NPCs, and a probe that lied first

Four NPCs spawned and their positions were **identical at 2 s and 9 s of virtual time**,
which looked like a stuck-NPC bug. It was the probe. Headless Chrome with software GL
renders about 29 frames by 2 s and 56 by 9 s, so the two runs were one short run twice.
Printing the NPCs' frame counters beside their positions settled it: they move 0.03 units a
frame, as specified, and step up one block. Headless virtual time is not frame time. Any
motion check has to read a frame counter.

## The gate itself failed, and looked like a verdict

On 2026-09-23 every round, including the known-good good13, came back "NOT promoted" with
no PIXELS line. On the GPU box, `python3` is a wrapper that sets `ulimit -v 16 GiB`. The gate's
Chrome inherits that limit and dies with SIGTRAP (rc -5) before writing a screenshot. A
direct `google-chrome` run from bash worked, which hid the cause. The gate now exits with
`INSTRUMENT ...` when no screenshot appears, and every round runs under `PY_MEM_CAP=none`.
Negative control: capped, it prints INSTRUMENT. Positive: uncapped, good13 PASSes.

## Round 17: dead code the gate cannot see

The prompt said "in swingSword(), call hitEnemies()". The model wrote a correct `hitEnemies()`
and never called it. The frame looked right, so the gate passed it. Reading the diff caught
it. A targeted retry added exactly the call.

The functional probe calls the game's functions directly rather than waiting on headless
frames. On good17: contact takes HP 20 -> 18 and starts the 60-frame cooldown, a swing
facing **away** leaves the enemy at 3 HP, and three swings facing it kill it and remove it
from the scene. The unfixed cand17 is the negative control: every line is identical except
the swings do nothing. So the probe distinguishes the defect and is not measuring its own
setup. Probe: `probe-combat.py` (session scratch, copied to `/tmp` on the GPU box).

**Capture note:** in headless screenshots the bottom ~88 px is page background. The canvas
is sized from `window.innerHeight`, which headless reports as smaller than the 720 px shot.
Check this in the Xvfb kiosk capture before recording.

## Round 18: W walked backward since round 4

Found by reading good13, not by the gate or the eye, because a still frame cannot show walking.
The movement code used `(0, 0, 1)` as forward, but a three.js camera looks down -Z. Probed by
holding W and taking the dot product of the displacement with the view direction: good17
**-4.95** (all backward), good18 **+6.48**. The fix also set the Euler order to 'YXZ'. The
old default 'XYZ' was the reason the old walk distance was shorter.

**Headless rAF under virtual time stalls.** The first walk probe measured 0 frames in 1.3 s
and moved=0.000, which reads as "movement broken" and was the instrument. The probes now shim
`requestAnimationFrame` to a 16 ms `setTimeout`: 81 frames in 1.3 s, deterministic.

## Round 19: a gate-passing build that froze

The prompt said "animate(): first line `frameCount++;`". The model replaced
`requestAnimationFrame(animate);` with it, so the game drew one frame and stopped. A
screenshot only needs one frame, so the gate passed. The ambiguity was in **my** wording:
"first line" can mean insert or replace. A targeted retry restored the call.

Probe (`probe-moves.py`, rAF shimmed), good19: walk 2.56 vs sprint 4.46 in the same window
(1.74x vs 1.8x specified); contact hit 2 HP, guarded 1 HP, during a dodge 0 HP; a keydown/
keyup/keydown on W triggers a dodge (dodgeFrames=12); dodge distance 4.20 = 12 x 0.35. The
frozen cand19 is the negative control: frameCount stays 1 and nothing moves.

**Pattern across rounds 14-19:** four defects passed the gate. Three were introduced in
feature rounds 14, 17 and 19 (3 of 6), and one (W walking backward) was inherited from round 4.
All four were found by reading the diff or by a functional probe, never by the frame. Three
of the four were *omissions or deletions*: water skipped, a call never made, rAF removed. A line-level diff
review catches those in seconds.

## Rounds 20-21: the model's code was exact, and my demo design was wrong

Both demo rounds implemented the specified timeline line for line. Every defect was in the
choreography I wrote. A trace printing position, yaw, HP, enemy count and nearest-enemy
distance every 60 frames found them, rendered at 320x180 because only the numbers were
needed. It took 1 minute against 21 for a 1280x720 contact sheet, whose frame 545 then hung
Chrome for 900 s anyway.

- Round 20: enemies chase anything within 10 units on a 32-unit map, so they caught the
  player by frame 60. The walk ended against the z = -15.5 world clamp, and the three
  bunched enemies took HP to 0 by frame 660.
- Round 21 route was planned from a Python replica of the heightmap and spawn scans (it
  matched the trace to 0.1 unit): east shore -> north shore -> fight -> break/place -> south
  shore. Two more of my own bugs: `demoTurnTo` lerped yaw without wrapping, so near +/-PI the
  player walked north into the edge instead of south, and a left dodge at that heading landed
  in the lake (eye y 2.6, under the water surface). Fixed by `atan2(sin d, cos d)` and a
  backward dodge after the last swing.

Final trace: all 3 enemies dead by frame 900, HP ends at 12, dodge lands on land, break then
place (world 5349 -> 5348 -> 5349), south-shore walk arrives at frame ~1,740, idle after.
Useful footage: frames 0-1,800 (30 s at 60 fps).
