"""
CLI Client Configuration

The only file you need to edit on the company Mac.
Points to your personal Windows laptop's Tailscale IP.
"""

# JARVIS server URL — change to your personal laptop's Tailscale IP
# After installing Tailscale on both machines, run `tailscale ip` on Windows
# to get the stable IP (looks like 100.x.x.x)
#
# Examples:
#   Local (same machine):  http://localhost:8000
#   Tailscale:             http://100.64.1.23:8000
#   Same WiFi (fallback):  http://192.168.1.42:8000

JARVIS_SERVER_URL = "http://localhost:8000"

# Client identification
CLIENT_SOURCE = "cli"
