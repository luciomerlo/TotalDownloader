"""Descarga de video/audio vía yt-dlp (YouTube y sitios soportados)."""

from pathlib import Path

import yt_dlp


def download_media(url: str, output_dir: Path, audio_only: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts: dict = {
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "format": "bestaudio/best" if audio_only else "bestvideo+bestaudio/best",
        "noplaylist": True,
    }
    if audio_only:
        ydl_opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
        ]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))
