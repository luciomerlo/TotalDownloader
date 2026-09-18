"""Interfaz de línea de comandos de TotalDownloader.

Flujo: analiza la fuente, muestra lo detectado (formatos/archivos/extensiones),
pregunta el alcance (números o extensiones tildadas) y descarga en paralelo
donde el tipo de fuente lo permite.
"""

from pathlib import Path

import click

from .concurrency import run_concurrent
from .config import DEFAULT_DOWNLOAD_DIR
from .dispatch import detect_source_type
from .selection import parse_selection


def _ask_selection(count: int, exts: list[str]) -> list[int]:
    raw = click.prompt(
        "¿Cuáles descargar? (números, extensiones separadas por coma, o 'todos')",
        default="todos",
        show_default=True,
    )
    return parse_selection(raw, count, exts)


def _handle_media(source: str, output_dir: Path, yes: bool, concurrency: int) -> None:
    from .media import download_media, list_media_formats

    formats = list_media_formats(source)
    click.echo(f"Formatos detectados ({len(formats)}):")
    for i, f in enumerate(formats, 1):
        size = f"~{f.filesize / 1_048_576:.1f} MB" if f.filesize else "tamaño desconocido"
        click.echo(f"  [{i}] .{f.ext:<5} {f.note:<12} {size}")
    exts = [f.ext for f in formats]
    click.echo(f"Extensiones detectadas: {', '.join(sorted(set(exts)))}")

    indices = list(range(len(formats))) if yes else _ask_selection(len(formats), exts)
    if not indices:
        click.echo("Nada seleccionado.")
        return

    tasks = [
        (lambda i=i: download_media(source, output_dir, format_id=formats[i].format_id))
        for i in indices
    ]
    for i, result in zip(indices, run_concurrent(tasks, max_workers=concurrency), strict=True):
        if isinstance(result, Exception):
            click.echo(f"Error en formato [{i + 1}]: {result}")
        else:
            click.echo(f"Descargado: {result}")


def _handle_torrent(source: str, output_dir: Path, yes: bool) -> None:
    from .torrent import download_torrent, list_torrent_files

    files = list_torrent_files(source)
    click.echo(f"Archivos detectados ({len(files)}):")
    for i, tf in enumerate(files, 1):
        click.echo(f"  [{i}] {tf.path}  (~{tf.size / 1_048_576:.1f} MB)")
    exts = [tf.ext for tf in files]
    click.echo(f"Extensiones detectadas: {', '.join(sorted(set(exts)))}")

    indices = list(range(len(files))) if yes else _ask_selection(len(files), exts)
    if not indices:
        click.echo("Nada seleccionado.")
        return

    # libtorrent baja piezas de todos los archivos priorizados en paralelo dentro
    # de una misma sesión: no hace falta orquestar concurrencia manualmente acá.
    dest = download_torrent(source, output_dir, file_indices=indices)
    click.echo(f"Descargado: {dest}")


def _handle_http(source: str, output_dir: Path, yes: bool, concurrency: int) -> None:
    from .http_direct import download_http_concurrent, list_http_target

    target = list_http_target(source)
    click.echo(f"Archivo detectado: {target.filename} (.{target.ext})")

    if yes or click.confirm("¿Descargar?", default=True):
        dest = download_http_concurrent(source, output_dir, connections=concurrency)
        click.echo(f"Descargado: {dest}")


def _handle_scribd(source: str, output_dir: Path, yes: bool) -> None:
    from .scribd import download_scribd, list_scribd_target

    target = list_scribd_target(source)
    click.echo(f"Documento detectado: {target.filename}")

    if yes or click.confirm("¿Descargar?", default=True):
        dest = download_scribd(source, output_dir)
        click.echo(f"Descargado: {dest}")


def _handle_scrape(source: str, output_dir: Path, yes: bool, prompt: str | None) -> None:
    from .scrape import download_scrape, list_scrape_target

    if not prompt:
        prompt = click.prompt("¿Qué querés extraer de la página?")

    target = list_scrape_target(source, prompt)
    click.echo(f"Fuente: {target.url}")
    click.echo(f"Prompt: {target.prompt}")

    if yes or click.confirm("¿Scrapear?", default=True):
        dest = download_scrape(source, target.prompt, output_dir)
        click.echo(f"Resultado guardado: {dest}")


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
    "-c",
    "--concurrency",
    type=int,
    default=4,
    show_default=True,
    help="Descargas en paralelo: formatos de media seleccionados, o conexiones HTTP por archivo.",
)
@click.option(
    "--type",
    "source_type",
    type=click.Choice(["auto", "media", "http", "torrent", "scribd", "scrape"]),
    default="auto",
    help="Forzar el tipo de fuente en lugar de autodetectarlo.",
)
@click.option(
    "--prompt",
    "scrape_prompt",
    default=None,
    help="Prompt de extracción para --type scrape (si no se pasa, se pregunta).",
)
def main(
    source: str,
    output_dir: Path,
    yes: bool,
    concurrency: int,
    source_type: str,
    scrape_prompt: str | None,
) -> None:
    """Analiza SOURCE, lista lo detectado y descarga el alcance elegido."""
    kind = detect_source_type(source) if source_type == "auto" else source_type

    if kind == "media":
        _handle_media(source, output_dir, yes, concurrency)
    elif kind == "torrent":
        _handle_torrent(source, output_dir, yes)
    elif kind == "scribd":
        _handle_scribd(source, output_dir, yes)
    elif kind == "scrape":
        _handle_scrape(source, output_dir, yes, scrape_prompt)
    else:
        _handle_http(source, output_dir, yes, concurrency)


if __name__ == "__main__":
    main()
