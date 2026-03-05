from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from uuid import uuid4

from universe_core.models import utc_now_iso


@dataclass(slots=True)
class DLQEntry:
    entry_id: str
    channel: str
    payload: dict[str, str]
    error: str
    created_at: str
    attempts: int = 0


class DeadLetterQueue:
    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("", encoding="utf-8")

    def enqueue(self, channel: str, payload: dict[str, str], error: str) -> DLQEntry:
        entry = DLQEntry(
            entry_id=str(uuid4()),
            channel=channel,
            payload=payload,
            error=error,
            created_at=utc_now_iso(),
            attempts=0,
        )
        with self.file_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        return entry

    def _read_all(self) -> list[DLQEntry]:
        entries: list[DLQEntry] = []
        for line in self.file_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            entries.append(DLQEntry(**raw))
        return entries

    def replay(self, handlers: dict[str, Callable[[dict[str, str]], None]], max_attempts: int = 3) -> dict[str, int]:
        entries = self._read_all()
        if not entries:
            return {"replayed": 0, "remaining": 0}

        remaining: list[DLQEntry] = []
        replayed = 0
        for entry in entries:
            handler = handlers.get(entry.channel)
            if handler is None:
                remaining.append(entry)
                continue
            try:
                handler(entry.payload)
                replayed += 1
            except Exception as exc:
                entry.attempts += 1
                entry.error = str(exc)
                if entry.attempts < max_attempts:
                    remaining.append(entry)

        content = "\n".join(json.dumps(asdict(item), ensure_ascii=False) for item in remaining)
        if content:
            content += "\n"
        self.file_path.write_text(content, encoding="utf-8")
        return {"replayed": replayed, "remaining": len(remaining)}
