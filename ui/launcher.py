# launcher.py
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def main() -> int:
    ui_dir = Path(__file__).resolve().parent
    project_root = ui_dir.parent
    app = ui_dir / "app_streamlit.py"

    # Pick a port. 8501 is Streamlit default; using an explicit port is predictable.
    port = 8501
    url = f"http://localhost:{port}"

    # Start Streamlit server
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--client.toolbarMode", "minimal",
    ]

    creationflags = 0
    if os.name == "nt":
        # Helps keep process group separate; makes shutdown cleaner.
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    # Give the server a moment to start
    time.sleep(1.2)
    webbrowser.open(url)

    # Keep launcher alive while Streamlit runs
    try:
        while proc.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            proc.terminate()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
