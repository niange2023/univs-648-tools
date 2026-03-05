from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = REPO_ROOT / "universe-core"
TOOLS_PATH = REPO_ROOT / "universe-tools"
for candidate in (str(CORE_PATH), str(TOOLS_PATH)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from universe_core.memory.sqlite_store import SQLiteMemoryStore
from universe_core.memory.vector_store import LocalVectorStore
from universe_core.router.gateway import TaskRouter
from universe_tools.email.gateway import EmailGateway
from universe_tools.runtime import build_mail_client, load_settings
from universe_tools.scraper.gateway import ScraperGateway
from universe_tools.workflow.dlq import DeadLetterQueue
from universe_tools.workflow.heartbeat import HeartbeatRunner
from universe_tools.workflow.scraper_jobs import ScraperWorkflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Universe-648 heartbeat workflow")
    parser.add_argument("--config", default=str(REPO_ROOT / "config" / "settings.example.toml"))
    parser.add_argument("--continuous", action="store_true")
    args = parser.parse_args()

    settings = load_settings(args.config)
    db_path = settings.get("storage", {}).get("sqlite_path", "./data/universe648.db")

    memory = SQLiteMemoryStore(db_path)
    memory.migrate()
    vector_store = LocalVectorStore()
    router = TaskRouter(memory_store=memory, vector_store=vector_store)

    mail_client = build_mail_client(settings)
    gateway = EmailGateway(mail_client=mail_client, router=router)

    workflow_settings = settings.get("workflow", {})
    dlq = DeadLetterQueue(str(workflow_settings.get("dlq_path", "./data/dlq.jsonl")))

    scraper_settings = settings.get("scraper", {})
    scraper_urls = list(scraper_settings.get("seed_urls", []))
    scraper_output_dir = str(scraper_settings.get("output_dir", "./universe-corpus/drafts"))
    scraper_workflow = ScraperWorkflow(scraper_gateway=ScraperGateway(), output_dir=scraper_output_dir)

    runner = HeartbeatRunner(
        email_gateway=gateway,
        interval_seconds=int(settings.get("app", {}).get("heartbeat_interval_seconds", 300)),
        dlq=dlq,
        scraper_workflow=scraper_workflow,
        scraper_urls=scraper_urls,
    )

    if args.continuous:
        runner.run_forever()
        return

    metrics = runner.run_once()
    print(
        {
            "cycles": metrics.cycles,
            "success_count": metrics.success_count,
            "failure_count": metrics.failure_count,
            "replayed_count": metrics.replayed_count,
            "scraper_success_count": metrics.scraper_success_count,
            "scraper_failure_count": metrics.scraper_failure_count,
        }
    )


if __name__ == "__main__":
    main()
