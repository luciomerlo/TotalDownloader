# TotalDownloader

Unified Python command-line downloader that automatically detects the source type (magnet/torrent, yt-dlp URL, or direct HTTP) and downloads video/audio, torrents, or files with resumable, configurable-concurrency downloads, listing the content and asking for the scope before downloading anything.

## Installation

```bash
pip install -e ".[dev]"
# For torrent/magnet support:
pip install -e ".[torrent]"
```

## Usage

```bash
totaldownloader <URL or magnet or .torrent> [-o DIRECTORY] [-y] [-c CONCURRENCY] [--type auto|media|http|torrent]
```

The source type is auto-detected: `magnet:` links and `.torrent` files go to the torrent engine, URLs from sites supported by yt-dlp go to the media engine, and everything else is treated as a direct HTTP download.

Before downloading, the tool analyzes the source and shows what it detected, asking for the scope. The selection accepts numbers ("1,3"), extensions ("mp4,srt"), or "all":

- **Media**: lists the available formats (resolution/quality, extension, approximate size). The chosen formats are downloaded **in parallel** (`-c`, default 4 workers).
- **Torrent/magnet**: lists the included files (path, size). libtorrent already downloads pieces from all prioritized files in parallel within the same session — no need to orchestrate threads.
- **Direct HTTP**: shows the detected file and asks for confirmation. If the server supports `Range`, it downloads **multi-connection** (segmented into `-c` parallel parts); if not, it falls back to a single connection with resume support.

`-y`/`--yes` skips the questions and downloads everything detected.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## Status

MVP: all three engines (media, HTTP, torrent) analyze the source, list what they detect (selectable by number or extension), and download the chosen scope with parallelism where applicable. Pending: desktop GUI, more granular per-engine error handling.
