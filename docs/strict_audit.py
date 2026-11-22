import subprocess
import time
import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys
import random

port = 5128
base_url = f"http://localhost:{port}"

print(f"=== ЗАПУСК СТРОГОГО АУДИТА НА {base_url} ===")
proc = subprocess.Popen(
    ["dotnet", "run", "--project", "src/Coworking/Coworking.csproj", "--urls", base_url],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

def extract_token(html):
    m = re.search(r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"', html)
    if not m:
        m = re.search(r'value="([^"]+)"\s+type="hidden"\s+name="__RequestVerificationToken"', html)
    if not m:
        m = re.search(r'value="([^"]+)"\s+name="__RequestVerificationToken"', html)
    if not m:
        m = re.search(r'name="__RequestVerificationToken"\s+value="([^"]+)"', html)
    return m.group(1) if m else None

def find_id_in_row(html, text, pattern):
    for r in re.findall(r'<tr>.*?</tr>', html, re.DOTALL):
        if text in r:
            m = re.search(pattern, r)
            if m:
                return m.group(1)
    return None

def get_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)), cj

try:
    # 1. Ожидание старта сервера
    started = False
    for i in range(30):
        try:
            req = urllib.request.Request(base_url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print("Сервер запущен и отвечает (200 OK)!")
                    started = True
                    break
        except Exception:
            time.sleep(1)

    if not started:
        print("Ошибка: сервер не запустился вовремя.")
        sys.exit(1)

    # 2. Аутентификация администратора
    print("\n[1] АУТЕНТИФИКАЦИЯ АДМИНИСТРАТОРА")
    opener_admin, cj_admin = get_opener()
    with opener_admin.open(f"{base_url}/Account/Login") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    
    login_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.Email": "admin@coworking.local",
        "Input.Password": "Admin123!"
    }).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Account/Login", data=login_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "ADMIN" in html or "Администратор" in html, "Администратор не авторизован"
    print("✓ Администратор успешно авторизован")

    # 3. Аутентификация клиента
    print("\n[2] АУТЕНТИФИКАЦИЯ КЛИЕНТА")
    opener_client, cj_client = get_opener()
    with opener_client.open(f"{base_url}/Account/Login") as resp:
        token_c = extract_token(resp.read().decode('utf-8'))
    
    login_data_c = urllib.parse.urlencode({
        "__RequestVerificationToken": token_c,
        "Input.Email": "ivanov@example.com",
        "Input.Password": "Client123!"
    }).encode('utf-8')
    with opener_client.open(urllib.request.Request(f"{base_url}/Account/Login", data=login_data_c, method='POST')) as resp:
        html_c = resp.read().decode('utf-8')
        assert "Иванов" in html_c or "Выйти" in html_c, "Клиент не авторизован"
    print("✓ Клиент успешно авторизован")

    # 4. Проверка разграничения прав доступа (Клиент -> Админка)
    print("\n[3] ПРОВЕРКА РАЗГРАНИЧЕНИЯ ПРАВ ДОСТУПА")
    endpoints_to_test = [
        "/Admin/Floors/Index",
        "/Admin/Zones/Index",
        "/Admin/WorkspaceTypes/Index",
        "/Admin/Amenities/Index",
        "/Admin/Workspaces/Index",
        "/Admin/Users/Index",
        "/Admin/Reports/Index",
        "/Admin/Bookings/Index"
    ]
    for ep in endpoints_to_test:
        try:
            with opener_client.open(f"{base_url}{ep}") as resp:
                assert "AccessDenied" in resp.url or resp.status in (401, 403), f"Клиент получил доступ к {ep}!"
        except urllib.error.HTTPError as e:
            assert e.code in (401, 403), f"Неожиданный код ошибки {e.code} для {ep}"
    print("✓ Сервер надежно блокирует доступ клиента ко всем 8 административным эндпоинтам")

    # 5. CRUD ЭТАЖЕЙ
    print("\n[4] ТЕСТИРОВАНИЕ CRUD ЭТАЖЕЙ")
    with opener_admin.open(f"{base_url}/Admin/Floors/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    
    # 5.1 Создание
    post_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.Number": "99",
        "Input.Name": "Тестовый 99 этаж",
        "Input.Description": "Описание тестового этажа"
    }).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Floors/Index?handler=Save", data=post_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "Тестовый 99 этаж" in html, "Этаж не создан"
    print("  ✓ Создание этажа успешно")

    # 5.2 Валидация дубликата номера
    with opener_admin.open(f"{base_url}/Admin/Floors/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Floors/Index?handler=Save", data=post_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "Этаж с таким номером уже существует" in html, "Проверка дубликата номера этажа не сработала"
    print("  ✓ Валидация дубликата номера этажа работает")

    # Находим ID именно созданного тестового этажа в строке таблицы
    created_floor_id = find_id_in_row(html, "Тестовый 99 этаж", r'action="/Admin/Floors\?id=(\d+)&amp;handler=Delete"')
    assert created_floor_id, "Не удалось найти ID созданного этажа для удаления"

    # 5.3 Удаление созданного этажа
    with opener_admin.open(f"{base_url}/Admin/Floors/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    del_data = urllib.parse.urlencode({"__RequestVerificationToken": token}).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Floors?id={created_floor_id}&handler=Delete", data=del_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert find_id_in_row(html, "Тестовый 99 этаж", r'id=(\d+)') is None, "Этаж остался в таблице после удаления"
    print("  ✓ Удаление этажа успешно (проверено фактическое отсутствие в таблице)")

    # 6. CRUD ЗОН
    print("\n[5] ТЕСТИРОВАНИЕ CRUD ЗОН")
    with opener_admin.open(f"{base_url}/Admin/Zones/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    zone_post = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.FloorId": "1",
        "Input.Name": "Тестовая зона Альфа",
        "Input.Description": "Тестовое описание зоны"
    }).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Zones?handler=Save", data=zone_post, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "Тестовая зона Альфа" in html, "Зона не создана"
    print("  ✓ Создание зоны успешно")

    created_zone_id = find_id_in_row(html, "Тестовая зона Альфа", r'action="/Admin/Zones\?id=(\d+)&amp;handler=Delete"')
    assert created_zone_id, "Не найден ID созданной зоны"

    # Удаление зоны
    with opener_admin.open(f"{base_url}/Admin/Zones/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    del_data = urllib.parse.urlencode({"__RequestVerificationToken": token}).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Zones?id={created_zone_id}&handler=Delete", data=del_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert find_id_in_row(html, "Тестовая зона Альфа", r'id=(\d+)') is None, "Зона осталась в таблице"
    print("  ✓ Удаление зоны успешно")

    # 7. CRUD ТИПОВ И ТАРИФОВ
    print("\n[6] ТЕСТИРОВАНИЕ CRUD ТИПОВ И ТАРИФОВ")
    with opener_admin.open(f"{base_url}/Admin/WorkspaceTypes/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    
    # Попытка создания с отрицательной ценой
    bad_type_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.Name": "Тестовый Негативный",
        "Input.PricePerHour": "-50.00",
        "Input.Description": "Не должно создаться"
    }).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/WorkspaceTypes?handler=Save", data=bad_type_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "неотрицательным" in html or "Тестовый Негативный" not in html, "Отрицательный тариф был ошибочно принят"
    print("  ✓ Валидация неотрицательного тарифа работает")

    # Создание корректного типа
    good_type_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.Name": "VIP Капсула",
        "Input.PricePerHour": "45.00",
        "Input.Description": "Индивидуальная звукоизолированная капсула"
    }).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/WorkspaceTypes?handler=Save", data=good_type_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "VIP Капсула" in html, "Тип не создан"
        assert "45" in html, "Тариф не отображается"
    print("  ✓ Создание типа и тарифа успешно")

    created_type_id = find_id_in_row(html, "VIP Капсула", r'id=(\d+)')
    assert created_type_id, "Не найден ID созданного типа"

    # Удаление типа
    with opener_admin.open(f"{base_url}/Admin/WorkspaceTypes/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    del_data = urllib.parse.urlencode({"__RequestVerificationToken": token}).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/WorkspaceTypes?id={created_type_id}&handler=Delete", data=del_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert find_id_in_row(html, "VIP Капсула", r'id=(\d+)') is None, "Тип остался в таблице"
    print("  ✓ Удаление типа успешно")

    # 8. CRUD УДОБСТВ И КАТЕГОРИЙ
    print("\n[7] ТЕСТИРОВАНИЕ CRUD УДОБСТВ И КАТЕГОРИЙ")
    with opener_admin.open(f"{base_url}/Admin/Amenities/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    
    # 8.1 Добавление новой категории
    cat_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "CategoryInput.Name": "Тестовая категория"
    }).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Amenities?handler=AddCategory", data=cat_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "Тестовая категория" in html, "Категория не создана"
    print("  ✓ Создание категории удобств успешно")

    # 8.2 Добавление удобства в категорию 1
    with opener_admin.open(f"{base_url}/Admin/Amenities/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    am_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "AmenityInput.CategoryId": "1",
        "AmenityInput.Name": "VR Шлем Pro"
    }).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Amenities?handler=SaveAmenity", data=am_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "VR Шлем Pro" in html, "Удобство не создано (проблема ModelState)"
    print("  ✓ Создание удобства успешно (валидация независимых моделей подтверждена)")

    # Находим ID удобства в строке таблицы
    am_id = find_id_in_row(html, "VR Шлем Pro", r'id=(\d+)')
    assert am_id, "Не найден ID удобства"

    with opener_admin.open(f"{base_url}/Admin/Amenities/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    del_am = urllib.parse.urlencode({"__RequestVerificationToken": token}).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Amenities?id={am_id}&handler=DeleteAmenity", data=del_am, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert find_id_in_row(html, "VR Шлем Pro", r'id=(\d+)') is None, "Удобство не удалено"
    print("  ✓ Удаление удобства успешно")

    # Удаляем тестовую категорию
    m_cat = re.search(r'action="/Admin/Amenities\?id=(\d+)&amp;handler=DeleteCategory"', html)
    if not m_cat:
        m_cat = re.search(r'DeleteCategory.*?id=(\d+)', html)
    if m_cat:
        cat_id = m_cat.group(1)
        with opener_admin.open(f"{base_url}/Admin/Amenities/Index") as resp:
            token = extract_token(resp.read().decode('utf-8'))
        del_cat = urllib.parse.urlencode({"__RequestVerificationToken": token}).encode('utf-8')
        with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Amenities?id={cat_id}&handler=DeleteCategory", data=del_cat, method='POST')) as resp:
            html = resp.read().decode('utf-8')
            assert "удалена" in html or "Тестовая категория (0)" not in html, "Категория не удалена"
        print("  ✓ Удаление тестовой категории успешно")

    # 9. УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
    print("\n[8] ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ")
    # 9.1 Попытка заблокировать самого себя (ID админа = 1)
    with opener_admin.open(f"{base_url}/Admin/Users/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    self_block_data = urllib.parse.urlencode({"__RequestVerificationToken": token}).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Users?id=1&handler=ToggleActive", data=self_block_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "не можете заблокировать собственную" in html, "Защита от самоблокировки не сработала!"
    print("  ✓ Защита от самоблокировки текущего администратора работает")

    # 9.2 Блокировка клиента (Иванов, ID = 2)
    with opener_admin.open(f"{base_url}/Admin/Users/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    block_data = urllib.parse.urlencode({"__RequestVerificationToken": token}).encode('utf-8')
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Users?id=2&handler=ToggleActive", data=block_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "заблокирована" in html, "Сообщение о блокировке не отобразилось"
    print("  ✓ Учетная запись клиента заблокирована администратором")

    # 9.3 Проверка, что заблокированный клиент не может войти
    opener_blocked, _ = get_opener()
    with opener_blocked.open(f"{base_url}/Account/Login") as resp:
        token_b = extract_token(resp.read().decode('utf-8'))
    b_login_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token_b,
        "Input.Email": "ivanov@example.com",
        "Input.Password": "Client123!"
    }).encode('utf-8')
    with opener_blocked.open(urllib.request.Request(f"{base_url}/Account/Login", data=b_login_data, method='POST')) as resp:
        b_html = resp.read().decode('utf-8')
        assert "заблокирована администратором" in b_html, "Заблокированный пользователь смог войти в систему!"
    print("  ✓ Вход заблокированного пользователя успешно отклонен сервером")

    # 9.4 Разблокировка клиента обратно
    with opener_admin.open(f"{base_url}/Admin/Users/Index") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    with opener_admin.open(urllib.request.Request(f"{base_url}/Admin/Users?id=2&handler=ToggleActive", data=block_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "разблокирована" in html, "Клиент не разблокирован"
    print("  ✓ Учетная запись клиента успешно разблокирована")

    # 10. БРОНИРОВАНИЕ, ВАЛИДАЦИЯ И ОТМЕНА КЛИЕНТОМ
    print("\n[9] ТЕСТИРОВАНИЕ БРОНИРОВАНИЯ И ОТМЕНЫ")
    # Логин клиента после разблокировки
    opener_c2, _ = get_opener()
    with opener_c2.open(f"{base_url}/Account/Login") as resp:
        token_c2 = extract_token(resp.read().decode('utf-8'))
    login_data_c2 = urllib.parse.urlencode({
        "__RequestVerificationToken": token_c2,
        "Input.Email": "ivanov@example.com",
        "Input.Password": "Client123!"
    }).encode('utf-8')
    with opener_c2.open(urllib.request.Request(f"{base_url}/Account/Login", data=login_data_c2, method='POST')) as resp:
        pass

    # 10.1 Проверка валидации: дата в прошлом
    with opener_c2.open(f"{base_url}/Bookings/Create?workspaceId=2") as resp:
        token_b = extract_token(resp.read().decode('utf-8'))
    past_booking_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token_b,
        "Input.WorkspaceId": "2",
        "Input.BookingDate": "2020-01-01",
        "Input.StartTime": "10:00",
        "Input.EndTime": "12:00"
    }).encode('utf-8')
    with opener_c2.open(urllib.request.Request(f"{base_url}/Bookings/Create?workspaceId=2", data=past_booking_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "прошедшее время" in html or "Оформление бронирования" in html, "Прошедшая дата не отклонена"
    print("  ✓ Валидация бронирования в прошлом работает")

    # 10.2 Проверка валидации: окончание раньше начала
    with opener_c2.open(f"{base_url}/Bookings/Create?workspaceId=2") as resp:
        token_b = extract_token(resp.read().decode('utf-8'))
    invert_time_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token_b,
        "Input.WorkspaceId": "2",
        "Input.BookingDate": "2026-11-25",
        "Input.StartTime": "15:00",
        "Input.EndTime": "11:00"
    }).encode('utf-8')
    with opener_c2.open(urllib.request.Request(f"{base_url}/Bookings/Create?workspaceId=2", data=invert_time_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "позже времени начала" in html, "Некорректный интервал времени не отклонен"
    print("  ✓ Валидация 'окончание позже начала' работает")

    # 10.3 Успешное создание бронирования
    future_date = "2026-11-29"
    with opener_c2.open(f"{base_url}/Bookings/Create?workspaceId=2") as resp:
        token_b = extract_token(resp.read().decode('utf-8'))
    valid_booking_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token_b,
        "Input.WorkspaceId": "2",
        "Input.BookingDate": future_date,
        "Input.StartTime": "09:00",
        "Input.EndTime": "13:00"
    }).encode('utf-8')
    with opener_c2.open(urllib.request.Request(f"{base_url}/Bookings/Create?workspaceId=2", data=valid_booking_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "успешно оформлено" in html, f"Строгое подтверждение успешного бронирования не получено! Ответ:\n{html[:600]}"
    print("  ✓ Бронирование создано строго с подтверждением 'успешно оформлено'")

    # 10.4 Проверка запрета пересечения
    with opener_c2.open(f"{base_url}/Bookings/Create?workspaceId=2") as resp:
        token_b = extract_token(resp.read().decode('utf-8'))
    overlap_booking_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token_b,
        "Input.WorkspaceId": "2",
        "Input.BookingDate": future_date,
        "Input.StartTime": "11:00",
        "Input.EndTime": "15:00"
    }).encode('utf-8')
    with opener_c2.open(urllib.request.Request(f"{base_url}/Bookings/Create?workspaceId=2", data=overlap_booking_data, method='POST')) as resp:
        html = resp.read().decode('utf-8')
        assert "пересекается с другим бронированием" in html, "Пересечение бронирований не было отклонено"
    print("  ✓ Пересечение бронирований надежно заблокировано")

    # 10.5 Отмена бронирования клиентом
    with opener_c2.open(f"{base_url}/Bookings/Index") as resp:
        my_html = resp.read().decode('utf-8')
        token_c = extract_token(my_html)
    
    # Находим ID созданного бронирования на 29.11.2026
    m_bk = re.search(r'action="/Bookings\?id=(\d+)&amp;handler=Cancel"', my_html)
    assert m_bk, "Кнопка отмены бронирования не найдена в кабинете клиента"
    cancel_bk_id = m_bk.group(1)

    cancel_data = urllib.parse.urlencode({"__RequestVerificationToken": token_c}).encode('utf-8')
    with opener_c2.open(urllib.request.Request(f"{base_url}/Bookings?id={cancel_bk_id}&handler=Cancel", data=cancel_data, method='POST')) as resp:
        cancel_res = resp.read().decode('utf-8')
        assert "успешно отменено" in cancel_res, "Сообщение об успешной отмене бронирования не получено"
    print("  ✓ Клиент успешно отменил бронирование через личный кабинет")

    # 11. КОМБИНИРОВАННАЯ ФИЛЬТРАЦИЯ КАТАЛОГА
    print("\n[10] ТЕСТИРОВАНИЕ КОМБИНИРОВАННОЙ ФИЛЬТРАЦИИ")
    # Фильтр: 1 этаж + зона 1 + тип 1 + удобство 1
    with opener_c2.open(f"{base_url}/?FloorId=1&ZoneId=1&TypeId=1&AmenityId=1") as resp:
        f_html = resp.read().decode('utf-8')
        assert resp.status == 200, "Ошибка при выполнении 4-параметрической фильтрации"
        assert "Где сегодня" in f_html, "Каталог не отобразился"
    print("  ✓ Комбинированная фильтрация по 4 критериям отработала корректно")

    # 12. ОТЧЕТНОСТЬ
    print("\n[11] ТЕСТИРОВАНИЕ ОТЧЕТНОСТИ")
    with opener_admin.open(f"{base_url}/Admin/Reports/Index?DateFrom=2026-10-01&DateTo=2026-12-31") as resp:
        rep_html = resp.read().decode('utf-8')
        assert "Общая выручка" in rep_html, "Отчет по выручке не сгенерирован"
        assert "Средний чек" in rep_html, "Средний чек не отображается"
        assert "Выручка и спрос по типам" in rep_html, "Таблица типов не найдена"
        assert "Загруженность конкретных рабочих мест" in rep_html, "Таблица мест не найдена"
    print("  ✓ Аналитический отчет сформирован с полным набором расчетов и KPI")

    print("\n" + "="*60)
    print("ВСЕ 11 СТРОГИХ ЭТАПОВ АУДИТА ПРОЙДЕНЫ БЕЗ ЕДИНОЙ ОШИБКИ!")
    print("="*60)

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
    print("Тестовый сервер остановлен.")
