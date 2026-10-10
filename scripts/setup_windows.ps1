# ============================================
# JARVIS -- Windows Setup Script
# Run this ONCE on your personal Windows laptop
# ============================================
# 
# Open PowerShell as Administrator and run:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   cd C:\path\to\JARVIS
#   .\scripts\setup_windows.ps1
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. -- Windows Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "IMPORTANT: Check 'Add Python to PATH' during installation!" -ForegroundColor Red
    exit 1
}
Write-Host "  Found: $pythonVersion" -ForegroundColor Green

# Step 2: Create virtual environment
Write-Host ""
Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  Virtual environment already exists. Skipping." -ForegroundColor Green
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Virtual environment created." -ForegroundColor Green
}

# Step 3: Activate venv and install dependencies
Write-Host ""
Write-Host "[3/5] Installing dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
    exit 1
}
Write-Host "  All dependencies installed." -ForegroundColor Green

# Step 4: Create .env file from template
Write-Host ""
Write-Host "[4/5] Setting up configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  .env file already exists. Skipping." -ForegroundColor Green
    Write-Host "  (Edit it manually if you need to change settings)" -ForegroundColor DarkGray
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env from template." -ForegroundColor Green
    Write-Host ""
    Write-Host "  IMPORTANT: Edit .env and add your keys:" -ForegroundColor Red
    Write-Host "    - OPENAI_API_KEY (required)" -ForegroundColor Red
    Write-Host "    - TELEGRAM_BOT_TOKEN (optional, for mobile)" -ForegroundColor Red
    Write-Host "    - TELEGRAM_ALLOWED_USER_ID (optional, for mobile)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Open .env in Notepad:" -ForegroundColor Yellow
    Write-Host "    notepad .env" -ForegroundColor White
}

# Step 5: Create data directories
Write-Host ""
Write-Host "[5/5] Creating data directories..." -ForegroundColor Yellow
$dirs = @(
    "server\data\chroma_db",
    "server\data\jarvis_workspace",
    "server\data\conversation_logs"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "  Data directories ready." -ForegroundColor Green

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env with your OpenAI API key" -ForegroundColor White
Write-Host "  2. Run JARVIS:" -ForegroundColor White
Write-Host "     .\scripts\start_server.bat" -ForegroundColor Green
Write-Host ""
Write-Host "  Or manually:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "     python -m server.main" -ForegroundColor Green
Write-Host ""
