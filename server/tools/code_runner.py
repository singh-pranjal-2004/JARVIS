"""
Code Runner Tool

JARVIS's ability to execute Python code locally with safety constraints.
Runs in a subprocess with timeout protection.
"""

import os
import subprocess
import tempfile
from pathlib import Path


# Safety limits
EXECUTION_TIMEOUT = 15  # seconds
MAX_OUTPUT_LENGTH = 5000  # characters


def execute_python_code(script_content: str) -> str:
    """
    Execute a Python script in a sandboxed subprocess.
    
    Safety measures:
    - Runs in a subprocess (isolated from JARVIS server process)
    - Hard timeout of 15 seconds
    - Output truncated to prevent memory issues
    - Temp file cleaned up after execution
    
    Args:
        script_content: The Python code to execute.
    
    Returns:
        Execution result with stdout/stderr, or error message.
    """
    temp_file = None

    try:
        # Write to a temp file (auto-cleaned by OS if we crash)
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            prefix="jarvis_exec_",
            delete=False,
            encoding="utf-8"
        )
        temp_file.write(script_content)
        temp_file.close()

        # Execute in subprocess
        result = subprocess.run(
            ["python", temp_file.name],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            cwd=tempfile.gettempdir()  # Run from temp dir, not project dir
        )

        output_parts = []

        if result.stdout:
            stdout = result.stdout[:MAX_OUTPUT_LENGTH]
            if len(result.stdout) > MAX_OUTPUT_LENGTH:
                stdout += "\n[...output truncated]"
            output_parts.append(f"STDOUT:\n{stdout}")

        if result.stderr:
            stderr = result.stderr[:MAX_OUTPUT_LENGTH]
            if len(result.stderr) > MAX_OUTPUT_LENGTH:
                stderr += "\n[...error output truncated]"
            output_parts.append(f"STDERR:\n{stderr}")

        if result.returncode == 0:
            status = "Execution successful."
            if not output_parts:
                output_parts.append("(No output produced)")
        else:
            status = f"Execution failed (exit code {result.returncode})."

        return f"{status}\n" + "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return (
            f"Execution timed out after {EXECUTION_TIMEOUT} seconds. "
            f"The script may contain an infinite loop or heavy computation."
        )
    except FileNotFoundError:
        return (
            "Python interpreter not found. "
            "Ensure 'python' is available in the system PATH."
        )
    except Exception as e:
        return f"Execution error: {type(e).__name__}: {e}"
    finally:
        # Always clean up the temp file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
            except OSError:
                pass
