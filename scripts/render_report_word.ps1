param(
    [string]$Docx = "docs/BAO_CAO_DO_AN.docx",
    [string]$Pdf = "tmp/report/BAO_CAO_DO_AN.pdf"
)
$ErrorActionPreference = "Stop"
$docxPath = (Resolve-Path -LiteralPath $Docx).Path
$pdfPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Pdf))
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($pdfPath)) | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null
try {
    $document = $word.Documents.Open($docxPath, $false, $false)
    $document.Fields.Update() | Out-Null
    foreach ($toc in $document.TablesOfContents) { $toc.Update() }
    $document.Repaginate()
    foreach ($toc in $document.TablesOfContents) { $toc.UpdatePageNumbers() }
    $document.Save()
    $document.ExportAsFixedFormat($pdfPath, 17)
    Write-Output ("PDF: " + $pdfPath)
    Write-Output ("Pages: " + $document.ComputeStatistics(2))
} finally {
    if ($null -ne $document) { $document.Close(0) }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
