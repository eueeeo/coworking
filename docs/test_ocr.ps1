[Windows.Media.Ocr.OcrEngine, Windows.Foundation.Diagnostics, ContentType = WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Foundation.Diagnostics, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation.Diagnostics, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }

function AwaitAction($asyncOp, $resType) {
    $m = $asTaskGeneric[0].MakeGenericMethod($resType)
    $t = $m.Invoke($null, @($asyncOp))
    $t.Wait()
    return $t.Result
}

$lang = [Windows.Globalization.Language]::new('ru-RU')
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if (-not $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}
Write-Host "OCR Engine: $($engine.RecognizerLanguage.LanguageTag)"

function Run-Ocr($path) {
    Write-Host "=== OCR FOR $path ==="
    $absPath = [System.IO.Path]::GetFullPath($path)
    $fileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($absPath)
    $file = AwaitAction $fileOp ([Windows.Storage.StorageFile])
    $streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = AwaitAction $streamOp ([Windows.Storage.Streams.IRandomAccessStream])
    $decoderOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = AwaitAction $decoderOp ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmpOp = $decoder.GetSoftwareBitmapAsync()
    $bmp = AwaitAction $bmpOp ([Windows.Graphics.Imaging.SoftwareBitmap])
    $ocrOp = $engine.RecognizeAsync($bmp)
    $res = AwaitAction $ocrOp ([Windows.Media.Ocr.OcrResult])
    Write-Host $res.Text
}

Run-Ocr "docs/chen_from_primer_sokr.png"
Run-Ocr "docs/chen_from_primer_horoshiy.png"
