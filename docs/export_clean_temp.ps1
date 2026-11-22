
$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open('D:\Coworking\docs\Пояснительная_записка_исправленная_по_образцу.docx')
    $doc.Repaginate()
    $pages = $doc.ComputeStatistics(2)
    $words = $doc.Words.Count
    Write-Host "DOCX opened successfully! Pages: $pages, Words: $words"
    
    $doc.ExportAsFixedFormat('D:\Coworking\docs\Пояснительная_записка_исправленная_по_образцу.pdf', 17)
    Write-Host "Exported to PDF: D:\Coworking\docs\Пояснительная_записка_исправленная_по_образцу.pdf"
    $doc.Close(0)
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
