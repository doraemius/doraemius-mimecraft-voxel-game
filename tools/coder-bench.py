#!/usr/bin/env python3
"""EP007 T4 gate: can a local coding model actually do 10 real tasks?

Pre-registered BEFORE any script exists (idea #4, IDEAS-SELFHOST-SERIES.md):
  premise  - "a 30B MoE on a 10 GB card is a usable coding agent, not a demo"
  falsifier- run 10 tasks drawn from THIS repo's real work and execute the output
  verdict  - each task PASSES only if its generated code runs and its assertions hold.
             No partial credit, no human reading it charitably.
  stop     - if <= 3/10 pass, the episode is "why local coding agents are not there yet"
             and must be scripted that way. Do not script the conclusion first.
"""
import json, subprocess, sys, tempfile, time, urllib.request, pathlib

KEY = open(__import__("os").path.expanduser("~/.config/llama-server/api-keys")).read().split()[0]
URL = "http://localhost:8080/v1/chat/completions"

# Each task: a prompt, and a test that must pass when the generated code is executed.
TASKS = [
    ("parse-asciicast",
     "Write a Python function `cast_text(path)` that reads an asciinema v2 .cast file "
     "(first line is a JSON header, each later line is a JSON array [time, kind, data]) "
     "and returns the concatenated `data` of every event whose kind == 'o'. Code only.",
     "import json,os\n"
     "p='/tmp/_t.cast'\n"
     "open(p,'w').write(json.dumps({'version':2})+'\\n'+json.dumps([0.1,'o','he'])+'\\n'+json.dumps([0.2,'o','llo'])+'\\n'+json.dumps([0.3,'i','X'])+'\\n')\n"
     "assert cast_text(p)=='hello', cast_text(p)\n"),

    ("strip-ansi",
     "Write a Python function `strip_sgr(s)` that removes ANSI SGR colour sequences "
     "(ESC [ digits and semicolons m) from a string, leaving all other text untouched. Code only.",
     "assert strip_sgr('\\x1b[1;32mok\\x1b[0m done')=='ok done'\n"
     "assert strip_sgr('plain')=='plain'\n"),

    ("hold-rule",
     "Write a Python function `over_hold(shots, limit=8.0)` where shots is a list of dicts "
     "with 't0' and 't1' floats. Return the list of indexes whose duration exceeds limit. Code only.",
     "s=[{'t0':0,'t1':9},{'t0':9,'t1':10},{'t0':10,'t1':30}]\n"
     "assert over_hold(s)==[0,2], over_hold(s)\n"),

    ("exact-line-score",
     "Write `score(gold, got)` taking two lists of strings. Return the number of gold lines "
     "that appear EXACTLY (after stripping leading/trailing whitespace) somewhere in got. Code only.",
     "assert score(['a','b','c'],['  a','x','c'])==2\n"
     "assert score(['a'],['ab'])==0\n"),

    ("token-multiplier",
     "Write `resend_cost(items, turns)` where items is a list of (turn_index, tokens). "
     "Each item is re-sent on every turn after the one it was added on. "
     "Return the total tokens sent across the whole session. Code only.",
     "assert resend_cost([(0,100)],3)==300, resend_cost([(0,100)],3)\n"
     "assert resend_cost([(2,10)],3)==10, resend_cost([(2,10)],3)\n"),

    ("wrap-cols",
     "Write `wrap(text, cols)` that hard-wraps a string at exactly `cols` characters "
     "(no word awareness), returning a list of lines. Newlines in the input start a new line. Code only.",
     "assert wrap('abcdef',3)==['abc','def']\n"
     "assert wrap('ab\\ncd',3)==['ab','cd']\n"),

    ("srt-timestamp",
     "Write `srt_time(seconds)` returning an SRT timestamp 'HH:MM:SS,mmm'. Code only.",
     "assert srt_time(0)=='00:00:00,000', srt_time(0)\n"
     "assert srt_time(3661.5)=='01:01:01,500', srt_time(3661.5)\n"),

    ("dedupe-links",
     "Write `dedupe(urls)` taking a list of URLs that may mix 'https://x.com/a' and bare "
     "'x.com/a'. Return a list of unique links preferring the scheme-ful form, order preserved. Code only.",
     "r=dedupe(['https://x.com/a','x.com/a','y.com'])\n"
     "assert r==['https://x.com/a','y.com'], r\n"),

    ("vram-fit",
     "Write `fits(model_gb, kv_gb, total_gb, reserve_gb=0.7)` returning True only if "
     "model_gb + kv_gb + reserve_gb <= total_gb. Code only.",
     "assert fits(5.0,2.0,10.0) is True\n"
     "assert fits(9.0,2.0,10.0) is False\n"),

    ("grid-fit",
     "Write `fit_grid(cols, rows, box_w, box_h)` that returns the largest integer font size "
     "from 34 down to 14 such that cols*round(font*0.6) <= box_w and rows*round(font*1.34) <= box_h. "
     "Return 14 if none fit. Code only.",
     "assert fit_grid(10,5,1000,500)==34, fit_grid(10,5,1000,500)\n"
     "assert fit_grid(200,100,100,100)==14\n"),
]


def ask(prompt: str) -> tuple[str, float, int]:
    body = {"model": "x", "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": 700}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + KEY})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=600))
    return (r["choices"][0]["message"]["content"], time.time() - t0,
            r.get("usage", {}).get("completion_tokens", 0))


def extract(md: str) -> str:
    if "```" in md:
        blocks = md.split("```")
        for b in blocks[1::2]:
            b = b.split("\n", 1)[1] if b.split("\n", 1)[0].strip() in ("python", "py", "") else b
            if "def " in b:
                return b
    return md


def main() -> None:
    passed = 0
    rows = []
    for name, prompt, test in TASKS:
        out, dt, toks = ask(prompt)
        code = extract(out)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
            fh.write(code + "\n\n" + test)
            path = fh.name
        run_output = subprocess.run([sys.executable, path], capture_output=True,
                                    text=True, timeout=60)
        ok = run_output.returncode == 0        # the verdict IS "the generated code ran"
        passed += ok
        err = (run_output.stderr.strip().splitlines() or [""])[-1][:70]
        rows.append((name, ok, dt, toks, "" if ok else err))
        print(f"{'PASS' if ok else 'FAIL'}  {name:18} {dt:5.1f}s {toks:4} tok  {err}", flush=True)
    tps = sum(r[3] for r in rows) / max(sum(r[2] for r in rows), 1e-9)
    print(f"\n{passed}/10 executed and passed their assertions | {tps:.1f} tok/s aggregate")
    print("VERDICT:", "usable coding agent" if passed >= 7 else
          ("mixed - script the caveats" if passed > 3 else
           "NOT there yet - the episode is why, per the pre-registered stop rule"))
    pathlib.Path("/tmp/coder-bench-result.json").write_text(json.dumps(
        {"passed": passed, "n": 10, "tok_s": round(tps, 1),
         "rows": [{"task": r[0], "pass": r[1], "s": round(r[2], 1), "tok": r[3], "err": r[4]}
                  for r in rows]}, indent=1))


if __name__ == "__main__":
    main()
