"""Normalización, validación y deduplicación de URLs de entrada."""
from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

# Acepta \n, coma o punto y coma como separadores de la caja de texto masiva.
_SPLIT_PATTERN = re.compile(r"[\n,;]+")

_URL_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def _ensure_scheme(raw: str) -> str:
    """Antepone https:// cuando la URL no trae esquema explícito."""
    if not _URL_SCHEME_PATTERN.match(raw):
        return f"https://{raw}"
    return raw


def _normalize_url(raw: str) -> str | None:
    """Normaliza una URL individual: trim, esquema, minúsculas de host, sin fragment."""
    candidate = raw.strip()
    if not candidate:
        return None

    candidate = _ensure_scheme(candidate)

    try:
        parsed = urlparse(candidate)
    except ValueError:
        return None

    if not parsed.netloc or not parsed.scheme.startswith("http"):
        return None

    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    normalized = urlunparse((parsed.scheme, netloc, path, parsed.params, parsed.query, ""))
    return normalized


def parse_urls(raw_text: str) -> list[str]:
    """Convierte el contenido de la caja de texto multilínea en una lista de URLs.

    - Divide por salto de línea, coma o punto y coma.
    - Sanitiza y valida el formato de cada URL.
    - Elimina duplicados preservando el orden de aparición.
    """
    if not raw_text:
        return []

    tokens = _SPLIT_PATTERN.split(raw_text)

    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        normalized = _normalize_url(token)
        if normalized is None:
            if token.strip():
                logger.warning("URL inválida descartada: %s", token.strip())
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)

    logger.info("parse_urls: %d URLs válidas de %d tokens", len(result), len(tokens))
    return result


def get_domain(url: str) -> str:
    """Extrae el dominio (netloc en minúsculas) de una URL."""
    return urlparse(url).netloc.lower()
