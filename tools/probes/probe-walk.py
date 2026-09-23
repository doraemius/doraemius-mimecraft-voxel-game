#!/usr/bin/env python3
"""Does holding W move the player the way the camera faces? dot(displacement, view dir) > 0."""
import pathlib, subprocess, re, sys
D = pathlib.Path("/tmp/vox"); src = (D / sys.argv[1]).read_text()
JS = r"""<script>var P0,DIR;setTimeout(function(){mouseLocked=true;player.velocity.set(0,0,0);
var d=new THREE.Vector3();camera.getWorldDirection(d);d.y=0;d.normalize();DIR=d;P0=player.position.clone();window.F0=npcs[0].frame;
moveState.forward=true;},1200);
setTimeout(function(){var m=player.position.clone().sub(P0);m.y=0;
document.title="frames="+(npcs[0].frame-F0)+" y="+player.position.y.toFixed(2)+" W dot="+(m.dot(DIR)).toFixed(3)+" moved="+m.length().toFixed(3)+" order="+player.rotation.order;},2500);</script></body>"""
f = D / "walk.html"; f.write_text(src.replace("<head>", "<head><script>window.requestAnimationFrame=function(cb){return setTimeout(function(){cb(performance.now())},16)};</script>",1).replace("</body>", JS))
out = subprocess.run(["/usr/bin/google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--use-gl=swiftshader",
      "--enable-unsafe-swiftshader", "--window-size=1280,720", "--virtual-time-budget=3500", "--dump-dom", f"file://{f}"],
      capture_output=True, text=True).stdout
print(sys.argv[1], re.search(r"<title>([^<]*)</title>", out).group(1))
