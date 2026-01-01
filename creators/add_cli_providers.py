"""
CLI Provider Configuration Tool

Fügt CLI-Provider-Konfiguration zu Agent-Familien oder einzelnen Agents hinzu.

Zwei Modi:
1. Familie-Modus: Aktualisiert alle Agents einer Familie
2. Agent-Modus: Aktualisiert nur einen spezifischen Agent

Usage:
    # Ganze Familie aktualisieren
    python creators/add_cli_providers.py --family developer

    # Einzelnen Agent aktualisieren
    python creators/add_cli_providers.py --family developer --agent architect --provider claude --model sonnet

    # Interactive Mode
    python creators/add_cli_providers.py --interactive

    # Alle Familien mit Auto-Strategie
    python creators/add_cli_providers.py --all
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional, List


# Provider-Konfigurationen
PROVIDER_CONFIGS = {
    'architect': {
        'cli_provider': 'claude',
        'model': 'sonnet',
        'cli_parameters': {
            'max_turns': 3,
            'allowed_tools': 'Read,Glob,Grep'
        }
    },
    'implementer': {
        'cli_provider': 'codex',
    },
    'tester': {
        'cli_provider': 'gemini',
        'model': 'gemini-2.5-flash',
        'cli_parameters': {
            'temperature': 0.5
        }
    },
    'reviewer': {
        'cli_provider': 'claude',
        'model': 'opus',
        'cli_parameters': {
            'max_turns': 2,
            'append_system_prompt': 'Fokus: Security, Performance, Maintainability'
        }
    },
    'integrator': {
        'cli_provider': 'claude',
        'model': 'haiku',
        'cli_parameters': {
            'max_turns': 1
        }
    }
}


def detect_role_type(role_id: str) -> str:
    """Detect role type from role ID."""
    role_id_lower = role_id.lower()

    if 'architect' in role_id_lower:
        return 'architect'
    elif 'designer' in role_id_lower or 'implementer' in role_id_lower:
        return 'implementer'
    elif 'tester' in role_id_lower or 'test' in role_id_lower:
        return 'tester'
    elif 'reviewer' in role_id_lower or 'review' in role_id_lower:
        return 'reviewer'
    elif 'integrator' in role_id_lower or 'integration' in role_id_lower:
        return 'integrator'
    else:
        return 'unknown'


def get_cli_config_for_role(role_type: str) -> dict:
    """Get optimal CLI configuration for a role type."""
    return PROVIDER_CONFIGS.get(role_type, {'cli_provider': 'codex'})


def update_single_agent(
    family_path: Path,
    agent_id: str,
    provider: str,
    model: Optional[str] = None,
    parameters: Optional[Dict] = None
) -> bool:
    """Update CLI config for a single agent in a family."""

    if not family_path.exists():
        print(f"[ERROR] Family config not found: {family_path}")
        return False

    with open(family_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Find the agent
    found = False
    for role in data.get('roles', []):
        if role.get('id') == agent_id:
            found = True

            # Update CLI config
            role['cli_provider'] = provider

            if model:
                role['model'] = model
            elif 'model' in role:
                del role['model']  # Remove if not specified

            if parameters:
                role['cli_parameters'] = parameters
            elif 'cli_parameters' in role:
                del role['cli_parameters']  # Remove if not specified

            print(f"[OK] Updated {agent_id}: {provider} ({model or 'default'})")
            break

    if not found:
        print(f"[ERROR] Agent '{agent_id}' not found in {family_path.name}")
        return False

    # Write back
    with open(family_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved {family_path.name}")
    return True


def update_family(family_path: Path, auto_strategy: bool = True) -> bool:
    """Update CLI config for all agents in a family."""

    if not family_path.exists():
        print(f"[ERROR] Family config not found: {family_path}")
        return False

    print(f"\n[UPDATING] {family_path.name}")

    with open(family_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated_count = 0
    for role in data.get('roles', []):
        role_id = role.get('id', '')

        # Skip if already has CLI provider and not forcing
        if 'cli_provider' in role and not auto_strategy:
            print(f"  - {role_id}: Already configured, skipping")
            continue

        # Detect role type and add CLI config
        role_type = detect_role_type(role_id)
        cli_config = get_cli_config_for_role(role_type)

        # Update role
        role.update(cli_config)

        provider = cli_config.get('cli_provider', 'codex')
        model = cli_config.get('model', 'default')
        print(f"  + {role_id:25} -> {provider:10} ({model})")
        updated_count += 1

    # Write back
    with open(family_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Updated {updated_count} agents in {family_path.name}\n")
    return True


def interactive_mode():
    """Interactive CLI provider configuration."""
    print("\n=== Interactive CLI Provider Configuration ===\n")

    # List available families
    families_dir = Path('agent_families')
    if not families_dir.exists():
        print("[ERROR] agent_families/ directory not found")
        return

    families = sorted(families_dir.glob('*_main.json'))
    families = [f for f in families if f.name != 'multi_cli_example.json']

    print("Available Families:")
    for i, family in enumerate(families, 1):
        family_name = family.stem.replace('_main', '')
        print(f"  {i}. {family_name}")

    # Select family
    try:
        choice = input("\nSelect family (number or name): ").strip()
        if choice.isdigit():
            family_path = families[int(choice) - 1]
        else:
            family_path = families_dir / f"{choice}_main.json"

        if not family_path.exists():
            print(f"[ERROR] Family not found: {choice}")
            return
    except (ValueError, IndexError):
        print("[ERROR] Invalid selection")
        return

    # Load family
    with open(family_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Select mode
    print("\nMode:")
    print("  1. Update all agents (auto-strategy)")
    print("  2. Update single agent")

    mode = input("Select mode (1/2): ").strip()

    if mode == '1':
        # Update all agents
        confirm = input(f"\nUpdate all agents in {family_path.stem}? (y/N): ").strip().lower()
        if confirm == 'y':
            update_family(family_path, auto_strategy=True)

    elif mode == '2':
        # List agents
        print("\nAgents:")
        for i, role in enumerate(data.get('roles', []), 1):
            role_id = role.get('id', '')
            current_provider = role.get('cli_provider', 'none')
            print(f"  {i}. {role_id:20} (current: {current_provider})")

        # Select agent
        agent_choice = input("\nSelect agent (number or id): ").strip()
        if agent_choice.isdigit():
            agent_id = data['roles'][int(agent_choice) - 1]['id']
        else:
            agent_id = agent_choice

        # Select provider
        print("\nAvailable Providers:")
        print("  1. codex (default)")
        print("  2. claude")
        print("  3. gemini")

        provider_choice = input("Select provider (1-3): ").strip()
        provider_map = {'1': 'codex', '2': 'claude', '3': 'gemini'}
        provider = provider_map.get(provider_choice, 'codex')

        # Select model (if Claude or Gemini)
        model = None
        if provider == 'claude':
            print("\nClaude Models:")
            print("  1. sonnet (balanced)")
            print("  2. opus (highest quality)")
            print("  3. haiku (fast & cheap)")
            model_choice = input("Select model (1-3): ").strip()
            model_map = {'1': 'sonnet', '2': 'opus', '3': 'haiku'}
            model = model_map.get(model_choice, 'sonnet')

        elif provider == 'gemini':
            print("\nGemini Models:")
            print("  1. gemini-2.5-flash (fast & cheap)")
            print("  2. gemini-2.5-pro (balanced)")
            model_choice = input("Select model (1-2): ").strip()
            model_map = {'1': 'gemini-2.5-flash', '2': 'gemini-2.5-pro'}
            model = model_map.get(model_choice, 'gemini-2.5-flash')

        # Parameters
        parameters = None
        add_params = input("\nAdd custom parameters? (y/N): ").strip().lower()
        if add_params == 'y':
            parameters = {}
            print("Enter parameters (key=value, empty to finish):")
            while True:
                param = input("  > ").strip()
                if not param:
                    break
                if '=' in param:
                    key, value = param.split('=', 1)
                    # Try to parse as number
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep as string
                    parameters[key.strip()] = value

        # Update
        update_single_agent(family_path, agent_id, provider, model, parameters)

    else:
        print("[ERROR] Invalid mode")


def main():
    parser = argparse.ArgumentParser(
        description='Add CLI provider configuration to agent families or agents'
    )

    parser.add_argument(
        '--family',
        help='Family name (e.g., developer, designer)'
    )
    parser.add_argument(
        '--agent',
        help='Agent ID (e.g., architect, implementer) - for single agent mode'
    )
    parser.add_argument(
        '--provider',
        choices=['codex', 'claude', 'gemini'],
        help='CLI provider to use'
    )
    parser.add_argument(
        '--model',
        help='Model name (e.g., sonnet, opus, haiku, gemini-2.5-flash)'
    )
    parser.add_argument(
        '--parameters',
        help='JSON string with CLI parameters (e.g., \'{"max_turns": 3}\')'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Update all families with auto-strategy'
    )
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Interactive mode'
    )

    args = parser.parse_args()

    # Interactive mode
    if args.interactive:
        interactive_mode()
        return

    families_dir = Path('agent_families')
    if not families_dir.exists():
        print("[ERROR] agent_families/ directory not found")
        print("Make sure you run this from the project root directory")
        sys.exit(1)

    # Update all families
    if args.all:
        main_files = list(families_dir.glob('*_main.json'))
        main_files = [f for f in main_files if f.name != 'multi_cli_example.json']

        print(f"[INFO] Updating {len(main_files)} families...\n")

        for family_path in sorted(main_files):
            update_family(family_path, auto_strategy=True)

        print("=" * 60)
        print(f"[OK] Successfully updated {len(main_files)} families!")
        return

    # Single agent mode
    if args.agent:
        if not args.family:
            print("[ERROR] --family required when --agent is specified")
            sys.exit(1)

        if not args.provider:
            print("[ERROR] --provider required when --agent is specified")
            sys.exit(1)

        family_path = families_dir / f"{args.family}_main.json"

        # Parse parameters
        parameters = None
        if args.parameters:
            try:
                parameters = json.loads(args.parameters)
            except json.JSONDecodeError:
                print(f"[ERROR] Invalid JSON in --parameters: {args.parameters}")
                sys.exit(1)

        success = update_single_agent(
            family_path,
            args.agent,
            args.provider,
            args.model,
            parameters
        )

        sys.exit(0 if success else 1)

    # Family mode
    elif args.family:
        family_path = families_dir / f"{args.family}_main.json"
        success = update_family(family_path, auto_strategy=True)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        print("\n[TIP] Use --interactive for guided configuration")
        sys.exit(1)


if __name__ == '__main__':
    main()
