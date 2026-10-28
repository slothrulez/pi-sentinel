"""Versioned, bounded Event (raw observation) and derived-record schemas (guide section 9).

A raw observation is the privacy-filtered normalized input persisted *before* any enrichment.
Guide section 9 fields are mapped as follows:

* ``event_id``, ``timestamp``, ``source_ip``, ``destination_service``, ``event_type``,
  ``action``, ``metadata``, ``session_id``, ``severity`` -> observation body (this module).
* ``previous_hash``, ``current_hash`` -> chain envelope columns (``evidence_records``).
* ``model_label``, ``confidence``, ``shap_summary``, ``response_action`` -> separate derived
  records that reference observations; they never rewrite an observation.

Credential-like metadata keys and secret-shaped string values are discarded at this boundary
(only a count is kept). Validation errors name the field and reason category, never the value.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pisentinel.edge.evidence.canonical import MAX_SAFE_INTEGER
from pisentinel.safe_logging import looks_like_secret

EVENT_SCHEMA_VERSION = "pisentinel.event.v1"
DERIVED_SCHEMA_VERSION = "pisentinel.derived.v1"

OBSERVATION = "observation"
# Record kinds from ARCHITECTURE.md section 3. M1 only defines the generic derived envelope;
# the content of each derived kind is specified by its owning milestone.
DERIVED_RECORD_TYPES = frozenset(
    {"session_association", "assessment", "explanation", "decision", "result", "closure"}
)
RECORD_TYPES = DERIVED_RECORD_TYPES | {OBSERVATION}

# Proposed M1 severity vocabulary (assumption, see PROJECT_STATUS.md); the guide shows "medium".
SEVERITIES = ("info", "low", "medium", "high", "critical")

ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
TOKEN_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
SERVICE_PATTERN = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")
METADATA_KEY_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")

# Proposed initial limits (ARCHITECTURE.md section 3), not guide values or measured capacity.
MAX_USERNAME_CHARS = 256
MAX_METADATA_STRING_CHARS = 2048
MAX_METADATA_KEYS = 32
MAX_METADATA_DEPTH = 3
MAX_METADATA_LIST_ITEMS = 32
MAX_TIMESTAMP_CHARS = 40
MAX_REFERENCES = 64

# Metadata keys whose values are always discarded before persistence.
CREDENTIAL_KEY_PATTERN = re.compile(
    r"(^|_)(password|passwd|passphrase|pwd|secret|token|cookie|cookies|authorization|"
    r"api_?key|private_?key|credential|credentials|session_?key|otp|bearer|set_cookie)(_|$)"
)
OBSERVATION_FIELDS = frozenset(
    {
        "event_id",
        "timestamp",
        "source_ip",
        "source_port",
        "destination_service",
        "destination_port",
        "event_type",
        "action",
        "metadata",
        "session_id",
        "severity",
    }
)
REQUIRED_FIELDS = frozenset(
    {"event_id", "timestamp", "source_ip", "destination_service", "event_type", "action"}
)


class ValidationError(ValueError):
    """Rejected input. ``field`` and ``reason`` are safe to log; the value is never included."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


def _clean_text(field: str, value: Any, max_chars: int) -> str:
    if not isinstance(value, str):
        raise ValidationError(field, "must be a string")
    if not value:
        raise ValidationError(field, "must not be empty")
    if len(value) > max_chars:
        raise ValidationError(field, f"longer than {max_chars} characters")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise ValidationError(field, "invalid Unicode") from None
    if any(ord(ch) < 0x20 and ch not in "\t" or ord(ch) == 0x7F for ch in value):
        raise ValidationError(field, "contains control characters")
    return value


def _pattern(field: str, value: Any, pattern: re.Pattern[str], description: str) -> str:
    if not isinstance(value, str) or not pattern.match(value):
        raise ValidationError(field, f"must match {description}")
    return value


def _port(field: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValidationError(field, "must be an integer between 1 and 65535")
    return value


def parse_timestamp(field: str, value: Any) -> tuple[str, str]:
    """Validate an RFC 3339 timestamp with explicit offset; return (original, UTC normalized)."""
    text = _clean_text(field, value, MAX_TIMESTAMP_CHARS)
    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?(Z|[+-]\d{2}:\d{2})", text
    )
    if not match:
        raise ValidationError(field, "must be RFC 3339 with an explicit UTC offset")
    base, fraction, offset = match.groups()
    normalized = f"{base}.{(fraction or '').ljust(6, '0')}{'+00:00' if offset == 'Z' else offset}"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise ValidationError(field, "not a valid date/time") from None
    return text, format_utc(parsed)


def format_utc(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("naive datetime")
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass
class _Discarded:
    count: int = 0


def _sanitize_value(path: str, value: Any, depth: int, discarded: _Discarded) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise ValidationError(path, "integer outside safe range")
        return value
    if isinstance(value, float):
        raise ValidationError(path, "floating-point values are not permitted (use integers)")
    if isinstance(value, str):
        limit = MAX_USERNAME_CHARS if path.endswith(".username") else MAX_METADATA_STRING_CHARS
        if len(value) > limit:
            raise ValidationError(path, f"longer than {limit} characters")
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            raise ValidationError(path, "invalid Unicode") from None
        if looks_like_secret(value):
            discarded.count += 1
            return None
        return value
    if depth >= MAX_METADATA_DEPTH:
        raise ValidationError(path, f"nested deeper than {MAX_METADATA_DEPTH}")
    if isinstance(value, Mapping):
        return _sanitize_mapping(path, value, depth + 1, discarded)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        if len(value) > MAX_METADATA_LIST_ITEMS:
            raise ValidationError(path, f"more than {MAX_METADATA_LIST_ITEMS} items")
        return [
            _sanitize_value(f"{path}[{i}]", item, depth + 1, discarded)
            for i, item in enumerate(value)
        ]
    raise ValidationError(path, "unsupported value type")


def _sanitize_mapping(
    path: str, value: Mapping[Any, Any], depth: int, discarded: _Discarded
) -> dict[str, Any]:
    if len(value) > MAX_METADATA_KEYS:
        raise ValidationError(path, f"more than {MAX_METADATA_KEYS} keys")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not METADATA_KEY_PATTERN.match(key):
            raise ValidationError(path, "keys must match [a-z][a-z0-9_]{0,63}")
        if CREDENTIAL_KEY_PATTERN.search(key):
            discarded.count += 1
            continue
        result[key] = _sanitize_value(f"{path}.{key}", item, depth, discarded)
    return result


def build_observation_body(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and privacy-filter a normalized observation into its canonical body."""
    if not isinstance(raw, Mapping):
        raise ValidationError("observation", "must be a mapping")
    unknown = set(raw) - OBSERVATION_FIELDS
    if unknown:
        raise ValidationError("observation", f"{len(unknown)} unknown field(s)")
    missing = REQUIRED_FIELDS - set(raw)
    if missing:
        raise ValidationError(sorted(missing)[0], "required")

    timestamp, timestamp_utc = parse_timestamp("timestamp", raw["timestamp"])
    source_ip_raw = _clean_text("source_ip", raw["source_ip"], 64)
    try:
        source_ip = str(ipaddress.ip_address(source_ip_raw))
    except ValueError:
        raise ValidationError("source_ip", "not an IPv4/IPv6 address") from None

    discarded = _Discarded()
    metadata_raw = raw.get("metadata", {})
    if not isinstance(metadata_raw, Mapping):
        raise ValidationError("metadata", "must be an object")
    metadata = _sanitize_mapping("metadata", metadata_raw, 1, discarded)

    body: dict[str, Any] = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": _pattern("event_id", raw["event_id"], ID_PATTERN, "an identifier"),
        "timestamp": timestamp,
        "timestamp_utc": timestamp_utc,
        "source_ip": source_ip,
        "destination_service": _pattern(
            "destination_service", raw["destination_service"], SERVICE_PATTERN, "a service name"
        ),
        "event_type": _pattern("event_type", raw["event_type"], TOKEN_PATTERN, "a token"),
        "action": _pattern("action", raw["action"], TOKEN_PATTERN, "a token"),
        "metadata": metadata,
        "discarded_sensitive_values": discarded.count,
    }
    if raw.get("source_port") is not None:
        body["source_port"] = _port("source_port", raw["source_port"])
    if raw.get("destination_port") is not None:
        body["destination_port"] = _port("destination_port", raw["destination_port"])
    if raw.get("session_id") is not None:
        body["session_id"] = _pattern("session_id", raw["session_id"], ID_PATTERN, "an identifier")
    if raw.get("severity") is not None:
        if raw["severity"] not in SEVERITIES:
            raise ValidationError("severity", f"must be one of {', '.join(SEVERITIES)}")
        body["severity"] = raw["severity"]
    return body


def build_derived_body(
    record_type: str, refers_to: Sequence[str], data: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate a derived (enrichment) record body that references earlier records."""
    if record_type not in DERIVED_RECORD_TYPES:
        raise ValidationError("record_type", "not a derived record type")
    if isinstance(refers_to, str) or not isinstance(refers_to, Sequence) or not refers_to:
        raise ValidationError("refers_to", "must be a non-empty list of record IDs")
    if len(refers_to) > MAX_REFERENCES:
        raise ValidationError("refers_to", f"more than {MAX_REFERENCES} references")
    refs = [_pattern("refers_to", ref, ID_PATTERN, "an identifier") for ref in refers_to]
    if len(set(refs)) != len(refs):
        raise ValidationError("refers_to", "duplicate reference")
    if not isinstance(data, Mapping):
        raise ValidationError("data", "must be an object")
    discarded = _Discarded()
    return {
        "schema_version": DERIVED_SCHEMA_VERSION,
        "refers_to": refs,
        "data": _sanitize_mapping("data", data, 1, discarded),
        "discarded_sensitive_values": discarded.count,
    }
