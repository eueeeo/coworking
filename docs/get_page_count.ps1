$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open((Resolve-Path "docs/Пояснительная_записка_исправленная_по_образцу.docx").Path)
$pages = $doc.ComputeStatistics(2)
Write-Host "Total pages: $pages"
$doc.Close([ref]0)
$word.Quit()
