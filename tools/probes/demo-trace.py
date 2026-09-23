#!/usr/bin/env python3
"""Trace the ?demo=1 run: player xyz/yaw, HP, enemy count and nearest-enemy distance every 60 demo frames."""
import pathlib, subprocess, re, sys
D = pathlib.Path("/tmp/vox"); name = sys.argv[1]
SHIM = "<head><script>window.requestAnimationFrame=function(cb){return setTimeout(function(){cb(performance.now())},16)};</script>"
JS = r"""<script>var T=[],last=-1;(function w(){if(typeof demoFrame!=='undefined'&&demoFrame!==last&&demoFrame%60===0){last=demoFrame;
var p=player.position,nd=enemies.reduce(function(m,e){return Math.min(m,Math.hypot(e.group.position.x-p.x,e.group.position.z-p.z))},99);
T.push(demoFrame+":"+p.x.toFixed(1)+","+p.y.toFixed(1)+","+p.z.toFixed(1)+" yaw"+player.rotation.y.toFixed(2)+" hp"+playerHP+" en"+enemies.length+" d"+nd.toFixed(1)+" w"+world.size);
document.title=T.join(" ; ");}if(typeof demoFrame==='undefined'||demoFrame<2160)setTimeout(w,2);})();</script></body>"""
f = D / "trace.html"; f.write_text((D / name).read_text().replace("<head>", SHIM, 1).replace("</body>", JS))
out = subprocess.run(["/usr/bin/google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--use-gl=swiftshader",
      "--enable-unsafe-swiftshader", "--window-size=320,180", "--virtual-time-budget=40000",
      "--user-data-dir=/tmp/vox/prof_trace", "--dump-dom", f"file://{f}?demo=1"], capture_output=True, text=True, timeout=1500).stdout
m = re.search(r"<title>([^<]*)</title>", out); print("\n".join((m.group(1) if m else "NO TITLE").split(" ; ")))
