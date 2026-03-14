import argparse
import sys
from pathlib import Path

# Initialize system paths using bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "11-核心引擎"))
import path_bootstrap

REPO_ROOT = Path(__file__).resolve().parents[2]

from universe_tools.email.client import Mail163Client
from universe_tools.email.gateway import EmailGateway
from engine.router.gateway import TaskRouter
from engine.memory.sqlite_store import SQLiteMemoryStore
from engine.memory.vector_store import LocalVectorStore
from universe_tools.workflow.heartbeat import HeartbeatRunner

def main() -> None:
    parser = argparse.ArgumentParser(description="Universe-648 heartbeat daemon runner")
    parser.add_argument("--config", default=str(REPO_ROOT / "config" / "settings.toml"))
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--db", default=str(REPO_ROOT / "data" / "universe648.db"))
    args = parser.parse_args()

    # NOTE: The actual implementation of config loading and mail client init is omitted here
    # assuming settings.toml is read and parsed here in a real scenario.
    # We initialize the dummy dependencies just to show the pipeline structure.
    memory = SQLiteMemoryStore(args.db)
    vector_store = LocalVectorStore()
    router = TaskRouter(memory_store=memory, vector_store=vector_store)
    
    # Mail163Client would need real credentials in production
    mail_client = Mail163Client(username="dummy", password="dummy")
    email_gateway = EmailGateway(mail_client=mail_client, router=router)

    runner = HeartbeatRunner(
        email_gateway=email_gateway,
        interval_seconds=args.interval
    )
    
    print(f"Starting heartbeat runner every {args.interval} seconds...")
    runner.run_forever()

if __name__ == "__main__":
    main()
