"""Configuración centralizada de la aplicación mediante dataclasses tipadas."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "downloads"


@dataclass(slots=True)
class ScraperConfig:
    """Parámetros de configuración del motor de scraping recursivo."""

    max_depth: int = 2
    same_domain_only: bool = True
    extension_whitelist: tuple[str, ...] = ()
    extension_blacklist: tuple[str, ...] = ()
    user_agents: list[str] = field(default_factory=lambda: list(DEFAULT_USER_AGENTS))
    extra_headers: dict[str, str] = field(default_factory=dict)
    request_timeout: float = 15.0
    max_pages: int = 500


@dataclass(slots=True)
class DownloadConfig:
    """Parámetros de configuración del motor de descarga multihilo."""

    output_dir: Path = field(default_factory=lambda: DEFAULT_DOWNLOAD_DIR)
    max_workers: int = 8
    chunk_size: int = 1024 * 64
    max_retries: int = 5
    backoff_base: float = 1.5
    speed_limit_kbps: int = 0
    preserve_structure: bool = True
    user_agents: list[str] = field(default_factory=lambda: list(DEFAULT_USER_AGENTS))


@dataclass(slots=True)
class AppConfig:
    """Configuración global agregada de la aplicación."""

    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
