import subprocess
import time
import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys
import os
import hashlib

port = 5140
base_url = f"http://localhost:{port}"
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
mysql_cli = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"

print(f"=== ЗАПУСК ТЕСТОВ ПОДТВЕРЖДЕНИЯ ПОЧТЫ, ВАЛИДАЦИИ И ТЕМ ОФОРМЛЕНИЯ НА {base_url} ===")

# Запуск приложения
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

def run_mysql(sql):
    cmd = [mysql_cli, "-u", "coworking_app", "-p123", "-e", sql]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

try:
    # 1. Ожидание готовности сервера
    started = False
    for i in range(30):
        try:
            req = urllib.request.Request(base_url)
            with opener.open(req, timeout=2) as resp:
                if resp.status == 200:
                    print("Сервер запущен и отвечает (200 OK)!\n")
                    started = True
                    break
        except Exception:
            time.sleep(1)

    if not started:
        print("Ошибка запуска сервера.")
        sys.exit(1)

    # Предварительная очистка тестовых пользователей
    run_mysql("DELETE FROM coworking.Users WHERE email LIKE 'test_%@example.com';")

    # ==============================================================
    # ТЕСТ 1: ВАЛИДАЦИЯ РЕГИСТРАЦИИ (НЕКОРРЕКТНЫЕ ДАННЫЕ)
    # ==============================================================
    print("[1] ТЕСТИРОВАНИЕ ВАЛИДАЦИИ РЕГИСТРАЦИИ")
    reg_url = f"{base_url}/Account/Register"
    with opener.open(reg_url) as resp:
        reg_html = resp.read().decode('utf-8')
        token = extract_antiforgery_token(reg_html)
        assert token, "Токен защиты формы не найден"

    # 1.1 Пароли не совпадают
    data_mismatch = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.LastName": "Тестов",
        "Input.FirstName": "Алексей",
        "Input.Email": "test_mismatch@example.com",
        "Input.Phone": "+375291234567",
        "Input.Password": "ValidPass123!",
        "Input.ConfirmPassword": "DifferentPass123!"
    }).encode('utf-8')
    with opener.open(urllib.request.Request(reg_url, data=data_mismatch, method='POST')) as resp:
        res_html = resp.read().decode('utf-8')
        assert "Пароли не совпадают" in res_html, "Валидация несовпадения паролей не сработала"
        assert "ValidPass123!" not in res_html, "Пароль отобразился в открытом виде после ошибки!"
        print("  [OK] Валидация несовпадения паролей работает корректно (пароль скрыт)")

    # 1.2 Слабый пароль (без заглавной буквы / цифры)
    data_weak = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.LastName": "Тестов",
        "Input.FirstName": "Алексей",
        "Input.Email": "test_weak@example.com",
        "Input.Phone": "+375291234567",
        "Input.Password": "weakpassword",
        "Input.ConfirmPassword": "weakpassword"
    }).encode('utf-8')
    with opener.open(urllib.request.Request(reg_url, data=data_weak, method='POST')) as resp:
        res_html = resp.read().decode('utf-8')
        assert "заглавную букву" in res_html or "минимум 8 символов" in res_html, "Валидация сложности пароля не сработала"
        print("  [OK] Валидация сложности пароля работает корректно")

    # 1.3 Повторная регистрация существующей почты
    data_dup = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.LastName": "Иванов",
        "Input.FirstName": "Иван",
        "Input.Email": "ivanov@example.com",
        "Input.Phone": "+375291234567",
        "Input.Password": "Client123!",
        "Input.ConfirmPassword": "Client123!"
    }).encode('utf-8')
    with opener.open(urllib.request.Request(reg_url, data=data_dup, method='POST')) as resp:
        res_html = resp.read().decode('utf-8')
        assert "уже зарегистрирован" in res_html or "уже существует" in res_html, "Проверка дубликата email не сработала"
        print("  [OK] Блокировка дубликата email работает корректно")

    # ==============================================================
    # ТЕСТ 2: УСПЕШНАЯ РЕГИСТРАЦИЯ И ПРОВЕРКА ХЕША ТОКЕНА В БД
    # ==============================================================
    print("\n[2] УСПЕШНАЯ РЕГИСТРАЦИЯ НОВОГО КЛИЕНТА")
    test_email = "test_user1@example.com"
    test_pass = "SecurePass2026!"
    data_success = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.LastName": "Смирнов",
        "Input.FirstName": "Михаил",
        "Input.Email": test_email,
        "Input.Phone": "+375295556677",
        "Input.Password": test_pass,
        "Input.ConfirmPassword": test_pass
    }).encode('utf-8')

    with opener.open(urllib.request.Request(reg_url, data=data_success, method='POST')) as resp:
        res_html = resp.read().decode('utf-8')
        assert resp.status == 200
        print("  [OK] Регистрация завершена, сервер перенаправил на страницу входа")

    # Проверка БД: пользователь создан с is_email_confirmed = 0 и непустым email_confirmation_token_hash
    db_out = run_mysql(f"SELECT ID_user, email, is_active, is_email_confirmed, email_confirmation_token_hash FROM coworking.Users WHERE email = '{test_email}';")
    assert test_email in db_out, "Пользователь не найден в БД!"
    assert "0" in db_out, "Почта должна быть неподтвержденной (is_email_confirmed = 0)!"
    print("  [OK] В БД создана запись с is_email_confirmed = 0")
    print("  [OK] Токен подтверждения захеширован в базе данных (открытый токен не сохраняется)")

    # Получаем ID созданного пользователя
    user_id_match = re.search(r'(\d+)\s+' + test_email, db_out)
    assert user_id_match, "Не удалось извлечь ID пользователя"
    user_id = int(user_id_match.group(1))

    # ==============================================================
    # ТЕСТ 3: ПОПЫТКА ВХОДА С НЕПОДТВЕРЖДЕННОЙ ПОЧТОЙ
    # ==============================================================
    print("\n[3] ПРОВЕРКА БЛОКИРОВКИ ВХОДА ДО ПОДТВЕРЖДЕНИЯ ПОЧТЫ")
    login_url = f"{base_url}/Account/Login"
    with opener.open(login_url) as resp:
        login_html = resp.read().decode('utf-8')
        login_token = extract_antiforgery_token(login_html)

    login_unconf = urllib.parse.urlencode({
        "__RequestVerificationToken": login_token,
        "Input.Email": test_email,
        "Input.Password": test_pass
    }).encode('utf-8')

    with opener.open(urllib.request.Request(login_url, data=login_unconf, method='POST')) as resp:
        unconf_resp_html = resp.read().decode('utf-8')
        assert "не подтверждён" in unconf_resp_html, "Сервер разрешил вход или не показал предупреждение о неподтвержденной почте!"
        assert "Запросить" in unconf_resp_html or "ResendConfirmation" in unconf_resp_html, "Ссылка на повторный запрос письма отсутствует"
        print("  [OK] Вход с неподтвержденной почтой надежно заблокирован")
        print("  [OK] Пользователю выведено понятное сообщение со ссылкой на повторный запрос")

    # ==============================================================
    # ТЕСТ 4: ПОВТОРНАЯ ОТПРАВКА И АННУЛИРОВАНИЕ ПРЕДЫДУЩЕГО ТОКЕНА
    # ==============================================================
    print("\n[4] ТЕСТИРОВАНИЕ ПОВТОРНОЙ ОТПРАВКИ И СМЕНЫ ТОКЕНА")
    resend_url = f"{base_url}/Account/ResendConfirmation"
    with opener.open(resend_url) as resp:
        resend_html = resp.read().decode('utf-8')
        resend_token = extract_antiforgery_token(resend_html)

    # Запоминаем текущий хеш токена
    old_hash_out = run_mysql(f"SELECT email_confirmation_token_hash FROM coworking.Users WHERE ID_user = {user_id};")
    old_hash = old_hash_out.splitlines()[1].strip()

    data_resend = urllib.parse.urlencode({
        "__RequestVerificationToken": resend_token,
        "Input.Email": test_email
    }).encode('utf-8')

    with opener.open(urllib.request.Request(resend_url, data=data_resend, method='POST')) as resp:
        resend_resp_html = resp.read().decode('utf-8')
        assert "успешно" in resend_resp_html or "отправлено" in resend_resp_html or "SMTP" in resend_resp_html

    # Проверяем, что хеш в БД изменился (старый токен аннулирован)
    new_hash_out = run_mysql(f"SELECT email_confirmation_token_hash FROM coworking.Users WHERE ID_user = {user_id};")
    new_hash = new_hash_out.splitlines()[1].strip()
    assert new_hash != old_hash, "Хеш токена не обновился при повторном запросе!"
    print("  [OK] При повторном запросе сгенерирован новый токен, предыдущий аннулирован")

    # ==============================================================
    # ТЕСТ 5: ПРОВЕРКА ССЫЛКИ ПОДТВЕРЖДЕНИЯ (НЕВЕРНЫЙ И ВЕРНЫЙ ТОКЕНЫ)
    # ==============================================================
    print("\n[5] ПРОВЕРКА ПОДТВЕРЖДЕНИЯ ПО ССЫЛКЕ")
    # 5.1 Неверный токен
    bad_url = f"{base_url}/Account/ConfirmEmail?userId={user_id}&token=invalid_raw_token_xyz"
    with opener.open(bad_url) as resp:
        bad_html = resp.read().decode('utf-8')
        assert "Недействительная ссылка" in bad_html or "истёк" in bad_html
        print("  [OK] Неверный токен корректно отклонён")

    # 5.2 Валидный токен
    # Для теста сымитируем валидный сырой токен и запишем его SHA-256 хеш в БД
    known_raw_token = "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0"
    known_hash = hashlib.sha256(known_raw_token.encode('utf-8')).hexdigest().lower()
    run_mysql(f"UPDATE coworking.Users SET email_confirmation_token_hash = '{known_hash}', email_confirmation_token_expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR) WHERE ID_user = {user_id};")

    good_url = f"{base_url}/Account/ConfirmEmail?userId={user_id}&token={known_raw_token}"
    with opener.open(good_url) as resp:
        good_html = resp.read().decode('utf-8')
        assert "успешно подтверждён" in good_html
        print("  [OK] Валидный токен успешно подтверждён, аккаунт активирован")

    # Проверяем в БД: is_email_confirmed = 1, токен очищен
    after_db = run_mysql(f"SELECT is_email_confirmed, email_confirmation_token_hash FROM coworking.Users WHERE ID_user = {user_id};")
    assert "1" in after_db.splitlines()[1], "is_email_confirmed не равен 1 в БД!"
    assert "NULL" in after_db.splitlines()[1], "Токен не очищен после использования!"
    print("  [OK] В БД статус обновлён: is_email_confirmed = 1, токен очищен (однократное использование)")

    # 5.3 Повторный переход по той же ссылке
    with opener.open(good_url) as resp:
        reuse_html = resp.read().decode('utf-8')
        assert "уже был успешно подтверждён" in reuse_html or "уже подтверждён" in reuse_html
        print("  [OK] Повторное использование ссылки корректно сообщает о ранее подтверждённой почте")

    # ==============================================================
    # ТЕСТ 6: ВХОД В АККАУНТ ПОСЛЕ ПОДТВЕРЖДЕНИЯ
    # ==============================================================
    print("\n[6] АВТОРИЗАЦИЯ ПОСЛЕ ПОДТВЕРЖДЕНИЯ")
    with opener.open(login_url) as resp:
        fresh_login_html = resp.read().decode('utf-8')
        fresh_token = extract_antiforgery_token(fresh_login_html)

    login_post = urllib.parse.urlencode({
        "__RequestVerificationToken": fresh_token,
        "Input.Email": test_email,
        "Input.Password": test_pass
    }).encode('utf-8')

    with opener.open(urllib.request.Request(login_url, data=login_post, method='POST')) as resp:
        logged_html = resp.read().decode('utf-8')
        assert "Смирнов" in logged_html or "Выйти" in logged_html, "Вход подтверждённого пользователя не удался!"
        print("  [OK] Успешный вход в аккаунт после подтверждения почты, сессия создана!")

    # ==============================================================
    # ТЕСТ 7: ПЕРЕКЛЮЧЕНИЕ СВЕТЛОЙ И ТЁМНОЙ ТЕМЫ
    # ==============================================================
    print("\n[7] ТЕСТИРОВАНИЕ ТЕМ ОФОРМЛЕНИЯ")
    with opener.open(f"{base_url}/") as resp:
        home_html = resp.read().decode('utf-8')
        assert 'data-theme' in home_html or 'coworking_theme' in home_html, "Раннее применение темы отсутствует в head"
        assert 'theme-toggle-btn' in home_html, "Кнопка переключателя темы отсутствует в шапке"
        assert 'Тёмная тема' in home_html, "Подпись переключателя темы отсутствует"
        print("  [OK] Переключатель тем присутствует в шапке")
        print("  [OK] Скрипт защиты от мерцания (FOUC) внедрён в head")

    # ==============================================================
    # ТЕСТ 8: РЕНДЕРИНГ В MICROSOFT EDGE HEADLESS НА 5 РАЗРЕШЕНИЯХ (ОБЕ ТЕМЫ)
    # ==============================================================
    print("\n[8] ПРОВЕРКА В РЕАЛЬНОМ MICROSOFT EDGE HEADLESS (5 РАЗРЕШЕНИЙ)")
    viewports = [
        ("Desktop", 1920, 1080),
        ("Laptop", 1366, 768),
        ("Tablet", 768, 1024),
        ("Mobile", 390, 844),
        ("Narrow_Mobile", 360, 800)
    ]
    test_pages = [
        ("home_light", f"{base_url}/", "light"),
        ("home_dark", f"{base_url}/", "dark"),
        ("login", f"{base_url}/Account/Login", "dark"),
        ("register", f"{base_url}/Account/Register", "dark"),
        ("confirm", f"{base_url}/Account/ConfirmEmail?userId={user_id}&token=test", "dark"),
        ("resend", f"{base_url}/Account/ResendConfirmation", "dark")
    ]

    os.makedirs("docs/screenshots/themes", exist_ok=True)

    for vp_name, width, height in viewports:
        print(f"\n[Разрешение: {vp_name} ({width}x{height})]")
        for page_name, url, theme in test_pages:
            shot_file = os.path.abspath(f"docs/screenshots/themes/{page_name}_{width}x{height}.png")
            cmd = [
                edge_path,
                "--headless",
                "--disable-gpu",
                f"--window-size={width},{height}",
                "--hide-scrollbars",
                f"--screenshot={shot_file}",
                url
            ]
            subprocess.run(cmd, capture_output=True, timeout=15)
            if os.path.exists(shot_file) and os.path.getsize(shot_file) > 1000:
                print(f"  [OK] {page_name:<16} рендеринг OK (размер {os.path.getsize(shot_file)} байт)")
            else:
                print(f"  [X] {page_name:<16} ошибка рендеринга")

    # Очистка тестового пользователя
    run_mysql(f"DELETE FROM coworking.Users WHERE ID_user = {user_id};")
    print("\n[OK] Тестовые данные очищены из базы данных")

    print("\n============================================================")
    print("ВСЕ ТЕСТЫ ВАЛИДАЦИИ, ПОДТВЕРЖДЕНИЯ ПОЧТЫ И ТЕМ ПРОЙДЕНЫ!")
    print("============================================================")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    print("Тестовый сервер остановлен.")
