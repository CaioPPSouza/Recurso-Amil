from pathlib import Path

from app.chrome_launcher import build_chrome_command


def test_debug_chrome_command_contains_remote_port():
    command = build_chrome_command(port=9222, profile_dir=Path("tmp-profile"))
    assert "--remote-debugging-port=9222" in command


def test_debug_chrome_command_opens_amil_url():
    command = build_chrome_command(port=9222, profile_dir=Path("tmp-profile"))
    assert "https://credenciado.amil.com.br/" in command
