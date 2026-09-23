#!/usr/bin/env python3
"""Real-time fps of the ?demo=1 run per Chrome GL backend. The page reports demoFrame/6 s and
its WebGL renderer string to an in-process HTTP beacon (no background server to pgrep/pkill)."""
import http.server, subprocess, threading, urllib.parse, sys
got = []
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        got.append(urllib.parse.unquote(self.path)); self.send_response(204); self.end_headers()
    def log_message(self, *a): pass
srv = http.server.HTTPServer(("127.0.0.1", 8766), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
src = open("/tmp/vox/good21.html").read().replace("</body>",
  '<script>setTimeout(function(){var g=renderer.getContext(),x=g.getExtension("WEBGL_debug_renderer_info");'
  'fetch("http://127.0.0.1:8766/fps="+(demoFrame/6).toFixed(1)+"/"+(x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):"?"),{mode:"no-cors"});},6000);</script></body>')
open("/tmp/vox/fps.html", "w").write(src)
MODES = {"swiftshader": ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--disable-gpu"],
         "angle-vulkan": ["--use-angle=vulkan", "--enable-features=Vulkan", "--ignore-gpu-blocklist"],
         "angle-gl-egl": ["--use-angle=gl-egl", "--ignore-gpu-blocklist"],
         "default-gpu": ["--ignore-gpu-blocklist"]}
for name, flags in MODES.items():
    got.clear()
    try:
        subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", *flags, "--window-size=1280,720",
                        f"--user-data-dir=/tmp/vox/prof_fps_{name}", "file:///tmp/vox/fps.html?demo=1"],
                       capture_output=True, timeout=11)
    except subprocess.TimeoutExpired:
        pass
    print(f"{name:13s} {got[-1][:110] if got else 'NO REPORT'}", flush=True)
srv.shutdown()
