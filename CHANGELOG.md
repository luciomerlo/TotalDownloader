# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionado según [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0] - 2026-09-18

### Added
- Andamiaje inicial: core de descarga para media (yt-dlp), HTTP directo y torrents/magnet (libtorrent), más CLI (`totaldownloader`).
- Flujo genérico: detección de tipo de fuente, listado de formatos/archivos disponibles y selección de alcance antes de descargar.
- Selección por extensión (`selection.py`) y descarga concurrente por tipo de fuente (media en paralelo con `ThreadPoolExecutor`, HTTP segmentado por rangos, torrents vía piece picker de libtorrent).
- README con instrucciones de instalación, uso y estado del proyecto.

[Unreleased]: https://github.com/luciomerlo/TotalDownloader/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/luciomerlo/TotalDownloader/releases/tag/v0.1.0
