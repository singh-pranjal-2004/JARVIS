# 🌌 J.A.R.V.I.S. — Just A Rather Very Intelligent System

A personal AI assistant with a 3-tier memory system, tool execution, and multi-interface access (Terminal CLI + Telegram mobile). Built to run on your personal Windows laptop while you code and control it from anywhere.

```
Company Mac (CLI) ──────┐
                        ├──(Tailscale VPN)──> Personal Windows Laptop (JARVIS Server)
Phone (Telegram) ───────┘                          │
                                                   ├── OpenAI API (gpt-4o-mini / gpt-4o)
                                                   ├── 3-Tier Memory (Short-term + ChromaDB + Profile)
                                                   └── Tools (File ops, Code runner, System info)
```

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Tailscale Setup (Network Bridge)](#step-1-tailscale-setup-network-bridge)
4. [Step 2: Personal Windows Laptop Setup (Server)](#step-2-personal-windows-laptop-setup-server)
5. [Step 3: OpenAI API Key Setup](#step-3-openai-api-key-setup)
6. [Step 4: Start the Server](#step-4-start-the-server)
7. [Step 5: Company Mac Setup (CLI Client)](#step-5-company-mac-setup-cli-client)
8. [Step 6: Telegram Bot Setup (Mobile)](#step-6-telegram-bot-setup-mobile)
9. [Usage Guide](#usage-guide)
10. [Memory System Explained](#memory-system-explained)
11. [API Reference](#api-reference)
12. [Troubleshooting](#troubleshooting)
13. [Cost Breakdown](#cost-breakdown)

---

## Architecture Overview

| Component | Where it runs | What it does |
|---|---|---|
| JARVIS Server | Personal Windows laptop | Brain, memory, tools, Telegram bot — everything |
| CLI Client | Company Mac | Thin terminal chat — just sends HTTP, zero AI processing |
| Telegram Bot | Your phone | Mobile interface — messages routed to server |
| Tailscale VPN | Both machines | Encrypted tunnel so Mac can reach Windows securely |

**Why this split?** Your company Mac stays clean — no API keys, no AI processing, no IT flags. All the intelligence runs on your personal machine.

---

## Prerequisites

- **Personal Windows laptop** with Python 3.10+ installed
- **Company Mac** with Python 3.10+ installed (just for the thin CLI client)
- **OpenAI API account** with an API key ([platform.openai.com](https://platform.openai.com))
- **Telegram account** (optional, for mobile access)
- **GitHub account** (you already have this — the repo is there)

---

## Step 1: Tailscale Setup (Network Bridge)

Tailscale creates an encrypted VPN mesh between your machines. Each device gets a stable IP (like `100.x.x.x`) that never changes — even across different WiFi networks.

### Why Tailscale?

- **Free** for personal use (up to 100 devices)
- **Zero config** — no port forwarding, no router settings
- **Works everywhere** — same WiFi, different networks, even office → home
- **Encrypted** — WireGuard protocol, enterprise-grade security

### Install on Personal Windows Laptop

1. Go to [tailscale.com/download/windows](https://tailscale.com/download/windows)
2. Download and run the installer
3. Sign in with your **GitHub account** (same one for both machines)
4. After sign-in, Tailscale appears in your system tray (bottom-right)
5. Open PowerShell and run:
   ```powershell
   tailscale ip
   ```
6. **Write down the IP** — it looks like `100.64.x.x` or `100.100.x.x`. This is your JARVIS server's permanent address.

### Install on Company Mac

1. Go to [tailscale.com/download/mac](https://tailscale.com/download/mac) or install from the Mac App Store
2. Open the app and sign in with the **same GitHub account**
3. Verify connection — open Terminal on Mac and run:
   ```bash
   # Replace with your Windows laptop's Tailscale IP
   ping 100.64.x.x
   ```
   If you see replies, the tunnel is working.

### Verify the Connection

From your Mac terminal:
```bash
# Replace with your actual Tailscale IP from step 5
curl http://100.64.x.x:8000/
```
(This will fail for now — the server isn't running yet. But if it says "connection refused" instead of "timeout", Tailscale is working correctly.)

---

## Step 2: Personal Windows Laptop Setup (Server)

### Clone the Repository

Open PowerShell on your personal Windows laptop:

```powershell
cd C:\Users\YourName\Desktop
git clone https://github.com/YOUR_USERNAME/JARVIS.git
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

## Step 3: OpenAI API Key Setup

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

## Step 4: Start the Server

### Option A: Double-click launcher
Double-click `scripts/start_server.bat`

### Option B: Manual start
```powershell
cd C:\Users\YourName\Desktop\JARVIS
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

---

## Step 5: Company Mac Setup (CLI Client)

The CLI client is intentionally lightweight. You only need two dependencies.

### Option A: Use from the cloned repo

```bash
cd ~/Desktop
git clone https://github.com/YOUR_USERNAME/JARVIS.git
cd JARVIS

# Install only client dependencies (no server deps needed)
pip3 install httpx rich

# Edit the server URL to point to your Windows laptop
nano client/config.py
```

Change `JARVIS_SERVER_URL` to your Tailscale IP:

```python
JARVIS_SERVER_URL = "http://100.64.x.x:8000"  # Your Tailscale IP
```

### Run the CLI

```bash
python3 -m client.jarvis_cli
```

You should see:
```
╭──────────────────────────────────────╮
│ J.A.R.V.I.S. — CLI Terminal Interface│
│ Connecting to http://100.64.x.x:8000│
╰──────────────────────────────────────╯
✓ Connected. Neural link established.
Type /help for commands. Type /exit to disconnect.

You: 
```

### Option B: Minimal standalone (no repo clone needed)

If you don't want the full repo on your company Mac, just create these two files anywhere:

**jarvis_cli_standalone.py** — copy `client/jarvis_cli.py` but hardcode the URL:
```python
# At the top, replace the import with:
JARVIS_SERVER_URL = "http://100.64.x.x:8000"
CLIENT_SOURCE = "cli"
```

Then run: `python3 jarvis_cli_standalone.py`

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

1. **Is the server running?** Check your Windows laptop
2. **Is Tailscale connected?** Check the system tray icon on both machines
3. **Correct IP?** Run `tailscale ip` on Windows and update `client/config.py`
4. **Firewall?** Windows Firewall might block port 8000:
   ```powershell
   # Run as Administrator on Windows
   netsh advfirewall firewall add rule name="JARVIS" dir=in action=allow protocol=tcp localport=8000
   ```

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

---

## Cost Breakdown

### gpt-4o-mini (Default — Recommended)

| Component | Monthly Cost |
|---|---|
| Chat (casual daily use) | ~₹70 ($0.85) |
| Embeddings (memory) | ~₹2 (negligible) |
| Telegram | Free |
| Tailscale | Free |
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
│   └── config.py             # Server URL config
│
└── scripts/
    ├── setup_windows.ps1     # One-time Windows setup
    └── start_server.bat      # Quick launcher
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
