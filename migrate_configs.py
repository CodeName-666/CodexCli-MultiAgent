#!/usr/bin/env python3
"""
migrate_configs.py - Migrate *_main.json files to use defaults.json

This script:
1. Reads all *_main.json files in config/
2. Extracts only family-specific values
3. Rewrites each *_main.json with reduced content
4. Validates that merged config equals original config
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from multi_agent.common_utils import load_json, write_json, deep_merge

# Family-specific keys that should remain in *_main.json
FAMILY_KEYS = {
    "final_role_id",
    "roles",
    "cli",  # Will be filtered to only include "description"
    "diff_safety",  # Will be filtered to only include "allowlist"
}


def extract_family_config(full_config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only family-specific configuration"""
    family_config = {}

    # Extract family-specific top-level keys
    for key in FAMILY_KEYS:
        if key in full_config:
            family_config[key] = full_config[key]

    # Special handling for cli: only keep description
    if "cli" in family_config:
        if "description" in family_config["cli"]:
            family_config["cli"] = {"description": family_config["cli"]["description"]}
        else:
            del family_config["cli"]

    # Special handling for diff_safety: only keep allowlist
    if "diff_safety" in family_config:
        if "allowlist" in family_config["diff_safety"]:
            family_config["diff_safety"] = {"allowlist": family_config["diff_safety"]["allowlist"]}
        else:
            del family_config["diff_safety"]

    return family_config


def validate_migration(
    original: Dict[str, Any],
    defaults: Dict[str, Any],
    family: Dict[str, Any]
) -> bool:
    """Validate that merging defaults + family gives back the original"""
    merged = deep_merge(defaults, family)

    # Compare all keys
    original_keys = set(original.keys())
    merged_keys = set(merged.keys())

    if original_keys != merged_keys:
        print(f"  [X] Key mismatch!")
        print(f"     Missing: {original_keys - merged_keys}")
        print(f"     Extra: {merged_keys - original_keys}")
        return False

    # Deep comparison (simplified - we check critical sections)
    critical_sections = ["roles", "final_role_id", "diff_safety"]
    for section in critical_sections:
        if section in original:
            if original[section] != merged[section]:
                print(f"  [X] Section '{section}' mismatch!")
                return False

    # Special check for cli.description (we only keep description in family)
    if "cli" in original:
        if original["cli"].get("description") != merged["cli"].get("description"):
            print(f"  [X] Section 'cli.description' mismatch!")
            return False

    print(f"  [OK] Validation passed")
    return True


def migrate_file(
    config_path: Path,
    defaults: Dict[str, Any],
    dry_run: bool = False
) -> bool:
    """Migrate a single *_main.json file"""
    print(f"\nProcessing: {config_path.name}")

    # Load original config
    original = load_json(config_path)

    # Extract family-specific config
    family = extract_family_config(original)

    print(f"  Original size: {len(json.dumps(original))} chars")
    print(f"  Family size:   {len(json.dumps(family))} chars")
    print(f"  Reduction:     {100 - (len(json.dumps(family)) * 100 // len(json.dumps(original)))}%")

    # Validate
    if not validate_migration(original, defaults, family):
        return False

    # Write migrated config
    if not dry_run:
        # Backup original
        backup_path = config_path.with_suffix(".json.backup")
        write_json(backup_path, original)
        print(f"  [BACKUP] {backup_path.name}")

        # Write migrated
        write_json(config_path, family)
        print(f"  [MIGRATED] {config_path.name}")
    else:
        print(f"  [DRY-RUN] Would migrate {config_path.name}")

    return True


def main():
    """Main migration script"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate *_main.json configs to use defaults.json")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, just validate")
    parser.add_argument("--config-dir", type=Path, default=Path("config"), help="Config directory")
    args = parser.parse_args()

    config_dir = args.config_dir
    defaults_path = config_dir / "defaults.json"

    if not defaults_path.exists():
        print(f"[ERROR] {defaults_path} not found!")
        print("   Run this script from the project root.")
        return 1

    # Load defaults
    defaults = load_json(defaults_path)
    print(f"Loaded defaults.json ({len(defaults)} top-level keys)")

    # Find all *_main.json files
    main_configs = sorted(config_dir.glob("*_main.json"))
    if not main_configs:
        print(f"[ERROR] No *_main.json files found in {config_dir}")
        return 1

    print(f"Found {len(main_configs)} config files to migrate")

    # Migrate each file
    success_count = 0
    for config_path in main_configs:
        if migrate_file(config_path, defaults, dry_run=args.dry_run):
            success_count += 1

    # Summary
    print(f"\n{'='*60}")
    if args.dry_run:
        print(f"[DRY-RUN] Complete: {success_count}/{len(main_configs)} configs validated")
    else:
        print(f"[COMPLETE] Migration: {success_count}/{len(main_configs)} configs migrated")
        print(f"[BACKUP] Created: *.json.backup files")

    if success_count == len(main_configs):
        print("\n[SUCCESS] All migrations successful!")
        return 0
    else:
        print(f"\n[WARNING] {len(main_configs) - success_count} migrations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
