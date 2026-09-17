# TotalDownloader

Descargador unificado: video/audio, HTTP directo y torrents/magnet. Python, CLI primero (core reutilizable pensado para una futura GUI).

## Estructura

- `src/totaldownloader/dispatch.py` — detecta el tipo de fuente (magnet/.torrent → torrent; URL soportada por yt-dlp → media; resto → http) y enruta.
- `src/totaldownloader/media.py` — motor de video/audio, wrapper de yt-dlp. `list_media_formats()` inspecciona sin descargar; `download_media()` descarga un `format_id` puntual.
- `src/totaldownloader/http_direct.py` — motor de descarga HTTP directa. `list_http_target()` solo deriva el nombre/extensión desde la URL (no hace request). `download_http()` es single-connection con reanudación vía `Range`; `download_http_concurrent()` la segmenta en N conexiones en paralelo (`split_ranges()`) si el servidor anuncia `Accept-Ranges: bytes`, y si no cae a `download_http()`.
- `src/totaldownloader/torrent.py` — motor de torrents/magnet vía `libtorrent` (dependencia opcional, extra `torrent`). `list_torrent_files()` resuelve metadata y lista archivos sin descargar; `download_torrent()` acepta `file_indices` para descargar solo un subconjunto. La concurrencia entre archivos ya la maneja libtorrent internamente (piece picker sobre los archivos priorizados) — no se orquesta desde acá.
- `src/totaldownloader/selection.py` — parseo puro (sin `click`) del texto de selección de alcance a índices: acepta números ("1,3"), extensiones tildadas ("mp4,srt", requiere pasar la lista `exts` paralela a los ítems) o "todos".
- `src/totaldownloader/concurrency.py` — `run_concurrent()`: corre una lista de tareas (`Callable[[], T]`) en un `ThreadPoolExecutor`, capturando excepciones por tarea sin abortar el resto. Usado para bajar varios formatos de media en paralelo.
- `src/totaldownloader/cli.py` — CLI (`click`), único punto de entrada (`totaldownloader`). Flujo: detectar tipo → listar lo disponible (`list_*`) → preguntar alcance (`selection.parse_selection`, salvo `-y`) → descargar en paralelo donde aplica (`-c/--concurrency`, default 4).

## Convenciones

- El core (`dispatch`, `media`, `http_direct`, `torrent`, `selection`, `concurrency`) no debe depender de `click` ni de nada de `cli.py` — mantiene el código reutilizable para una GUI futura. Cada motor separa "listar/inspeccionar" (sin descargar) de "descargar" (recibe lo ya elegido).
- `torrent.py` importa `libtorrent` de forma perezosa (dentro de la función) para que el resto de la herramienta funcione sin esa dependencia instalada.
- Tests en `tests/` cubren lógica pura (detección de tipo, parseo de selección/nombres/extensiones, `describe_format`, `split_ranges`, `run_concurrent`), no descargas ni resolución de metadata reales contra la red. `download_http_concurrent()` se validó manualmente end-to-end contra un servidor HTTP local con soporte de `Range` (no forma parte de la suite automatizada).

## Comandos

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

CI (`.github/workflows/ci.yml`) corre `ruff check .` y `pytest` en cada push/PR a `main`. No instala el extra `torrent` (evita depender de `libtorrent` en CI).
