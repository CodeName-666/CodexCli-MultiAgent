"""Utilities for parsing and analyzing unified diffs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Set

# Regex patterns for unified diff parsing
DIFF_FILE_PATTERN = re.compile(r"^(?:\+\+\+|---)\s+([ab]/)(.+)$")


def extract_touched_files_from_unified_diff(diff_text: str) -> Set[str]:
    """
    Extract the set of file paths that are modified in a unified diff.

    Parses lines like:
        +++ b/path/to/file.py
        --- a/path/to/file.py

    Ignores /dev/null entries and normalizes paths.

    Args:
        diff_text: The unified diff content as a string

    Returns:
        Set of normalized file paths (without a/ or b/ prefix)
    """
    if not diff_text:
        return set()

    touched_files: Set[str] = set()
    lines = diff_text.splitlines()

    for line in lines:
        match = DIFF_FILE_PATTERN.match(line)
        if not match:
            continue

        prefix = match.group(1)  # 'a/' or 'b/'
        filepath = match.group(2)

        # Ignore /dev/null (used for new/deleted files in some diff formats)
        if filepath == "/dev/null" or filepath.startswith("dev/null"):
            continue

        # Normalize the path (remove any leading './')
        normalized = Path(filepath).as_posix()
        if normalized.startswith("./"):
            normalized = normalized[2:]

        touched_files.add(normalized)

    return touched_files


def check_path_matches_globs(filepath: str, glob_patterns: list[str]) -> bool:
    """
    Check if a file path matches any of the given glob patterns.

    Args:
        filepath: The file path to check (e.g., "multi_agent/models.py")
        glob_patterns: List of glob patterns (e.g., ["multi_agent/**", "*.py"])

    Returns:
        True if the file matches any pattern, False otherwise
    """
    if not glob_patterns:
        return True

    # Special case: ["**"] matches everything
    if glob_patterns == ["**"]:
        return True

    path = Path(filepath)
    for pattern in glob_patterns:
        # PurePath.match() matches from the right, so "multi_agent/**" won't match "multi_agent/sub/file.py"
        # We need to check if the path starts with the pattern prefix
        if pattern.endswith("/**"):
            # For directory wildcards, check if path starts with the directory
            dir_prefix = pattern[:-3]  # Remove "/**"
            if filepath.startswith(dir_prefix + "/") or filepath == dir_prefix:
                return True
        # Use match for other patterns
        elif path.match(pattern):
            return True

    return False


def validate_touched_files_against_allowed_paths(
    touched_files: Set[str],
    allowed_paths: list[str],
) -> tuple[bool, list[str]]:
    """
    Validate that all touched files are within allowed paths.

    Args:
        touched_files: Set of file paths that were modified
        allowed_paths: List of glob patterns for allowed file modifications

    Returns:
        Tuple of (is_valid, violations)
        - is_valid: True if all files are allowed, False otherwise
        - violations: List of file paths that violate the allowed_paths constraint
    """
    if not allowed_paths or allowed_paths == ["**"]:
        return True, []

    violations: list[str] = []
    for filepath in touched_files:
        if not check_path_matches_globs(filepath, allowed_paths):
            violations.append(filepath)

    is_valid = len(violations) == 0
    return is_valid, violations


def detect_file_overlaps(
    instance_diffs: dict[str, Set[str]],
) -> dict[str, list[str]]:
    """
    Detect which files are modified by multiple instances (overlaps).

    Args:
        instance_diffs: Mapping of instance_id -> set of touched files

    Returns:
        Dictionary mapping overlapping file paths to list of instance IDs that touched them
    """
    file_to_instances: dict[str, list[str]] = {}

    for instance_id, touched_files in instance_diffs.items():
        for filepath in touched_files:
            if filepath not in file_to_instances:
                file_to_instances[filepath] = []
            file_to_instances[filepath].append(instance_id)

    # Filter to only overlapping files (touched by >1 instance)
    overlaps = {
        filepath: instances
        for filepath, instances in file_to_instances.items()
        if len(instances) > 1
    }

    return overlaps
