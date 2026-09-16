"""Punto de entrada de la aplicación.

Lanza el dashboard Streamlit. Uso equivalente:
    python main.py
    streamlit run ui/dashboard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import cli as stcli

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    dashboard_path = PROJECT_ROOT / "ui" / "dashboard.py"
    sys.argv = ["streamlit", "run", str(dashboard_path)]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
