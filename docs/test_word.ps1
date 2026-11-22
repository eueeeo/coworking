$word = New-Object -ComObject Word.Application
Write-Host "Word COM Version: $($word.Version)"
$word.Quit()
