import json
from generate_coursework_note import build_coursework_doc
import subprocess
import os

with open("docs/toc_pages.json", "r", encoding="utf-8-sig") as f:
    toc_pages = json.load(f)

print("Applying exact TOC pages:", toc_pages)
docx_path = "docs/Пояснительная_записка_исправленная_по_образцу.docx"
build_coursework_doc(docx_path, toc_pages)

# Re-run Word COM to export updated PDF and get page count
cmd = """
$docxPath = (Resolve-Path "docs/Пояснительная_записка_исправленная_по_образцу.docx").Path
$pdfPath = [System.IO.Path]::ChangeExtension($docxPath, ".pdf")
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docxPath)
    $doc.Repaginate()
    $pages = $doc.ComputeStatistics(2)
    Write-Host "TOTAL_PAGES:$pages"
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    Write-Host "Updated PDF generated: $pdfPath"
} finally {
    $doc.Close([ref]0)
    $word.Quit()
}
"""
with open("docs/export_pdf.ps1", "w", encoding="utf-8-sig") as f:
    f.write(cmd)

res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "docs/export_pdf.ps1"], capture_output=True)
stdout = res.stdout.decode('cp1251', errors='replace')
print("PowerShell Output:\n", stdout)
print("DOCX and PDF finalized successfully!")
