"""Dashboard Streamlit: entrada de URLs, configuración, y monitoreo en tiempo real.

Ejecutar con: streamlit run ui/dashboard.py

Notas de diseño:
- El monitoreo en vivo usa `st.fragment(run_every=...)` en lugar de
  `time.sleep` + `st.rerun()` sobre todo el script: sólo esa sección se
  vuelve a ejecutar cada segundo, evitando parpadeo y pérdida de foco en
  los widgets de entrada/configuración.
- `st.session_state` sólo se lee/escribe desde el hilo principal de
  Streamlit. El hilo de fondo del pipeline (scraping + descarga) nunca
  llama a `st.*` ni toca `st.session_state`: su progreso se comunica a
  través de `PipelineState`, un objeto plano protegido por un lock cuya
  única referencia vive en session_state. Esto evita el problema conocido
  de Streamlit donde `st.session_state` requiere un `ScriptRunContext`
  que los hilos manuales no tienen.
"""
from __future__ import annotations

import csv
import io
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

import streamlit as st

# Permite ejecutar `streamlit run ui/dashboard.py` desde la raíz del proyecto
# resolviendo los paquetes `core` y `utils` sin necesidad de instalación.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.engine import DownloadManager, DownloadStatus
from core.parser import parse_urls
from core.scraper import RecursiveScraper
from utils.config import DownloadConfig, ScraperConfig

st.set_page_config(page_title="TotalDownloader", page_icon="⬇️", layout="wide")


@dataclass
class PipelineState:
    """Estado compartido entre el hilo de fondo y la UI, ajeno a session_state."""

    lock: threading.Lock = field(default_factory=threading.Lock)
    phase: str = "idle"  # idle | scraping | downloading | done | stopped | error
    is_running: bool = False
    current_page: str = ""
    scraped_count: int = 0
    scrape_log: list[str] = field(default_factory=list)
    error_message: str | None = None
    last_toast_phase: str | None = None


def _init_state() -> None:
    if "pipeline_state" not in st.session_state:
        st.session_state["pipeline_state"] = PipelineState()
    st.session_state.setdefault("manager", None)
    st.session_state.setdefault("pipeline_thread", None)


_init_state()
pstate: PipelineState = st.session_state["pipeline_state"]


# ---------------------------------------------------------------------------
# Pipeline en hilo de fondo (no llama a ninguna API de Streamlit)
# ---------------------------------------------------------------------------
def _run_pipeline(
    base_urls: list[str],
    scraper_cfg: ScraperConfig,
    manager: DownloadManager,
    state: PipelineState,
) -> None:
    """Ejecuta scraping + descarga en un hilo de fondo, actualizando `state`.

    Cualquier excepción no controlada se captura y se expone en
    `state.error_message` para que la UI la muestre, en lugar de silenciarla
    o dejar el hilo morir sin dejar rastro (patrón de resiliencia de yt-dlp).
    """

    def on_scrape_progress(url: str, pages: int, files: int) -> None:
        with state.lock:
            state.current_page = url
            state.scraped_count = files

    try:
        with state.lock:
            state.phase = "scraping"
        scraper = RecursiveScraper(scraper_cfg, on_progress=on_scrape_progress)

        all_file_urls: list[str] = []
        for base_url in base_urls:
            result = scraper.scrape(base_url)
            all_file_urls.extend(f.url for f in result.files)
            with state.lock:
                state.scrape_log.append(
                    f"{base_url}: {len(result.files)} archivos, {len(result.visited_pages)} páginas"
                )

        if not all_file_urls:
            with state.lock:
                state.phase = "done"
            return

        manager.enqueue(all_file_urls)
        with state.lock:
            state.phase = "downloading"
        manager.start()
        manager.wait()
        with state.lock:
            state.phase = "done"
    except Exception as exc:  # noqa: BLE001 - se reporta a la UI, no se silencia.
        with state.lock:
            state.error_message = f"{type(exc).__name__}: {exc}"
            state.phase = "error"
    finally:
        with state.lock:
            state.is_running = False


def _start_pipeline(urls: list[str]) -> None:
    old_manager: DownloadManager | None = st.session_state["manager"]
    if old_manager is not None:
        old_manager.stop()
        old_manager.shutdown()

    output_dir = Path(st.session_state["cfg_output_dir"]).expanduser()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        st.error(f"No se pudo crear la carpeta de destino '{output_dir}': {exc}")
        return

    scraper_cfg = ScraperConfig(
        max_depth=st.session_state["cfg_max_depth"],
        same_domain_only=st.session_state["cfg_same_domain"],
        extension_whitelist=tuple(st.session_state["cfg_extensions"]),
    )
    download_cfg = DownloadConfig(
        output_dir=output_dir,
        max_workers=st.session_state["cfg_workers"],
        speed_limit_kbps=st.session_state["cfg_speed_limit"],
    )

    manager = DownloadManager(download_cfg)
    new_state = PipelineState(is_running=True, phase="scraping")
    st.session_state["manager"] = manager
    st.session_state["pipeline_state"] = new_state

    thread = threading.Thread(
        target=_run_pipeline, args=(urls, scraper_cfg, manager, new_state), daemon=True
    )
    st.session_state["pipeline_thread"] = thread
    thread.start()


def _stop_pipeline() -> None:
    manager: DownloadManager | None = st.session_state["manager"]
    if manager is not None:
        manager.stop()
        manager.shutdown()
    with pstate.lock:
        pstate.is_running = False
        pstate.phase = "stopped"


def _tasks_to_csv(tasks: list) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=["url", "status", "http_status", "attempts", "downloaded_bytes", "error"]
    )
    writer.writeheader()
    for t in tasks:
        writer.writerow(
            {
                "url": t.url,
                "status": t.status.value,
                "http_status": t.http_status,
                "attempts": t.attempts,
                "downloaded_bytes": t.downloaded_bytes,
                "error": t.error or "",
            }
        )
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Sidebar: Panel de Configuración
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")

    st.slider("Hilos de descarga paralela", 1, 64, 8, key="cfg_workers")
    st.slider("Profundidad máxima de scraping", 0, 10, 2, key="cfg_max_depth")
    st.number_input(
        "Límite de velocidad (KB/s, 0 = ilimitado)", min_value=0, value=0, step=64, key="cfg_speed_limit"
    )
    st.text_input("Carpeta de destino", value="downloads", key="cfg_output_dir")
    st.text_input(
        "Filtro de extensiones (ej: pdf,zip,mp4 — vacío = todas)",
        value="",
        key="cfg_extensions_raw",
    )
    st.checkbox("Restringir al dominio base", value=True, key="cfg_same_domain")

    st.session_state["cfg_extensions"] = [
        f".{e.strip().lstrip('.').lower()}"
        for e in st.session_state["cfg_extensions_raw"].split(",")
        if e.strip()
    ]

    st.divider()
    st.caption(f"Log: `{Path('downloads/downloader_app.log')}`")


# ---------------------------------------------------------------------------
# Panel de Entrada
# ---------------------------------------------------------------------------
st.title("⬇️ TotalDownloader")
st.caption("Scraper recursivo y descargador masivo multihilo")

urls_raw = st.text_area(
    "URLs (separadas por salto de línea, coma o punto y coma)",
    height=280,
    placeholder="https://ejemplo.com/archivos/\nhttps://otro-sitio.com/descargas/",
    key="urls_raw",
)

b1, b2, b3, b4, b5 = st.columns(5)
start_clicked = b1.button("▶ Iniciar", disabled=pstate.is_running, width="stretch")

manager_for_buttons: DownloadManager | None = st.session_state["manager"]
is_paused = manager_for_buttons.is_paused if manager_for_buttons else False
pause_label = "⏵ Reanudar" if is_paused else "⏸ Pausar"
pause_toggle_clicked = b2.button(pause_label, disabled=not pstate.is_running, width="stretch")

stop_clicked = b3.button("⏹ Detener", disabled=not pstate.is_running, width="stretch")
clear_clicked = b4.button("🗑 Limpiar", width="stretch")
export_clicked = b5.button("⬇ Exportar", width="stretch")

if start_clicked:
    parsed = parse_urls(urls_raw)
    if not parsed:
        st.warning("No se encontraron URLs válidas.")
    else:
        _start_pipeline(parsed)
        st.rerun()

if pause_toggle_clicked and manager_for_buttons:
    manager_for_buttons.resume() if is_paused else manager_for_buttons.pause()
    st.rerun()

if stop_clicked:
    _stop_pipeline()
    st.rerun()

if clear_clicked:
    if st.session_state["manager"]:
        st.session_state["manager"].clear_queue()
    with pstate.lock:
        pstate.scrape_log = []
        pstate.error_message = None
    st.rerun()

if export_clicked:
    manager = st.session_state["manager"]
    if manager and manager.tasks:
        st.download_button(
            "Descargar reporte CSV",
            data=_tasks_to_csv(list(manager.tasks.values())),
            file_name="totaldownloader_report.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay tareas para exportar todavía.")

if pstate.error_message:
    st.error(f"Error en el pipeline: {pstate.error_message}")

st.divider()


# ---------------------------------------------------------------------------
# Panel de Monitoreo (fragmento con auto-refresh acotado a esta sección)
# ---------------------------------------------------------------------------
@st.fragment(run_every=1.0 if pstate.is_running else None)
def render_monitor() -> None:
    state: PipelineState = st.session_state["pipeline_state"]
    st.subheader("📊 Monitoreo")

    if state.phase == "scraping":
        st.info(f"Rastreando: {state.current_page} — {state.scraped_count} archivos hallados")

    manager: DownloadManager | None = st.session_state["manager"]

    if manager is None:
        st.write("Sin actividad. Ingresá URLs y presioná **Iniciar**.")
        return

    tasks = list(manager.tasks.values())
    total = len(tasks)
    completed = [t for t in tasks if t.status == DownloadStatus.COMPLETED]
    failed = [t for t in tasks if t.status == DownloadStatus.FAILED]
    active = [t for t in tasks if t.status == DownloadStatus.DOWNLOADING]
    queued = [t for t in tasks if t.status == DownloadStatus.QUEUED]

    total_mb = sum(t.downloaded_bytes for t in tasks) / (1024 * 1024)
    combined_speed_kb = sum(t.speed_bps for t in active) / 1024

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total", total)
    m2.metric("Completados", len(completed))
    m3.metric("Fallidos", len(failed))
    m4.metric("Transferido (MB)", f"{total_mb:.1f}")
    m5.metric("Velocidad (KB/s)", f"{combined_speed_kb:.0f}")

    overall_pct = (len(completed) / total) if total else 0.0
    st.progress(overall_pct, text=f"Progreso general: {len(completed)}/{total} completados, {len(failed)} fallidos")

    tab_active, tab_queue, tab_done, tab_log = st.tabs(
        [
            f"Activas ({len(active)})",
            f"En cola ({len(queued)})",
            f"Finalizadas ({len(completed) + len(failed)})",
            "Log",
        ]
    )

    with tab_active:
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

    with tab_queue:
        st.dataframe([{"URL": t.url} for t in queued], width="stretch", height=240)

    with tab_done:
        finished = completed + failed
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
            width="stretch",
            height=240,
        )

    with tab_log:
        if state.scrape_log:
            for line in state.scrape_log:
                st.text(line)
        else:
            st.caption("Sin actividad de scraping registrada todavía.")

    # Notificación única al finalizar el pipeline (evita repetir el toast en cada refresh).
    if state.phase in ("done", "error", "stopped") and state.last_toast_phase != state.phase:
        state.last_toast_phase = state.phase
        if state.phase == "done":
            st.toast(f"Pipeline finalizado: {len(completed)} completados, {len(failed)} fallidos.", icon="✅")
        elif state.phase == "stopped":
            st.toast("Pipeline detenido por el usuario.", icon="⏹")
        else:
            st.toast("El pipeline finalizó con errores.", icon="⚠️")


render_monitor()
