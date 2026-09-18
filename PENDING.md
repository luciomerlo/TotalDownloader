# Pendientes

Cosas mencionadas en conversaciones/README/CLAUDE.md que quedan abiertas.

- GUI de escritorio (el core ya está separado de `click` pensando en esto).
- Manejo de errores más granular por motor (media/http/torrent).
- `download_http_concurrent()` solo se validó manualmente end-to-end contra un servidor local con soporte de `Range`; no forma parte de la suite automatizada — falta decidir cómo testearla en CI (mock server, fixture local, etc.).
- Crear tag `v0.1.0` en el repo (el CHANGELOG ya referencia ese tag/release, pero todavía no existe en GitHub).
