# TotalDownloader

Descargador unificado: video/audio, HTTP directo y torrents/magnet. Python, CLI primero (core reutilizable pensado para una futura GUI).

## Estructura

- `src/totaldownloader/dispatch.py` — detecta el tipo de fuente (magnet/.torrent → torrent; URL soportada por yt-dlp → media; resto → http) y enruta.
- `src/totaldownloader/media.py` — motor de video/audio, wrapper de yt-dlp. `list_media_formats()` inspecciona sin descargar; `download_media()` descarga un `format_id` puntual.
- `src/totaldownloader/http_direct.py` — motor de descarga HTTP directa, con reanudación vía `Range`. `list_http_target()` solo deriva el nombre/extensión desde la URL (no hace request).
- `src/totaldownloader/torrent.py` — motor de torrents/magnet vía `libtorrent` (dependencia opcional, extra `torrent`). `list_torrent_files()` resuelve metadata y lista archivos sin descargar; `download_torrent()` acepta `file_indices` para descargar solo un subconjunto.
- `src/totaldownloader/selection.py` — parseo puro (sin `click`) del texto de selección de alcance ("1,3", "todos") a índices.
- `src/totaldownloader/cli.py` — CLI (`click`), único punto de entrada (`totaldownloader`). Flujo: detectar tipo → listar lo disponible (`list_*`) → preguntar alcance (`selection.parse_selection`, salvo `-y`) → descargar solo lo elegido.

## Convenciones

- El core (`dispatch`, `media`, `http_direct`, `torrent`, `selection`) no debe depender de `click` ni de nada de `cli.py` — mantiene el código reutilizable para una GUI futura. Cada motor separa "listar/inspeccionar" (sin descargar) de "descargar" (recibe lo ya elegido).
- `torrent.py` importa `libtorrent` de forma perezosa (dentro de la función) para que el resto de la herramienta funcione sin esa dependencia instalada.
- Tests en `tests/` cubren lógica pura (detección de tipo, parseo de selección/nombres/extensiones, `describe_format`), no descargas ni resolución de metadata reales contra la red.

## Comandos

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

CI (`.github/workflows/ci.yml`) corre `ruff check .` y `pytest` en cada push/PR a `main`. No instala el extra `torrent` (evita depender de `libtorrent` en CI).
