"""
File Operations Tool

JARVIS's ability to save and read files in the workspace directory.
All file operations are sandboxed to the jarvis_workspace/ folder.
"""

import os
from pathlib import Path

from server.config import WORKSPACE_PATH


def _get_safe_path(filename: str) -> Path:
    """
    Resolve filename to a safe path within the workspace.
    Prevents directory traversal attacks (e.g., ../../etc/passwd).
    """
    workspace = Path(WORKSPACE_PATH).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    # Resolve the target and ensure it's inside workspace
    target = (workspace / filename).resolve()
    if not str(target).startswith(str(workspace)):
        raise ValueError(f"Access denied: path escapes workspace boundary — '{filename}'")

    return target


def save_project_file(filename: str, content: str) -> str:
    """
    Save a file to the JARVIS workspace.
    Creates subdirectories automatically if the filename includes paths.
    
    Args:
        filename: Name of the file (e.g., 'notes.md', 'scripts/app.py')
        content: Text content to write.
    
    Returns:
        Status message confirming the write.
    """
    try:
        filepath = _get_safe_path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return f"File written successfully: {filepath.relative_to(Path(WORKSPACE_PATH).resolve())}"
    except ValueError as e:
        return f"Security error: {e}"
    except Exception as e:
        return f"File write failed: {e}"


def read_project_file(filename: str) -> str:
    """
    Read a file from the JARVIS workspace.
    
    Args:
        filename: Name of the file to read.
    
    Returns:
        File contents, or an error message.
    """
    try:
        filepath = _get_safe_path(filename)

        if not filepath.exists():
            return f"Error: File '{filename}' does not exist in the workspace."

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Truncate very large files to prevent token explosion
        if len(content) > 10000:
            return content[:10000] + f"\n\n[...truncated. Full file is {len(content)} characters.]"

        return content
    except ValueError as e:
        return f"Security error: {e}"
    except Exception as e:
        return f"File read failed: {e}"


def list_workspace_files() -> str:
    """
    List all files in the JARVIS workspace directory.
    
    Returns:
        Formatted directory listing, or a message if empty.
    """
    workspace = Path(WORKSPACE_PATH)
    workspace.mkdir(parents=True, exist_ok=True)

    files = []
    for item in sorted(workspace.rglob("*")):
        if item.is_file():
            rel_path = item.relative_to(workspace)
            size_kb = item.stat().st_size / 1024
            files.append(f"  {rel_path} ({size_kb:.1f} KB)")

    if not files:
        return "Workspace is empty. No files have been created yet."

    return f"Workspace contents ({len(files)} files):\n" + "\n".join(files)
