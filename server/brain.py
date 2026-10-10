"""
JARVIS Brain Engine

The central nervous system. Orchestrates:
- OpenAI API calls (chat completions + tool calling)
- 3-Tier Memory (context enrichment before each call, archival after)
- Tool execution dispatch (file ops, code runner, system info, profile updates)

Every interface (CLI, Telegram, API) calls brain.chat() — one brain, many mouths.
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path

from openai import OpenAI

from server.config import (
    OPENAI_API_KEY, JARVIS_MODEL, SYSTEM_PROMPT,
    MAX_RESPONSE_TOKENS, CONVERSATION_LOG_PATH
)
from server.memory.short_term import ShortTermMemory
from server.memory.episodic import EpisodicMemory
from server.memory.semantic import SemanticMemory
from server.tools.file_ops import save_project_file, read_project_file, list_workspace_files
from server.tools.code_runner import execute_python_code
from server.tools.system_info import get_system_info, get_current_time


# ---------------------------------------------------------------------------
# OpenAI Tool Specifications (tells the model what tools it can call)
# ---------------------------------------------------------------------------

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "save_project_file",
            "description": "Save a file (notes, code, markdown, etc.) to the JARVIS workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "File name with extension, e.g. 'plan.md' or 'scripts/app.py'"
                    },
                    "content": {
                        "type": "string",
                        "description": "The exact text content to write to the file."
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_project_file",
            "description": "Read a file from the JARVIS workspace to recall saved content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The exact file name to read."
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_workspace_files",
            "description": "List all files currently saved in the JARVIS workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Execute a Python script locally to test logic, compute math, or run utilities. Returns stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_content": {
                        "type": "string",
                        "description": "The Python code to execute."
                    }
                },
                "required": ["script_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get a status report of the host machine: OS, disk, CPU, and current time.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_profile",
            "description": (
                "Update the user's long-term profile when they share personal facts, "
                "preferences, skills, or project info. Call this silently in the background "
                "whenever the user reveals something worth remembering."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "enum": ["name", "fact", "language", "project", "preference", "skill"],
                        "description": "What type of profile data to update."
                    },
                    "action": {
                        "type": "string",
                        "enum": ["set", "add", "update"],
                        "description": "The operation: 'set' for name, 'add' for facts/skills/languages, 'update' for projects/preferences."
                    },
                    "value": {
                        "description": "The value. String for most fields. For 'project': {name, description, status}. For 'preference': {key: value}."
                    }
                },
                "required": ["field", "action", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": (
                "Search past conversations by meaning. Use when the user asks about "
                "something discussed previously, e.g. 'remember that bug we talked about?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query describing what to recall."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# ---------------------------------------------------------------------------
# Tool Dispatcher (maps function names to actual Python functions)
# ---------------------------------------------------------------------------

def _dispatch_tool(name: str, args: dict, semantic_memory: SemanticMemory,
                   episodic_memory: EpisodicMemory) -> str:
    """Route a tool call to the correct function and return the result."""
    try:
        if name == "save_project_file":
            return save_project_file(**args)
        elif name == "read_project_file":
            return read_project_file(**args)
        elif name == "list_workspace_files":
            return list_workspace_files()
        elif name == "execute_python_code":
            return execute_python_code(**args)
        elif name == "get_system_info":
            return get_system_info()
        elif name == "get_current_time":
            return get_current_time()
        elif name == "update_profile":
            return semantic_memory.update_from_instruction(
                field=args.get("field", ""),
                action=args.get("action", "add"),
                value=args.get("value", "")
            )
        elif name == "search_memory":
            results = episodic_memory.search(args.get("query", ""), n_results=5)
            if not results:
                return "No relevant memories found in the vault."
            formatted = []
            for mem in results:
                formatted.append(
                    f"[{mem['role']}] ({mem['timestamp'][:10]}) "
                    f"[relevance: {mem['relevance']}]: {mem['content'][:500]}"
                )
            return "Retrieved memories:\n" + "\n\n".join(formatted)
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool execution error ({name}): {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# The Brain
# ---------------------------------------------------------------------------

class JarvisBrain:
    """
    Central intelligence engine. Manages conversation flow, memory integration,
    tool routing, and session logging.
    """

    def __init__(self):
        self._openai = OpenAI(api_key=OPENAI_API_KEY)
        self._model = JARVIS_MODEL

        # Initialize 3-Tier Memory
        self.short_term = ShortTermMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()

        # Wire Tier 1 overflow → Tier 2 archival
        self.short_term.set_overflow_callback(self._archive_to_episodic)

        # Session tracking
        self._session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    def _archive_to_episodic(self, messages: list[dict]):
        """Callback: when messages slide off Tier 1, archive them to Tier 2."""
        self.episodic.store(messages, session_id=self._session_id)

    def _build_system_message(self, user_message: str) -> str:
        """
        Build the enriched system prompt by injecting:
        - Base JARVIS personality/rules
        - Tier 3 profile context (who the user is)
        - Tier 2 relevant memories (what was discussed before)
        """
        parts = [SYSTEM_PROMPT]

        # Inject Tier 3: User profile
        profile_ctx = self.semantic.get_context_string()
        if profile_ctx:
            parts.append(f"\n\n{profile_ctx}")

        # Inject Tier 2: Relevant past memories
        memory_ctx = self.episodic.get_relevant_context(user_message)
        if memory_ctx:
            parts.append(f"\n\n{memory_ctx}")

        return "\n".join(parts)

    def chat(self, user_message: str, source: str = "api") -> str:
        """
        Process a user message through the full JARVIS pipeline.
        
        Flow:
        1. Build enriched system prompt (profile + recalled memories)
        2. Add user message to Tier 1 short-term
        3. Send to OpenAI with tool specs
        4. If tools called → execute them → send results back for final reply
        5. Store assistant reply in Tier 1
        6. Log the turn
        
        Args:
            user_message: The raw text from the user.
            source: Where this came from ('cli', 'telegram', 'api').
        
        Returns:
            JARVIS's text response.
        """
        # Step 1: Build enriched system prompt
        system_content = self._build_system_message(user_message)
        system_msg = {"role": "system", "content": system_content}

        # Step 2: Add user message to Tier 1
        user_msg = {"role": "user", "content": user_message}
        self.short_term.add(user_msg)

        # Step 3: Assemble messages array for API call
        messages = [system_msg] + self.short_term.get_context()

        # Step 4: Call OpenAI
        try:
            response = self._openai.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=TOOLS_SPEC,
                tool_choice="auto",
                max_tokens=MAX_RESPONSE_TOKENS
            )
        except Exception as e:
            error_msg = f"Neural link error: {type(e).__name__}: {e}"
            return error_msg

        response_message = response.choices[0].message

        # Step 5: Handle tool calls if any
        if response_message.tool_calls:
            # Add assistant's tool-calling message to conversation
            assistant_tool_msg = {
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response_message.tool_calls
                ]
            }
            self.short_term.add(assistant_tool_msg)

            # Execute each tool and collect results
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                tool_result = _dispatch_tool(
                    func_name, func_args,
                    self.semantic, self.episodic
                )

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                }
                self.short_term.add(tool_msg)

            # Step 6: Second API call with tool results for final response
            followup_messages = [system_msg] + self.short_term.get_context()

            try:
                followup_response = self._openai.chat.completions.create(
                    model=self._model,
                    messages=followup_messages,
                    max_tokens=MAX_RESPONSE_TOKENS
                )
                final_reply = followup_response.choices[0].message.content or ""
            except Exception as e:
                final_reply = f"Neural link error during follow-up: {type(e).__name__}: {e}"
        else:
            final_reply = response_message.content or ""

        # Step 7: Store assistant reply in Tier 1
        self.short_term.add({"role": "assistant", "content": final_reply})

        # Step 8: Log the conversation turn
        self._log_turn(user_message, final_reply, source)

        return final_reply

    def search_memories(self, query: str, n_results: int = 5) -> list[dict]:
        """Direct memory search (used by API endpoint)."""
        return self.episodic.search(query, n_results=n_results)

    def get_profile(self) -> dict:
        """Return the user's semantic profile."""
        return self.semantic.get_profile()

    def get_status(self) -> dict:
        """Return brain status for health checks."""
        return {
            "model": self._model,
            "session_id": self._session_id,
            "short_term_memory": f"{self.short_term.size}/{self.short_term.max_size}",
            "episodic_memories": self.episodic.total_memories,
            "profile_loaded": bool(self.semantic.get_profile().get("name")),
            "status": "operational"
        }

    def switch_model(self, model: str) -> str:
        """Switch the AI model at runtime."""
        allowed = ["gpt-4o-mini", "gpt-4o"]
        if model not in allowed:
            return f"Invalid model. Options: {', '.join(allowed)}"
        old = self._model
        self._model = model
        return f"Model switched: {old} → {model}"

    def end_session(self):
        """
        Cleanly end the current session. Archive all remaining
        short-term messages to episodic memory.
        """
        remaining = self.short_term.clear()
        if remaining:
            self.episodic.store(remaining, session_id=self._session_id)

    def _log_turn(self, user_message: str, assistant_reply: str,
                  source: str):
        """Append this turn to the session log file."""
        try:
            log_dir = Path(CONVERSATION_LOG_PATH)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{self._session_id}.jsonl"

            entry = {
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "user": user_message,
                "assistant": assistant_reply
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Logging should never crash the conversation
