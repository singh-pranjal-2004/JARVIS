"""
JARVIS CLI Client — The Thin Terminal Interface

A lightweight script that sends your messages to the JARVIS server
and displays responses with nice formatting. This is what you run
on your company Mac — zero AI processing happens here.

Usage:
    python -m client.jarvis_cli

Requirements (install on company Mac):
    pip install httpx rich
"""

import sys
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from client.config import JARVIS_SERVER_URL, CLIENT_SOURCE

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

console = Console()
API_BASE = JARVIS_SERVER_URL.rstrip("/") + "/api"
TIMEOUT = 60.0  # seconds — some responses take time (tool calls, deep thinking)


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


# ---------------------------------------------------------------------------
# Local CLI Commands (handled before sending to server)
# ---------------------------------------------------------------------------

LOCAL_COMMANDS = {
    "/help": "Show available commands",
    "/status": "Show JARVIS system status",
    "/model <name>": "Switch model (gpt-4o-mini or gpt-4o)",
    "/search <query>": "Search past conversation memories",
    "/clear": "Clear the terminal screen",
    "/server": "Show current server URL",
    "/exit": "Disconnect from JARVIS",
}


def handle_local_command(user_input: str) -> bool:
    """
    Handle CLI-local commands. Returns True if handled, False to pass to server.
    """
    cmd = user_input.strip().lower()
    parts = user_input.strip().split(maxsplit=1)
    command = parts[0].lower()

    if command == "/help":
        console.print("\n[bold cyan]Available Commands[/bold cyan]")
        for cmd_name, desc in LOCAL_COMMANDS.items():
            console.print(f"  [green]{cmd_name:<20}[/green] {desc}")
        console.print()
        return True

    elif command == "/status":
        try:
            status = get_status()
            brain = status.get("brain", {})
            memory = status.get("memory", {})
            console.print(Panel(
                f"[cyan]Model:[/cyan] {brain.get('model', '?')}\n"
                f"[cyan]Session:[/cyan] {brain.get('session_id', '?')}\n"
                f"[cyan]Status:[/cyan] {brain.get('status', '?')}\n"
                f"[cyan]Short-term:[/cyan] {memory.get('short_term', '?')}\n"
                f"[cyan]Episodic:[/cyan] {memory.get('episodic', '?')}\n"
                f"[cyan]Profile:[/cyan] {'loaded' if memory.get('semantic_profile') else 'empty'}",
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
            f"If using Tailscale, ensure both machines are connected.[/dim]\n"
        )
        sys.exit(1)

    console.print("[green]✓ Connected. Neural link established.[/green]")
    console.print("[dim]Type /help for commands. Type /exit to disconnect.[/dim]\n")

    while True:
        try:
            # Prompt
            user_input = console.input("[bold green]You:[/bold green] ").strip()

            if not user_input:
                continue

            # Check for local commands first
            if user_input.startswith("/"):
                result = handle_local_command(user_input)
                if result == "EXIT":
                    console.print("\n[cyan]J.A.R.V.I.S.:[/cyan] Severing neural link. Goodbye, Sir.\n")
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
                # Try to render as markdown for code blocks, lists, etc.
                try:
                    console.print(Markdown(reply))
                except Exception:
                    console.print(reply)
                console.print()

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
