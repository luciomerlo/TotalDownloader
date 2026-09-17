"""Descarga de video/audio vía yt-dlp (YouTube y sitios soportados)."""

from dataclasses import dataclass
from pathlib import Path

import yt_dlp


@dataclass
class MediaFormat:
    format_id: str
    ext: str
    note: str
    filesize: int | None


def describe_format(f: dict) -> str:
    if f.get("resolution") and f.get("resolution") != "audio only":
        return f["resolution"]
    if f.get("vcodec") not in (None, "none"):
        return "video"
    if f.get("acodec") not in (None, "none"):
        return "audio"
    return "?"


def list_media_formats(url: str) -> list[MediaFormat]:
    with yt_dlp.YoutubeDL({"noplaylist": True, "quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats") or [info]
    return [
        MediaFormat(
            format_id=f["format_id"],
            ext=f.get("ext", "?"),
            note=f.get("format_note") or describe_format(f),
            filesize=f.get("filesize") or f.get("filesize_approx"),
        )
        for f in formats
    ]


def download_media(url: str, output_dir: Path, format_id: str = "bestvideo+bestaudio/best") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "outtmpl": str(output_dir / "%(title)s.%(format_id)s.%(ext)s"),
        "format": format_id,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))
