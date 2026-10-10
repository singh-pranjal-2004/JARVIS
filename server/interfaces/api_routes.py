"""
JARVIS REST API Routes

Endpoints for the CLI client and any future web UI to interact with the brain.
All routes share a single JarvisBrain instance (injected by main.py).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# Brain instance — set by main.py at startup
_brain = None


def set_brain(brain):
    """Inject the shared JarvisBrain instance."""
    global _brain
    _brain = brain


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="The user's message")
    source: str = Field(default="api", description="Where this request came from (cli, api, web)")


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    n_results: int = Field(default=5, ge=1, le=20)


class ModelSwitchRequest(BaseModel):
    model: str = Field(..., description="Target model: 'gpt-4o-mini' or 'gpt-4o'")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check():
    """Quick health check — is the server alive and brain loaded?"""
    if not _brain:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    status = _brain.get_status()
    return {
        "status": "online",
        "jarvis": status
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Send a message, get JARVIS's response.
    Used by CLI client, future web UI, or any HTTP client.
    """
    if not _brain:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    reply = _brain.chat(request.message, source=request.source)

    return ChatResponse(
        reply=reply,
        session_id=_brain._session_id,
        model=_brain._model
    )


@router.post("/memory/search")
async def search_memory(request: MemorySearchRequest):
    """Search episodic memory (Tier 2) by meaning."""
    if not _brain:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    results = _brain.search_memories(request.query, n_results=request.n_results)
    return {
        "query": request.query,
        "results": results,
        "total_memories": _brain.episodic.total_memories
    }


@router.get("/profile")
async def get_profile():
    """Return the user's semantic profile (Tier 3)."""
    if not _brain:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    return _brain.get_profile()


@router.post("/model/switch")
async def switch_model(request: ModelSwitchRequest):
    """Switch the AI model at runtime (gpt-4o-mini ↔ gpt-4o)."""
    if not _brain:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    result = _brain.switch_model(request.model)
    return {"message": result, "current_model": _brain._model}


@router.get("/status")
async def full_status():
    """Detailed system status including memory stats."""
    if not _brain:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    return {
        "brain": _brain.get_status(),
        "memory": {
            "short_term": f"{_brain.short_term.size}/{_brain.short_term.max_size} messages",
            "episodic": f"{_brain.episodic.total_memories} stored memories",
            "semantic_profile": bool(_brain.semantic.get_profile().get("name"))
        }
    }


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)
    voice: str = Field(default="onyx")


@router.post("/voice/tts")
async def text_to_speech(request: TTSRequest):
    """
    Generate speech audio from text using OpenAI TTS.
    Returns raw MP3 audio bytes.
    Called by the CLI client for premium TTS (routes through server
    so the Mac doesn't need direct OpenAI access).
    """
    if not _brain:
        raise HTTPException(status_code=503, detail="Brain not initialized.")

    from fastapi.responses import Response

    try:
        response = _brain._openai.audio.speech.create(
            model="tts-1",
            voice=request.voice,
            input=request.text,
            response_format="mp3"
        )
        audio_bytes = response.read()
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")
