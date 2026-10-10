# ============================================
# JARVIS -- Cloudflare Tunnel Setup (One-Time)
# Run this ONCE on your personal Windows laptop
# ============================================
#
# This installs cloudflared -- the tool that creates a
# secure tunnel from your laptop to the internet.
# After this, you can access JARVIS from anywhere.
#
# Open PowerShell and run:
#   cd C:\path\to\JARVIS
#   .\scripts\setup_cloudflare.ps1
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel -- Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create a tools directory
$toolsDir = Join-Path $PSScriptRoot "..\tools"
if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
}

$cloudflaredPath = Join-Path $toolsDir "cloudflared.exe"

# Step 2: Check if already installed
if (Test-Path $cloudflaredPath) {
    Write-Host "cloudflared already installed at:" -ForegroundColor Green
    Write-Host "  $cloudflaredPath" -ForegroundColor Green
    Write-Host ""
    & $cloudflaredPath --version
    Write-Host ""
    Write-Host "To start a tunnel, run:" -ForegroundColor Yellow
    Write-Host "  .\scripts\start_tunnel.bat" -ForegroundColor White
    exit 0
}

# Step 3: Download cloudflared
Write-Host "[1/2] Downloading cloudflared..." -ForegroundColor Yellow

$downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $cloudflaredPath -UseBasicParsing
    Write-Host "  Downloaded successfully." -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to download cloudflared!" -ForegroundColor Red
    Write-Host "  Try downloading manually from:" -ForegroundColor Red
    Write-Host "  https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor Red
    Write-Host "  Save the .exe as: $cloudflaredPath" -ForegroundColor Red
    exit 1
}

# Step 4: Verify it works
Write-Host ""
Write-Host "[2/2] Verifying installation..." -ForegroundColor Yellow

try {
    $version = & $cloudflaredPath --version 2>&1
    Write-Host "  $version" -ForegroundColor Green
} catch {
    Write-Host "ERROR: cloudflared downloaded but won't run." -ForegroundColor Red
    Write-Host "  Try running it manually: $cloudflaredPath --version" -ForegroundColor Red
    exit 1
}

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "cloudflared is installed at:" -ForegroundColor White
Write-Host "  $cloudflaredPath" -ForegroundColor Green
Write-Host ""
Write-Host "To start a tunnel (when you need remote access):" -ForegroundColor Yellow
Write-Host "  .\scripts\start_tunnel.bat" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: You do NOT need a Cloudflare account." -ForegroundColor Cyan
Write-Host "The free 'trycloudflare.com' tunnel works without signup." -ForegroundColor Cyan
Write-Host ""
