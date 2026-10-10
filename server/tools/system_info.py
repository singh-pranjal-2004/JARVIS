"""
System Info Tool

JARVIS's ability to report on the host machine's status.
Useful for quick diagnostics without leaving the chat.
"""

import os
import platform
import shutil
from datetime import datetime


def get_system_info() -> str:
    """
    Gather and format key system information.
    
    Returns:
        Formatted string with OS, CPU, memory, disk, and uptime details.
    """
    info_parts = ["SYSTEM STATUS REPORT", "=" * 40]

    # OS & Machine
    info_parts.append(f"OS: {platform.system()} {platform.release()}")
    info_parts.append(f"Machine: {platform.machine()}")
    info_parts.append(f"Hostname: {platform.node()}")
    info_parts.append(f"Python: {platform.python_version()}")

    # Disk usage (root drive)
    try:
        disk = shutil.disk_usage("/")
        total_gb = disk.total / (1024 ** 3)
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        usage_pct = (disk.used / disk.total) * 100
        info_parts.append(f"\nDisk: {used_gb:.1f} GB / {total_gb:.1f} GB ({usage_pct:.1f}% used, {free_gb:.1f} GB free)")
    except Exception:
        info_parts.append("\nDisk: Unable to read disk usage.")

    # CPU count
    cpu_count = os.cpu_count()
    if cpu_count:
        info_parts.append(f"CPU cores: {cpu_count}")

    # Current time
    info_parts.append(f"\nServer time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(info_parts)


def get_current_time() -> str:
    """Return the current date and time in a readable format."""
    now = datetime.now()
    return now.strftime("It is %A, %B %d, %Y at %I:%M %p.")
