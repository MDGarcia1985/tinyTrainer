#!/usr/bin/env python3
"""
tools/rename_tiny_trainer.py

Purpose:
- Replace all occurrences of the string "tiny_trainer"
  with "tiny_trainer" across the repository.

Design goals:
- Simple, readable, and safe
- No AST parsing or regex cleverness
- Skip generated and virtual-environment directories
- Only modify files that actually change

This is intended as a one-time refactor tool.
"""

from pathlib import Path

OLD = "tiny_trainer"
NEW = "tiny_trainer"

# Directories we do not want to touch
EXCLUDES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
}

# File extensions we consider safe to edit as text
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".rst",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
}


def should_skip(path: Path) -> bool:
    """Return True if the path is inside an excluded directory."""
    return any(part in EXCLUDES for part in path.parts)


def process_file(path: Path) -> bool:
    """
    Replace OLD with NEW in the given file if present.

    Returns True if the file was modified.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Skip binary or non-UTF8 files safely
        return False

    if OLD not in text:
        return False

    new_text = text.replace(OLD, NEW)
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    root = Path(".").resolve()
    changed_files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if should_skip(path):
            continue

        if path.suffix not in TEXT_EXTENSIONS:
            continue

        if process_file(path):
            changed_files.append(path)

    print(f"[rename] Replaced '{OLD}' → '{NEW}' in {len(changed_files)} file(s).")
    for p in changed_files:
        print(f"  - {p.relative_to(root)}")


if __name__ == "__main__":
    main()