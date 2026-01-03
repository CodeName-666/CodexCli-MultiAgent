"""Shared helpers for formatting and printing CLI errors."""

from __future__ import annotations

import sys


def format_error(message: str) -> str:
    """Normalize an error message with a consistent prefix."""
    msg = (message or "").strip()
    if not msg:
        return "Fehler: Unbekannter Fehler."
    if msg.lower().startswith("fehler:"):
        return msg
    return f"Fehler: {msg}"


def print_error(message: str) -> None:
    """Print a formatted error message to stderr."""
    print(format_error(message), file=sys.stderr)
