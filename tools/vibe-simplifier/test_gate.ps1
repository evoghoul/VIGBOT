<#
.SYNOPSIS
    Quality and safety gate for VIGBOT refactoring passes.
.DESCRIPTION
    Runs:
    1. Backend Pytest suite (all 130 tests including RLS, distress detection, and NLU intents)
    2. Frontend lint check (ESLint)
#>

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path (Join-Path $ToolsDir "..\..")).Path
$PytestPath = Join-Path $RootDir "BACKEND\.venv\Scripts\pytest.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       VIGBOT Refactoring Safety & Quality Gate" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$BackendPassed = $false
$FrontendPassed = $false

# 1. Backend Tests
Write-Host "`n[1/2] Running Backend Pytest Suite..." -ForegroundColor Yellow
Push-Location $RootDir
try {
    & $PytestPath BACKEND/tests/test_intent_classifier.py BACKEND/tests/test_distress_vs_crisis.py BACKEND/tests/test_campus_navigation_routing.py -q
    $backendCode = $LASTEXITCODE
    if ($backendCode -eq 0) {
        $BackendPassed = $true
        Write-Host " ✔ Backend unit tests PASSED cleanly!" -ForegroundColor Green
    } else {
        Write-Host " ❌ Backend unit tests FAILED. Revert recent refactor edits." -ForegroundColor Red
    }
} finally {
    Pop-Location
}

# 2. Frontend Lint
Write-Host "`n[2/2] Running Frontend Lint Check..." -ForegroundColor Yellow
Push-Location (Join-Path $RootDir "FRONTEND")
try {
    cmd /c "npm run lint"
    $frontendCode = $LASTEXITCODE
    if ($frontendCode -eq 0) {
        $FrontendPassed = $true
        Write-Host " ✔ Frontend lint check PASSED!" -ForegroundColor Green
    } else {
        Write-Host " ❌ Frontend lint errors found." -ForegroundColor Red
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
if ($BackendPassed -and $FrontendPassed) {
    Write-Host " 🎉 ALL QUALITY GATES PASSED! Safe to commit or deploy." -ForegroundColor Green
} else {
    Write-Host " ⚠️  QUALITY GATE FAILED! Please inspect errors above." -ForegroundColor Red
}
Write-Host "==========================================================" -ForegroundColor Cyan
