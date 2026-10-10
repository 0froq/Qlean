#!/usr/bin/env python3
"""Concatenate nested CSS into the single theme.css Obsidian loads.

Language badges and alternative-checkbox icons are expanded from src/data.
Nesting stays in the output. `&` is only used to reach inward.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "css"
DATA = ROOT / "src" / "data"
OUT = ROOT / "theme.css"

FILES = [
    "tokens.css",
    "editor.css",
    "tasks.css",
    "blocks.css",
    "code.css",
    "tables.css",
    "tags.css",
    "workspace.css",
    "file-tree.css",
    "controls.css",
    "modes.css",
    "plugins.css",
    "style-settings.css",
]

MARKER = re.compile(r"^([ \t]*)/\* @generate ([^*]+)\*/[ \t]*$", re.M)


def css_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_languages(indent: str) -> str:
    names: list[str] = json.loads((DATA / "languages.json").read_text())
    blocks: list[str] = []
    for name in names:
        token = css_string(name)
        blocks.append(
            f"{indent}&.language-{token} {{\n"
            f"{indent}  position: relative;\n"
            f"{indent}  &:before {{\n"
            f"{indent}    font-family: var(--font-text);\n"
            f"{indent}    font-size: 0.875em;\n"
            f"{indent}    font-weight: 400;\n"
            f"{indent}    color: var(--text-muted);\n"
            f'{indent}    content: "{token}";\n'
            f"{indent}  }}\n"
            f"{indent}}}"
        )
    return "\n".join(blocks)


def render_checkboxes(which: str, indent: str) -> str:
    payload = json.loads((DATA / "checkboxes.json").read_text())
    hover = payload["hover"]
    blocks: list[str] = []
    for item in payload["sets"][which]:
        char = css_string(item["char"])
        blocks.append(
            f'{indent}&[data-task="{char}"] .task-list-item-checkbox {{\n'
            f"{indent}  &:hover::after {{\n"
            f"{indent}    background-color: {hover};\n"
            f"{indent}  }}\n"
            f"{indent}  &:after {{\n"
            f"{indent}    border: 1px solid transparent;\n"
            f"{indent}    mask-image: url('data:image/svg+xml;charset=utf8, {item['svg']}');\n"
            f"{indent}    background-color: {item['color']};\n"
            f"{indent}  }}\n"
            f"{indent}}}"
        )
    return "\n".join(blocks)


def expand(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        indent, kind = match.group(1), match.group(2).strip()
        if kind == "languages":
            return render_languages(indent)
        if kind.startswith("checkboxes "):
            return render_checkboxes(kind.split(" ", 1)[1], indent)
        raise SystemExit(f"unknown generate marker: {kind}")

    return MARKER.sub(replace, text)


def main() -> None:
    parts = [expand((SRC / name).read_text().rstrip()) + "\n" for name in FILES]
    text = "\n".join(parts)
    if not text.endswith("\n"):
        text += "\n"
    OUT.write_text(text)
    print(f"theme.css {text.count(chr(10))} lines")


if __name__ == "__main__":
    main()
