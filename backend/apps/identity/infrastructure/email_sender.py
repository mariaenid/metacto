"""Console email sender for dev/test. Production swaps for SES/Mailgun."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ConsoleEmailSender:
    def send_verification(self, *, to: str, token: str) -> None:
        logger.info("[email] verify %s token=%s", to, token)

    def send_password_reset(self, *, to: str, token: str) -> None:
        logger.info("[email] reset %s token=%s", to, token)
