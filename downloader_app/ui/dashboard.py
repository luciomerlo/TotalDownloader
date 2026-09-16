"""Dashboard Streamlit: entrada de URLs, configuración, y monitoreo en tiempo real.

Ejecutar con: streamlit run ui/dashboard.py
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import streamlit as st

# Permite ejecutar `streamlit run ui/dashboard.py` desde la raíz del proyecto
# resolviendo los paquetes `core` y `utils` sin necesidad de instalación.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.engine import DownloadManager, DownloadStatus
from core.parser import parse_urls
from core.scraper import RecursiveScraper
from utils.config import DownloadConfig, ScraperConfig

st.set_page_config(page_title="TotalDownloader", layout="wide")


def _init_state() -> None:
    defaults = {
        "manager": None,
        "worker_thread": None,
        "is_running": False,
        "phase": "idle",  # idle | scraping | downloading | done
        "scrape_log": [],
        "scraped_count": 0,
        "current_page": "",
        "base_urls": [],
        "lock": threading.Lock(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()


def _run_pipeline(base_urls: list[str], scraper_cfg: ScraperConfig, download_cfg: DownloadConfig) -> None:
    """Ejecuta scraping + descarga en un hilo de fondo, actualizando session_state."""

    def on_scrape_progress(url: str, pages: int, files: int) -> None:
        with st.session_state["lock"]:
            st.session_state["current_page"] = url
            st.session_state["scraped_count"] = files

    st.session_state["phase"] = "scraping"
    scraper = RecursiveScraper(scraper_cfg, on_progress=on_scrape_progress)

    all_file_urls: list[str] = []
    for base_url in base_urls:
        result = scraper.scrape(base_url)
        all_file_urls.extend(f.url for f in result.files)
        with st.session_state["lock"]:
            st.session_state["scrape_log"].append(
                f"{base_url}: {len(result.files)} archivos, {len(result.visited_pages)} páginas"
            )

    manager: DownloadManager = st.session_state["manager"]
    manager.enqueue(all_file_urls)

    st.session_state["phase"] = "downloading"
    manager.start()
    manager.wait()
    st.session_state["phase"] = "done"
    st.session_state["is_running"] = False


def _start_pipeline(urls: list[str]) -> None:
    scraper_cfg = ScraperConfig(
        max_depth=st.session_state["cfg_max_depth"],
        same_domain_only=st.session_state["cfg_same_domain"],
        extension_whitelist=tuple(st.session_state["cfg_extensions"]),
    )
    download_cfg = DownloadConfig(
        output_dir=Path(st.session_state["cfg_output_dir"]),
        max_workers=st.session_state["cfg_workers"],
        speed_limit_kbps=st.session_state["cfg_speed_limit"],
    )

    manager = DownloadManager(download_cfg)
    st.session_state["manager"] = manager
    st.session_state["base_urls"] = urls
    st.session_state["scrape_log"] = []
    st.session_state["is_running"] = True

    thread = threading.Thread(
        target=_run_pipeline, args=(urls, scraper_cfg, download_cfg), daemon=True
    )
    st.session_state["worker_thread"] = thread
    thread.start()


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
st.title("TotalDownloader")
st.caption("Scraper recursivo y descargador masivo multihilo")

col_input, col_config = st.columns([2, 1])

with col_input:
    st.subheader("Panel de Entrada")
    urls_raw = st.text_area(
        "URLs (separadas por salto de línea, coma o punto y coma)",
        height=420,
        placeholder="https://ejemplo.com/archivos/\nhttps://otro-sitio.com/descargas/",
        key="urls_raw",
    )

    b1, b2, b3, b4 = st.columns(4)
    start_clicked = b1.button(
        "▶ Iniciar Scraping y Descarga", disabled=st.session_state["is_running"]
    )
    pause_clicked = b2.button("⏸ Pausar Cola", disabled=not st.session_state["is_running"])
    resume_clicked = b2.button("⏵ Reanudar", disabled=not st.session_state["is_running"])
    clear_clicked = b3.button("🗑 Limpiar Cola")
    export_clicked = b4.button("⬇ Exportar Lista")

with col_config:
    st.subheader("Panel de Configuración")
    st.slider("Hilos de descarga paralela", 1, 64, 8, key="cfg_workers")
    st.slider("Profundidad máxima de scraping", 0, 10, 2, key="cfg_max_depth")
    st.number_input(
        "Límite de velocidad (KB/s, 0 = ilimitado)", min_value=0, value=0, key="cfg_speed_limit"
    )
    st.text_input("Carpeta de destino", value="downloads", key="cfg_output_dir")
    st.text_input(
        "Filtro de extensiones (ej: pdf,zip,mp4 — vacío = todas)",
        value="",
        key="cfg_extensions_raw",
    )
    st.checkbox("Restringir al dominio base", value=True, key="cfg_same_domain")

    exts = [
        f".{e.strip().lstrip('.').lower()}"
        for e in st.session_state["cfg_extensions_raw"].split(",")
        if e.strip()
    ]
    st.session_state["cfg_extensions"] = exts

# --- Acciones de botones ---
if start_clicked:
    parsed = parse_urls(urls_raw)
    if not parsed:
        st.warning("No se encontraron URLs válidas.")
    else:
        _start_pipeline(parsed)
        st.rerun()

if pause_clicked and st.session_state["manager"]:
    st.session_state["manager"].pause()

if resume_clicked and st.session_state["manager"]:
    st.session_state["manager"].resume()

if clear_clicked:
    if st.session_state["manager"]:
        st.session_state["manager"].clear_queue()
    st.session_state["scrape_log"] = []
    st.rerun()

if export_clicked:
    manager = st.session_state["manager"]
    lines = list(manager.tasks.keys()) if manager else []
    st.download_button(
        "Descargar lista.txt",
        data="\n".join(lines),
        file_name="lista_urls.txt",
        mime="text/plain",
    )

st.divider()

# ---------------------------------------------------------------------------
# Panel de Monitoreo
# ---------------------------------------------------------------------------
st.subheader("Panel de Monitoreo")

manager: DownloadManager | None = st.session_state["manager"]

if st.session_state["phase"] == "scraping":
    st.info(f"Rastreando: {st.session_state['current_page']} — {st.session_state['scraped_count']} archivos hallados")

if manager is None:
    st.write("Sin actividad. Ingresá URLs y presioná *Iniciar Scraping y Descarga*.")
else:
    tasks = list(manager.tasks.values())
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == DownloadStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == DownloadStatus.FAILED)
    active = [t for t in tasks if t.status == DownloadStatus.DOWNLOADING]
    queued = [t for t in tasks if t.status == DownloadStatus.QUEUED]

    overall_pct = (completed / total) if total else 0.0
    st.progress(overall_pct, text=f"Progreso general: {completed}/{total} completados, {failed} fallidos")

    st.markdown("**Descargas activas**")
    if active:
        for task in active:
            speed_kb = task.speed_bps / 1024
            eta = f"{task.eta_seconds:.0f}s" if task.eta_seconds else "—"
            mb_done = task.downloaded_bytes / (1024 * 1024)
            mb_total = (task.total_bytes or 0) / (1024 * 1024)
            st.progress(
                task.progress_pct / 100,
                text=(
                    f"{task.dest_path.name} — {task.progress_pct:.1f}% "
                    f"({mb_done:.1f}/{mb_total:.1f} MB) · {speed_kb:.1f} KB/s · ETA {eta}"
                ),
            )
    else:
        st.caption("Ninguna descarga activa en este momento.")

    col_q, col_c = st.columns(2)
    with col_q:
        st.markdown("**Cola de espera (Queued)**")
        st.dataframe(
            [{"URL": t.url} for t in queued],
            use_container_width=True,
            height=200,
        )
    with col_c:
        st.markdown("**Finalizados (Completed / Failed)**")
        finished = [t for t in tasks if t.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED)]
        st.dataframe(
            [
                {
                    "URL": t.url,
                    "Estado": t.status.value,
                    "HTTP": t.http_status,
                    "Intentos": t.attempts,
                    "Error": t.error or "",
                }
                for t in finished
            ],
            use_container_width=True,
            height=200,
        )

    if st.session_state["scrape_log"]:
        with st.expander("Log de scraping"):
            for line in st.session_state["scrape_log"]:
                st.text(line)

# Auto-refresh mientras haya actividad en curso, para reflejar progreso en vivo.
if st.session_state["is_running"]:
    time.sleep(1.0)
    st.rerun()
