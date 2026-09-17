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
totaldownloader <URL o magnet o .torrent> [-o DIRECTORIO] [--audio-only] [--type auto|media|http|torrent]
```

El tipo de fuente se autodetecta: enlaces `magnet:` y `.torrent` van al motor de torrents, URLs de sitios soportados por yt-dlp van al motor de media, y el resto se trata como descarga HTTP directa.

## Desarrollo

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## Estado

MVP inicial: los tres motores (media, HTTP, torrent) tienen implementación funcional mínima. Pendiente: descargas HTTP multi-conexión/segmentadas, GUI de escritorio, manejo de errores más granular por motor.
