#!/usr/bin/env python3
"""Round 17 combat, called directly (headless rAF is too slow to wait for): contact damage,
cooldown, a hit when FACING the enemy, and no hit when facing AWAY (negative control)."""
import pathlib, subprocess, re, sys
D = pathlib.Path("/tmp/vox"); src = (D / sys.argv[1]).read_text()
JS = r"""<script>setTimeout(function(){var L=[];
var e=enemies[0],p=e.group.position; L.push("enemies="+enemies.length);
function aim(tx,tz){camera.position.set(player.position.x,player.position.y,player.position.z);
 camera.lookAt(tx,player.position.y,tz);player.rotation.copy(camera.rotation);camera.updateMatrixWorld();}
player.position.set(p.x+0.6,p.y+player.eyeHeight,p.z); damageCooldown=0;
var hp0=playerHP; for(var k=0;k<5;k++)updateEnemies(); L.push("contact hp "+hp0+"->"+playerHP+" cd="+damageCooldown);
player.position.set(p.x+1.5,p.y+player.eyeHeight,p.z);
aim(p.x+10,p.z); var h0=e.hp; swingFrame=0; swingSword(); L.push("facing AWAY hp "+h0+"->"+e.hp);
aim(p.x,p.z); for(var k=0;k<3;k++){swingFrame=0;swingSword();} L.push("facing 3 swings hp->"+e.hp+" enemies="+enemies.length+" inScene="+(scene.children.indexOf(e.group)>=0));
document.title="C "+L.join(" | ");},1500);</script></body>"""
f = D / "combat.html"; f.write_text(src.replace("</body>", JS))
out = subprocess.run(["/usr/bin/google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--use-gl=swiftshader",
      "--enable-unsafe-swiftshader", "--window-size=1280,720", "--virtual-time-budget=3000", "--dump-dom", f"file://{f}"],
      capture_output=True, text=True).stdout
print(re.search(r"<title>([^<]*)</title>", out).group(1))
