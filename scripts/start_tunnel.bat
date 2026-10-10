@echo off
REM ============================================
REM JARVIS -- Start Cloudflare Tunnel
REM Run this when you need remote access
REM ============================================
REM
REM This creates a temporary public URL that routes
REM to your local JARVIS server on port 8000.
REM
REM The URL looks like: https://xxx-xxx-xxx.trycloudflare.com
REM Copy it and paste into client/config.py on your Mac.
REM
REM No Cloudflare account needed. Completely free.
REM Press Ctrl+C to stop the tunnel.
REM ============================================

echo.
echo ========================================
echo   JARVIS -- Cloudflare Tunnel
echo ========================================
echo.

REM Navigate to project root
cd /d "%~dp0\.."

REM Check if cloudflared exists
if not exist "tools\cloudflared.exe" (
    echo ERROR: cloudflared not found!
    echo Run setup first: powershell -File scripts\setup_cloudflare.ps1
    pause
    exit /b 1
)

echo Starting tunnel to localhost:8000...
echo.
echo ----------------------------------------
echo   IMPORTANT: Look for the line that says
echo   something like:
echo.
echo   https://xxx-xxx-xxx.trycloudflare.com
echo.
echo   Copy that URL and use it in your
echo   client/config.py on the company Mac.
echo ----------------------------------------
echo.
echo Press Ctrl+C to stop the tunnel.
echo.

tools\cloudflared.exe tunnel --url http://localhost:8000
