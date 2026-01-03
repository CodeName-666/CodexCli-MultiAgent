"""
CLI Provider Configuration Tool

Fügt CLI-Provider-Konfiguration zu Agent-Familien oder einzelnen Agents hinzu.

Drei Modi:
1. Family-Modus: Setzt ALLE Rollen einer Familie auf denselben Provider
2. Single-Agent-Modus: Aktualisiert nur einen spezifischen Agent
3. Interactive Mode: Vollständig interaktiver Durchlauf durch alle Rollen einer Familie

Usage:
    # Family Mode - Alle Rollen auf denselben Provider setzen
    python creators/add_cli_providers.py --family developer --provider claude --model sonnet
    python creators/add_cli_providers.py --family designer --provider codex

    # Single Agent Mode - Nur einen Agent aktualisieren
    python creators/add_cli_providers.py --family developer --agent architect --provider claude --model sonnet

    # Interactive Mode - Für jede Rolle einzeln entscheiden (empfohlen)
    python creators/add_cli_providers.py --interactive

    # Mit custom Parameters
    python creators/add_cli_providers.py --family developer --agent architect \
        --provider claude --model sonnet --parameters '{"max_turns": 3, "allowed_tools": "Read,Glob,Grep"}'
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional, List


# Provider-Konfigurationen (nur als EMPFEHLUNGEN, NICHT automatisch angewendet)
PROVIDER_RECOMMENDATIONS = {
    'architect': {
        'cli_provider': 'claude',
        'model': 'sonnet',
        'cli_parameters': {
            'max_turns': 3,
            'allowed_tools': 'Read,Glob,Grep'
        }
    },
    'designer': {
        'cli_provider': 'codex',
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
    """Detect role type from role ID (for recommendations only)."""
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


def get_recommendation_for_role(role_id: str) -> Optional[dict]:
    """Get recommended CLI configuration for a role (optional)."""
    role_type = detect_role_type(role_id)
    return PROVIDER_RECOMMENDATIONS.get(role_type)


def format_cli_config(role: dict) -> str:
    """Format current CLI config as readable string."""
    if 'cli_provider' not in role:
        return 'none'

    provider = role['cli_provider']
    model = role.get('model', 'default')
    params = role.get('cli_parameters', {})

    config_str = f"{provider}"
    if model != 'default':
        config_str += f"/{model}"
    if params:
        param_strs = [f"{k}={v}" for k, v in params.items()]
        config_str += f" ({', '.join(param_strs)})"

    return config_str


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


def update_family(
    family_path: Path,
    provider: str,
    model: Optional[str] = None,
    parameters: Optional[Dict] = None
) -> bool:
    """
    Update CLI config for ALL agents in a family (non-interactive).

    Sets all roles to the same provider/model/parameters.
    """

    if not family_path.exists():
        print(f"[ERROR] Family config not found: {family_path}")
        return False

    with open(family_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    family_name = family_path.stem.replace('_main', '')
    print(f"\n[INFO] Updating family: {family_name}")
    print(f"[INFO] Setting all roles to: {provider} ({model or 'default'})")

    # Update all roles
    updated_count = 0
    for role in data.get('roles', []):
        role_id = role.get('id', '')

        # Remove old CLI config
        if 'cli_provider' in role:
            del role['cli_provider']
        if 'model' in role:
            del role['model']
        if 'cli_parameters' in role:
            del role['cli_parameters']

        # Set new config
        role['cli_provider'] = provider

        if model:
            role['model'] = model

        if parameters:
            role['cli_parameters'] = parameters

        print(f"  + {role_id:25} -> {provider} ({model or 'default'})")
        updated_count += 1

    # Write back
    with open(family_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Updated {updated_count} roles in {family_path.name}")
    return True


def configure_role_interactive(role_id: str, current_config: dict) -> Optional[dict]:
    """
    Interactively configure CLI provider for a single role.

    Returns:
        - dict with cli_provider, model, cli_parameters if user wants to configure
        - None if user wants to remove CLI config
        - current_config if user wants to keep current
    """
    print(f"\n{'=' * 60}")
    print(f"Role: {role_id}")
    print(f"{'=' * 60}")

    # Show current config
    current_cli = format_cli_config(current_config)
    print(f"Current: {current_cli}")

    # Show recommendation
    recommendation = get_recommendation_for_role(role_id)
    if recommendation:
        rec_provider = recommendation.get('cli_provider', 'codex')
        rec_model = recommendation.get('model', 'default')
        rec_params = recommendation.get('cli_parameters', {})
        rec_str = f"{rec_provider}"
        if rec_model != 'default':
            rec_str += f"/{rec_model}"
        if rec_params:
            param_strs = [f"{k}={v}" for k, v in rec_params.items()]
            rec_str += f" ({', '.join(param_strs)})"
        print(f"Recommendation: {rec_str}")
    else:
        print(f"Recommendation: codex (default)")

    # Options
    print("\nOptions:")
    print("  [1] Keep current")
    print("  [2] Change provider")
    if recommendation:
        print("  [3] Use recommendation")
    print("  [4] Remove CLI config (use default: codex)")

    choice = input("\nSelect option (1-4): ").strip()

    if choice == '1':
        # Keep current
        return current_config

    elif choice == '2':
        # Change provider
        return configure_provider_manually()

    elif choice == '3' and recommendation:
        # Use recommendation
        print("[OK] Using recommendation")
        return recommendation

    elif choice == '4':
        # Remove CLI config
        print("[OK] Removing CLI config (will use default: codex)")
        return None

    else:
        print("[WARNING] Invalid choice, keeping current config")
        return current_config


def configure_provider_manually() -> dict:
    """Manually configure CLI provider (interactive)."""

    # Select provider
    print("\nAvailable Providers:")
    print("  [1] codex (default)")
    print("  [2] claude")
    print("  [3] gemini")

    provider_choice = input("Select provider (1-3): ").strip()
    provider_map = {'1': 'codex', '2': 'claude', '3': 'gemini'}
    provider = provider_map.get(provider_choice, 'codex')

    config = {'cli_provider': provider}

    # Select model (if Claude or Gemini)
    model = None
    if provider == 'claude':
        print("\nClaude Models:")
        print("  [1] sonnet (balanced)")
        print("  [2] opus (highest quality)")
        print("  [3] haiku (fast & cheap)")
        model_choice = input("Select model (1-3): ").strip()
        model_map = {'1': 'sonnet', '2': 'opus', '3': 'haiku'}
        model = model_map.get(model_choice, 'sonnet')
        config['model'] = model

    elif provider == 'gemini':
        print("\nGemini Models:")
        print("  [1] gemini-2.5-flash (fast & cheap)")
        print("  [2] gemini-2.5-pro (balanced)")
        model_choice = input("Select model (1-2): ").strip()
        model_map = {'1': 'gemini-2.5-flash', '2': 'gemini-2.5-pro'}
        model = model_map.get(model_choice, 'gemini-2.5-flash')
        config['model'] = model

    # Parameters
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

        if parameters:
            config['cli_parameters'] = parameters

    return config


def interactive_mode():
    """Fully interactive CLI provider configuration."""
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

    family_name = family_path.stem.replace('_main', '')
    print(f"\n{'=' * 60}")
    print(f"Configuring Family: {family_name}")
    print(f"{'=' * 60}")
    print(f"Roles: {len(data.get('roles', []))}")
    print(f"\nYou will be asked to configure each role individually.")

    confirm = input("\nProceed? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("[CANCELLED]")
        return

    # Configure each role
    updated_count = 0
    for role in data.get('roles', []):
        role_id = role.get('id', '')

        # Get new config
        new_config = configure_role_interactive(role_id, role)

        # Apply changes
        if new_config is None:
            # Remove CLI config
            if 'cli_provider' in role:
                del role['cli_provider']
            if 'model' in role:
                del role['model']
            if 'cli_parameters' in role:
                del role['cli_parameters']
            updated_count += 1
        elif new_config != role:
            # Update with new config
            # Remove old fields first
            if 'cli_provider' in role:
                del role['cli_provider']
            if 'model' in role:
                del role['model']
            if 'cli_parameters' in role:
                del role['cli_parameters']

            # Add new config
            role.update(new_config)
            updated_count += 1

    # Write back
    with open(family_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"[OK] Updated {updated_count} roles in {family_path.name}")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description='Add CLI provider configuration to agent families or agents',
        epilog="""
Examples:
  # Interactive mode (recommended)
  python creators/add_cli_providers.py --interactive

  # Set all roles in a family to same provider
  python creators/add_cli_providers.py --family developer --provider claude --model sonnet

  # Set single agent
  python creators/add_cli_providers.py --family developer --agent architect --provider claude --model sonnet
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--family',
        help='Family name (e.g., developer, designer)'
    )
    parser.add_argument(
        '--agent',
        help='Agent ID (e.g., architect, implementer) - for single agent mode only'
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
        '--interactive',
        '-i',
        action='store_true',
        help='Interactive mode (recommended)'
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

    # Check if family is provided
    if not args.family:
        parser.print_help()
        print("\n[TIP] Use --interactive for guided configuration")
        sys.exit(1)

    # Parse parameters
    parameters = None
    if args.parameters:
        try:
            parameters = json.loads(args.parameters)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON in --parameters: {args.parameters}")
            sys.exit(1)

    family_path = families_dir / f"{args.family}_main.json"

    # Single agent mode
    if args.agent:
        if not args.provider:
            print("[ERROR] --provider required when --agent is specified")
            sys.exit(1)

        success = update_single_agent(
            family_path,
            args.agent,
            args.provider,
            args.model,
            parameters
        )

        sys.exit(0 if success else 1)

    # Family mode (all agents)
    elif args.provider:
        success = update_family(
            family_path,
            args.provider,
            args.model,
            parameters
        )

        sys.exit(0 if success else 1)

    else:
        print("[ERROR] --provider required (or use --interactive)")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
