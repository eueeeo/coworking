import subprocess
import time
import urllib.request
import os
import sys

port = 5135
base_url = f"http://localhost:{port}"
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"=== ЗАПУСК ПРОВЕРКИ АДАПТИВНОСТИ НА {base_url} ===")
print(f"Microsoft Edge: {edge_path} (существует: {os.path.exists(edge_path)})")

os.makedirs("docs/screenshots", exist_ok=True)

proc = subprocess.Popen(
    ["dotnet", "run", "--project", "src/Coworking/Coworking.csproj", "--urls", base_url],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

viewports = [
    ("Desktop", 1920, 1080),
    ("Laptop", 1366, 768),
    ("Tablet", 768, 1024),
    ("Mobile", 390, 844),
    ("Narrow_Mobile", 360, 800)
]

pages = [
    ("home", f"{base_url}/"),
    ("login", f"{base_url}/Account/Login"),
    ("register", f"{base_url}/Account/Register"),
    ("booking_create", f"{base_url}/Bookings/Create?workspaceId=1")
]

try:
    # 1. Ожидание старта сервера
    started = False
    for i in range(30):
        try:
            req = urllib.request.Request(base_url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print("Сервер запущен и готов к тестированию!")
                    started = True
                    break
        except Exception:
            time.sleep(1)

    if not started:
        print("Ошибка: сервер не запустился вовремя.")
        sys.exit(1)

    all_passed = True
    print("\n--- РЕНДЕРИНГ И ПРОВЕРКА ЭКРАНОВ ---")

    for vp_name, width, height in viewports:
        print(f"\n[Viewport: {vp_name} ({width}x{height})]")
        for page_name, url in pages:
            shot_file = os.path.abspath(f"docs/screenshots/{page_name}_{width}x{height}.png")
            cmd = [
                edge_path,
                "--headless",
                "--disable-gpu",
                f"--window-size={width},{height}",
                "--hide-scrollbars",
                f"--screenshot={shot_file}",
                url
            ]
            res = subprocess.run(cmd, capture_output=True, timeout=15)
            if os.path.exists(shot_file) and os.path.getsize(shot_file) > 1000:
                print(f"  [OK] {page_name:<16} рендеринг OK (скриншот {os.path.getsize(shot_file)} байт)")
            else:
                print(f"  [X] {page_name:<16} ошибка рендеринга")
                all_passed = False

    print("\n=======================================================")
    if all_passed:
        print("ВСЕ 5 РАЗРЕШЕНИЙ И 4 СТРАНИЦЫ УСПЕШНО ОТРИСОВАНЫ В EDGE!")
    else:
        print("ОШИБКА: часть страниц не отрендерилась.")
    print("=======================================================")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    print("Тестовый сервер остановлен.")
