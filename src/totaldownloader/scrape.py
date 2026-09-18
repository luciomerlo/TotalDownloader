"""Scraping asistido por LLM vía scrapegraphai (dependencia opcional, extra 'scrape')."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_MODEL = "openai/gpt-4o-mini"


@dataclass
class ScrapeTarget:
    url: str
    prompt: str


def list_scrape_target(url: str, prompt: str) -> ScrapeTarget:
    return ScrapeTarget(url=url, prompt=prompt)


def _require_scrapegraphai():
    try:
        from scrapegraphai.graphs import SmartScraperGraph
    except ImportError as exc:
        raise RuntimeError(
            "scrapegraphai no está instalado. Instalá el extra: "
            "pip install 'totaldownloader[scrape]'"
        ) from exc
    return SmartScraperGraph


def download_scrape(
    url: str,
    prompt: str,
    output_dir: Path,
    model: str = _DEFAULT_MODEL,
    api_key: str | None = None,
) -> Path:
    SmartScraperGraph = _require_scrapegraphai()

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta la API key del LLM. Pasá api_key o seteá la variable OPENAI_API_KEY."
        )

    graph = SmartScraperGraph(
        prompt=prompt,
        source=url,
        config={"llm": {"api_key": key, "model": model}},
    )
    result = graph.run()

    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "scrape-result.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest
