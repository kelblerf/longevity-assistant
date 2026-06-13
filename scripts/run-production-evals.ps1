param(
    [string[]]$PytestArgs = @()
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$suitePath = "src/backend/tests/test_production_eval_suite.py"
$pythonCandidates = @(
    (Join-Path $repoRoot ".venv\Scripts\python.exe"),
    (Join-Path $repoRoot ".venv/bin/python"),
    "python"
)

function Resolve-PythonCommand {
    param(
        [string[]]$Candidates
    )

    foreach ($candidate in $Candidates) {
        if ($candidate -eq "python") {
            $resolved = Get-Command python -ErrorAction SilentlyContinue
            if ($resolved) {
                return $resolved.Source
            }
            continue
        }

        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

$pythonExe = Resolve-PythonCommand -Candidates $pythonCandidates

if (-not $pythonExe) {
    Write-Error "Python runtime not found. Checked: $($pythonCandidates -join ', ')"
    exit 1
}

$arguments = @(
    "-m",
    "pytest",
    $suitePath,
    "-q"
) + $PytestArgs

$commandPreview = "$pythonExe " + ($arguments -join " ")

Write-Host ""
Write-Host "Production eval suite"
Write-Host "Command: $commandPreview"

$startTime = Get-Date
$output = & $pythonExe @arguments 2>&1
$exitCode = $LASTEXITCODE
$duration = (Get-Date) - $startTime

if ($output) {
    $output | ForEach-Object { Write-Host $_ }
}

$statusLabel = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
$statusColor = if ($exitCode -eq 0) { "Green" } else { "Red" }

Write-Host ""
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "Status: $statusLabel" -ForegroundColor $statusColor
Write-Host ("Duration: {0:N2}s" -f $duration.TotalSeconds)
Write-Host "Suite: $suitePath"

exit $exitCode
