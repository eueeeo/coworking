
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
