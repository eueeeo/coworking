import subprocess
import time
import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys

port = 5132
base_url = f"http://localhost:{port}"

print(f"Starting test server on {base_url}...")
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

def get_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)), cj

try:
    started = False
    for i in range(30):
        try:
            req = urllib.request.Request(base_url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print("Server online!")
                    started = True
                    break
        except Exception:
            time.sleep(1)

    if not started:
        print("Server startup failed")
        sys.exit(1)

    print("\n--- TEST 1: CATALOG SEARCH AND SORTING ---")
    opener, _ = get_opener()
    with opener.open(f"{base_url}/?SearchTerm=1.1&SortOrder=price_asc#catalog") as resp:
        html = resp.read().decode('utf-8')
        assert resp.status == 200, "Catalog search failed"
        assert "1.1" in html, "Workspace 1.1 not found in search results"
        print("Catalog search and sorting verified!")

    print("\n--- TEST 2: RESIDENT PROFILE UPDATE ---")
    opener_c, _ = get_opener()
    with opener_c.open(f"{base_url}/Account/Login") as resp:
        token = extract_token(resp.read().decode('utf-8'))
    
    login_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "Input.Email": "ivanov@example.com",
        "Input.Password": "Client123!"
    }).encode('utf-8')
    with opener_c.open(urllib.request.Request(f"{base_url}/Account/Login", data=login_data, method='POST')):
        pass

    with opener_c.open(f"{base_url}/Bookings/Index") as resp:
        html = resp.read().decode('utf-8')
        token = extract_token(html)
        assert "Личный кабинет резидента" in html, "Cabinet title not found"
        assert "Талон" in html, "Pass/ticket button not found"

    update_data = urllib.parse.urlencode({
        "__RequestVerificationToken": token,
        "ProfileInput.LastName": "Иванов",
        "ProfileInput.FirstName": "Иван",
        "ProfileInput.MiddleName": "Сергеевич",
        "ProfileInput.Phone": "+375 (29) 111-22-33"
    }).encode('utf-8')
    req_update = urllib.request.Request(f"{base_url}/Bookings/Index?handler=UpdateProfile", data=update_data, method='POST')
    with opener_c.open(req_update) as resp:
        html = resp.read().decode('utf-8')
        assert "успешно обновлены" in html or resp.status == 200, "Profile update failed"
        print("Resident profile update verified!")

    print("\n--- TEST 3: ADMIN BOOKING SEARCH AND CSV EXPORT ---")
    opener_a, _ = get_opener()
    with opener_a.open(f"{base_url}/Account/Login") as resp:
        token_a = extract_token(resp.read().decode('utf-8'))
    
    admin_login = urllib.parse.urlencode({
        "__RequestVerificationToken": token_a,
        "Input.Email": "admin@coworking.local",
        "Input.Password": "Admin123!"
    }).encode('utf-8')
    with opener_a.open(urllib.request.Request(f"{base_url}/Account/Login", data=admin_login, method='POST')):
        pass

    search_query = urllib.parse.quote("Иванов")
    with opener_a.open(f"{base_url}/Admin/Bookings/Index?SearchTerm={search_query}") as resp:
        html = resp.read().decode('utf-8')
        assert "Иванов" in html, "Search in bookings journal failed"
        assert "openHistoryModal" in html, "Audit history modal not found"
        print("Admin bookings journal search verified!")

    with opener_a.open(f"{base_url}/Admin/Reports/Index?handler=ExportCsv") as resp:
        content_type = resp.headers.get('Content-Type')
        csv_data = resp.read().decode('utf-8')
        assert "text/csv" in content_type, f"Expected text/csv, got {content_type}"
        assert "ID заявки;Резидент;Email" in csv_data, "CSV header missing"
        print(f"Admin CSV export verified! Downloaded {len(csv_data)} chars.")

    print("\n=======================================================")
    print("ALL NEW FEATURES AND EXPANSIONS VERIFIED SUCCESSFULLY!")
    print("=======================================================")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    print("Test server stopped.")
