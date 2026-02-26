from __future__ import annotations

import socket
import subprocess
from pathlib import Path

DEFAULT_START_URL = "https://credenciado.amil.com.br/"


def build_chrome_command(
    port: int,
    profile_dir: Path,
    chrome_binary: str | None = None,
    start_url: str = DEFAULT_START_URL,
) -> list[str]:
    executable = chrome_binary or _default_chrome_binary()
    return [
        executable,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--new-window",
        start_url,
    ]


def _default_chrome_binary() -> str:
    candidates = [
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "chrome.exe"


def is_debug_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.6)
        return sock.connect_ex((host, port)) == 0


def launch_chrome_debug(
    port: int,
    profile_dir: Path,
    chrome_binary: str | None = None,
    start_url: str = DEFAULT_START_URL,
) -> subprocess.Popen[bytes] | None:
    if is_debug_port_open(port):
        return None

    profile_dir.mkdir(parents=True, exist_ok=True)
    command = build_chrome_command(
        port=port,
        profile_dir=profile_dir,
        chrome_binary=chrome_binary,
        start_url=start_url,
    )
    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
