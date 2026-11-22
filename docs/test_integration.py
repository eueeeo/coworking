import subprocess
import time
import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys
import random

port = 5123
base_url = f"http://localhost:{port}"

print(f"Starting Coworking app on {base_url}...")
proc = subprocess.Popen(
    ["dotnet", "run", "--project", "src/Coworking/Coworking.csproj", "--urls", base_url],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def extract_antiforgery_token(html):
    m = re.search(r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"', html)
    if not m:
        m = re.search(r'value="([^"]+)"\s+type="hidden"\s+name="__RequestVerificationToken"', html)
    if not m:
        m = re.search(r'value="([^"]+)"\s+name="__RequestVerificationToken"', html)
    if not m:
        m = re.search(r'name="__RequestVerificationToken"\s+value="([^"]+)"', html)
    return m.group(1) if m else None

try:
    # 1. Wait for server to start
    started = False
    for i in range(30):
        try:
            req = urllib.request.Request(base_url)
            with opener.open(req, timeout=2) as resp:
                if resp.status == 200:
                    print("Server is up and responding!")
                    started = True
                    break
        except Exception:
            time.sleep(1)

    if not started:
        print("Error: Server failed to start within timeout.")
        sys.exit(1)

    # 2. Test Catalog Page & Amenity Filter
    print("\n--- TEST 1: CATALOG PAGE & AMENITY FILTER ---")
    req = urllib.request.Request(f"{base_url}/")
    with opener.open(req) as resp:
        html = resp.read().decode('utf-8')
        assert "Где сегодня" in html or "Каталог" in html, "Каталог не загрузился"
        assert "Забронировать" in html, "Кнопки бронирования отсутствуют"
        assert "Удобство" in html, "Фильтр по удобствам отсутствует"
        print("Catalog page OK: workspaces rendered with booking buttons and filters!")

    # Test Amenity filter request
    req_amenity = urllib.request.Request(f"{base_url}/?AmenityId=1")
    with opener.open(req_amenity) as resp:
        amenity_html = resp.read().decode('utf-8')
        assert resp.status == 200, "Фильтрация по удобству вернула ошибку"
        print("Amenity Filter OK: filtered catalog loaded successfully!")

    # 3. Test Client Login
    print("\n--- TEST 2: LOGIN AS CLIENT ---")
    login_url = f"{base_url}/Account/Login"
    with opener.open(login_url) as resp:
        login_html = resp.read().decode('utf-8')
        token = extract_antiforgery_token(login_html)
        assert token, "Антифорджери токен не найден на странице логина"

    login_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.Email": "ivanov@example.com",
        "Input.Password": "Client123!"
    }).encode('utf-8')

    req_login = urllib.request.Request(login_url, data=login_data, method='POST')
    with opener.open(req_login) as resp:
        resp_html = resp.read().decode('utf-8')
        assert "Иванов" in resp_html or "Выйти" in resp_html, "Авторизация клиента не удалась"
        print("Login OK: logged in as Иванов Иван!")

    # 4. Test Create Booking for Workspace 1 with unique date
    print("\n--- TEST 3: CREATE BOOKING ---")
    create_url = f"{base_url}/Bookings/Create?workspaceId=1"
    with opener.open(create_url) as resp:
        create_html = resp.read().decode('utf-8')
        create_token = extract_antiforgery_token(create_html)
        assert create_token, "Антифорджери токен не найден на странице создания бронирования"

    rand_day = random.randint(1, 28)
    booking_date = f"2026-12-{rand_day:02d}"
    booking_data = urllib.parse.urlencode({
        "__RequestVerificationToken": create_token,
        "Input.WorkspaceId": "1",
        "Input.BookingDate": booking_date,
        "Input.StartTime": "10:00",
        "Input.EndTime": "14:00"
    }).encode('utf-8')

    req_create = urllib.request.Request(create_url, data=booking_data, method='POST')
    with opener.open(req_create) as resp:
        created_html = resp.read().decode('utf-8')
        assert "успешно оформлено" in created_html, f"Создание бронирования не подтверждено flash-сообщением. Ответ: {created_html[:400]}"
        print("Create Booking OK: booking created successfully and displayed with confirmation message!")

    # 5. Test Overlap validation (Try booking overlapping interval on same workspace 1)
    print("\n--- TEST 4: OVERLAPPING BOOKING REJECTION ---")
    with opener.open(create_url) as resp:
        new_token = extract_antiforgery_token(resp.read().decode('utf-8'))

    overlap_data = urllib.parse.urlencode({
        "__RequestVerificationToken": new_token,
        "Input.WorkspaceId": "1",
        "Input.BookingDate": booking_date,
        "Input.StartTime": "12:00",
        "Input.EndTime": "16:00"
    }).encode('utf-8')

    req_overlap = urllib.request.Request(create_url, data=overlap_data, method='POST')
    with opener.open(req_overlap) as resp:
        overlap_html = resp.read().decode('utf-8')
        assert "пересекается с другим бронированием" in overlap_html, "Проверка на пересечение интервалов не сработала!"
        print("Overlap Validation OK: Overlapping booking correctly rejected by server!")

    # 6. Test Client Access Denied to Admin Area
    print("\n--- TEST 5: CLIENT ACCESS DENIED TO ADMIN AREA ---")
    try:
        admin_req_by_client = urllib.request.Request(f"{base_url}/Admin/Workspaces/Index")
        with opener.open(admin_req_by_client) as resp:
            # Либо 302 на AccessDenied, либо страница AccessDenied
            assert "AccessDenied" in resp.url or resp.status in (401, 403), "Клиент не должен иметь доступ к разделу администратора"
            print("Access Control OK: Client is denied access to admin section!")
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403), f"Ожидался код 401/403, получен {e.code}"
        print("Access Control OK: Server returned HTTP 401/403 for unauthorized access!")

    # 7. Test Admin Login & Management Areas
    print("\n--- TEST 6: ADMIN LOGIN & ALL MANAGEMENT AREAS ---")
    cj_admin = http.cookiejar.CookieJar()
    opener_admin = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj_admin))

    with opener_admin.open(login_url) as resp:
        admin_token = extract_antiforgery_token(resp.read().decode('utf-8'))

    admin_login_data = urllib.parse.urlencode({
        "__RequestVerificationToken": admin_token,
        "Input.Email": "admin@coworking.local",
        "Input.Password": "Admin123!"
    }).encode('utf-8')

    with opener_admin.open(urllib.request.Request(login_url, data=admin_login_data, method='POST')) as resp:
        admin_home = resp.read().decode('utf-8')
        assert "ADMIN" in admin_home or "Администратор" in admin_home, "Логин администратора не удался"
        print("Admin Login OK!")

    # Проверка журнала бронирований
    with opener_admin.open(f"{base_url}/Admin/Bookings/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Журнал бронирований" in html, "Журнал бронирований недоступен"
        print("- Admin Bookings Journal OK")

    # Проверка управления этажами
    with opener_admin.open(f"{base_url}/Admin/Floors/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Этажи" in html, "Раздел этажей недоступен"
        print("- Admin Floors Management OK")

    # Проверка управления зонами
    with opener_admin.open(f"{base_url}/Admin/Zones/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Зоны" in html, "Раздел зон недоступен"
        print("- Admin Zones Management OK")

    # Проверка типов и тарифов
    with opener_admin.open(f"{base_url}/Admin/WorkspaceTypes/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Типы и тарифы" in html, "Раздел типов и тарифов недоступен"
        print("- Admin Types & Tariffs Management OK")

    # Проверка удобств
    with opener_admin.open(f"{base_url}/Admin/Amenities/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Удобства" in html, "Раздел удобств недоступен"
        print("- Admin Amenities Management OK")

    # Проверка рабочих мест
    with opener_admin.open(f"{base_url}/Admin/Workspaces/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Рабочие места" in html, "Раздел рабочих мест недоступен"
        print("- Admin Workspaces Management OK")

    # Проверка управления пользователями
    with opener_admin.open(f"{base_url}/Admin/Users/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Пользователи" in html, "Раздел пользователей недоступен"
        assert "ivanov@example.com" in html, "Пользователь Иванов не отображается в списке"
        print("- Admin Users Management OK")

    # Проверка отчетов и выручки
    with opener_admin.open(f"{base_url}/Admin/Reports/Index") as resp:
        html = resp.read().decode('utf-8')
        assert "Аналитический отчет и выручка" in html, "Отчетность недоступна"
        assert "Общая выручка" in html, "Показатель выручки не отображается"
        print("- Admin Reports & Analytics OK")

    print("\n=======================================================")
    print("ALL 6 INTEGRATION AND END-TO-END TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    try:
        subprocess.run([r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe", "-u", "coworking_app", "-p123", "coworking", "-e", "DELETE FROM Booking_status_history WHERE ID_booking > 4; DELETE FROM Bookings WHERE ID_booking > 4;"], capture_output=True)
    except Exception:
        pass
    print("Test server stopped.")
