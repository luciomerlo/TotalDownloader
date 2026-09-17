"""Ejecución concurrente de tareas independientes (sin dependencia de UI)."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypeVar

T = TypeVar("T")


def run_concurrent(tasks: list[Callable[[], T]], max_workers: int = 4) -> list[T | Exception]:
    """Corre cada tarea en un hilo y devuelve resultados (o la excepción) en el orden original."""
    if not tasks:
        return []

    results: list[T | Exception] = [None] * len(tasks)  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as executor:
        future_to_index = {executor.submit(task): i for i, task in enumerate(tasks)}
        for future in as_completed(future_to_index):
            i = future_to_index[future]
            try:
                results[i] = future.result()
            except Exception as exc:
                results[i] = exc
    return results
