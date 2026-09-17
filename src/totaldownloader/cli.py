"""Interfaz de línea de comandos de TotalDownloader.

Flujo: analiza la fuente, muestra lo detectado (formatos/archivos/extensiones)
y pregunta el alcance antes de descargar.
"""

from pathlib import Path

import click

from .config import DEFAULT_DOWNLOAD_DIR
from .dispatch import detect_source_type
from .selection import parse_selection


def _ask_selection(count: int) -> list[int]:
    raw = click.prompt(
        "¿Cuáles descargar? (números separados por coma, o 'todos')",
        default="todos",
        show_default=True,
    )
    return parse_selection(raw, count)


def _handle_media(source: str, output_dir: Path, yes: bool) -> None:
    from .media import download_media, list_media_formats

    formats = list_media_formats(source)
    click.echo(f"Formatos detectados ({len(formats)}):")
    for i, f in enumerate(formats, 1):
        size = f"~{f.filesize / 1_048_576:.1f} MB" if f.filesize else "tamaño desconocido"
        click.echo(f"  [{i}] .{f.ext:<5} {f.note:<12} {size}")
    exts = sorted({f.ext for f in formats})
    click.echo(f"Extensiones detectadas: {', '.join(exts)}")

    indices = list(range(len(formats))) if yes else _ask_selection(len(formats))
    for i in indices:
        dest = download_media(source, output_dir, format_id=formats[i].format_id)
        click.echo(f"Descargado: {dest}")


def _handle_torrent(source: str, output_dir: Path, yes: bool) -> None:
    from .torrent import download_torrent, list_torrent_files

    files = list_torrent_files(source)
    click.echo(f"Archivos detectados ({len(files)}):")
    for i, tf in enumerate(files, 1):
        click.echo(f"  [{i}] {tf.path}  (~{tf.size / 1_048_576:.1f} MB)")
    exts = sorted({tf.ext for tf in files})
    click.echo(f"Extensiones detectadas: {', '.join(exts)}")

    indices = list(range(len(files))) if yes else _ask_selection(len(files))
    dest = download_torrent(source, output_dir, file_indices=indices)
    click.echo(f"Descargado: {dest}")


def _handle_http(source: str, output_dir: Path, yes: bool) -> None:
    from .http_direct import download_http, list_http_target

    target = list_http_target(source)
    click.echo(f"Archivo detectado: {target.filename} (.{target.ext})")

    if yes or click.confirm("¿Descargar?", default=True):
        dest = download_http(source, output_dir)
        click.echo(f"Descargado: {dest}")


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
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="No preguntar el alcance: descargar todo lo detectado.",
)
@click.option(
    "--type",
    "source_type",
    type=click.Choice(["auto", "media", "http", "torrent"]),
    default="auto",
    help="Forzar el tipo de fuente en lugar de autodetectarlo.",
)
def main(source: str, output_dir: Path, yes: bool, source_type: str) -> None:
    """Analiza SOURCE, lista lo detectado y descarga el alcance elegido."""
    kind = detect_source_type(source) if source_type == "auto" else source_type

    if kind == "media":
        _handle_media(source, output_dir, yes)
    elif kind == "torrent":
        _handle_torrent(source, output_dir, yes)
    else:
        _handle_http(source, output_dir, yes)


if __name__ == "__main__":
    main()
