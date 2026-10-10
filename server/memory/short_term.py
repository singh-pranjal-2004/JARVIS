"""
Tier 1: Short-Term Memory (Sensory Buffer)

A sliding window of the last N messages. Keeps the active conversation context alive
for OpenAI API calls while keeping token costs minimal.

When a message slides off the end, it gets archived to Tier 2 (Episodic Memory)
so nothing is truly lost.
"""

from collections import deque
from typing import Optional
from server.config import SHORT_TERM_MEMORY_SIZE


class ShortTermMemory:
    """Sliding window buffer for active conversation context."""

    def __init__(self, max_size: int = SHORT_TERM_MEMORY_SIZE):
        self._max_size = max_size
        self._buffer: deque[dict] = deque(maxlen=max_size)
        self._overflow_callback: Optional[callable] = None

    def set_overflow_callback(self, callback: callable):
        """
        Register a function to call when messages slide off the buffer.
        Used to auto-archive to Tier 2 (Episodic Memory).
        
        The callback receives a list of messages that were evicted.
        """
        self._overflow_callback = callback

    def add(self, message: dict):
        """
        Add a message to the buffer. If the buffer is full, the oldest
        message gets evicted and sent to the overflow callback.
        
        Args:
            message: OpenAI-format message dict with 'role' and 'content' keys.
        """
        evicted = None

        # If buffer is at capacity, capture the message about to be evicted
        if len(self._buffer) >= self._max_size:
            evicted = self._buffer[0]  # leftmost = oldest

        self._buffer.append(message)

        # Archive evicted message to Tier 2
        if evicted and self._overflow_callback:
            self._overflow_callback([evicted])

    def get_context(self) -> list[dict]:
        """Return the current buffer as a list for the OpenAI messages array."""
        return list(self._buffer)

    def get_last_n(self, n: int) -> list[dict]:
        """Return the last N messages from the buffer."""
        items = list(self._buffer)
        return items[-n:] if n < len(items) else items

    def clear(self) -> list[dict]:
        """
        Clear the buffer and return all messages that were in it.
        Useful for session end — archive everything to Tier 2.
        """
        messages = list(self._buffer)
        self._buffer.clear()
        return messages

    @property
    def size(self) -> int:
        return len(self._buffer)

    @property
    def max_size(self) -> int:
        return self._max_size

    def __repr__(self) -> str:
        return f"ShortTermMemory(size={self.size}/{self._max_size})"
