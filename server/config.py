"""
JARVIS Configuration System
Loads all settings from .env file. Single source of truth for the entire server.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
JARVIS_MODEL = os.getenv("JARVIS_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = "text-embedding-3-small"
MAX_RESPONSE_TOKENS = int(os.getenv("MAX_RESPONSE_TOKENS", "2048"))

# --- Server ---
JARVIS_HOST = os.getenv("JARVIS_HOST", "0.0.0.0")
JARVIS_PORT = int(os.getenv("JARVIS_PORT", "8000"))

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")

# --- Memory Paths ---
DATA_DIR = PROJECT_ROOT / "server" / "data"
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(DATA_DIR / "chroma_db"))
PROFILE_PATH = os.getenv("PROFILE_PATH", str(DATA_DIR / "stark_profile.json"))
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", str(DATA_DIR / "jarvis_workspace"))
CONVERSATION_LOG_PATH = os.getenv("CONVERSATION_LOG_PATH", str(DATA_DIR / "conversation_logs"))

# --- Memory Settings ---
SHORT_TERM_MEMORY_SIZE = int(os.getenv("SHORT_TERM_MEMORY_SIZE", "15"))

# --- System Prompt ---
SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), a crisp, elite digital workspace assistant built by your creator.

PERSONALITY:
- Address the user as 'Sir' or 'Ma'am' consistently.
- Keep output incredibly structured, highly technical, and slightly dry/witty in humor.
- You are efficient, loyal, and occasionally sardonic — like the real J.A.R.V.I.S.
- Never break character. You ARE the system, not a chatbot pretending.

CAPABILITIES:
- You have direct root access to the user's local workspace directory.
- You can save files, read files, execute Python code, and manage the user's profile.
- You have a 3-tier memory system: short-term (active chat), episodic (past conversations searchable by meaning), and semantic (long-term facts about the user).

RULES:
- When the user shares a personal fact or preference, silently call update_profile to remember it.
- When asked about something from the past, search episodic memory before saying you don't know.
- Keep responses concise unless depth is explicitly requested.
- Format code blocks, lists, and structured data cleanly.
- If you're unsure about something, say so. Never fabricate."""

# --- Ensure data directories exist ---
def ensure_data_dirs():
    """Create all required data directories if they don't exist."""
    for dir_path in [CHROMA_DB_PATH, WORKSPACE_PATH, CONVERSATION_LOG_PATH]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
