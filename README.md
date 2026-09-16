# TotalDownloader

A local Python application for recursive web scraping and multithreaded mass file downloading, with a real-time Streamlit dashboard.

Paste dozens of base URLs, recursively crawl their subfolders for target files (PDFs, images, ISOs, ZIPs, video, documents, etc.), and download them concurrently with resume support, adjustable speed limits, and automatic retries.

## Features

- **Bulk URL input** — paste 20+ URLs separated by newline, comma, or semicolon; automatic sanitization and deduplication.
- **Recursive scraping** — configurable max depth, extension whitelist/blacklist, same-domain restriction, rotating User-Agents.
- **Multithreaded downloads** — 1 to 64 concurrent workers, HTTP `Range`-based resume, exponential backoff retries, optional speed cap (KB/s).
- **Live dashboard** — overall progress, per-file speed/ETA/%/MB, queued table, and completed/failed history with HTTP status codes.

## Project Structure

```
downloader_app/
├── core/       # scraper.py, engine.py, parser.py
├── ui/         # dashboard.py (Streamlit)
├── utils/      # config.py, logger.py
├── downloads/  # default output directory
├── main.py
└── requirements.txt
```

## Installation & Usage

```bash
cd downloader_app
pip install -r requirements.txt
python main.py
# or: streamlit run ui/dashboard.py
```

The dashboard opens at `http://localhost:8501`.

## Design References

The architecture adapts patterns observed in **aria2** (Range-based segmented downloads), **gallery-dl** (recursive link/subfolder extraction), **yt-dlp** (retry/backoff resilience and progress hooks), and **Scrapy** (depth-bounded crawling with visited-URL hashing to avoid cycles). See [`downloader_app/README.md`](downloader_app/README.md) for full details and attribution.

## License

Not yet specified.
