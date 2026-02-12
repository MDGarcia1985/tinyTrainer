#!/usr/bin/env python3
"""
tools/gpl_header_min.py

Purpose:
- Insert a short GPLv3 file header into Python files that do not already have it.

What it adds (verbatim intent, wrapped as a Python docstring):
tinyTrainer – Interactive training kit for embedded systems
Copyright (c) 2026 Michael Garcia
... (GPL notice) ...

Modes:
- One-shot: scan existing .py files and add the header if missing.
- Watch: keep running and add the header when new/changed .py files appear.

Usage:
  python tools/gpl_header_min.py --once
  python tools/gpl_header_min.py --watch
  python tools/gpl_header_min.py --watch --interval 0.5
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Iterable


# We store the notice as a Python docstring block so it is valid syntax.
# That makes it safe for any Python file, including modules and scripts.
HEADER = '''"""
tinyTrainer – Interactive training kit for embedded systems
Copyright (c) 2026 Michael Garcia

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
'''

# Sentinel strings used to decide whether a file already contains this notice.
# We keep these stable and specific to reduce accidental matches.
SENTINELS = (
    "tinyTrainer – Interactive training kit for embedded systems",
    "GNU General Public License",
    "Copyright (c) 2026 Michael Garcia",
)

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
    Yield .py files under root, skipping excluded directories.

    We prune directories in-place so os.walk does not descend into them.
    This keeps scanning fast and avoids generated/third-party files.
    """
    exclude_set = set(excludes)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_set]

        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn


def file_has_header(text: str) -> bool:
    """
    Return True if the file already appears to contain the header.

    We deliberately use substring checks instead of parsing.
    That keeps behavior predictable and avoids edge cases.
    """
    return any(s in text for s in SENTINELS)


def insert_header(path: Path) -> bool:
    """
    Insert the header if missing.

    Returns:
        True  -> file modified
        False -> no change

    We preserve:
    - shebang line (must remain first line for executable scripts)
    - PEP 263 encoding cookie (must be in line 1 or 2)
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # If a file is not UTF-8, skipping it is safer than corrupting it.
        return False
    except FileNotFoundError:
        return False

    if file_has_header(raw):
        return False

    lines = raw.splitlines(True)  # keep line endings
    prefix = ""
    i = 0

    # Preserve shebang (e.g., "#!/usr/bin/env python3")
    if i < len(lines) and lines[i].startswith("#!"):
        prefix += lines[i]
        i += 1

    # Preserve encoding cookie if present (PEP 263)
    if i < len(lines) and "coding" in lines[i] and lines[i].lstrip().startswith("#"):
        prefix += lines[i]
        i += 1

    rest = "".join(lines[i:])

    # Enforce exactly one blank line between header and code.
    if rest.strip() == "":
        new_text = prefix + HEADER + "\n"
    else:
        new_text = prefix + HEADER + "\n" + rest.lstrip("\n")

    path.write_text(new_text, encoding="utf-8")
    return True


def run_once(root: Path, excludes: Iterable[str]) -> int:
    """
    One-shot mode: apply header insertion across the repo.
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

    We track (mtime, size) so we can detect new/changed files.
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
                # Record before modifying to reduce self-trigger loops.
                seen[p] = sig
                insert_header(p)

        time.sleep(interval)


def main() -> None:
    """
    Command-line entry point.

    If neither --once nor --watch is specified, we default to --once.
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
        print(f"[gpl_header_min] Updated {changed} file(s).")

    if args.watch:
        print(f"[gpl_header_min] Watching {root} (interval={args.interval}s)... Ctrl+C to stop.")
        watch(root, excludes, args.interval)


if __name__ == "__main__":
    main()
