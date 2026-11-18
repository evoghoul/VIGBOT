<#
.SYNOPSIS
    Packs VIGBOT codebase into clean, token-counted context files for AI code simplification.
.DESCRIPTION
    Uses Repomix to aggregate files according to target (backend, frontend, or all)
    with all build artifacts, virtualenvs, and node_modules ignored.
.PARAMETER Target
    Target codebase slice: 'backend', 'frontend', or 'all' (default: 'backend')
.EXAMPLE
    .\pack.ps1 -Target backend
    .\pack.ps1 -Target frontend
    .\pack.ps1 -Target all
#>

param(
    [ValidateSet("backend", "frontend", "all")]
    [string]$Target = "backend"
)

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path (Join-Path $ToolsDir "..\..")).Path
$OutputDir = Join-Path $ToolsDir "output"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   VIGBOT Code Simplifier: Context Packer (Repomix)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

switch ($Target) {
    "backend" {
        $ConfigFile = Join-Path $ToolsDir "configs\backend.json"
        $TargetLabel = "Python Backend & Tests"
        $OutFile = Join-Path $OutputDir "backend-packed.md"
    }
    "frontend" {
        $ConfigFile = Join-Path $ToolsDir "configs\frontend.json"
        $TargetLabel = "TypeScript Next.js Frontend"
        $OutFile = Join-Path $OutputDir "frontend-packed.md"
    }
    "all" {
        $ConfigFile = Join-Path $ToolsDir "repomix.config.json"
        $TargetLabel = "Full VIGBOT Repository (Frontend + Backend)"
        $OutFile = Join-Path $OutputDir "vigbot-packed.md"
    }
}

Write-Host "[1/2] Packing target: $TargetLabel..." -ForegroundColor Yellow
Write-Host "      Config: $ConfigFile" -ForegroundColor Gray

Push-Location $RootDir
try {
    npx --yes repomix --config $ConfigFile
    if ($LASTEXITCODE -eq 0 -and (Test-Path $OutFile)) {
        $Item = Get-Item $OutFile
        $SizeKB = [math]::Round($Item.Length / 1KB, 1)
        Write-Host ""
        Write-Host "[2/2] Packing SUCCESSFUL!" -ForegroundColor Green
        Write-Host "      Output file: $OutFile ($SizeKB KB)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next step: Copy $OutFile or upload it to your AI model (Antigravity, Claude, or GPT) with a prompt from PROMPTS.md!" -ForegroundColor Cyan
    } else {
        Write-Host "Repomix encountered an issue. See output above." -ForegroundColor Red
    }
} finally {
    Pop-Location
}
