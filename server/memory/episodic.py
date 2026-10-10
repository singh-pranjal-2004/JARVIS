"""
Tier 2: Episodic Memory (The Vault)

Uses ChromaDB to store past conversation turns as vector embeddings.
When the user says "remember that bug from last week?", this tier
searches by meaning (semantic similarity), not exact keywords.

Runs entirely locally — no cloud, no subscriptions.
Embedding cost: ~₹1.70 per 1 million words via OpenAI text-embedding-3-small.
"""

import json
import time
from datetime import datetime
from typing import Optional

import chromadb
from openai import OpenAI

from server.config import OPENAI_API_KEY, CHROMA_DB_PATH, EMBEDDING_MODEL


class EpisodicMemory:
    """ChromaDB-backed vector store for long-term conversation recall."""

    def __init__(self):
        self._client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self._collection = self._client.get_or_create_collection(
            name="jarvis_episodic",
            metadata={"description": "JARVIS conversation history vault"}
        )
        self._openai = OpenAI(api_key=OPENAI_API_KEY)

    def _embed(self, text: str) -> list[float]:
        """Generate embedding vector for a piece of text."""
        response = self._openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def store(self, messages: list[dict], session_id: str = "default",
              topic: str = "general"):
        """
        Archive conversation messages to the vector store.
        
        Args:
            messages: List of OpenAI-format message dicts.
            session_id: Identifier for the conversation session.
            topic: Auto-extracted or manual topic tag.
        """
        for msg in messages:
            # Skip system messages and tool messages — they're not useful for recall
            if msg.get("role") in ("system", "tool"):
                continue

            content = msg.get("content", "")
            if not content or not isinstance(content, str):
                continue

            # Truncate very long messages for embedding (save tokens)
            embed_text = content[:2000] if len(content) > 2000 else content

            timestamp = datetime.now().isoformat()
            doc_id = f"{session_id}_{int(time.time() * 1000)}_{hash(content) % 100000}"

            try:
                embedding = self._embed(embed_text)

                self._collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[{
                        "role": msg.get("role", "unknown"),
                        "session_id": session_id,
                        "topic": topic,
                        "timestamp": timestamp
                    }]
                )
            except Exception as e:
                # Don't crash the conversation if archiving fails
                print(f"[Memory Vault] Warning: Failed to archive message: {e}")

    def search(self, query: str, n_results: int = 5,
               session_id: Optional[str] = None) -> list[dict]:
        """
        Search past memories by meaning.
        
        Args:
            query: Natural language search query.
            n_results: Max number of results to return.
            session_id: Optional filter to search within a specific session.
            
        Returns:
            List of dicts with 'content', 'role', 'timestamp', 'session_id', 'relevance'.
        """
        if self._collection.count() == 0:
            return []

        try:
            query_embedding = self._embed(query)

            where_filter = None
            if session_id:
                where_filter = {"session_id": session_id}

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, self._collection.count()),
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            memories = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0

                    memories.append({
                        "content": doc,
                        "role": meta.get("role", "unknown"),
                        "timestamp": meta.get("timestamp", ""),
                        "session_id": meta.get("session_id", ""),
                        "topic": meta.get("topic", ""),
                        "relevance": round(1 - distance, 4)  # Convert distance to similarity
                    })

            return memories

        except Exception as e:
            print(f"[Memory Vault] Warning: Search failed: {e}")
            return []

    def get_relevant_context(self, query: str, max_tokens_estimate: int = 500) -> str:
        """
        Get a formatted string of relevant past memories to inject into the system prompt.
        Used by the Brain to enrich context before each API call.
        
        Args:
            query: The current user message to find relevant memories for.
            max_tokens_estimate: Rough character limit to keep context injection small.
        """
        memories = self.search(query, n_results=3)

        if not memories:
            return ""

        context_parts = ["[RECALLED MEMORIES FROM PAST CONVERSATIONS]"]
        char_count = 0

        for mem in memories:
            # Only include reasonably relevant memories
            if mem["relevance"] < 0.3:
                continue

            entry = f"- [{mem['role']}] ({mem['timestamp'][:10]}): {mem['content'][:300]}"
            if char_count + len(entry) > max_tokens_estimate * 4:  # Rough char-to-token ratio
                break

            context_parts.append(entry)
            char_count += len(entry)

        if len(context_parts) <= 1:
            return ""

        return "\n".join(context_parts)

    @property
    def total_memories(self) -> int:
        return self._collection.count()

    def __repr__(self) -> str:
        return f"EpisodicMemory(total_memories={self.total_memories})"
