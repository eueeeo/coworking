import os, subprocess

path = os.path.abspath('docs/Пояснительная_записка_исправленная_по_образцу.docx')
ps_code = f"""
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {{
    $doc = $word.Documents.Open('{path}')
    $doc.Repaginate()
    $pages = $doc.ComputeStatistics(2)
    Write-Host "WORD SUCCESS! Total Pages:" $pages
    Write-Host "Total Words:" $doc.Words.Count
    Write-Host "Total Paragraphs:" $doc.Paragraphs.Count
    
    # Check headings pages
    $headings = @(
        "Введение",
        "1. Постановка задачи",
        "1.1. Описание предметной области",
        "1.2. Обзор существующих аналогов",
        "1.3. Функциональное назначение",
        "2. Проектирование задачи",
        "2.1. Разработка диаграммы вариантов использования",
        "2.2. Концептуальное проектирование базы данных",
        "2.3. Логическое проектирование базы данных"
    )
    
    for ($i = 45; $i -le $doc.Paragraphs.Count; $i++) {{
        $p = $doc.Paragraphs.Item($i)
        $txt = $p.Range.Text.Trim()
        foreach ($h in $headings) {{
            if ($txt -eq $h) {{
                $pg = $p.Range.Information(3)
                Write-Host "$h -> Page $pg"
            }}
        }}
    }}
    
    # Export PDF
    $pdfPath = "D:\\Coworking\\docs\\Пояснительная_записка_исправленная_по_образцу.pdf"
    $doc.ExportAsFixedFormat($pdfPath, 17)
    Write-Host "WORD SUCCESS: PDF Exported to $pdfPath"
    
    $doc.Close([ref]$false)
}} catch {{
    Write-Host "WORD ERROR: " $_.Exception.Message
}} finally {{
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}}
"""

with open('docs/verify_clean_word.ps1', 'w', encoding='utf-8-sig') as f:
    f.write(ps_code)

res = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'docs/verify_clean_word.ps1'], capture_output=True, text=True, encoding='utf-8')
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
