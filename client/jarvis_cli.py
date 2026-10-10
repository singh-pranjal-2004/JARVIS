"""
JARVIS CLI Client — The Thin Terminal Interface

A lightweight script that sends your messages to the JARVIS server
and displays responses with nice formatting. Supports voice input
(Whisper STT) and voice output (local pyttsx3 or premium OpenAI TTS).

Usage:
    python -m client.jarvis_cli

Requirements (install in venv):
    pip install httpx rich sounddevice soundfile pyttsx3 numpy openai
"""

import sys
import os
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from client.config import JARVIS_SERVER_URL, CLIENT_SOURCE

# Voice system (graceful if deps missing)
try:
    from client.voice import VoiceManager
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

console = Console()
API_BASE = JARVIS_SERVER_URL.rstrip("/") + "/api"
TIMEOUT = 60.0  # seconds

# Voice manager -- initialized in main() after connection check
voice: "VoiceManager | None" = None


def check_connection() -> bool:
    """Verify the JARVIS server is reachable."""
    try:
        resp = httpx.get(f"{API_BASE}/health", timeout=5.0)
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def send_message(message: str) -> str:
    """Send a message to JARVIS and return the reply."""
    resp = httpx.post(
        f"{API_BASE}/chat",
        json={"message": message, "source": CLIENT_SOURCE},
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()["reply"]


def get_status() -> dict:
    """Get JARVIS system status."""
    resp = httpx.get(f"{API_BASE}/status", timeout=10.0)
    resp.raise_for_status()
    return resp.json()


def search_memory(query: str) -> list:
    """Search JARVIS episodic memory."""
    resp = httpx.post(
        f"{API_BASE}/memory/search",
        json={"query": query, "n_results": 5},
        timeout=15.0
    )
    resp.raise_for_status()
    return resp.json()


def switch_model(model: str) -> str:
    """Switch the AI model."""
    resp = httpx.post(
        f"{API_BASE}/model/switch",
        json={"model": model},
        timeout=10.0
    )
    resp.raise_for_status()
    return resp.json()["message"]


def get_openai_key_from_server() -> str:
    """Fetch the OpenAI API key hint from server health (for voice client)."""
    # The client needs its own OpenAI key for Whisper/TTS since those
    # run client-side. Check env var or config.
    return os.environ.get("OPENAI_API_KEY", "")


# ---------------------------------------------------------------------------
# Local CLI Commands
# ---------------------------------------------------------------------------

LOCAL_COMMANDS = {
    "/help": "Show available commands",
    "/status": "Show JARVIS system status",
    "/model <name>": "Switch model (gpt-4o-mini or gpt-4o)",
    "/search <query>": "Search past conversation memories",
    "/voice on|off": "Toggle voice input (speak to JARVIS)",
    "/speak on|off": "Toggle voice output (JARVIS speaks back)",
    "/speak local": "Use free offline TTS (default)",
    "/speak premium": "Use OpenAI TTS (onyx voice, costs money)",
    "/vstatus": "Show voice system status",
    "/clear": "Clear the terminal screen",
    "/server": "Show current server URL",
    "/exit": "Disconnect from JARVIS",
}


def handle_local_command(user_input: str) -> bool:
    """
    Handle CLI-local commands. Returns True if handled, False to pass to server.
    Returns "EXIT" string to quit.
    """
    parts = user_input.strip().split(maxsplit=1)
    command = parts[0].lower()

    if command == "/help":
        console.print("\n[bold cyan]Available Commands[/bold cyan]")
        for cmd_name, desc in LOCAL_COMMANDS.items():
            console.print(f"  [green]{cmd_name:<25}[/green] {desc}")
        if voice and (voice.voice_input_enabled or voice.voice_output_enabled):
            console.print(f"\n  [yellow]Tip:[/yellow] Just press Enter on an empty line to use voice input")
        console.print()
        return True

    elif command == "/status":
        try:
            status = get_status()
            brain = status.get("brain", {})
            memory = status.get("memory", {})
            voice_info = ""
            if voice:
                vs = voice.get_status()
                voice_info = (
                    f"\n[cyan]Voice input:[/cyan] {vs['voice_input']}\n"
                    f"[cyan]Voice output:[/cyan] {vs['voice_output']} ({vs['tts_mode']})"
                )
            console.print(Panel(
                f"[cyan]Model:[/cyan] {brain.get('model', '?')}\n"
                f"[cyan]Session:[/cyan] {brain.get('session_id', '?')}\n"
                f"[cyan]Status:[/cyan] {brain.get('status', '?')}\n"
                f"[cyan]Short-term:[/cyan] {memory.get('short_term', '?')}\n"
                f"[cyan]Episodic:[/cyan] {memory.get('episodic', '?')}\n"
                f"[cyan]Profile:[/cyan] {'loaded' if memory.get('semantic_profile') else 'empty'}"
                f"{voice_info}",
                title="📊 System Status",
                border_style="cyan"
            ))
        except Exception as e:
            console.print(f"[red]Failed to get status: {e}[/red]")
        return True

    elif command == "/model":
        if len(parts) < 2:
            console.print("[yellow]Usage: /model gpt-4o-mini  or  /model gpt-4o[/yellow]")
            return True
        try:
            result = switch_model(parts[1])
            console.print(f"[green]🔄 {result}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to switch model: {e}[/red]")
        return True

    elif command == "/search":
        if len(parts) < 2:
            console.print("[yellow]Usage: /search <your query>[/yellow]")
            return True
        try:
            results = search_memory(parts[1])
            memories = results.get("results", [])
            if not memories:
                console.print("[dim]No relevant memories found.[/dim]")
            else:
                console.print(f"\n[bold cyan]🔍 Search: \"{parts[1]}\"[/bold cyan]\n")
                for i, mem in enumerate(memories, 1):
                    preview = mem.get("content", "")[:200]
                    console.print(
                        f"  [green]{i}.[/green] [{mem.get('role', '?')}] "
                        f"({mem.get('timestamp', '?')[:10]}) "
                        f"[dim]relevance: {mem.get('relevance', 0)}[/dim]\n"
                        f"     {preview}\n"
                    )
        except Exception as e:
            console.print(f"[red]Memory search failed: {e}[/red]")
        return True

    elif command == "/voice":
        if not voice:
            console.print("[red]Voice system not available. Install: pip install sounddevice soundfile numpy openai[/red]")
            return True
        arg = parts[1].lower() if len(parts) > 1 else ""
        if arg == "on":
            if not voice.can_record:
                console.print("[red]Mic not available. Install: pip install sounddevice soundfile numpy[/red]")
            elif not voice.can_transcribe:
                console.print("[red]Whisper not available. Set OPENAI_API_KEY environment variable.[/red]")
            else:
                voice.voice_input_enabled = True
                console.print("[green]🎤 Voice input ON[/green] — press Enter on empty line to speak")
        elif arg == "off":
            voice.voice_input_enabled = False
            console.print("[dim]🎤 Voice input OFF[/dim]")
        else:
            state = "ON" if voice.voice_input_enabled else "OFF"
            console.print(f"[cyan]Voice input: {state}[/cyan]")
            console.print("[yellow]Usage: /voice on  or  /voice off[/yellow]")
        return True

    elif command == "/speak":
        if not voice:
            console.print("[red]Voice system not available. Install: pip install pyttsx3[/red]")
            return True
        arg = parts[1].lower() if len(parts) > 1 else ""
        if arg == "on":
            voice.voice_output_enabled = True
            console.print(f"[green]🔊 Voice output ON[/green] (mode: {voice.tts_mode})")
        elif arg == "off":
            voice.voice_output_enabled = False
            console.print("[dim]🔇 Voice output OFF[/dim]")
        elif arg == "local":
            voice.tts_mode = "local"
            voice.voice_output_enabled = True
            console.print("[green]🔊 Voice output ON[/green] — using local TTS (free)")
        elif arg == "premium":
            if not voice.can_speak_premium:
                console.print("[red]Premium TTS not available. Set OPENAI_API_KEY environment variable.[/red]")
            else:
                voice.tts_mode = "premium"
                voice.voice_output_enabled = True
                console.print("[green]🔊 Voice output ON[/green] — using OpenAI onyx voice (costs apply)")
        else:
            state = "ON" if voice.voice_output_enabled else "OFF"
            console.print(f"[cyan]Voice output: {state} (mode: {voice.tts_mode})[/cyan]")
            console.print("[yellow]Usage: /speak on|off|local|premium[/yellow]")
        return True

    elif command == "/vstatus":
        if not voice:
            console.print("[red]Voice system not available.[/red]")
            return True
        vs = voice.get_status()
        console.print(Panel(
            f"[cyan]Voice input:[/cyan] {vs['voice_input']}\n"
            f"[cyan]Voice output:[/cyan] {vs['voice_output']}\n"
            f"[cyan]TTS mode:[/cyan] {vs['tts_mode']}\n"
            f"[cyan]Mic available:[/cyan] {'✅' if vs['mic_available'] else '❌'}\n"
            f"[cyan]Whisper (STT):[/cyan] {'✅' if vs['whisper_available'] else '❌'}\n"
            f"[cyan]Local TTS:[/cyan] {'✅' if vs['local_tts_available'] else '❌'}\n"
            f"[cyan]Premium TTS:[/cyan] {'✅' if vs['premium_tts_available'] else '❌'}",
            title="🎤 Voice System Status",
            border_style="yellow"
        ))
        return True

    elif command == "/clear":
        console.clear()
        return True

    elif command == "/server":
        console.print(f"[cyan]Connected to:[/cyan] {JARVIS_SERVER_URL}")
        return True

    elif command in ("/exit", "/quit", "/shutdown"):
        return "EXIT"

    return False


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

def main():
    global voice

    console.print(Panel(
        "[bold cyan]J.A.R.V.I.S.[/bold cyan] — CLI Terminal Interface\n"
        f"[dim]Connecting to {JARVIS_SERVER_URL}...[/dim]",
        border_style="cyan"
    ))

    # Check connection
    if not check_connection():
        console.print(
            f"\n[bold red]⚠ Cannot reach JARVIS server at {JARVIS_SERVER_URL}[/bold red]\n"
            f"[dim]Make sure the server is running on your personal laptop.\n"
            f"Check client/config.py for the correct server URL.\n"
            f"Run 'ipconfig' on Windows to verify the IP. Check firewall if ping works but curl doesn't.[/dim]\n"
        )
        sys.exit(1)

    console.print("[green]✓ Connected. Neural link established.[/green]")

    # Initialize voice system
    if VOICE_AVAILABLE:
        api_key = get_openai_key_from_server()
        voice = VoiceManager(openai_api_key=api_key)
        voice_caps = []
        if voice.can_record and voice.can_transcribe:
            voice_caps.append("mic")
        if voice.can_speak_local:
            voice_caps.append("local TTS")
        if voice.can_speak_premium:
            voice_caps.append("premium TTS")
        if voice_caps:
            console.print(f"[dim]🎤 Voice ready: {', '.join(voice_caps)}. Use /voice on and /speak on to enable.[/dim]")
        else:
            console.print("[dim]🎤 Voice deps partially installed. Run /vstatus for details.[/dim]")
    else:
        console.print("[dim]Voice not available (optional deps not installed).[/dim]")

    console.print("[dim]Type /help for commands. Type /exit to disconnect.[/dim]\n")

    while True:
        try:
            # Build prompt with voice indicator
            prompt_parts = ["[bold green]You"]
            if voice and voice.voice_input_enabled:
                prompt_parts.append(" 🎤")
            prompt_parts.append(":[/bold green] ")
            prompt = "".join(prompt_parts)

            user_input = console.input(prompt).strip()

            # Empty input + voice enabled = voice input mode
            if not user_input and voice and voice.voice_input_enabled:
                console.print("[yellow]🎤 Listening... (speak now, silence stops recording)[/yellow]")
                transcribed = voice.listen()
                if transcribed:
                    console.print(f"[green]You (voice):[/green] {transcribed}")
                    user_input = transcribed
                else:
                    console.print("[dim]No speech detected. Try again.[/dim]")
                    continue

            if not user_input:
                continue

            # Check for local commands first
            if user_input.startswith("/"):
                result = handle_local_command(user_input)
                if result == "EXIT":
                    msg = "Severing neural link. Goodbye, Sir."
                    console.print(f"\n[cyan]J.A.R.V.I.S.:[/cyan] {msg}\n")
                    if voice:
                        voice.speak(msg)
                    break
                if result:
                    continue

            # Send to JARVIS server
            try:
                with console.status("[dim]J.A.R.V.I.S. is thinking...[/dim]", spinner="dots"):
                    reply = send_message(user_input)

                # Display response with nice formatting
                console.print()
                console.print(f"[bold cyan]J.A.R.V.I.S.:[/bold cyan]")
                try:
                    console.print(Markdown(reply))
                except Exception:
                    console.print(reply)
                console.print()

                # Speak the response if voice output is enabled
                if voice and voice.voice_output_enabled:
                    voice.speak(reply)

            except httpx.ConnectError:
                console.print("[red]⚠ Lost connection to JARVIS server. Is it still running?[/red]\n")
            except httpx.TimeoutException:
                console.print("[red]⚠ Request timed out. The server might be processing a heavy task.[/red]\n")
            except httpx.HTTPStatusError as e:
                console.print(f"[red]⚠ Server error: {e.response.status_code} — {e.response.text}[/red]\n")
            except Exception as e:
                console.print(f"[red]⚠ Error: {e}[/red]\n")

        except KeyboardInterrupt:
            console.print("\n\n[cyan]J.A.R.V.I.S.:[/cyan] Neural link interrupted. Powering down.\n")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
