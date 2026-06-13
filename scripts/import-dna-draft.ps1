param(
    [string]$InputFile = "notes\dna-import-source.txt",
    [string]$SourceType = "google_doc",
    [string]$SourceLabel = "DNA rozbor - Google dokument",
    [string]$ApiBaseUrl = "http://127.0.0.1:8000"
)

if (-not (Test-Path -LiteralPath $InputFile)) {
    Write-Error "Input file not found: $InputFile"
    exit 1
}

$rawText = [string](Get-Content -LiteralPath $InputFile -Raw -Encoding UTF8)
if ([string]::IsNullOrWhiteSpace($rawText)) {
    Write-Error "Input file is empty: $InputFile"
    exit 1
}

$payload = @{
    sourceType = $SourceType
    sourceLabel = $SourceLabel
    rawText = $rawText
} | ConvertTo-Json -Depth 6

$draft = Invoke-RestMethod `
    -Method Post `
    -Uri "$ApiBaseUrl/genetics/import-draft" `
    -ContentType "application/json; charset=utf-8" `
    -Body $payload

$draft | ConvertTo-Json -Depth 8
