from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from universe_tools.scraper.gateway import ScraperGateway


@dataclass(slots=True)
class ScraperMetrics:
    processed: int = 0
    failed: int = 0


class ScraperWorkflow:
    def __init__(self, scraper_gateway: ScraperGateway, output_dir: str) -> None:
        self.scraper_gateway = scraper_gateway
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_urls(
        self,
        urls: list[str],
        on_error: Callable[[dict[str, str], Exception], None] | None = None,
    ) -> ScraperMetrics:
        metrics = ScraperMetrics()
        for url in urls:
            try:
                result = self.scraper_gateway.fetch_markdown(url)
                safe_name = "".join(ch if ch.isalnum() else "_" for ch in result.title)[:80] or "scraped"
                (self.output_dir / f"{safe_name}.md").write_text(result.markdown, encoding="utf-8")
                metrics.processed += 1
            except Exception as exc:
                metrics.failed += 1
                if on_error:
                    on_error({"url": url}, exc)
        return metrics
