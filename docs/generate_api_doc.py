#!/usr/bin/env python3
"""
Generate an HTML API reference from module, class, and function docstrings.
"""

from __future__ import annotations

import ast
import html
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = Path(__file__).resolve().parent / "api_reference.html"
SOURCE_DIRS = ["multi_agent", "creators", "evaluation"]
ROOT_FILES = ["multi_agent_codex.py", "migrate_configs.py"]


@dataclass(frozen=True)
class MethodInfo:
    name: str
    doc: str


@dataclass(frozen=True)
class ClassInfo:
    name: str
    doc: str
    methods: List[MethodInfo]


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    doc: str


@dataclass(frozen=True)
class ModuleInfo:
    path: Path
    doc: str
    classes: List[ClassInfo]
    functions: List[FunctionInfo]


def _iter_python_files() -> Iterable[Path]:
    for rel_dir in SOURCE_DIRS:
        base = ROOT / rel_dir
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            yield path
    for filename in ROOT_FILES:
        path = ROOT / filename
        if path.exists():
            yield path


def _parse_module(path: Path) -> ModuleInfo:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    module_doc = ast.get_docstring(tree) or ""

    classes: List[ClassInfo] = []
    functions: List[FunctionInfo] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node) or ""
            methods: List[MethodInfo] = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(MethodInfo(child.name, ast.get_docstring(child) or ""))
            classes.append(ClassInfo(node.name, class_doc, methods))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(FunctionInfo(node.name, ast.get_docstring(node) or ""))

    return ModuleInfo(path=path, doc=module_doc, classes=classes, functions=functions)


def _escape(text: str) -> str:
    escaped = html.escape(text)
    return escaped.encode("ascii", "xmlcharrefreplace").decode("ascii")


def _summary_line(doc: str, max_len: int = 90) -> str:
    for line in doc.splitlines():
        if line.strip():
            summary = line.strip()
            if len(summary) > max_len:
                return summary[: max_len - 3].rstrip() + "..."
            return summary
    return ""


def _render_doc_summary(doc: str) -> str:
    summary = _summary_line(doc)
    if not summary:
        return '<span class="empty">No docstring.</span>'
    return f"<span>{_escape(summary)}</span>"


def _anchor_id(path: str) -> str:
    return "module-" + path.replace("/", "-").replace(".", "-")


def build_html(modules: List[ModuleInfo]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    toc_items = []
    for module in modules:
        rel_path = module.path.relative_to(ROOT).as_posix()
        toc_items.append(f'<li><a href="#{_anchor_id(rel_path)}">{_escape(rel_path)}</a></li>')
    toc_html = "\n".join(toc_items)

    sections = []
    for module in modules:
        rel_path = module.path.relative_to(ROOT).as_posix()
        section = [f'<section id="{_anchor_id(rel_path)}">']
        section.append(f"<h2>{_escape(rel_path)}</h2>")
        section.append(f"<p>{_render_doc_summary(module.doc)}</p>")

        if module.classes:
            section.append("<h3>Classes</h3>")
            section.append("<ul>")
            for cls in module.classes:
                summary = _render_doc_summary(cls.doc)
                section.append(f"<li><strong>{_escape(cls.name)}</strong>: {summary}</li>")
            section.append("</ul>")

        if module.functions:
            section.append("<h3>Functions</h3>")
            section.append("<ul>")
            for func in module.functions:
                summary = _render_doc_summary(func.doc)
                section.append(f"<li><strong>{_escape(func.name)}</strong>: {summary}</li>")
            section.append("</ul>")

        section.append("</section>")
        sections.append("\n".join(section))

    sections_html = "\n".join(sections)

    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>MultiAgent API Reference</title>"
        "<style>body{font-family:Georgia,\"Times New Roman\",serif;margin:24px;"
        "background:#f6f1ea;color:#2b2620}h1{margin:0 0 8px 0}h2{margin-top:24px;"
        "border-bottom:2px solid #b8a59b}h3{margin-top:16px}ul{padding-left:20px}"
        ".empty{color:#6f6258;font-style:italic}</style></head><body>"
        f"<h1>MultiAgent API Reference</h1><p>Generated {timestamp}.</p>"
        f"<h2>Table of Contents</h2><ul>{toc_html}</ul>{sections_html}</body></html>"
    )


def main() -> None:
    modules = [_parse_module(path) for path in sorted(_iter_python_files(), key=lambda p: p.as_posix())]
    html_text = build_html(modules)
    OUTPUT_PATH.write_text(html_text, encoding="utf-8")
    rel_out = OUTPUT_PATH.relative_to(ROOT)
    print(f"Wrote {rel_out}")


if __name__ == "__main__":
    main()
