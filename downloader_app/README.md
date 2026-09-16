# TotalDownloader

Aplicación local (escritorio/web) en Python para scraping recursivo y descarga masiva multihilo de archivos a partir de URLs base.

## Descripción General

TotalDownloader combina un motor de rastreo recursivo de enlaces con un motor de descarga concurrente basado en hilos, expuestos a través de un dashboard Streamlit. Permite pegar decenas de URLs base, rastrear sus subcarpetas en busca de archivos (PDFs, imágenes, ISOs, ZIPs, video, documentos, etc.) y descargarlos en paralelo con soporte de reanudación, control de velocidad y reintentos automáticos.

### Arquitectura

```
downloader_app/
├── core/
│   ├── parser.py    # Normalización, validación y deduplicación de URLs de entrada
│   ├── scraper.py   # Motor de scraping recursivo (BFS con control de profundidad y dominio)
│   └── engine.py    # Motor de descarga multihilo (ThreadPoolExecutor + requests)
├── ui/
│   └── dashboard.py # Dashboard Streamlit (entrada, configuración, monitoreo en tiempo real)
├── utils/
│   ├── logger.py    # Logging a archivo y consola
│   └── config.py    # Dataclasses de configuración tipadas
├── downloads/       # Directorio por defecto de almacenamiento
└── main.py          # Punto de entrada
```

**Capacidades principales:**

- Entrada masiva de URLs (mínimo 20 renglones) separadas por salto de línea, coma o punto y coma, con sanitización y deduplicación automática.
- Rastreo recursivo con profundidad máxima configurable, filtros de extensión (whitelist/blacklist), restricción de dominio y rotación de User-Agents.
- Descarga multihilo (1 a 64 workers) con `Content-Range` / `Accept-Ranges` para reanudación, reintentos con backoff exponencial y límite de velocidad opcional (KB/s).
- Dashboard en tiempo real con progreso general, progreso individual por archivo (velocidad, ETA, % y MB transferidos), cola de espera y tabla de finalizados/fallidos con código HTTP.

## Requisitos e Instalación

```bash
pip install -r requirements.txt
```

### Ejecución

```bash
python main.py
# o equivalentemente:
streamlit run ui/dashboard.py
```

El dashboard se abre en el navegador en `http://localhost:8501`.

## Referencias e Inspiración de Repositorios de Código Abierto

Este proyecto no reutiliza código de los siguientes repositorios, pero adapta explícitamente los siguientes patrones de diseño observados en cada uno:

- **[aria2](https://github.com/aria2/aria2)** — Algoritmos de segmentación de archivos y manejo eficiente de conexiones multihilo mediante cabeceras `Range`. Se adoptó en `core/engine.py` el patrón de solicitar descargas parciales con `Range: bytes=<offset>-` para reanudar archivos existentes, y de detectar soporte de rangos vía el código de estado `206 Partial Content` devuelto por el servidor.
- **[gallery-dl](https://github.com/mikf/gallery-dl)** — Lógica modular de extracción de enlaces, recursividad de directorios y parseo de subcarpetas. Se adoptó en `core/scraper.py` la separación entre "páginas navegables" (HTML) y "archivos objetivo" (por `Content-Type` o extensión), y el recorrido recursivo de subcarpetas anidadas del sitio.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — Estrategias de resiliencia ante fallos de red, reintentos con backoff exponencial y hooks de monitoreo de progreso. Se adoptó en `core/engine.py` el bucle de reintentos con backoff exponencial (`backoff_base ** intento`) y el patrón de callback (`on_update`) para notificar progreso en tiempo real a la UI.
- **[Scrapy](https://github.com/scrapy/scrapy)** — Estructura de rastreo (crawling) de enlaces en profundidades configurables evitando ciclos infinitos mediante tablas hash de URLs visitadas. Se adoptó en `core/scraper.py` la cola BFS `(url, profundidad)` combinada con un `set()` de URLs visitadas para evitar ciclos infinitos y respetar `max_depth`.

## Configuración disponible en el Dashboard

| Parámetro | Rango / Default | Descripción |
|---|---|---|
| Hilos de descarga paralela | 1–64 (default 8) | Tamaño del `ThreadPoolExecutor` |
| Profundidad máxima de scraping | 0–10 (default 2) | Niveles de subcarpetas a rastrear |
| Límite de velocidad | KB/s, 0 = ilimitado | Aplicado por worker vía `RateLimiter` |
| Carpeta de destino | `downloads/` | Ruta local de almacenamiento |
| Filtro de extensiones | vacío = todas | Lista blanca, ej: `pdf,zip,mp4` |
| Restringir al dominio base | activado | Evita seguir enlaces externos |

## Logs

Los logs de ejecución se escriben en `downloads/downloader_app.log` y en consola.
