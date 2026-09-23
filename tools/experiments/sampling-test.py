#!/usr/bin/env python3
"""Does off-spec sampling explain the failures? Controlled A/B on a prompt that FAILED twice.

Prompt: the terrain-coherence ask, described as an OUTCOME (no formula). Under my session
settings it produced confetti once and flat stripes once. Here the same prompt runs under
(A) my settings and (B) the model card's recommended settings, three samples each, and the
resulting terrain is judged by the same pixel gate.

Card: temperature=0.7, top_p=0.8, top_k=20, repetition_penalty=1.05
Mine: temperature=0.2, everything else left to llama-server defaults
"""
import json, pathlib, subprocess, time, urllib.request

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
D = pathlib.Path("/tmp/vox")
base = (D / "good10.html").read_text()      # pre-terrain-fix build, the one that failed

PROMPT = ("The terrain is not coherent: neighbouring columns jump to wildly different "
          "heights so the landscape looks like scattered confetti rather than hills and "
          "valleys. Fix the height function so the world has recognisable smooth hills and "
          "valleys, while still varying enough to be interesting. Keep everything else "
          "exactly as it is.\n\nReturn the COMPLETE single-file HTML only, no explanation. "
          "Do NOT add any self-evaluation, metrics or telemetry code.\n\n"
          "Here is the current file:\n\n" + base)

ARMS = {
    "mine  (t=0.2, defaults)": {"temperature": 0.2},
    "card  (t=0.7/p0.8/k20/r1.05)": {"temperature": 0.7, "top_p": 0.8, "top_k": 20,
                                     "repeat_penalty": 1.05},
}


def run(name: str, opts: dict, i: int) -> str:
    body = {"model": "x", "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": 16000, **opts}
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
    f = D / f"ab_{i}.html"; f.write_text(out)
    g = subprocess.run(["python3", "/tmp/game-gate-linux.py", str(f), "--budget", "10000",
                        "--no-telemetry", "--shot", str(D / f"ab_{i}.png")],
                       capture_output=True, text=True)
    px = [l for l in g.stdout.splitlines() if l.startswith("PIXELS")]
    verdict = "PASS" if g.returncode == 0 else "FAIL"
    return (f"{name:30} #{i}  {time.time()-t0:5.0f}s  {verdict}  "
            f"{px[0][10:] if px else ''}")


i = 0
for name, opts in ARMS.items():
    for _ in range(3):
        i += 1
        print(run(name, opts, i), flush=True)
