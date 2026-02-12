"""
tinyTrainer - Interactive training kit for embedded systems
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

# data/logger.py
#
# Intent:
# - Produce a human-readable test report file that can be committed or archived.
# - Work with "plain pytest" output without requiring extra plugins.
#
# Design decisions:
# - We do not parse internal pytest objects. Instead we capture stdout/stderr and
#   extract the important information that humans look for:
#   * pass/fail counts
#   * failures (with short context)
#   * warnings summary
#   * runtime and environment basics
# - Reports are written as Markdown so they read well in GitHub/GitLab and in editors.

from __future__ import annotations

import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class TestRunResult:
    """
    Captures the essentials of a pytest run in a format that is stable and easy to read.

    We keep the raw output too, because when something goes sideways,
    the raw text is the truth.
    """

    return_code: int
    started_at_utc: str
    finished_at_utc: str
    duration_seconds: float

    passed: int
    failed: int
    skipped: int
    xfailed: int
    xpassed: int
    errors: int

    warnings_count: int
    short_summary: str

    stdout: str
    stderr: str


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _ensure_dir(path: Path) -> None:
    """
    Ensure the parent directory exists.

    We do not create the file here. We only ensure the folder is present,
    because folder creation is the piece that commonly fails on first run.
    """
    path.parent.mkdir(parents=True, exist_ok=True)


def _parse_counts(pytest_output: str) -> dict:
    """
    Extract pass/fail/etc counts from pytest's summary line.

    We accept that pytest formats can vary slightly across versions.
    If parsing fails, we return zeros and keep the raw output for reference.
    """
    # Examples we handle:
    # - "29 passed in 0.58s"
    # - "29 passed, 1 skipped, 2 warnings in 0.58s"
    # - "1 failed, 28 passed in 0.58s"
    # - "3 errors in 0.11s"
    counts = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "errors": 0,
        "warnings": 0,
    }

    # This grabs phrases like "29 passed" or "3 errors" from the summary line.
    tokens = re.findall(r"(\d+)\s+(passed|failed|skipped|xfailed|xpassed|errors|warnings)", pytest_output)
    for num, key in tokens:
        counts[key] = int(num)

    return counts


def _extract_short_summary(pytest_output: str, pytest_stderr: str) -> str:
    """
    Produce a human-friendly, single-line summary.

    If pytest prints a clear summary line, we use it.
    Otherwise we fall back to the last non-empty line of combined output.
    """
    combined = (pytest_output + "\n" + pytest_stderr).strip().splitlines()
    combined = [line.strip() for line in combined if line.strip()]

    # Prefer pytest's standard "short test summary info" and last status line.
    for i in range(len(combined) - 1, -1, -1):
        line = combined[i]
        if re.search(r"\b(passed|failed|errors?)\b", line) and "in " in line:
            return line

    return combined[-1] if combined else "No output captured."


def _extract_failures_block(pytest_output: str) -> str:
    """
    Pull the failure and error sections out of pytest output.

    The goal is not to perfectly parse pytest. The goal is to provide the
    relevant blocks in a report so a person can quickly see what broke.
    """
    # Common section headers in pytest output
    anchors = [
        "FAILURES",
        "ERRORS",
        "short test summary info",
        "=========================== short test summary info ===========================",
    ]

    lines = pytest_output.splitlines()
    idxs = [i for i, line in enumerate(lines) if any(a in line for a in anchors)]
    if not idxs:
        return ""

    # Grab from the first important section to the end.
    start = idxs[0]
    block = "\n".join(lines[start:]).strip()
    return block


def run_pytest_and_capture(
    args: Optional[Iterable[str]] = None,
    cwd: Optional[Path] = None,
) -> TestRunResult:
    """
    Execute pytest as a subprocess and capture results.

    Why subprocess:
    - It behaves the same as the command line.
    - It avoids surprises from importing pytest into the program environment.
    - It keeps this module small and reliable.

    Args:
        args: Extra arguments passed to pytest. Example: ["-q"]
        cwd: Working directory to run pytest from. Defaults to current directory.

    Returns:
        A TestRunResult that can be rendered to Markdown.
    """
    started = datetime.utcnow()
    started_iso = started.replace(microsecond=0).isoformat() + "Z"

    cmd: List[str] = [sys.executable, "-m", "pytest"]
    if args:
        cmd.extend(list(args))

    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    finished = datetime.utcnow()
    finished_iso = finished.replace(microsecond=0).isoformat() + "Z"
    duration = (finished - started).total_seconds()

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    counts = _parse_counts(stdout + "\n" + stderr)
    summary = _extract_short_summary(stdout, stderr)

    return TestRunResult(
        return_code=proc.returncode,
        started_at_utc=started_iso,
        finished_at_utc=finished_iso,
        duration_seconds=duration,
        passed=counts["passed"],
        failed=counts["failed"],
        skipped=counts["skipped"],
        xfailed=counts["xfailed"],
        xpassed=counts["xpassed"],
        errors=counts["errors"],
        warnings_count=counts["warnings"],
        short_summary=summary,
        stdout=stdout,
        stderr=stderr,
    )


def render_markdown_report(result: TestRunResult, repo_name: str = "tiny_trainer") -> str:
    """
    Render a human-readable Markdown report.

    We prefer readable over fancy. This should be understandable
    by someone who has never used pytest before.
    """
    env_lines = [
        f"- Repo: `{repo_name}`",
        f"- Python: `{sys.version.split()[0]}`",
        f"- Platform: `{platform.platform()}`",
        f"- Started (UTC): `{result.started_at_utc}`",
        f"- Finished (UTC): `{result.finished_at_utc}`",
        f"- Duration: `{result.duration_seconds:.2f}s`",
        f"- Exit code: `{result.return_code}`",
    ]

    outcome_lines = [
        f"- Passed: **{result.passed}**",
        f"- Failed: **{result.failed}**",
        f"- Errors: **{result.errors}**",
        f"- Skipped: **{result.skipped}**",
        f"- XFailed: **{result.xfailed}**",
        f"- XPassed: **{result.xpassed}**",
        f"- Warnings: **{result.warnings_count}**",
    ]

    failures_block = _extract_failures_block(result.stdout + "\n" + result.stderr)
    failures_md = (
        "## Failures / Errors\n\n"
        "No failures or errors were detected in the captured output.\n"
        if not failures_block.strip()
        else "## Failures / Errors\n\n```text\n" + failures_block.strip() + "\n```\n"
    )

    # We keep raw output at the bottom because it is sometimes the only clue.
    # It is separated so the “human summary” stays near the top.
    raw_out = (result.stdout + "\n" + result.stderr).strip()
    if not raw_out:
        raw_out = "No raw output captured."

    md = "\n".join(
        [
            f"# Test Report — {repo_name}",
            "",
            "## Summary",
            "",
            f"**{result.short_summary}**",
            "",
            "## Environment",
            "",
            "\n".join(env_lines),
            "",
            "## Outcomes",
            "",
            "\n".join(outcome_lines),
            "",
            failures_md,
            "## Raw Output",
            "",
            "```text",
            raw_out,
            "```",
            "",
        ]
    )
    return md


def package_data_dir() -> Path:
    """
    Return the on-disk folder for the tiny_trainer.data package.

    We intentionally anchor outputs to the package directory so the report
    location is stable no matter where the command is run from.
    """
    return Path(__file__).resolve().parent


def default_reports_dir() -> Path:
    """
    Default location for human-readable test reports.

    This keeps all artifacts close to the code that generated them.
    """
    return package_data_dir() / "test_reports"


def write_test_report(
    result: TestRunResult,
    out_path: Optional[Path] = None,
    repo_name: str = "tiny_trainer",
) -> Path:
    """
    Write a Markdown test report to disk and return the path.

    If out_path is not provided, we write to tiny_trainer/data/test_reports/latest.md.
    """
    path = out_path if out_path is not None else (default_reports_dir() / "latest.md")
    _ensure_dir(path)
    md = render_markdown_report(result, repo_name=repo_name)
    path.write_text(md, encoding="utf-8")
    return path


def run_and_write_report(
    pytest_args: Optional[Iterable[str]] = None,
    out_dir: Optional[Path] = None,
    repo_name: str = "tiny_trainer",
) -> Path:
    """
    Convenience function:
    - run pytest
    - write a timestamped report
    - update a stable 'latest.md' copy for quick access

    Reports default to tiny_trainer/data/test_reports, regardless of where you run from.
    """
    result = run_pytest_and_capture(args=pytest_args)

    reports_dir = out_dir if out_dir is not None else default_reports_dir()

    print("[logger] __file__ =", Path(__file__).resolve())
    print("[logger] reports_dir =", reports_dir.resolve())


    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%SZ")
    timestamped = reports_dir / f"test_report_{stamp}.md"
    latest = reports_dir / "latest.md"

    write_test_report(result, out_path=timestamped, repo_name=repo_name)
    write_test_report(result, out_path=latest, repo_name=repo_name)

    return latest


if __name__ == "__main__":
    # Manual smoke test:
    # - Run pytest
    # - Write a report under tiny_trainer/data/test_reports
    report = run_and_write_report(pytest_args=["-q"], repo_name="tiny_trainer")
    print(f"[logger] Test report written to: {report}")
