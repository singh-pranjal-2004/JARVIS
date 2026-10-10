# 🌌 J.A.R.V.I.S. — Just A Rather Very Intelligent System

A personal AI assistant with a 3-tier memory system, tool execution, and multi-interface access (Terminal CLI + Telegram mobile). Built to run on your personal Windows laptop while you code and control it from anywhere.

```
                              ┌──────────────────────────────────────┐
Company Mac (CLI)             │  Personal Windows Laptop             │
  At home ──(local WiFi)────>│                                      │
  Away ────(Cloudflare)─────>│  JARVIS Server (FastAPI)             │
                              │    ├── OpenAI API (gpt-4o-mini/4o)  │
Phone (Telegram)              │    ├── 3-Tier Memory System         │
  Anywhere ──(Telegram)──────>│    └── Tools (files, code, system)  │
                              └──────────────────────────────────────┘
```

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Network Setup (How the Two Machines Connect)](#network-setup)
4. [Step 1: Personal Windows Laptop Setup (Server)](#step-1-personal-windows-laptop-setup-server)
5. [Step 2: OpenAI API Key Setup](#step-2-openai-api-key-setup)
6. [Step 3: Start the Server](#step-3-start-the-server)
7. [Step 4: Company Mac Setup (CLI Client)](#step-4-company-mac-setup-cli-client)
8. [Step 5: Cloudflare Tunnel (Remote Access)](#step-5-cloudflare-tunnel-remote-access)
9. [Step 6: Telegram Bot Setup (Mobile)](#step-6-telegram-bot-setup-mobile)
10. [Usage Guide](#usage-guide)
11. [Memory System Explained](#memory-system-explained)
12. [API Reference](#api-reference)
13. [Troubleshooting](#troubleshooting)
14. [Cost Breakdown](#cost-breakdown)

---

## Architecture Overview

| Component | Where it runs | What it does |
|---|---|---|
| JARVIS Server | Personal Windows laptop | Brain, memory, tools, Telegram bot — everything |
| CLI Client | Company Mac | Thin terminal chat — just sends HTTP, zero AI processing |
| Telegram Bot | Your phone | Mobile interface — works from anywhere, always |
| Local WiFi | Both machines at home | Direct connection via local IP (192.168.x.x) |
| Cloudflare Tunnel | Personal Windows only | Free public URL for remote access when away from home |

**Why this split?** Your company Mac stays clean — no API keys, no AI processing, no VPN installs, no IT flags. All the intelligence runs on your personal machine. The Mac only sends text over HTTP.

---

## Prerequisites

- **Personal Windows laptop** with Python 3.10+ installed
- **Company Mac** with Python 3.10+ installed (just for the thin CLI client)
- **OpenAI API account** with an API key ([platform.openai.com](https://platform.openai.com))
- **Telegram account** (optional, for mobile access)
- **GitHub account** (you already have this — the repo is there)

---

## Network Setup

### How the Two Machines Connect

There are **two modes** depending on where you are:

### Mode 1: At Home (Same WiFi) — Default

Both laptops are on the same WiFi network. Your Mac can reach your Windows laptop directly using its local IP address (like `192.168.1.42`). No extra software needed.

```
Company Mac ──(WiFi)──> 192.168.1.42:8000 ──> JARVIS Server
```

**How to find your Windows laptop's local IP:**

On your Windows laptop, open PowerShell and run:
```powershell
ipconfig
```

Look for the section that says **"Wireless LAN adapter Wi-Fi"** (or similar). Find the line:
```
IPv4 Address. . . . . . . . . : 192.168.1.42
```

That `192.168.1.x` number is what your Mac uses to reach it.

> **Tip:** This IP can occasionally change when your router reboots. If the CLI suddenly can't connect, re-run `ipconfig` on Windows and update `client/config.py` on your Mac. You can also set a static IP in your router settings to prevent this.

### Mode 2: Away from Home (Different Networks) — On Demand

When your Mac is at the office or a cafe and your Windows laptop is at home, they can't see each other on the local network. For this, you use a **Cloudflare Tunnel** — a free tool that runs on your Windows laptop and creates a temporary public URL.

```
Company Mac ──(internet)──> https://xxx.trycloudflare.com ──> JARVIS Server
```

- **Nothing gets installed on the company Mac** — it's just a normal HTTPS URL
- **No Cloudflare account needed** — the free `trycloudflare.com` quick tunnels work without signup
- **cloudflared only runs on your personal Windows laptop**
- Setup instructions in [Step 5](#step-5-cloudflare-tunnel-remote-access)

### Telegram: Always Works

Telegram uses a completely different mechanism. Your JARVIS server polls Telegram's cloud for new messages over the internet. Your phone sends messages to Telegram's servers, not directly to your laptop. So Telegram works from **anywhere** — home, office, mobile data — as long as your Windows laptop is on and the server is running.

```
Phone ──> Telegram Cloud ──> JARVIS polls and picks up messages
```

---

## Step 1: Personal Windows Laptop Setup (Server)

### Clone the Repository

Open PowerShell on your personal Windows laptop:

```powershell
cd $HOME\Desktop
git clone https://github.com/singh-pranjal-2004/JARVIS.git
cd JARVIS
```

### Run the Setup Script

```powershell
# Allow script execution (one-time)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Run setup
.\scripts\setup_windows.ps1
```

This will:
- ✅ Check Python is installed
- ✅ Create a virtual environment (`venv/`)
- ✅ Install all dependencies
- ✅ Create `.env` from the template
- ✅ Create data directories

### Manual Setup (if you prefer)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

---

## Step 2: OpenAI API Key Setup

### Get Your API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)

### Set a Spending Limit (IMPORTANT)

1. Go to [platform.openai.com/settings/organization/limits](https://platform.openai.com/settings/organization/limits)
2. Set a **hard limit of $5** (₹420)
3. This prevents any accidental cost surprises

### Add a Small Amount of Credit

1. Go to [platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing)
2. Add $5 (₹420) prepaid credit
3. This will last **weeks** with gpt-4o-mini

### Edit the .env File

On your Windows laptop, open the `.env` file:

```powershell
notepad .env
```

Fill in your key:

```env
OPENAI_API_KEY=sk-your-actual-key-here
JARVIS_MODEL=gpt-4o-mini
```

Save and close.

---

## Step 3: Start the Server

### Option A: Double-click launcher
Double-click `scripts/start_server.bat`

### Option B: Manual start
```powershell
cd $HOME\Desktop\JARVIS
.\venv\Scripts\Activate.ps1
python -m server.main
```

You should see:
```
==================================================
J.A.R.V.I.S. Core Systems Initializing...
==================================================
Brain online. Model: gpt-4o-mini
Session: session_20261011_143022_a1b2c3
Episodic memories loaded: 0
Telegram bot: DISABLED (no token configured)
API Server: http://0.0.0.0:8000
==================================================
All systems operational. Ready for instructions, Sir.
==================================================
```

### Test the Server

Open another PowerShell window:
```powershell
curl http://localhost:8000/
```

You should get a JSON response with JARVIS endpoint info.

### Windows Firewall

If your Mac can't connect later, allow port 8000 through the firewall. Open PowerShell **as Administrator**:

```powershell
netsh advfirewall firewall add rule name="JARVIS Server" dir=in action=allow protocol=tcp localport=8000
```

---

## Step 4: Company Mac Setup (CLI Client)

The CLI client is intentionally lightweight. No AI processing, no API keys — just sends text over HTTP.

### Create a Virtual Environment and Install Dependencies

macOS with Homebrew-managed Python blocks direct `pip install`. Use a venv:

```bash
cd ~/Desktop/Personal/JARVIS
python3 -m venv client_venv
source client_venv/bin/activate
pip install httpx rich
```

> **Every time you open a new terminal** to use the CLI, you need to activate the venv first:
> ```bash
> cd ~/Desktop/Personal/JARVIS
> source client_venv/bin/activate
> ```

### Configure the Server URL

```bash
nano client/config.py
```

Change `JARVIS_SERVER_URL` to your Windows laptop's local IP:

```python
JARVIS_SERVER_URL = "http://192.168.x.x:8000"  # Your Windows local IP from ipconfig
```

To find your Windows IP: open PowerShell on Windows and run `ipconfig`. Look for **"IPv4 Address"** under the Wi-Fi adapter.

Save: `Ctrl+O`, Enter, `Ctrl+X`.

### Run the CLI

```bash
python3 -m client.jarvis_cli
```

You should see:
```
╭────────────────────────────────────────────╮
│ J.A.R.V.I.S. — CLI Terminal Interface      │
│ Connecting to http://192.168.x.x:8000...   │
╰────────────────────────────────────────────╯
✓ Connected. Neural link established.
Type /help for commands. Type /exit to disconnect.

You: 
```

---

## Step 5: Cloudflare Tunnel (Remote Access)

Only needed when you're **away from home** and want to reach JARVIS from your company Mac over the internet. Skip this for now if you're just getting started.

### One-Time Setup (on Personal Windows Laptop)

```powershell
cd $HOME\Desktop\JARVIS
.\scripts\setup_cloudflare.ps1
```

This downloads `cloudflared.exe` (a single file, ~30MB) into the `tools/` folder. No Cloudflare account needed.

### Starting a Tunnel

Whenever you need remote access:

1. Make sure JARVIS server is running first (`scripts/start_server.bat`)
2. In a **separate** PowerShell window, run:
   ```powershell
   .\scripts\start_tunnel.bat
   ```
3. It prints output. Look for a line like:
   ```
   https://cabin-feelings-mercy-configured.trycloudflare.com
   ```
4. Copy that URL

### Using the Tunnel from Your Mac

Edit `client/config.py` on your Mac:

```python
# Comment out the local IP line and uncomment the Cloudflare line:
# JARVIS_SERVER_URL = "http://192.168.1.42:8000"
JARVIS_SERVER_URL = "https://cabin-feelings-mercy-configured.trycloudflare.com"
```

Then run the CLI normally: `python3 -m client.jarvis_cli`

### Notes on Cloudflare Tunnel

- **Free, no account needed** — uses `trycloudflare.com` quick tunnels
- The URL **changes every time** you restart the tunnel. Copy the new one each time.
- The tunnel runs alongside the server — keep both windows open
- When you're done, press `Ctrl+C` in the tunnel window to stop it
- **Switch back to local IP** when you get home for faster response

---

## Step 6: Telegram Bot Setup (Mobile)

### Create the Bot

1. Open Telegram on your phone
2. Search for **@BotFather** and start a chat
3. Send: `/newbot`
4. Give it a name: `JARVIS` (or anything you like)
5. Give it a username: `your_jarvis_bot` (must end in `bot`)
6. BotFather gives you an **HTTP API token** — copy it

### Get Your User ID

1. Search for **@userinfobot** on Telegram
2. Send: `/start`
3. It replies with your **numeric user ID** — copy it

### Configure JARVIS

Edit `.env` on your Windows laptop:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCDefghijklmnopqrstuvwxyz
TELEGRAM_ALLOWED_USER_ID=123456789
```

### Restart the Server

Stop the server (Ctrl+C) and start it again. You should see:

```
Telegram bot: ONLINE (polling mode)
```

### Test It

Open Telegram, find your bot, and send `/start`. JARVIS should reply.

---

## Usage Guide

### CLI Commands

| Command | Description |
|---|---|
| `/help` | Show all commands |
| `/status` | System status (model, memory stats) |
| `/model gpt-4o` | Switch to GPT-4o (or back to gpt-4o-mini) |
| `/search <query>` | Search past conversation memories |
| `/clear` | Clear the terminal |
| `/server` | Show server connection URL |
| `/exit` | Disconnect |

### Telegram Commands

| Command | Description |
|---|---|
| `/start` | Initialize and show help |
| `/status` | System status report |
| `/model gpt-4o-mini` | Switch AI model |
| `/profile` | View your user profile |
| `/search <query>` | Search episodic memories |

### What JARVIS Can Do

- **Chat** — Technical Q&A, brainstorming, code review
- **Save files** — "Save these notes as meeting_notes.md"
- **Read files** — "What's in that plan file we saved?"
- **Run Python code** — "Calculate the compound interest on 50000 at 8% for 5 years"
- **Remember things** — Mention facts about yourself and JARVIS updates your profile automatically
- **Recall past conversations** — "What did we discuss about that API bug?"
- **System status** — "What's my disk usage?"

---

## Memory System Explained

### Tier 1: Short-Term Memory
- **What:** Last 15 messages in the active conversation
- **Tech:** Python deque (in-memory)
- **Purpose:** Keeps the current chat flowing naturally
- **When it fills up:** Oldest messages auto-archive to Tier 2

### Tier 2: Episodic Memory (The Vault)
- **What:** All past conversations, searchable by meaning
- **Tech:** ChromaDB with OpenAI embeddings (local, free)
- **Purpose:** "Remember that bug from last week?" → finds it semantically
- **Cost:** ~₹1.70 per 1 million words for embeddings

### Tier 3: Semantic Memory (The Profile)
- **What:** Long-term facts about you (preferences, skills, projects)
- **Tech:** `stark_profile.json` file
- **Purpose:** JARVIS never asks "what language do you use?" twice
- **Updates:** Automatic — JARVIS calls `update_profile` silently when you mention facts

### How They Work Together

Every time you send a message, JARVIS:
1. Adds it to Tier 1 (short-term)
2. Searches Tier 2 for relevant past memories
3. Reads Tier 3 for your profile context
4. Injects memories + profile into the system prompt
5. Sends enriched context to OpenAI
6. After responding, logs the turn for future recall

---

## API Reference

All endpoints are prefixed with `/api`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Send a message, get a reply |
| `POST` | `/api/memory/search` | Search episodic memory |
| `GET` | `/api/profile` | Get user profile |
| `POST` | `/api/model/switch` | Switch AI model |
| `GET` | `/api/status` | Detailed system status |

### POST /api/chat

```json
{
  "message": "Hello JARVIS, what's the time?",
  "source": "cli"
}
```

Response:
```json
{
  "reply": "Good afternoon, Sir. It is Sunday, October 11, 2026 at 2:30 PM.",
  "session_id": "session_20261011_143022_a1b2c3",
  "model": "gpt-4o-mini"
}
```

### POST /api/memory/search

```json
{
  "query": "that database migration issue",
  "n_results": 3
}
```

---

## Troubleshooting

### "Cannot reach JARVIS server" from CLI

1. **Is the server running?** Check the PowerShell window on your Windows laptop
2. **Correct IP?** Re-run `ipconfig` on Windows and check the IP in `client/config.py`
3. **Same WiFi?** Both machines must be on the same WiFi network for local IP mode
4. **Firewall?** Windows Firewall might block port 8000:
   ```powershell
   # Run as Administrator on Windows
   netsh advfirewall firewall add rule name="JARVIS Server" dir=in action=allow protocol=tcp localport=8000
   ```
5. **Using Cloudflare tunnel?** Make sure the tunnel is running and the URL in `client/config.py` matches the current tunnel URL

### "OPENAI_API_KEY not set"

- Make sure `.env` exists in the project root (not `.env.example`)
- Make sure the key doesn't have quotes around it in `.env`
- Restart the server after editing `.env`

### Telegram bot not responding

- Verify `TELEGRAM_BOT_TOKEN` is correct in `.env`
- Verify `TELEGRAM_ALLOWED_USER_ID` is your numeric ID (not username)
- Check server logs for "Telegram bot: ONLINE"
- Try `/start` in the bot chat

### ChromaDB errors on startup

```powershell
# If ChromaDB has issues, reset the vector store:
rmdir /s /q server\data\chroma_db
# Then restart the server — it recreates automatically
```

### Server crashes with "Module not found"

```powershell
# Make sure venv is activated
.\venv\Scripts\Activate.ps1
# Reinstall dependencies
pip install -r requirements.txt
```

### Cloudflare tunnel won't start

- Make sure you ran `.\scripts\setup_cloudflare.ps1` first
- Check that `tools\cloudflared.exe` exists
- Make sure the JARVIS server is running before starting the tunnel
- If download fails, manually download from [cloudflare/cloudflared releases](https://github.com/cloudflare/cloudflared/releases/latest) and save as `tools\cloudflared.exe`

---

## Cost Breakdown

### gpt-4o-mini (Default — Recommended)

| Component | Monthly Cost |
|---|---|
| Chat (casual daily use) | ~₹70 ($0.85) |
| Embeddings (memory) | ~₹2 (negligible) |
| Telegram | Free |
| Cloudflare Tunnel | Free |
| ChromaDB | Free (local) |
| **Total** | **~₹70/month** |

### gpt-4o (Switch when needed)

| Component | Monthly Cost |
|---|---|
| Chat (daily use) | ~₹1,130 ($13.50) |
| Everything else | Same as above |
| **Total** | **~₹1,130/month** |

You only pay for API calls. If JARVIS sits idle for a week, cost is ₹0.

---

## Project Structure

```
JARVIS/
├── README.md
├── .env.example              # Template — copy to .env
├── .gitignore
├── requirements.txt
│
├── server/                   # The Brain (runs on Windows)
│   ├── main.py               # FastAPI entry point
│   ├── config.py             # All settings from .env
│   ├── brain.py              # OpenAI + memory + tool orchestration
│   ├── memory/
│   │   ├── short_term.py     # Tier 1: Sliding window
│   │   ├── episodic.py       # Tier 2: ChromaDB vault
│   │   └── semantic.py       # Tier 3: User profile
│   ├── tools/
│   │   ├── file_ops.py       # Save/read workspace files
│   │   ├── code_runner.py    # Execute Python safely
│   │   └── system_info.py    # OS/disk/time reporting
│   ├── interfaces/
│   │   ├── api_routes.py     # REST endpoints
│   │   └── telegram_bot.py   # Telegram handler
│   └── data/                 # Runtime data (gitignored)
│
├── client/                   # Thin CLI (runs on Mac)
│   ├── jarvis_cli.py         # Terminal chat interface
│   └── config.py             # Server URL config (local IP or Cloudflare URL)
│
├── scripts/
│   ├── setup_windows.ps1     # One-time Windows setup
│   ├── setup_cloudflare.ps1  # One-time Cloudflare tunnel setup
│   ├── start_server.bat      # Quick server launcher
│   └── start_tunnel.bat      # Quick tunnel launcher
│
└── tools/                    # Downloaded binaries (gitignored)
    └── cloudflared.exe       # Created by setup_cloudflare.ps1
```

---

## Development Workflow

```
Company Mac                          Personal Windows
───────────                          ─────────────────
Edit code in Kiro IDE                 
    │                                 
git push ──────────────────────────> git pull
    │                                     │
    │                                 Restart server
    │                                     │
python3 -m client.jarvis_cli ────────> JARVIS responds
```

To speed up the dev loop, you can set up auto-pull on Windows:
```powershell
# Quick pull-and-restart (run on Windows after pushing from Mac)
git pull && python -m server.main
```

---

## License

Personal project. Built with admiration for Tony Stark's vision.
