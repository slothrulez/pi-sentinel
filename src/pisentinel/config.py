"""Bounded, validated configuration (guide Appendix C step 1, PS-F01/PS-U03).

Configuration is loaded only by an explicit ``load_config`` call (no import-time binding).
Error messages name the setting and the reason category but never echo the supplied value, so a
secret pasted into the wrong variable is not written to logs or tracebacks.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PREFIX = "PISENTINEL_"
CASE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
MAX_PATH_CHARS = 1024
MAX_ENV_FILE_BYTES = 64 * 1024


@dataclass(frozen=True)
class IntBound:
    default: int
    minimum: int
    maximum: int


INT_SETTINGS: dict[str, IntBound] = {
    "MAX_RECORD_BYTES": IntBound(16384, 1024, 16384),
    "SQLITE_BUSY_TIMEOUT_MS": IntBound(5000, 100, 60000),
    "MIN_FREE_BYTES": IntBound(104857600, 0, 10 * 1024**3),
}
STR_DEFAULTS: dict[str, str] = {
    "DB_PATH": "data/cases/pisentinel.sqlite3",
    "CASE_ID": "CASE-0001",
    "LOG_LEVEL": "INFO",
}
KNOWN_SETTINGS = frozenset(INT_SETTINGS) | frozenset(STR_DEFAULTS)


class ConfigError(ValueError):
    """Invalid configuration. ``problems`` maps setting name to a value-free reason."""

    def __init__(self, problems: dict[str, str]) -> None:
        self.problems = dict(sorted(problems.items()))
        detail = "; ".join(f"{name}: {reason}" for name, reason in self.problems.items())
        super().__init__(f"invalid configuration: {detail}")


@dataclass(frozen=True)
class Config:
    db_path: Path
    case_id: str
    log_level: str
    max_record_bytes: int
    sqlite_busy_timeout_ms: int
    min_free_bytes: int


def read_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal ``KEY=VALUE`` file: no interpolation, no shell evaluation, no export."""
    problems: dict[str, str] = {}
    raw = Path(path).read_bytes()
    if len(raw) > MAX_ENV_FILE_BYTES:
        raise ConfigError({"env_file": f"larger than {MAX_ENV_FILE_BYTES} bytes"})
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ConfigError({"env_file": "not valid UTF-8"}) from None
    values: dict[str, str] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, sep, value = stripped.partition("=")
        key = key.strip()
        if not sep or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            problems[f"env_file line {number}"] = "malformed line"
            continue
        if key in values:
            problems[key] = "defined more than once"
        values[key] = value.strip()
    if problems:
        raise ConfigError(problems)
    return values


def _parse_int(name: str, raw: str, bound: IntBound, problems: dict[str, str]) -> int:
    if not re.fullmatch(r"[0-9]{1,12}", raw):
        problems[name] = "must be a non-negative decimal integer"
        return bound.default
    value = int(raw)
    if not bound.minimum <= value <= bound.maximum:
        problems[name] = f"must be between {bound.minimum} and {bound.maximum}"
    return value


def _parse_db_path(name: str, raw: str, problems: dict[str, str]) -> Path:
    if not raw or raw != raw.strip():
        problems[name] = "must be a non-empty path without surrounding whitespace"
    elif len(raw) > MAX_PATH_CHARS:
        problems[name] = f"longer than {MAX_PATH_CHARS} characters"
    elif any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in raw):
        problems[name] = "contains control characters"
    elif raw == ":memory:" or raw.lower().startswith("file:"):
        problems[name] = "must be a filesystem path (in-memory and URI databases are not durable)"
    return Path(raw)


def load_config(
    environ: Mapping[str, str] | None = None, env_file: Path | str | None = None
) -> Config:
    """Build a validated ``Config``. Process environment values override ``env_file`` values."""
    merged: dict[str, str] = {}
    if env_file is not None:
        merged.update(read_env_file(Path(env_file)))
    source = os.environ if environ is None else environ
    merged.update({k: v for k, v in source.items() if k.startswith(PREFIX)})

    problems: dict[str, str] = {}
    settings: dict[str, str] = {}
    for key, value in merged.items():
        if not key.startswith(PREFIX):
            continue
        short = key[len(PREFIX) :]
        if short not in KNOWN_SETTINGS:
            problems[key] = "unknown setting"
            continue
        settings[short] = value

    def raw(short: str) -> str:
        return settings.get(short, STR_DEFAULTS.get(short, ""))

    db_path = _parse_db_path(PREFIX + "DB_PATH", raw("DB_PATH"), problems)
    case_id = raw("CASE_ID")
    if not CASE_ID_PATTERN.match(case_id):
        problems[PREFIX + "CASE_ID"] = "must be 1-64 characters of A-Z a-z 0-9 . _ -"
    log_level = raw("LOG_LEVEL")
    if log_level not in LOG_LEVELS:
        problems[PREFIX + "LOG_LEVEL"] = f"must be one of {', '.join(LOG_LEVELS)}"
    ints = {
        short: _parse_int(PREFIX + short, settings.get(short, str(b.default)), b, problems)
        for short, b in INT_SETTINGS.items()
    }
    if problems:
        raise ConfigError(problems)
    return Config(
        db_path=db_path,
        case_id=case_id,
        log_level=log_level,
        max_record_bytes=ints["MAX_RECORD_BYTES"],
        sqlite_busy_timeout_ms=ints["SQLITE_BUSY_TIMEOUT_MS"],
        min_free_bytes=ints["MIN_FREE_BYTES"],
    )
