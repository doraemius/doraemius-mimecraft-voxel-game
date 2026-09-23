#!/usr/bin/env python3
"""NPCs: how many spawned, where, do they move, and does the frame change where they are."""
import pathlib, subprocess, re, sys
D = pathlib.Path("/tmp/vox"); src = (D / sys.argv[1]).read_text()
CH = ["/usr/bin/google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--use-gl=swiftshader",
      "--enable-unsafe-swiftshader", "--window-size=1280,720"]
POS = ('<script>setTimeout(function(){document.title="N "+npcs.length+" "+npcs.map(function(n){var p=n.group.position;'
       'return "f"+n.frame+" h"+n.heading.toFixed(2)+" "+p.x.toFixed(2)+","+p.y+","+p.z.toFixed(2)}).join(" | ");},%d);</script></body>')
for t in (2000, 9000):
    f = D / f"npc_{t}.html"; f.write_text(src.replace("</body>", POS % t))
    out = subprocess.run(CH + [f"--virtual-time-budget={t+1000}", "--dump-dom", f"file://{f}"], capture_output=True, text=True).stdout
    print(t, re.search(r"<title>([^<]*)</title>", out).group(1))
    subprocess.run(CH + [f"--virtual-time-budget={t}", f"--screenshot={D}/npc_{t}.png", f"file://{D / sys.argv[1]}"], capture_output=True)
