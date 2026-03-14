from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine.router.gateway import TaskRouter
from universe_tools.email.client import Mail163Client


@dataclass(slots=True)
class EmailProcessResult:
    session_id: str
    quality: float
    passed: bool


class EmailGateway:
    def __init__(self, mail_client: Mail163Client, router: TaskRouter) -> None:
        self.mail_client = mail_client
        self.router = router

    def process_message(self, message_id: str, subject: str, body: str) -> EmailProcessResult:
        thread_id = message_id or f"subject:{subject}"
        session = self.router.create_session(source="email", external_thread_id=thread_id)
        _, result = self.router.submit_writing_job(session.session_id, prompt=body.strip() or subject)
        return EmailProcessResult(session_id=session.session_id, quality=result.quality_score, passed=result.passed)

    def poll_and_process(
        self,
        limit: int = 10,
        on_error: Callable[[dict[str, str], Exception], None] | None = None,
    ) -> list[EmailProcessResult]:
        processed: list[EmailProcessResult] = []
        for message in self.mail_client.fetch_unseen(limit=limit):
            payload = {
                "message_id": message.message_id,
                "subject": message.subject,
                "body": message.body,
            }
            try:
                result = self.process_message(**payload)
                processed.append(result)
            except Exception as exc:
                if on_error:
                    on_error(payload, exc)
        return processed
