#!/usr/bin/env python3
"""Retry one round with an extra note describing the failure as STATE.

    python3 retry.py <round> "<note>"              builds on good<round-1>, gates, promotes on PASS
    python3 retry.py <round> "<note>" <base.html>  builds on that file instead (a targeted fix
                                                   to a candidate that passed the gate but not
                                                   the eye)

Run under PY_MEM_CAP=none on the GPU box: the gate's Chrome dies under the default 16 GiB cap.
"""
import json, pathlib, subprocess, sys, time, urllib.request

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
D = pathlib.Path("/tmp/vox")
n = int(sys.argv[1])
note = sys.argv[2]
base = (D / (sys.argv[3] if len(sys.argv) > 3 else f"good{n-1}.html")).read_text()

P = (note + "\n\nReturn the COMPLETE single-file HTML only, no explanation. "
     "Do NOT add any self-evaluation, metrics or telemetry code.\n\n"
     "Here is the current file:\n\n" + base)

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
dt = time.time() - t0
tok = r.get("usage", {}).get("completion_tokens", 0)
cand = D / f"cand{n}b.html"; cand.write_text(out)
print(f"retry {n}: {tok} tok in {dt:.0f}s = {tok/dt:.1f} tok/s")

g = subprocess.run(["python3", "/tmp/game-gate-linux.py", str(cand), "--budget", "11000",
                    "--no-telemetry", "--shot", str(D / f"r{n}.png")],
                   capture_output=True, text=True)
print(g.stdout.strip())
if g.returncode == 0:
    (D / f"good{n}.html").write_text(out)
    print(f"PROMOTED -> good{n}.html")
sys.exit(g.returncode)
