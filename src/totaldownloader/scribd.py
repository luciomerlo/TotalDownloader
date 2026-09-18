"""Descarga de documentos Scribd como PDF (dependencia opcional, extra 'scribd').

Envuelve el motor Selenium vendorizado en scribd-downloader/scribd-downloader.py
(carga y export página a página vía Chrome DevTools Protocol), sin duplicar su
lógica.
"""

import importlib.util
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

_ENGINE_PATH = Path(__file__).resolve().parents[2] / "scribd-downloader" / "scribd-downloader.py"


@dataclass
class ScribdTarget:
    filename: str


def _load_engine():
    if not _ENGINE_PATH.exists():
        raise RuntimeError(f"No se encontró el motor scribd-downloader en {_ENGINE_PATH}.")
    try:
        spec = importlib.util.spec_from_file_location("_scribd_engine", _ENGINE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError as exc:
        raise RuntimeError(
            "selenium/pypdf no están instalados. Instalá el extra: "
            "pip install 'totaldownloader[scribd]'"
        ) from exc
    return module


def list_scribd_target(url: str) -> ScribdTarget:
    engine = _load_engine()
    if engine.convert_scribd_link(url) == "Invalid Scribd URL":
        raise ValueError(f"URL de Scribd inválida: {url}")
    return ScribdTarget(filename=engine.get_filename_from_url(url))


def download_scribd(url: str, output_dir: Path) -> Path:
    engine = _load_engine()
    converted_url = engine.convert_scribd_link(url)
    if converted_url == "Invalid Scribd URL":
        raise ValueError(f"URL de Scribd inválida: {url}")

    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / engine.get_filename_from_url(url)

    with tempfile.TemporaryDirectory(prefix="scribd-chrome-profile-") as profile_dir:
        options = engine.build_chrome_options(profile_dir)
        driver = engine.webdriver.Chrome(options=options)
        try:
            driver.get(converted_url)
            time.sleep(1)
            engine.hide_cookie_dialogs(driver)

            total_pages = driver.execute_script(
                "return document.querySelectorAll('.outer_page').length;"
            )
            if total_pages == 0:
                raise RuntimeError("No se detectaron páginas del documento.")

            engine.prepare_document_for_print(driver)
            engine.inject_print_styles(driver)
            driver.execute_script("window.scrollTo(0, 0)")

            engine.save_pdf_pages_individually(driver, str(dest))
        finally:
            driver.quit()

    return dest
