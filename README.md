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
totaldownloader <URL o magnet o .torrent> [-o DIRECTORIO] [-y] [--type auto|media|http|torrent]
```

El tipo de fuente se autodetecta: enlaces `magnet:` y `.torrent` van al motor de torrents, URLs de sitios soportados por yt-dlp van al motor de media, y el resto se trata como descarga HTTP directa.

Antes de descargar, la herramienta analiza la fuente y muestra lo detectado, preguntando el alcance:

- **Media**: lista los formatos disponibles (resolución/calidad, extensión, tamaño aproximado) y pregunta cuáles descargar.
- **Torrent/magnet**: lista los archivos incluidos (ruta, tamaño) y pregunta cuáles descargar.
- **HTTP directo**: muestra el archivo detectado y pide confirmación.

`-y`/`--yes` salta las preguntas y descarga todo lo detectado.

## Desarrollo

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## Estado

MVP: los tres motores (media, HTTP, torrent) analizan la fuente, listan lo detectado y descargan el alcance elegido. Pendiente: descargas HTTP multi-conexión/segmentadas, GUI de escritorio, manejo de errores más granular por motor.
