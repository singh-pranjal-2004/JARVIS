@echo off
REM ============================================
REM JARVIS — Quick Start Script for Windows
REM Double-click this file or run from terminal
REM ============================================

echo.
echo ========================================
echo   J.A.R.V.I.S. — Starting Server...
echo ========================================
echo.

REM Navigate to project root (one level up from scripts/)
cd /d "%~dp0\.."

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Run setup first: powershell -File scripts\setup_windows.ps1
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and add your OpenAI API key.
    pause
    exit /b 1
)

REM Activate venv and start
call venv\Scripts\activate.bat
echo Virtual environment activated.
echo Starting JARVIS server...
echo.
python -m server.main

REM If server exits, pause so user can see any errors
echo.
echo Server stopped.
pause
