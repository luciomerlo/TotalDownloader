"""Descarga HTTP(S) directa: single-connection con reanudación, o multi-conexión (segmentada)."""

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from tqdm import tqdm


def filename_from_url(url: str) -> str:
    name = unquote(Path(urlparse(url).path).name)
    return name or "download.bin"


@dataclass
class HttpTarget:
    filename: str

    @property
    def ext(self) -> str:
        return Path(self.filename).suffix.lstrip(".") or "?"


def list_http_target(url: str) -> HttpTarget:
    return HttpTarget(filename=filename_from_url(url))


def download_http(url: str, output_dir: Path, chunk_size: int = 1024 * 1024) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / filename_from_url(url)
    resume_from = dest.stat().st_size if dest.exists() else 0

    headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}
    with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=30) as resp:
        if resume_from and resp.status_code == 200:
            # El servidor ignoró el Range: reiniciar desde cero.
            resume_from = 0
        resp.raise_for_status()

        total = int(resp.headers.get("Content-Length", 0)) + resume_from
        mode = "ab" if resume_from else "wb"
        with dest.open(mode) as f, tqdm(
            total=total or None,
            initial=resume_from,
            unit="B",
            unit_scale=True,
            desc=dest.name,
        ) as bar:
            for chunk in resp.iter_bytes(chunk_size):
                f.write(chunk)
                bar.update(len(chunk))

    return dest


def split_ranges(total: int, parts: int) -> list[tuple[int, int]]:
    """Divide [0, total) en `parts` rangos (start, end) inclusive de tamaño similar."""
    size = total // parts
    ranges = []
    start = 0
    for i in range(parts):
        end = total - 1 if i == parts - 1 else start + size - 1
        ranges.append((start, end))
        start = end + 1
    return ranges


def _download_range(
    url: str, dest: Path, start: int, end: int, bar: tqdm, lock: threading.Lock, chunk_size: int
) -> None:
    headers = {"Range": f"bytes={start}-{end}"}
    with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=30) as resp:
        resp.raise_for_status()
        with dest.open("r+b") as f:
            f.seek(start)
            for chunk in resp.iter_bytes(chunk_size):
                f.write(chunk)
                with lock:
                    bar.update(len(chunk))


def download_http_concurrent(
    url: str, output_dir: Path, connections: int = 4, chunk_size: int = 1024 * 1024
) -> Path:
    """Descarga con varias conexiones en paralelo (Range) si el servidor lo soporta.

    Si no lo soporta, o `connections <= 1`, cae a `download_http` (single-connection,
    con reanudación).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / filename_from_url(url)

    head = httpx.head(url, follow_redirects=True, timeout=30)
    total = int(head.headers.get("Content-Length", 0))
    accepts_ranges = head.headers.get("Accept-Ranges", "").lower() == "bytes"

    if connections <= 1 or not accepts_ranges or total <= 0:
        return download_http(url, output_dir, chunk_size=chunk_size)

    if dest.exists() and dest.stat().st_size == total:
        return dest

    with dest.open("wb") as f:
        f.truncate(total)

    lock = threading.Lock()
    with tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar:
        with ThreadPoolExecutor(max_workers=connections) as executor:
            futures = [
                executor.submit(_download_range, url, dest, start, end, bar, lock, chunk_size)
                for start, end in split_ranges(total, connections)
            ]
            for future in futures:
                future.result()

    return dest
