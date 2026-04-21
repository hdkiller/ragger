import os
import sys
from pathlib import Path


def _maybe_reexec_into_venv() -> None:
    project_root = Path(__file__).resolve().parent
    venv_python = project_root / ".venv" / "bin" / "python"

    if not venv_python.exists():
        return

    current_python = Path(sys.executable).resolve()
    if current_python == venv_python.resolve():
        return

    os.execv(str(venv_python), [str(venv_python), str(project_root / "main.py"), *sys.argv[1:]])

_maybe_reexec_into_venv()

from ragger.tui.app import RaggerApp

if __name__ == "__main__":
    app = RaggerApp()
    app.run()
