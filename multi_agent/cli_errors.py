from __future__ import annotations

import sys


def format_error(message: str) -> str:
    msg = (message or "").strip()
    if not msg:
        return "Fehler: Unbekannter Fehler."
    if msg.lower().startswith("fehler:"):
        return msg
    return f"Fehler: {msg}"


def print_error(message: str) -> None:
    print(format_error(message), file=sys.stderr)
