from __future__ import annotations

import sys

from .commands import build_dispatcher


def print_main_help() -> None:
    print("Multi-Agent Codex CLI")
    print("=" * 60)
    print("\nDieses CLI bietet mehrere Funktionen zum Arbeiten mit Multi-Agent-Systemen.\n")
    print("Verwendung:")
    print("  multi_agent_codex                                         # Interaktiver Modus")
    print("  multi_agent_codex run                                     # Interaktiver Modus (explizit)")
    print("  multi_agent_codex task --task <description> [options]     # Task-Modus")
    print("  multi_agent_codex create-family --description <text> [...]")
    print("  multi_agent_codex create-role --nl-description <text> [...]\n")
    print("Unterkommandos:")
    print("  run             Interaktiver Modus - Fuehre Task mit gefuehrter Eingabe aus (empfohlen)")
    print("  create-family   Erstelle eine neue Agent-Familie von einer")
    print("                  natuerlichsprachlichen Beschreibung")
    print("  create-role     Erstelle eine neue Agent-Rolle in einer bestehenden Familie\n")
    print("Standard-Verhalten (ohne Argument):")
    print("  Startet den interaktiven Modus.\n")
    print("Hilfe zu Unterkommandos:")
    print("  multi_agent_codex create-family --help")
    print("  multi_agent_codex create-role --help\n")
    print("Beispiele:")
    print("  # Interaktiver Modus (empfohlen fuer neue Benutzer)")
    print("  multi_agent_codex")
    print("  multi_agent_codex run")
    print("")
    print("  # Familie erstellen")
    print("  multi_agent_codex create-family --description \"Ein Team fuer ML-Entwicklung\"")
    print("")
    print("  # Rolle erstellen")
    print("  multi_agent_codex create-role --nl-description \"Ein Code Reviewer\"")
    print("")
    print("  # Task ausfuehren")
    print("  multi_agent_codex task --task \"Implementiere Feature X\" --apply")


def main() -> None:
    dispatcher = build_dispatcher()

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print_main_help()
        sys.exit(0)

    rc = dispatcher.dispatch(sys.argv[1:])
    sys.exit(rc)


if __name__ == "__main__":
    main()
