"""163 mail integration layer."""

from .client import EmailConfig, EmailMessage, Mail163Client
from .gateway import EmailGateway

__all__ = ["EmailConfig", "EmailMessage", "Mail163Client", "EmailGateway"]
