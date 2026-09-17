"""Parseo de la selección de alcance ingresada por el usuario (sin dependencia de UI)."""


def parse_selection(raw: str, count: int, exts: list[str] | None = None) -> list[int]:
    """Convierte texto tipo "1,3", "mp4,srt" o "todos"/"" en índices 0-based válidos.

    Cada término puede ser un número de ítem (1-based) o, si se pasa `exts`
    (una extensión por ítem, en el mismo orden), una extensión a tildar
    (selecciona todos los ítems que la tengan).
    """
    raw = raw.strip().lower()
    if raw in ("", "todos", "all"):
        return list(range(count))

    indices: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if part.isdigit():
            i = int(part) - 1
            if 0 <= i < count:
                indices.add(i)
        elif exts:
            indices.update(i for i, ext in enumerate(exts) if ext.lower() == part)

    return sorted(indices) if indices else list(range(count))
