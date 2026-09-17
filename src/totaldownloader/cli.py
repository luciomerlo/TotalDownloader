"""Interfaz de línea de comandos de TotalDownloader."""

from pathlib import Path

import click

from .config import DEFAULT_DOWNLOAD_DIR
from .dispatch import detect_source_type


@click.command()
@click.argument("source")
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_DOWNLOAD_DIR,
    help="Directorio de destino.",
)
@click.option("--audio-only", is_flag=True, help="Solo audio (fuentes de tipo media).")
@click.option(
    "--type",
    "source_type",
    type=click.Choice(["auto", "media", "http", "torrent"]),
    default="auto",
    help="Forzar el tipo de fuente en lugar de autodetectarlo.",
)
def main(source: str, output_dir: Path, audio_only: bool, source_type: str) -> None:
    """Descarga SOURCE: URL de video/audio, enlace HTTP directo, magnet o .torrent."""
    kind = detect_source_type(source) if source_type == "auto" else source_type

    if kind == "media":
        from .media import download_media

        dest = download_media(source, output_dir, audio_only=audio_only)
    elif kind == "torrent":
        from .torrent import download_torrent

        dest = download_torrent(source, output_dir)
    else:
        from .http_direct import download_http

        dest = download_http(source, output_dir)

    click.echo(f"Descargado: {dest}")


if __name__ == "__main__":
    main()
