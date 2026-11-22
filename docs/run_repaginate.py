import os
import json
import subprocess

ps1_content = """
$docxPath = (Resolve-Path "docs/Пояснительная_записка_исправленная_по_образцу.docx").Path
$pdfPath = [System.IO.Path]::ChangeExtension($docxPath, ".pdf")
$jsonPath = [System.IO.Path]::Combine((Get-Location).Path, "docs/toc_pages.json")

$word = New-Object -ComObject Word.Application
$word.Visible = $false

try {
    $doc = $word.Documents.Open($docxPath)
    $doc.Repaginate()

    $headings = @(
        @{ Key = "intro"; Pattern = "ВВЕДЕНИЕ" },
        @{ Key = "sec1";  Pattern = "1. ПОСТАНОВКА ЗАДАЧИ" },
        @{ Key = "sec11"; Pattern = "1.1. Описание предметной области" },
        @{ Key = "sec12"; Pattern = "1.2. Обзор существующих аналогов" },
        @{ Key = "sec13"; Pattern = "1.3. Функциональное назначение" },
        @{ Key = "sec2";  Pattern = "2. ПРОЕКТИРОВАНИЕ ЗАДАЧИ" },
        @{ Key = "sec21"; Pattern = "2.1. Разработка диаграммы вариантов использования" },
        @{ Key = "sec22"; Pattern = "2.2. Концептуальное проектирование базы данных" },
        @{ Key = "sec23"; Pattern = "2.3. Логическое проектирование базы данных" },
        @{ Key = "sec24"; Pattern = "2.4. Проектирование интерфейса" },
        @{ Key = "sec25"; Pattern = "2.5. Описание инструментов разработки" },
        @{ Key = "sec26"; Pattern = "2.6. Физическое проектирование базы данных" }
    )

    $result = @{}
    $wdActiveEndPageNumber = 3

    foreach ($h in $headings) {
        $found = $false
        foreach ($p in $doc.Paragraphs) {
            $txt = $p.Range.Text.Trim()
            if ($txt -eq $h.Pattern) {
                $page = $p.Range.Information($wdActiveEndPageNumber)
                $result[$h.Key] = $page
                Write-Host "$($h.Pattern) -> Page $page"
                $found = $true
                break
            }
        }
        if (-not $found) {
            Write-Host "Warning: Not found: $($h.Pattern)"
        }
    }

    $json = $result | ConvertTo-Json
    [System.IO.File]::WriteAllText($jsonPath, $json, [System.Text.Encoding]::UTF8)

    $doc.SaveAs([ref]$pdfPath, [ref]17) # 17 = wdFormatPDF
    Write-Host "PDF exported to: $pdfPath"
}
finally {
    $doc.Close([ref]0)
    $word.Quit()
}
"""

with open("docs/repaginate_utf8.ps1", "w", encoding="utf-8-sig") as f:
    f.write(ps1_content)

res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "docs/repaginate_utf8.ps1"], capture_output=True)
print("Returncode:", res.returncode)
try:
    print("STDOUT:\n", res.stdout.decode('cp1251'))
except Exception:
    print("STDOUT bytes:\n", res.stdout[:200])
