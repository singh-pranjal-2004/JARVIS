"""
JARVIS FastAPI Server — The Main Entry Point

Starts the FastAPI server, initializes the brain, wires up API routes
and (optionally) the Telegram bot.

Run with:
    python -m server.main
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import JARVIS_HOST, JARVIS_PORT, TELEGRAM_BOT_TOKEN, ensure_data_dirs
from server.brain import JarvisBrain
from server.interfaces.api_routes import router as api_router, set_brain as set_api_brain
from server.interfaces.telegram_bot import (
    set_brain as set_telegram_brain,
    create_telegram_app,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("jarvis.server")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

brain: JarvisBrain = None
telegram_app = None


# ---------------------------------------------------------------------------
# Lifespan (startup + shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of JARVIS subsystems."""
    global brain, telegram_app

    # --- Startup ---
    logger.info("=" * 50)
    logger.info("J.A.R.V.I.S. Core Systems Initializing...")
    logger.info("=" * 50)

    # Ensure data directories exist
    ensure_data_dirs()

    # Initialize the brain
    brain = JarvisBrain()
    set_api_brain(brain)
    set_telegram_brain(brain)
    logger.info(f"Brain online. Model: {brain._model}")
    logger.info(f"Session: {brain._session_id}")
    logger.info(f"Episodic memories loaded: {brain.episodic.total_memories}")

    # Start Telegram bot (if token is configured)
    if TELEGRAM_BOT_TOKEN:
        try:
            telegram_app = create_telegram_app()
            if telegram_app:
                await telegram_app.initialize()
                await telegram_app.start()
                await telegram_app.updater.start_polling(drop_pending_updates=True)
                logger.info("Telegram bot: ONLINE (polling mode)")
        except Exception as e:
            logger.warning(f"Telegram bot failed to start: {e}")
            logger.warning("Continuing without Telegram. Fix the token and restart.")
            telegram_app = None
    else:
        logger.info("Telegram bot: DISABLED (no token configured)")

    logger.info(f"API Server: http://{JARVIS_HOST}:{JARVIS_PORT}")
    logger.info("=" * 50)
    logger.info("All systems operational. Ready for instructions, Sir.")
    logger.info("=" * 50)

    yield

    # --- Shutdown ---
    logger.info("Initiating shutdown sequence...")

    # Archive remaining short-term memory to episodic
    if brain:
        brain.end_session()
        logger.info("Session archived to episodic memory.")

    # Stop Telegram bot
    if telegram_app:
        try:
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
            logger.info("Telegram bot: OFFLINE")
        except Exception as e:
            logger.warning(f"Telegram shutdown error: {e}")

    logger.info("J.A.R.V.I.S. powered down. Goodbye, Sir.")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="J.A.R.V.I.S.",
    description="Just A Rather Very Intelligent System — Personal AI Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allow CLI client and any local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "system": "J.A.R.V.I.S.",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "chat": "POST /api/chat",
            "health": "GET /api/health",
            "memory_search": "POST /api/memory/search",
            "profile": "GET /api/profile",
            "status": "GET /api/status",
            "model_switch": "POST /api/model/switch"
        }
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Run the JARVIS server."""
    uvicorn.run(
        "server.main:app",
        host=JARVIS_HOST,
        port=JARVIS_PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
