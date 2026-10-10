"""
CLI Client Configuration

The only file you need to edit on the company Mac.
Points to your personal Windows laptop.

TWO MODES:
  1. HOME (same WiFi):  Use your Windows laptop's local IP
     → Find it by running `ipconfig` in PowerShell on Windows
     → Look for "IPv4 Address" under your WiFi adapter (like 192.168.1.42)

  2. REMOTE (away from home):  Use your Cloudflare Tunnel URL
     → Start the tunnel on Windows: scripts/start_tunnel.bat
     → It prints a URL like https://xxx-xxx-xxx.trycloudflare.com
     → Paste that URL here
"""

# ============================================
# CHANGE THIS to your Windows laptop's address
# ============================================

# At home (same WiFi) — use local IP:
JARVIS_SERVER_URL = "http://192.168.1.42:8000"

# Away from home — switch to your Cloudflare tunnel URL:
# JARVIS_SERVER_URL = "https://your-tunnel-url.trycloudflare.com"

# ============================================

# Client identification
CLIENT_SOURCE = "cli"
