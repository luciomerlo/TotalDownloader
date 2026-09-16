"""Configuración centralizada de logging (archivo + consola)."""
from __future__ import annotations

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "downloads"
LOG_FILE = LOG_DIR / "downloader_app.log"

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger configurado con salida a archivo y consola.

    La configuración de handlers se realiza una única vez a nivel de
    módulo raíz para evitar handlers duplicados en llamadas sucesivas.
    """
    global _CONFIGURED

    root = logging.getLogger("downloader_app")
    if not _CONFIGURED:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        root.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        root.addHandler(file_handler)
        root.addHandler(console_handler)
        root.propagate = False
        _CONFIGURED = True

    if name == "downloader_app":
        return root
    return root.getChild(name)
