"""Descarga de torrents/magnet vía libtorrent (dependencia opcional, extra 'torrent')."""

import time
from pathlib import Path


def download_torrent(source: str, output_dir: Path, poll_interval: float = 1.0) -> Path:
    try:
        import libtorrent as lt
    except ImportError as exc:
        raise RuntimeError(
            "libtorrent no está instalado. Instalá el extra: pip install 'totaldownloader[torrent]'"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    session = lt.session()
    session.listen_on(6881, 6891)

    params = {"save_path": str(output_dir)}
    if source.startswith("magnet:"):
        handle = lt.add_magnet_uri(session, source, params)
    else:
        params["ti"] = lt.torrent_info(source)
        handle = session.add_torrent(params)

    while not handle.status().is_seeding:
        time.sleep(poll_interval)

    return output_dir / handle.status().name
