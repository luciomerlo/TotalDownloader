"""Descarga de torrents/magnet vía libtorrent (dependencia opcional, extra 'torrent')."""

import time
from dataclasses import dataclass
from pathlib import Path

_METADATA_TIMEOUT = 30.0


@dataclass
class TorrentFile:
    index: int
    path: str
    size: int

    @property
    def ext(self) -> str:
        return Path(self.path).suffix.lstrip(".") or "?"


def _require_libtorrent():
    try:
        import libtorrent as lt
    except ImportError as exc:
        raise RuntimeError(
            "libtorrent no está instalado. Instalá el extra: pip install 'totaldownloader[torrent]'"
        ) from exc
    return lt


def _resolve_handle(lt, source: str, session, save_path: str):
    params = {"save_path": save_path}
    if source.startswith("magnet:"):
        handle = lt.add_magnet_uri(session, source, params)
    else:
        params["ti"] = lt.torrent_info(source)
        handle = session.add_torrent(params)

    deadline = time.monotonic() + _METADATA_TIMEOUT
    while not handle.has_metadata():
        if time.monotonic() > deadline:
            raise TimeoutError("No se pudo obtener la metadata del torrent a tiempo.")
        time.sleep(0.5)
    return handle


def list_torrent_files(source: str) -> list[TorrentFile]:
    lt = _require_libtorrent()
    session = lt.session()
    handle = _resolve_handle(lt, source, session, save_path=".")

    storage = handle.torrent_file().files()
    return [
        TorrentFile(index=i, path=storage.file_path(i), size=storage.file_size(i))
        for i in range(storage.num_files())
    ]


def download_torrent(
    source: str,
    output_dir: Path,
    file_indices: list[int] | None = None,
    poll_interval: float = 1.0,
) -> Path:
    lt = _require_libtorrent()
    output_dir.mkdir(parents=True, exist_ok=True)

    session = lt.session()
    session.listen_on(6881, 6891)
    handle = _resolve_handle(lt, source, session, save_path=str(output_dir))

    if file_indices is not None:
        num_files = handle.torrent_file().files().num_files()
        priorities = [0] * num_files
        for i in file_indices:
            priorities[i] = 4
        handle.prioritize_files(priorities)

    while not handle.status().is_seeding:
        time.sleep(poll_interval)

    return output_dir / handle.status().name
