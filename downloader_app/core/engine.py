"""Motor de descarga multihilo.

Inspirado en:
- aria2: descargas por rangos (Range) y gestión eficiente de conexiones
  concurrentes.
- yt-dlp: resiliencia ante fallos de red mediante reintentos con backoff
  exponencial y hooks de monitoreo de progreso.
"""
from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import requests

from utils.config import DownloadConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class DownloadTask:
    """Estado mutable de una descarga individual, actualizado por el worker."""

    url: str
    dest_path: Path
    status: DownloadStatus = DownloadStatus.QUEUED
    total_bytes: int | None = None
    downloaded_bytes: int = 0
    speed_bps: float = 0.0
    eta_seconds: float | None = None
    http_status: int | None = None
    error: str | None = None
    attempts: int = 0

    @property
    def progress_pct(self) -> float:
        if not self.total_bytes:
            return 0.0
        return min(100.0, 100.0 * self.downloaded_bytes / self.total_bytes)


def build_local_path(url: str, output_dir: Path, preserve_structure: bool) -> Path:
    """Construye la ruta local de destino a partir de la URL remota."""
    parsed = urlparse(url)
    filename = Path(parsed.path).name or "index.html"

    if preserve_structure:
        remote_dir = str(Path(parsed.path).parent).lstrip("/")
        target_dir = output_dir / parsed.netloc / remote_dir
    else:
        target_dir = output_dir

    return target_dir / filename


class RateLimiter:
    """Limitador de velocidad simple (token-ish) compartido entre workers."""

    def __init__(self, limit_kbps: int):
        self._limit_bps = limit_kbps * 1024
        self._lock = threading.Lock()
        self._window_start = time.monotonic()
        self._window_bytes = 0

    def throttle(self, chunk_len: int) -> None:
        if self._limit_bps <= 0:
            return
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._window_start
            if elapsed >= 1.0:
                self._window_start = now
                self._window_bytes = 0
                elapsed = 0.0
            self._window_bytes += chunk_len
            expected_time = self._window_bytes / self._limit_bps
            sleep_for = expected_time - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)


class DownloadManager:
    """Gestiona la cola de descargas y su ejecución multihilo."""

    def __init__(self, config: DownloadConfig, on_update=None):
        self.config = config
        self.on_update = on_update
        self.tasks: dict[str, DownloadTask] = {}
        self._executor: ThreadPoolExecutor | None = None
        self._futures: list[Future] = []
        self._pause_event = threading.Event()
        self._pause_event.set()  # set = correr, clear = pausado
        self._stop_flag = threading.Event()
        self._rate_limiter = RateLimiter(config.speed_limit_kbps)

    def enqueue(self, urls: list[str]) -> None:
        for url in urls:
            if url in self.tasks:
                continue
            dest = build_local_path(url, self.config.output_dir, self.config.preserve_structure)
            self.tasks[url] = DownloadTask(url=url, dest_path=dest)

    def clear_queue(self) -> None:
        self.tasks = {k: v for k, v in self.tasks.items() if v.status == DownloadStatus.DOWNLOADING}

    def pause(self) -> None:
        self._pause_event.clear()

    def resume(self) -> None:
        self._pause_event.set()

    def stop(self) -> None:
        self._stop_flag.set()
        self._pause_event.set()

    def _headers(self, resume_from: int = 0) -> dict[str, str]:
        headers = {"User-Agent": random.choice(self.config.user_agents)}
        if resume_from:
            headers["Range"] = f"bytes={resume_from}-"
        return headers

    def _notify(self, task: DownloadTask) -> None:
        if self.on_update:
            self.on_update(task)

    def _download_one(self, task: DownloadTask) -> None:
        task.dest_path.parent.mkdir(parents=True, exist_ok=True)
        resume_from = task.dest_path.stat().st_size if task.dest_path.exists() else 0

        for attempt in range(1, self.config.max_retries + 1):
            if self._stop_flag.is_set():
                return
            self._pause_event.wait()

            task.attempts = attempt
            task.status = DownloadStatus.DOWNLOADING
            try:
                with requests.get(
                    task.url,
                    headers=self._headers(resume_from),
                    stream=True,
                    timeout=30,
                ) as response:
                    task.http_status = response.status_code

                    if response.status_code == 416:
                        # El archivo local ya está completo.
                        task.status = DownloadStatus.COMPLETED
                        task.downloaded_bytes = resume_from
                        task.total_bytes = resume_from
                        self._notify(task)
                        return

                    response.raise_for_status()

                    accepts_range = response.status_code == 206
                    mode = "ab" if accepts_range and resume_from else "wb"
                    if not accepts_range:
                        resume_from = 0

                    content_length = response.headers.get("Content-Length")
                    if content_length is not None:
                        task.total_bytes = resume_from + int(content_length)

                    downloaded = resume_from
                    start_time = time.monotonic()
                    last_notify = 0.0

                    with open(task.dest_path, mode) as fh:
                        for chunk in response.iter_content(chunk_size=self.config.chunk_size):
                            if self._stop_flag.is_set():
                                return
                            self._pause_event.wait()
                            if not chunk:
                                continue

                            fh.write(chunk)
                            downloaded += len(chunk)
                            task.downloaded_bytes = downloaded
                            self._rate_limiter.throttle(len(chunk))

                            elapsed = time.monotonic() - start_time
                            if elapsed > 0:
                                task.speed_bps = (downloaded - resume_from) / elapsed
                                if task.total_bytes and task.speed_bps > 0:
                                    remaining = task.total_bytes - downloaded
                                    task.eta_seconds = remaining / task.speed_bps

                            now = time.monotonic()
                            if now - last_notify > 0.2:
                                last_notify = now
                                self._notify(task)

                    task.status = DownloadStatus.COMPLETED
                    task.error = None
                    self._notify(task)
                    logger.info("Descarga completada: %s -> %s", task.url, task.dest_path)
                    return

            except requests.RequestException as exc:
                task.error = str(exc)
                logger.warning(
                    "Fallo intento %d/%d para %s: %s",
                    attempt,
                    self.config.max_retries,
                    task.url,
                    exc,
                )
                if attempt < self.config.max_retries:
                    backoff = self.config.backoff_base ** attempt
                    time.sleep(backoff)
                    resume_from = task.dest_path.stat().st_size if task.dest_path.exists() else 0
                else:
                    task.status = DownloadStatus.FAILED
                    self._notify(task)
                    logger.error("Descarga fallida definitivamente: %s", task.url)

    def start(self) -> None:
        """Lanza el ThreadPoolExecutor para procesar todas las tareas en cola."""
        self._stop_flag.clear()
        self._pause_event.set()
        pending = [t for t in self.tasks.values() if t.status != DownloadStatus.COMPLETED]

        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._futures = [self._executor.submit(self._download_one, task) for task in pending]

    def wait(self) -> None:
        for future in self._futures:
            future.result()

    def shutdown(self) -> None:
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in DownloadStatus}
        for task in self.tasks.values():
            counts[task.status.value] += 1
        return counts
