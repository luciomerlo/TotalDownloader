"""Parseo de la selección de alcance ingresada por el usuario (sin dependencia de UI)."""


def parse_selection(raw: str, count: int) -> list[int]:
    """Convierte texto tipo "1,3,5" o "todos"/"" en índices 0-based válidos."""
    raw = raw.strip().lower()
    if raw in ("", "todos", "all"):
        return list(range(count))

    indices = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            i = int(part) - 1
            if 0 <= i < count:
                indices.append(i)
    return indices or list(range(count))
