"""
Run pytest and write a human-readable Markdown report.

This is a convenience entry point for developers so test reports are
generated consistently.
"""

from tiny_trainer.data.logger import run_and_write_report


def main() -> None:
    report_path = run_and_write_report(pytest_args=["-q"], repo_name="tiny_trainer")
    print(f"[tests] Wrote report: {report_path}")


if __name__ == "__main__":
    main()