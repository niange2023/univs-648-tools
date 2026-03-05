from __future__ import annotations

import time
from dataclasses import dataclass

from universe_tools.email.gateway import EmailGateway
from universe_tools.workflow.dlq import DeadLetterQueue
from universe_tools.workflow.scraper_jobs import ScraperWorkflow


@dataclass(slots=True)
class HeartbeatMetrics:
    cycles: int = 0
    success_count: int = 0
    failure_count: int = 0
    replayed_count: int = 0
    scraper_success_count: int = 0
    scraper_failure_count: int = 0


class HeartbeatRunner:
    def __init__(
        self,
        email_gateway: EmailGateway,
        interval_seconds: int = 300,
        dlq: DeadLetterQueue | None = None,
        scraper_workflow: ScraperWorkflow | None = None,
        scraper_urls: list[str] | None = None,
    ) -> None:
        self.email_gateway = email_gateway
        self.interval_seconds = interval_seconds
        self.dlq = dlq
        self.scraper_workflow = scraper_workflow
        self.scraper_urls = scraper_urls or []

    def run_once(self) -> HeartbeatMetrics:
        metrics = HeartbeatMetrics(cycles=1)
        try:
            results = self.email_gateway.poll_and_process(on_error=self._handle_email_error)
            metrics.success_count = len(results)
        except Exception:
            metrics.failure_count = 1

        if self.scraper_workflow and self.scraper_urls:
            scraper_metrics = self.scraper_workflow.process_urls(self.scraper_urls, on_error=self._handle_scraper_error)
            metrics.scraper_success_count = scraper_metrics.processed
            metrics.scraper_failure_count = scraper_metrics.failed

        if self.dlq:
            handlers = {
                "email": lambda payload: self.email_gateway.process_message(**payload),
            }
            if self.scraper_workflow:
                handlers["scraper"] = lambda payload: self.scraper_workflow.process_urls([payload["url"]])
            replay_result = self.dlq.replay(handlers)
            metrics.replayed_count = replay_result.get("replayed", 0)
        return metrics

    def _handle_email_error(self, payload: dict[str, str], exc: Exception) -> None:
        if self.dlq:
            self.dlq.enqueue(channel="email", payload=payload, error=str(exc))

    def _handle_scraper_error(self, payload: dict[str, str], exc: Exception) -> None:
        if self.dlq:
            self.dlq.enqueue(channel="scraper", payload=payload, error=str(exc))

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.interval_seconds)
