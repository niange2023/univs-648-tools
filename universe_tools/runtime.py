from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from universe_tools.email.client import EmailConfig, Mail163Client


def bootstrap_paths() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    core_path = repo_root / "universe-core"
    tools_path = repo_root / "universe-tools"
    for path in (str(core_path), str(tools_path)):
        if path not in sys.path:
            sys.path.insert(0, path)


def load_settings(path: str) -> dict[str, Any]:
    import tomllib

    with open(path, "rb") as file:
        return tomllib.load(file)


def build_mail_client(settings: dict[str, Any]) -> Mail163Client:
    email_conf = settings.get("email", {})
    config = EmailConfig(
        imap_host=email_conf.get("imap_host", "imap.163.com"),
        imap_port=int(email_conf.get("imap_port", 993)),
        smtp_host=email_conf.get("smtp_host", "smtp.163.com"),
        smtp_port=int(email_conf.get("smtp_port", 465)),
        address=str(email_conf.get("address", "")),
        password=str(email_conf.get("password", "")),
        folder=str(email_conf.get("poll_folder", "INBOX")),
    )
    return Mail163Client(config)
