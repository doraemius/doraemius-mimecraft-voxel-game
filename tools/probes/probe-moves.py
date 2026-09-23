#!/usr/bin/env python3
"""Round 19: frames advance, sprint ~1.8x walk, guard halves damage, dodge = i-frames + ~4.2 units, double-tap W triggers it.
rAF is shimmed to a 16 ms setTimeout because headless rAF under virtual time stalls."""
import pathlib, subprocess, re, sys
D = pathlib.Path("/tmp/vox"); src = (D / sys.argv[1]).read_text()
SHIM = "<head><script>window.requestAnimationFrame=function(cb){return setTimeout(function(){cb(performance.now())},16)};</script>"
JS = r"""<script>var L=[],A,B,e;
function xz(){return new THREE.Vector2(player.position.x,player.position.z);}
function key(t,k){document.dispatchEvent(new KeyboardEvent(t,{key:k}));}
setTimeout(function(){mouseLocked=true;L.push("f0="+frameCount);A=xz();key("keydown","w");},1000);
setTimeout(function(){B=xz();L.push("walk="+B.distanceTo(A).toFixed(2));key("keydown","Shift");A=xz();},1500);
setTimeout(function(){B=xz();L.push("sprint="+B.distanceTo(A).toFixed(2));key("keyup","Shift");key("keyup","w");},2000);
setTimeout(function(){e=enemies[0];var p=e.group.position;
 player.position.set(p.x+0.6,p.y+player.eyeHeight,p.z);invulnFrames=0;
 damageCooldown=0;var h=playerHP;updateEnemies();L.push("hit "+h+"->"+playerHP);
 setGuard(true);damageCooldown=0;h=playerHP;updateEnemies();L.push("guarded "+h+"->"+playerHP);setGuard(false);
 startDodge("w");damageCooldown=0;h=playerHP;updateEnemies();L.push("dodging "+h+"->"+playerHP+" inv="+invulnFrames);
 dodgeFrames=0;invulnFrames=0;player.position.set(0,30,0);A=xz();
 key("keydown","w");key("keyup","w");key("keydown","w");L.push("dtap dodgeFrames="+dodgeFrames);key("keyup","w");},2100);
setTimeout(function(){B=xz();L.push("dodge dist="+B.distanceTo(A).toFixed(2)+" f="+frameCount);document.title="M "+L.join(" | ");},2800);
</script></body>"""
f = D / "moves.html"; f.write_text(src.replace("<head>", SHIM, 1).replace("</body>", JS))
out = subprocess.run(["/usr/bin/google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--use-gl=swiftshader",
      "--enable-unsafe-swiftshader", "--window-size=1280,720", "--virtual-time-budget=3500", "--dump-dom", f"file://{f}"],
      capture_output=True, text=True).stdout
m = re.search(r"<title>([^<]*)</title>", out); print(sys.argv[1], m.group(1) if m else out[-300:])
