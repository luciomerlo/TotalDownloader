"""Descarga HTTP(S) directa, con reanudación vía Range requests."""

from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from tqdm import tqdm


def filename_from_url(url: str) -> str:
    name = unquote(Path(urlparse(url).path).name)
    return name or "download.bin"


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
