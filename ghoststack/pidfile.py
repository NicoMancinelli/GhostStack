"""PID file management for remote supervisor control."""

import os
import signal
import sys
from typing import Optional

from ghoststack.paths import PIDFILE_PATH


def ensure_run_dir():
    run_dir = os.path.dirname(PIDFILE_PATH)
    os.makedirs(run_dir, exist_ok=True)


def write_pid(pid: Optional[int] = None, path: str = PIDFILE_PATH) -> int:
    ensure_run_dir()
    pid = pid or os.getpid()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(str(pid))
    return pid


def read_pid(path: str = PIDFILE_PATH) -> Optional[int]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return int(handle.read().strip())
    except (ValueError, OSError):
        return None


def remove_pid(path: str = PIDFILE_PATH):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def stop_supervisor(path: str = PIDFILE_PATH) -> bool:
    pid = read_pid(path)
    if not pid:
        print("[*] No running GhostStack supervisor (pidfile missing).")
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"[*] Sent SIGTERM to GhostStack supervisor (pid {pid}).")
        remove_pid(path)
        return True
    except ProcessLookupError:
        print(f"[-] Stale pidfile (pid {pid} not running). Removing pidfile.")
        remove_pid(path)
        return False
    except PermissionError:
        print(f"[-] Permission denied sending signal to pid {pid}.")
        sys.exit(1)
