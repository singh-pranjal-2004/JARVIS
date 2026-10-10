"""
JARVIS Telegram Bot Interface

Routes messages from Telegram to the shared JarvisBrain.
Only responds to the authorized user (TELEGRAM_ALLOWED_USER_ID).

Setup:
1. Message @BotFather on Telegram → /newbot → copy the token
2. Message @userinfobot → /start → copy your numeric user ID
3. Put both in .env
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from server.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_ID

logger = logging.getLogger("jarvis.telegram")

# Brain instance — set by main.py at startup
_brain = None


def set_brain(brain):
    """Inject the shared JarvisBrain instance."""
    global _brain
    _brain = brain


def _is_authorized(user_id: int) -> bool:
    """Check if the Telegram user is authorized."""
    if not TELEGRAM_ALLOWED_USER_ID:
        # If no user ID is set, allow nobody (secure default)
        return False
    try:
        return str(user_id) == str(TELEGRAM_ALLOWED_USER_ID)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied. This unit is not registered to your identity.")
        return

    await update.message.reply_text(
        "🔵 J.A.R.V.I.S. online.\n\n"
        "Core systems initialized. Neural link established via Telegram.\n"
        "Ready for your instructions, Sir.\n\n"
        "Commands:\n"
        "/status — System status report\n"
        "/model — Switch AI model\n"
        "/profile — View your profile\n"
        "/search <query> — Search past memories"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    if not _is_authorized(update.effective_user.id):
        return

    if not _brain:
        await update.message.reply_text("⚠️ Brain not initialized.")
        return

    status = _brain.get_status()
    msg = (
        f"📊 SYSTEM STATUS\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Model: {status['model']}\n"
        f"Session: {status['session_id']}\n"
        f"Short-term: {status['short_term_memory']}\n"
        f"Episodic memories: {status['episodic_memories']}\n"
        f"Profile loaded: {'✅' if status['profile_loaded'] else '❌'}\n"
        f"Status: {status['status']}"
    )
    await update.message.reply_text(msg)


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /model command — switch between models."""
    if not _is_authorized(update.effective_user.id):
        return

    if not _brain:
        await update.message.reply_text("⚠️ Brain not initialized.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            f"Current model: {_brain._model}\n\n"
            f"Usage: /model gpt-4o-mini  or  /model gpt-4o"
        )
        return

    result = _brain.switch_model(args[0])
    await update.message.reply_text(f"🔄 {result}")


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command — show user profile."""
    if not _is_authorized(update.effective_user.id):
        return

    if not _brain:
        await update.message.reply_text("⚠️ Brain not initialized.")
        return

    profile = _brain.get_profile()
    name = profile.get("name", "Not set")
    langs = ", ".join(profile.get("preferred_languages", [])) or "None recorded"
    projects = profile.get("active_projects", [])
    facts_count = len(profile.get("facts", []))

    msg = (
        f"👤 USER PROFILE\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Name: {name}\n"
        f"Languages: {langs}\n"
        f"Active projects: {len(projects)}\n"
        f"Known facts: {facts_count}\n"
    )

    if projects:
        msg += "\nProjects:\n"
        for p in projects:
            msg += f"  • {p.get('name', '?')} — {p.get('status', '?')}\n"

    await update.message.reply_text(msg)


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command — search episodic memory."""
    if not _is_authorized(update.effective_user.id):
        return

    if not _brain:
        await update.message.reply_text("⚠️ Brain not initialized.")
        return

    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /search <your query>\nExample: /search that bug we discussed last week")
        return

    results = _brain.search_memories(query, n_results=3)
    if not results:
        await update.message.reply_text("🔍 No relevant memories found in the vault.")
        return

    msg = f"🔍 Memory search: \"{query}\"\n━━━━━━━━━━━━━━━━━━\n\n"
    for i, mem in enumerate(results, 1):
        content_preview = mem["content"][:200]
        msg += (
            f"{i}. [{mem['role']}] ({mem['timestamp'][:10]})\n"
            f"   Relevance: {mem['relevance']}\n"
            f"   {content_preview}\n\n"
        )

    await update.message.reply_text(msg)


# ---------------------------------------------------------------------------
# Message Handler (main chat)
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages — route to brain."""
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return

    if not _brain:
        await update.message.reply_text("⚠️ Brain not initialized. Server may be starting up.")
        return

    user_text = update.message.text
    if not user_text:
        return

    # Send typing indicator while processing
    await update.message.chat.send_action("typing")

    # Route through the brain
    reply = _brain.chat(user_text, source="telegram")

    # Telegram has a 4096 char limit per message — split if needed
    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        # Split into chunks
        for i in range(0, len(reply), 4096):
            chunk = reply[i:i + 4096]
            await update.message.reply_text(chunk)


# ---------------------------------------------------------------------------
# Bot Application Builder
# ---------------------------------------------------------------------------

def create_telegram_app() -> Application:
    """
    Build and return the Telegram bot Application.
    Called by main.py to integrate with the FastAPI server.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled.")
        return None

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot application created.")
    return app
