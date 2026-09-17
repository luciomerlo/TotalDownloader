# TotalDownloader

Descargador unificado de línea de comandos: video/audio (vía yt-dlp), enlaces HTTP directos con reanudación, y torrents/magnet.

## Instalación

```bash
pip install -e ".[dev]"
# Para soporte de torrents/magnet:
pip install -e ".[torrent]"
```

## Uso

```bash
totaldownloader <URL o magnet o .torrent> [-o DIRECTORIO] [-y] [-c CONCURRENCIA] [--type auto|media|http|torrent]
```

El tipo de fuente se autodetecta: enlaces `magnet:` y `.torrent` van al motor de torrents, URLs de sitios soportados por yt-dlp van al motor de media, y el resto se trata como descarga HTTP directa.

Antes de descargar, la herramienta analiza la fuente y muestra lo detectado, preguntando el alcance. La selección acepta números ("1,3"), extensiones tildadas ("mp4,srt") o "todos":

- **Media**: lista los formatos disponibles (resolución/calidad, extensión, tamaño aproximado). Los formatos elegidos se descargan **en paralelo** (`-c`, default 4 workers).
- **Torrent/magnet**: lista los archivos incluidos (ruta, tamaño). libtorrent ya baja piezas de todos los archivos priorizados en paralelo dentro de una misma sesión — no hace falta orquestar hilos.
- **HTTP directo**: muestra el archivo detectado y pide confirmación. Si el servidor soporta `Range`, se descarga **multi-conexión** (segmentado en `-c` partes en paralelo); si no, cae a una sola conexión con reanudación.

`-y`/`--yes` salta las preguntas y descarga todo lo detectado.

## Desarrollo

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## Estado

MVP: los tres motores (media, HTTP, torrent) analizan la fuente, listan lo detectado (con selección por número o extensión) y descargan el alcance elegido con paralelismo donde aplica. Pendiente: GUI de escritorio, manejo de errores más granular por motor.
