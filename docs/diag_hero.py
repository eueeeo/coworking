import subprocess
import time
import urllib.request
import os

port = 5145
base_url = f"http://localhost:{port}"
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

os.makedirs("docs/screenshots/hero_diag", exist_ok=True)

proc = subprocess.Popen(
    ["dotnet", "run", "--project", "src/Coworking/Coworking.csproj", "--urls", base_url],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

try:
    for i in range(30):
        try:
            req = urllib.request.Request(base_url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(1)

    widths = [1920, 1366, 1200, 992, 768, 390]
    for w in widths:
        shot_file = os.path.abspath(f"docs/screenshots/hero_diag/home_{w}.png")
        cmd = [
            edge_path,
            "--headless",
            "--disable-gpu",
            f"--window-size={w},900",
            "--hide-scrollbars",
            f"--screenshot={shot_file}",
            base_url
        ]
        subprocess.run(cmd, capture_output=True, timeout=15)
        print(f"Captured {w}px -> {shot_file}")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
