"""Motor de scraping recursivo.

Inspirado en:
- Scrapy: estructura de rastreo por profundidades con tabla hash de URLs
  visitadas para evitar ciclos infinitos.
- gallery-dl: extracción modular de enlaces y recursividad sobre sub carpetas.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from core.parser import get_domain
from utils.config import ScraperConfig
from utils.logger import get_logger

logger = get_logger(__name__)

# Extensiones de "página" que deben seguir siendo recorridas en profundidad
# en lugar de tratarse como archivo final.
_BROWSABLE_EXTENSIONS = {"", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp"}


@dataclass(slots=True)
class ScrapedFile:
    """Representa un archivo objetivo detectado durante el scraping."""

    url: str
    source_page: str
    content_type: str | None = None
    size_bytes: int | None = None


@dataclass(slots=True)
class ScrapeResult:
    """Resultado agregado de una sesión de scraping recursivo."""

    files: list[ScrapedFile] = field(default_factory=list)
    visited_pages: set[str] = field(default_factory=set)
    errors: list[tuple[str, str]] = field(default_factory=list)


class RecursiveScraper:
    """Recorre recursivamente una URL base extrayendo archivos objetivo."""

    def __init__(self, config: ScraperConfig, on_progress=None):
        self.config = config
        self.on_progress = on_progress
        self._session = requests.Session()

    def _headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": random.choice(self.config.user_agents),
            "Accept": "*/*",
        }
        headers.update(self.config.extra_headers)
        return headers

    def _get_extension(self, url: str) -> str:
        path = urlparse(url).path
        if "." in path.rsplit("/", 1)[-1]:
            return "." + path.rsplit(".", 1)[-1].lower()
        return ""

    def _matches_filters(self, url: str) -> bool:
        ext = self._get_extension(url)
        if self.config.extension_blacklist and ext in self.config.extension_blacklist:
            return False
        if self.config.extension_whitelist:
            return ext in self.config.extension_whitelist
        return True

    def _is_browsable(self, url: str) -> bool:
        return self._get_extension(url) in _BROWSABLE_EXTENSIONS

    def _fetch(self, url: str) -> requests.Response | None:
        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                timeout=self.config.request_timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            logger.warning("Error al obtener %s: %s", url, exc)
            return None

    def scrape(self, base_url: str) -> ScrapeResult:
        """Ejecuta el rastreo recursivo desde `base_url` y devuelve los archivos hallados."""
        result = ScrapeResult()
        base_domain = get_domain(base_url)

        # (url, profundidad) — la tabla hash `visited` evita ciclos infinitos.
        queue: list[tuple[str, int]] = [(base_url, 0)]
        visited: set[str] = set()
        found_files: set[str] = set()

        while queue:
            if len(result.visited_pages) >= self.config.max_pages:
                logger.info("Límite de páginas alcanzado (%d)", self.config.max_pages)
                break

            url, depth = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            if self.config.same_domain_only and get_domain(url) != base_domain:
                continue

            if depth > self.config.max_depth:
                continue

            response = self._fetch(url)
            if response is None:
                result.errors.append((url, "request_failed"))
                continue

            result.visited_pages.add(url)
            content_type = response.headers.get("Content-Type", "")

            if self.on_progress:
                self.on_progress(url, len(result.visited_pages), len(result.files))

            if "text/html" not in content_type and not self._is_browsable(url):
                # Es un archivo directo, no una página navegable.
                if self._matches_filters(url) and url not in found_files:
                    found_files.add(url)
                    result.files.append(
                        ScrapedFile(url=url, source_page=url, content_type=content_type)
                    )
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all(["a", "img", "source", "link"]):
                href = tag.get("href") or tag.get("src")
                if not href:
                    continue
                absolute = urljoin(url, href)
                absolute = absolute.split("#", 1)[0]

                if self.config.same_domain_only and get_domain(absolute) != base_domain:
                    continue

                if self._is_browsable(absolute):
                    if absolute not in visited and depth + 1 <= self.config.max_depth:
                        queue.append((absolute, depth + 1))
                elif self._matches_filters(absolute) and absolute not in found_files:
                    found_files.add(absolute)
                    result.files.append(
                        ScrapedFile(url=absolute, source_page=url, content_type=None)
                    )

            time.sleep(0.05)  # Cortesía mínima entre requests para mitigar 429/403.

        logger.info(
            "Scraping finalizado: %d páginas visitadas, %d archivos encontrados",
            len(result.visited_pages),
            len(result.files),
        )
        return result
