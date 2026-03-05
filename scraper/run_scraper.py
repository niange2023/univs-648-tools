from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_PATH = REPO_ROOT / "universe-tools"
if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))

from universe_tools.scraper.gateway import ScraperGateway


def main() -> None:
    parser = argparse.ArgumentParser(description="Universe-648 scraper runner")
    parser.add_argument("url")
    parser.add_argument("--output", default=str(REPO_ROOT / "universe-corpus" / "drafts"))
    args = parser.parse_args()

    gateway = ScraperGateway()
    result = gateway.fetch_markdown(args.url)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in result.title)[:80] or "scraped"
    file_path = output_dir / f"{safe_name}.md"
    file_path.write_text(result.markdown, encoding="utf-8")
    print({"url": result.url, "title": result.title, "output": str(file_path)})


if __name__ == "__main__":
    main()
