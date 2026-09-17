# TotalDownloader

Descargador unificado: video/audio, HTTP directo y torrents/magnet. Python, CLI primero (core reutilizable pensado para una futura GUI).

## Estructura

- `src/totaldownloader/dispatch.py` — detecta el tipo de fuente (magnet/.torrent → torrent; URL soportada por yt-dlp → media; resto → http) y enruta.
- `src/totaldownloader/media.py` — motor de video/audio, wrapper de yt-dlp.
- `src/totaldownloader/http_direct.py` — motor de descarga HTTP directa, con reanudación vía `Range`.
- `src/totaldownloader/torrent.py` — motor de torrents/magnet vía `libtorrent` (dependencia opcional, extra `torrent`).
- `src/totaldownloader/cli.py` — CLI (`click`), único punto de entrada (`totaldownloader`).

## Convenciones

- El core (`dispatch`, `media`, `http_direct`, `torrent`) no debe depender de `click` ni de nada de `cli.py` — mantiene el código reutilizable para una GUI futura.
- `torrent.py` importa `libtorrent` de forma perezosa (dentro de la función) para que el resto de la herramienta funcione sin esa dependencia instalada.
- Tests en `tests/` cubren lógica pura (detección de tipo, parseo de nombres de archivo), no descargas reales contra la red.

## Comandos

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

CI (`.github/workflows/ci.yml`) corre `ruff check .` y `pytest` en cada push/PR a `main`. No instala el extra `torrent` (evita depender de `libtorrent` en CI).
