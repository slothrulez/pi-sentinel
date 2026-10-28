"""Secret-safe structured logging (PS-U03, SECURITY.md).

Log calls pass an event name plus a small set of fields. Values under sensitive key names are
replaced, strings matching credential shapes are redacted, long strings are truncated and
exception messages are never logged (only the exception class). A ``RedactingFilter`` also
scrubs ad-hoc messages that bypass ``log_event``.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from typing import Any

REDACTED = "[REDACTED]"
MAX_LOG_STRING = 200
MAX_LOG_FIELDS = 32

SENSITIVE_KEY_PATTERN = re.compile(
    r"pass(word|wd|phrase)?|pwd|secret|token|cookie|authori[sz]ation|auth|api_?key|"
    r"private_?key|credential|session_?key|otp|bearer|signature|key_?material",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"\b(password|passwd|pwd|secret|token|api_?key)\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"\b(sk|pk|ghp|gho|ghs|xox[abpr])[-_][A-Za-z0-9_-]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
)


def is_sensitive_key(key: str) -> bool:
    return SENSITIVE_KEY_PATTERN.search(key) is not None


def looks_like_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS)


def scrub_text(value: str) -> str:
    for pattern in SECRET_VALUE_PATTERNS:
        value = pattern.sub(REDACTED, value)
    if len(value) > MAX_LOG_STRING:
        value = value[:MAX_LOG_STRING] + "...[truncated]"
    return value


def _safe_value(key: str, value: Any, depth: int = 0) -> Any:
    if is_sensitive_key(key):
        return REDACTED
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if value == value and abs(value) != float("inf") else str(value)
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, BaseException):
        return type(value).__name__
    if isinstance(value, Mapping) and depth < 2:
        return {str(k): _safe_value(str(k), v, depth + 1) for k, v in list(value.items())[:16]}
    if isinstance(value, (list, tuple)) and depth < 2:
        return [_safe_value(key, v, depth + 1) for v in value[:16]]
    return f"<{type(value).__name__}>"


def safe_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    items = list(fields.items())[:MAX_LOG_FIELDS]
    return {str(k): _safe_value(str(k), v) for k, v in items}


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Emit a structured, redacted log record."""
    logger.log(level, event, extra={"pisentinel_fields": safe_fields(fields)})


class RedactingFilter(logging.Filter):
    """Scrub secrets from messages/args and strip exception text from any record."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - malformed format args must not leak or crash
            message = str(record.msg)
        record.msg = scrub_text(message)
        record.args = None
        if record.exc_info and record.exc_info[0] is not None:
            record.pisentinel_exc_class = record.exc_info[0].__name__
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "event": scrub_text(str(record.msg)),
        }
        fields = getattr(record, "pisentinel_fields", None)
        if isinstance(fields, dict):
            payload["fields"] = fields
        exc_class = getattr(record, "pisentinel_exc_class", None)
        if exc_class:
            payload["exception_class"] = exc_class
        return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def configure_logging(level: str = "INFO", stream: Any = None) -> logging.Logger:
    """Attach one redacting JSON handler to the ``pisentinel`` logger hierarchy."""
    logger = logging.getLogger("pisentinel")
    for handler in list(logger.handlers):
        if getattr(handler, "_pisentinel", False):
            logger.removeHandler(handler)
    handler = logging.StreamHandler(stream)
    handler._pisentinel = True  # type: ignore[attr-defined]
    handler.addFilter(RedactingFilter())
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
