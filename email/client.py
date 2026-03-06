from __future__ import annotations

import email
import imaplib
import smtplib
from dataclasses import dataclass
from email.header import decode_header
from email.mime.text import MIMEText


@dataclass(slots=True)
class EmailConfig:
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    address: str
    password: str
    folder: str = "INBOX"


@dataclass(slots=True)
class EmailMessage:
    message_id: str
    subject: str
    from_address: str
    body: str


def _decode_header_value(raw: str | None) -> str:
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded = []
    for value, charset in parts:
        if isinstance(value, bytes):
            decoded.append(value.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(value)
    return "".join(decoded)


def _extract_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
    payload = msg.get_payload(decode=True) or b""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


class Mail163Client:
    def __init__(self, config: EmailConfig) -> None:
        self.config = config

    def fetch_unseen(self, limit: int = 20) -> list[EmailMessage]:
        messages: list[EmailMessage] = []
        with imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port) as client:
            client.login(self.config.address, self.config.password)
            client.select(self.config.folder)
            _, data = client.search(None, "UNSEEN")
            ids = data[0].split()[-limit:]
            for message_uid in ids:
                _, message_data = client.fetch(message_uid, "(RFC822)")
                raw = message_data[0][1]
                parsed = email.message_from_bytes(raw)
                messages.append(
                    EmailMessage(
                        message_id=parsed.get("Message-ID", ""),
                        subject=_decode_header_value(parsed.get("Subject")),
                        from_address=_decode_header_value(parsed.get("From")),
                        body=_extract_text(parsed),
                    )
                )
            client.logout()
        return messages

    def send(self, to_address: str, subject: str, body: str) -> None:
        mime = MIMEText(body, _subtype="plain", _charset="utf-8")
        mime["From"] = self.config.address
        mime["To"] = to_address
        mime["Subject"] = subject

        with smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port) as client:
            client.login(self.config.address, self.config.password)
            client.sendmail(self.config.address, [to_address], mime.as_string())
