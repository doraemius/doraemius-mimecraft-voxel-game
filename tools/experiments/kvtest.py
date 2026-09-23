#!/usr/bin/env python3
"""Does the q8_0 KV cache cost real capability? A/B against f16 on a task that FAILED.

The task is the round-9 collision-correctness ask, chosen because its three defects are
GREPPABLE rather than eyeballed, so the scoring is objective:

  1. out-of-range sentinel must not be -Infinity (ground infinitely low = worse than the bug)
  2. the ceiling lookup must take the head height as a PARAMETER, not read a global body
  3. it must not scan scene.children per call

Under q8_0 at temperature 0.2 the model failed all three on its first attempt.

    python3 kvtest.py <label> <n>        run n samples against whatever is on :8080
"""
import json, re, sys, time, urllib.request

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
BASE = open("/tmp/vox/good8b.html").read()   # the pre-fix build round 9 started from

P = """Fix three collision correctness bugs. Change nothing about how the game looks.

1. OUT-OF-RANGE HEIGHT LOOKUP. getSurfaceHeight returns 0 when x,z is outside the terrain grid. Zero is a valid low ground height, so an out-of-range lookup silently reports ground level far BELOW the surrounding terrain and the body is placed inside the world. Make an out-of-range lookup return a value nothing can ever fall below - effectively an impassable wall - rather than 0, and make every caller treat it that way.

2. SURFACE MUST BE SCANNED, NOT STORED. getSurfaceHeight reads a stored per-column height, but blocks can be removed, so it goes stale after digging. Derive the surface from the highest SOLID block actually present in that column, and keep that lookup cheap.

3. NO CEILING CHECK. Nothing stops the player jumping up into a solid block. Add a head check that stops upward motion when the head reaches the underside of a solid block above, and that works for ANY body, not just the player.

Return the COMPLETE single-file HTML only, no explanation.

""" + BASE


def score(html: str) -> tuple[int, str]:
    notes = []
    neg_inf = "-Infinity" in html
    notes.append("sentinel_ok" if not neg_inf else "SENTINEL=-Infinity")
    m = re.search(r"function\s+(\w*[Cc]eiling\w*)\s*\(([^)]*)\)", html)
    if not m:
        param_ok = False; notes.append("NO_CEILING_FN")
    else:
        args = [a.strip() for a in m.group(2).split(",") if a.strip()]
        body_start = html.index(m.group(0))
        body = html[body_start:body_start + 900]
        reads_global = bool(re.search(r"\bplayer\.(position|eyeHeight)", body))
        param_ok = len(args) >= 3 and not reads_global
        notes.append("ceiling_param_ok" if param_ok else
                     f"CEILING args={len(args)} global={reads_global}")
    scan = "scene.children" in html
    notes.append("no_scene_scan" if not scan else "SCANS_scene.children")
    passed = (not neg_inf) + param_ok + (not scan)
    return passed, " | ".join(notes)


label, n = sys.argv[1], int(sys.argv[2])
for i in range(n):
    body = {"model": "x", "messages": [{"role": "user", "content": P}],
            "temperature": 0.2, "max_tokens": 16000}
    req = urllib.request.Request("http://localhost:8080/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + KEY})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=5400))
    out = r["choices"][0]["message"]["content"]
    if "```" in out:
        out = out.split("```")[1]
        out = out.split("\n", 1)[1] if out.split("\n", 1)[0].strip() in ("html", "") else out
    p, notes = score(out)
    open(f"/tmp/vox/kv_{label}_{i}.html", "w").write(out)
    print(f"{label:6} #{i}  {time.time()-t0:5.0f}s  {p}/3  {notes}", flush=True)
