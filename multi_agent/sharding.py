"""Shard planning for parallel agent execution."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

from .models import RoleConfig, Shard, ShardPlan
from .task_split import extract_headings, HeadingInfo


def create_shard_plan(
    role_cfg: RoleConfig,
    task_text: str,
) -> ShardPlan | None:
    """
    Create a shard plan for a role based on its configuration.

    Args:
        role_cfg: The role configuration
        task_text: The full task text to shard

    Returns:
        ShardPlan if sharding is enabled and instances > 1, otherwise None.
    """
    if role_cfg.shard_mode == "none":
        return None

    if role_cfg.instances <= 1:
        return None

    shard_count = role_cfg.shard_count or role_cfg.instances

    if role_cfg.shard_mode == "headings":
        shards = _plan_shards_by_headings(task_text, shard_count, role_cfg)
    elif role_cfg.shard_mode == "files":
        shards = _plan_shards_by_files(task_text, shard_count, role_cfg)
    elif role_cfg.shard_mode == "llm":
        raise NotImplementedError("LLM-based sharding is not implemented in V1")
    else:
        raise ValueError(f"Unknown shard_mode: {role_cfg.shard_mode}")

    if not shards:
        return None

    return ShardPlan(
        role_id=role_cfg.id,
        shard_mode=role_cfg.shard_mode,
        shard_count=len(shards),
        shards=shards,
        overlap_policy=role_cfg.overlap_policy,
        enforce_allowed_paths=role_cfg.enforce_allowed_paths,
    )


def _plan_shards_by_headings(
    task_text: str,
    shard_count: int,
    role_cfg: RoleConfig,
) -> List[Shard]:
    """
    Plan shards based on markdown headings (H1/H2/H3).

    Strategy:
    1. Extract H1 headings as section boundaries.
    2. Treat each heading as a section and preserve the preamble.
    3. Distribute sections across shards using a greedy-by-size algorithm.
    4. Extract goal and allowed_paths from each section when present.

    Args:
        task_text: The markdown task text
        shard_count: Target number of shards
        role_cfg: Role configuration

    Returns:
        List of Shard objects
    """
    # Extract only H1 headings as main section dividers
    headings = extract_headings(task_text, max_level=1)  # Only H1

    if not headings:
        # No headings found, create single shard with full text
        return [
            Shard(
                id="shard-1",
                title="Full Task",
                goal="Complete the task as described",
                content=task_text.strip(),
                allowed_paths=["**"],
            )
        ]

    lines = task_text.splitlines()

    # Extract preamble (text before first heading)
    preamble = ""
    if headings[0].line_no > 1:
        preamble = "\n".join(lines[: headings[0].line_no - 1]).strip()

    # Build sections from headings
    sections: List[tuple[HeadingInfo, str, str, List[str]]] = []
    for i, heading in enumerate(headings):
        start_line = heading.line_no - 1
        end_line = headings[i + 1].line_no - 1 if i + 1 < len(headings) else len(lines)

        section_lines = lines[start_line:end_line]
        section_text = "\n".join(section_lines).strip()

        # Extract goal and allowed paths from section
        goal, allowed_paths = _extract_section_metadata(section_text)

        sections.append((heading, section_text, goal, allowed_paths))

    # Distribute sections across shards using greedy-by-size
    if len(sections) <= shard_count:
        # Each section gets its own shard
        shards = []
        for i, (heading, section_text, goal, allowed_paths) in enumerate(sections, start=1):
            content = section_text
            if i == 1 and preamble:
                content = f"{preamble}\n\n{content}"

            shards.append(
                Shard(
                    id=f"shard-{i}",
                    title=heading.title,
                    goal=goal or heading.title,
                    content=content,
                    allowed_paths=allowed_paths if allowed_paths else ["**"],
                )
            )
        return shards
    return _group_sections_greedy(sections, shard_count, preamble)


def _extract_section_metadata(section_text: str) -> tuple[str, List[str]]:
    """
    Extract goal and allowed_paths from a markdown section.

    Looks for sections like "Goal" and "Allowed paths" and captures
    the first goal line plus list items under allowed paths.

    Returns:
        Tuple of (goal_text, allowed_paths_list)
    """
    goal = ""
    allowed_paths: List[str] = []

    lines = section_text.splitlines()
    current_section = None

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Detect section markers
        if line_lower.startswith("## goal") or line_lower.startswith("# goal"):
            current_section = "goal"
            continue
        elif line_lower.startswith("## allowed path") or line_lower.startswith("# allowed path"):
            current_section = "allowed_paths"
            continue
        elif line_stripped.startswith("#"):
            # Different heading, stop extracting from current section
            current_section = None
            continue

        # Extract content based on current section
        if current_section == "goal" and line_stripped:
            goal = line_stripped
            current_section = None  # Only take first line as goal
        elif current_section == "allowed_paths" and line_stripped:
            # Extract paths from list items only
            if line_stripped.startswith("-") or line_stripped.startswith("*"):
                path = line_stripped[1:].strip()
                if path:
                    allowed_paths.append(path)
            # Stop at non-list-item lines (but continue if empty line)
            elif not line_stripped.startswith("#"):
                # Empty line or non-list content - could be end of list
                pass

    return goal, allowed_paths


def _group_sections_greedy(
    sections: List[tuple[HeadingInfo, str, str, List[str]]],
    shard_count: int,
    preamble: str,
) -> List[Shard]:
    """
    Group sections into shards using greedy-by-size algorithm.

    Distributes sections across shards trying to balance size (line count),
    deduplicates allowed_paths, prepends the preamble to the first shard, and
    limits shard titles to the first three headings.

    Args:
        sections: List of (heading, content, goal, allowed_paths) tuples
        shard_count: Number of shards to create
        preamble: Text before first heading (added to first shard)

    Returns:
        List of Shard objects
    """
    # Sort sections by size (descending) for better distribution
    sorted_sections = sorted(sections, key=lambda s: len(s[1].splitlines()), reverse=True)

    # Initialize shard buckets
    shard_buckets: List[List[tuple[HeadingInfo, str, str, List[str]]]] = [[] for _ in range(shard_count)]
    shard_sizes = [0] * shard_count

    # Greedy assignment: assign each section to the smallest bucket
    for section in sorted_sections:
        section_size = len(section[1].splitlines())
        min_idx = shard_sizes.index(min(shard_sizes))
        shard_buckets[min_idx].append(section)
        shard_sizes[min_idx] += section_size

    # Build Shard objects
    shards = []
    for i, bucket in enumerate(shard_buckets, start=1):
        if not bucket:
            continue

        # Combine sections in bucket
        titles = [heading.title for heading, _, _, _ in bucket]
        combined_title = " / ".join(titles[:3])  # Limit title length
        if len(titles) > 3:
            combined_title += f" (+{len(titles) - 3} more)"

        contents = [text for _, text, _, _ in bucket]
        combined_content = "\n\n".join(contents)

        # Add preamble to first shard
        if i == 1 and preamble:
            combined_content = f"{preamble}\n\n{combined_content}"

        # Combine goals
        goals = [goal for _, _, goal, _ in bucket if goal]
        combined_goal = "; ".join(goals[:2]) if goals else combined_title

        # Combine allowed_paths
        all_allowed_paths: List[str] = []
        for _, _, _, paths in bucket:
            all_allowed_paths.extend(paths)
        # Deduplicate
        unique_paths = list(dict.fromkeys(all_allowed_paths))

        shards.append(
            Shard(
                id=f"shard-{i}",
                title=combined_title,
                goal=combined_goal,
                content=combined_content.strip(),
                allowed_paths=unique_paths if unique_paths else ["**"],
            )
        )

    return shards


def _plan_shards_by_files(
    task_text: str,
    shard_count: int,
    role_cfg: RoleConfig,
) -> List[Shard]:
    """
    Plan shards based on file paths mentioned in the task text.

    Strategy:
    1. Extract file paths from task text using heuristics.
    2. Group files by top-level directory.
    3. Create shards per directory group.
    4. If no paths found, fallback to heading-based sharding.

    Args:
        task_text: The task text
        shard_count: Target number of shards
        role_cfg: Role configuration

    Returns:
        List of Shard objects
    """
    # Extract candidate paths from task text
    candidate_paths = _extract_paths_from_text(task_text)

    if not candidate_paths:
        # Fallback to heading-based sharding
        return _plan_shards_by_headings(task_text, shard_count, role_cfg)

    # Group paths by top-level directory
    dir_groups: dict[str, List[str]] = {}
    for path in candidate_paths:
        parts = Path(path).parts
        if len(parts) > 0:
            top_dir = parts[0]
            if top_dir not in dir_groups:
                dir_groups[top_dir] = []
            dir_groups[top_dir].append(path)
        else:
            # Root-level file
            if "." not in dir_groups:
                dir_groups["."] = []
            dir_groups["."].append(path)

    # Create shards from directory groups
    shards = []
    for i, (dir_name, paths) in enumerate(dir_groups.items(), start=1):
        # Limit files per shard
        max_files = role_cfg.max_files_per_shard or 10
        limited_paths = paths[:max_files]

        # Create glob patterns
        glob_patterns = [f"{dir_name}/**"] if dir_name != "." else limited_paths

        shards.append(
            Shard(
                id=f"shard-{i}",
                title=f"Files in {dir_name}/",
                goal=f"Handle files in {dir_name}/ directory",
                content=task_text.strip(),  # Full task text for now (could be filtered)
                allowed_paths=glob_patterns,
            )
        )

    return shards[:shard_count]  # Limit to shard_count


def _extract_paths_from_text(text: str) -> List[str]:
    """
    Extract file paths from text using heuristics.

    Looks for tokens containing slashes, common file extensions, code blocks,
    and markdown links, then deduplicates and normalizes results.

    Args:
        text: The text to extract paths from

    Returns:
        List of extracted file paths
    """
    paths: List[str] = []

    # Pattern for file paths (containing / or ending in common extensions)
    path_pattern = re.compile(r'([a-zA-Z0-9_\-/]+(?:/[a-zA-Z0-9_\-./]+)+|[a-zA-Z0-9_\-/]+\.(?:py|json|md|txt|yaml|yml|toml|ini|cfg|conf|js|ts|tsx|jsx))')

    # Extract from backticks
    backtick_pattern = re.compile(r'`([^`]+)`')
    for match in backtick_pattern.finditer(text):
        content = match.group(1)
        if "/" in content or any(content.endswith(ext) for ext in [".py", ".json", ".md", ".txt"]):
            paths.append(content)

    # Extract from markdown links [text](path)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    for match in link_pattern.finditer(text):
        link_target = match.group(2)
        if not link_target.startswith("http"):
            paths.append(link_target)

    # Extract from plain text
    for match in path_pattern.finditer(text):
        path = match.group(0)
        # Filter out URLs
        if not path.startswith("http://") and not path.startswith("https://"):
            paths.append(path)

    # Deduplicate and normalize
    unique_paths = list(dict.fromkeys(paths))
    normalized = [Path(p).as_posix().rstrip(".") for p in unique_paths if p]

    return normalized


def save_shard_plan(shard_plan: ShardPlan, output_path: Path) -> None:
    """
    Save a shard plan to a JSON file.

    Args:
        shard_plan: The shard plan to save
        output_path: Path to save the JSON file
    """
    data = {
        "role_id": shard_plan.role_id,
        "shard_mode": shard_plan.shard_mode,
        "shard_count": shard_plan.shard_count,
        "overlap_policy": shard_plan.overlap_policy,
        "enforce_allowed_paths": shard_plan.enforce_allowed_paths,
        "shards": [
            {
                "id": shard.id,
                "title": shard.title,
                "goal": shard.goal,
                "allowed_paths": shard.allowed_paths,
            }
            for shard in shard_plan.shards
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
