#!/usr/bin/env python3
"""
tools/gpl_header.py

Purpose:
- Enforce a consistent GPL header across the repo’s Python files.
- Do it safely: only insert the header when it is missing.

Modes:
- One-shot: scan existing .py files and add a header if needed.
- Watch: keep running and add a header when new/changed .py files appear.

Usage:
  python tools/gpl_header.py --once
  python tools/gpl_header.py --watch
  python tools/gpl_header.py --watch --interval 0.5
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Iterable


# Header text to be inserted at the top of Python source files.
# This is a docstring so it is valid Python syntax and safe for tooling.
HEADER = '''"""
tinyTrainer - Interactive training kit for embedded systems

Copyright (c) 2026 Michael Garcia, M&E Design
Contact: michael@mandedesign.studio | mandedesign.studio

SPDX-License-Identifier: GPL-3.0-or-later

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""
'''

# Sentinel strings used to detect whether a file already has the correct header.
# These are intentionally simple and robust rather than perfectly precise.
SENTINELS = (
    "SPDX-License-Identifier: GPL-3.0-or-later",
    "GNU General Public License",
    "michael@mandedesign.studio",
)

# Directories that should never be scanned.
# These are common sources of generated or third-party files.
DEFAULT_EXCLUDES = (
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
)


def iter_py_files(root: Path, excludes: Iterable[str]) -> Iterable[Path]:
    """
    Yield all Python files under the given root directory,
    while pruning excluded directories to reduce noise and cost.
    """
    exclude_set = set(excludes)

    for dirpath, dirnames, filenames in os.walk(root):
        # Mutating dirnames in-place prevents os.walk from descending
        # into directories we explicitly want to ignore.
        dirnames[:] = [d for d in dirnames if d not in exclude_set]

        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn


def file_has_header(text: str) -> bool:
    """
    Return True if the file text appears to already contain the GPL header.

    We do not attempt to parse the AST or docstrings.
    Simple substring detection is sufficient and safer.
    """
    return any(s in text for s in SENTINELS)


def insert_header(path: Path) -> bool:
    """
    Insert the GPL header into the given file if it is missing.

    Returns:
        True  -> file was modified
        False -> file was left unchanged

    Design constraints:
    - Preserve shebang lines (scripts must remain executable).
    - Preserve PEP 263 encoding cookies (must stay in line 1 or 2).
    - Avoid rewriting files unnecessarily.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Skip non-UTF-8 files to avoid corruption.
        return False
    except FileNotFoundError:
        # File may have been deleted between discovery and read.
        return False

    if file_has_header(raw):
        return False

    lines = raw.splitlines(True)  # keep line endings
    prefix = ""
    i = 0

    # Preserve shebang line if present.
    if i < len(lines) and lines[i].startswith("#!"):
        prefix += lines[i]
        i += 1

    # Preserve encoding cookie if present (PEP 263).
    if i < len(lines) and "coding" in lines[i] and lines[i].lstrip().startswith("#"):
        prefix += lines[i]
        i += 1

    rest = "".join(lines[i:])

    # Build the final file text.
    # We enforce exactly one blank line between header and code.
    if rest.strip() == "":
        new_text = prefix + HEADER + "\n"
    else:
        new_text = prefix + HEADER + "\n" + rest.lstrip("\n")

    path.write_text(new_text, encoding="utf-8")
    return True


def run_once(root: Path, excludes: Iterable[str]) -> int:
    """
    One-shot mode: scan all Python files and insert headers where missing.
    Returns the number of files modified.
    """
    changed = 0
    for p in iter_py_files(root, excludes):
        if insert_header(p):
            changed += 1
    return changed


def watch(root: Path, excludes: Iterable[str], interval: float) -> None:
    """
    Watch mode using polling (standard library only).

    Change detection is based on (mtime, size) pairs.
    This avoids external dependencies and works consistently across platforms.
    """
    seen: dict[Path, tuple[float, int]] = {}

    while True:
        for p in iter_py_files(root, excludes):
            try:
                st = p.stat()
            except FileNotFoundError:
                continue

            sig = (st.st_mtime, st.st_size)
            prev = seen.get(p)

            if prev is None or prev != sig:
                # Update signature before modification to reduce self-trigger loops.
                seen[p] = sig
                insert_header(p)

        time.sleep(interval)


def main() -> None:
    """
    Command-line entry point.

    If neither --once nor --watch is specified, default to --once.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repo root to scan/watch (default: .)")
    ap.add_argument("--once", action="store_true", help="One-shot add headers to existing files")
    ap.add_argument("--watch", action="store_true", help="Watch for new/changed .py files and add header")
    ap.add_argument("--interval", type=float, default=1.0, help="Watch polling interval seconds (default: 1.0)")
    ap.add_argument(
        "--exclude",
        action="append",
        default=list(DEFAULT_EXCLUDES),
        help="Directory name to exclude (repeatable)",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    excludes = args.exclude

    if not args.once and not args.watch:
        args.once = True

    if args.once:
        changed = run_once(root, excludes)
        print(f"[gpl_header] Updated {changed} file(s).")

    if args.watch:
        print(f"[gpl_header] Watching {root} (interval={args.interval}s)... Ctrl+C to stop.")
        watch(root, excludes, args.interval)


# Standard entry guard so this module can be imported safely.
if __name__ == "__main__":
    main()