"""SQLite schema and migrations for the evidence store (PS-F01/PS-C02/PS-E01/PS-E02).

``evidence_records`` holds every chained record: raw observations and later derived records.
Append-only triggers stop accidental UPDATE/DELETE by application code; they are *not* a
security boundary (anyone with write access to the file can drop them, see
docs/EVIDENCE_CHAIN.md). ``UNIQUE(case_id, previous_hash)`` makes a chain fork unrepresentable.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

MIGRATIONS: dict[int, tuple[str, str]] = {
    1: (
        "evidence_records_v1",
        """
        CREATE TABLE evidence_records (
            case_id        TEXT    NOT NULL CHECK (typeof(case_id) = 'text'),
            sequence       INTEGER NOT NULL CHECK (typeof(sequence) = 'integer' AND sequence >= 1),
            record_type    TEXT    NOT NULL CHECK (typeof(record_type) = 'text'),
            event_id       TEXT    NOT NULL CHECK (typeof(event_id) = 'text'),
            recorded_at    TEXT    NOT NULL CHECK (typeof(recorded_at) = 'text'),
            canonical_json BLOB    NOT NULL CHECK (typeof(canonical_json) = 'blob'),
            previous_hash  TEXT    NOT NULL CHECK (length(previous_hash) = 64),
            current_hash   TEXT    NOT NULL CHECK (length(current_hash) = 64),
            PRIMARY KEY (case_id, sequence),
            UNIQUE (case_id, event_id),
            UNIQUE (case_id, previous_hash)
        );
        CREATE TRIGGER evidence_records_no_update BEFORE UPDATE ON evidence_records
        BEGIN SELECT RAISE(ABORT, 'evidence_records is append-only'); END;
        CREATE TRIGGER evidence_records_no_delete BEFORE DELETE ON evidence_records
        BEGIN SELECT RAISE(ABORT, 'evidence_records is append-only'); END;
        """,
    ),
}


class SchemaError(RuntimeError):
    """Database schema is missing, newer than this code, or inconsistent."""


def prepare_db_file(path: Path) -> None:
    """Create the parent directory (0700) and an empty DB file (0600) if absent (POSIX modes)."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.exists():
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)


def connect(path: Path, busy_timeout_ms: int) -> sqlite3.Connection:
    """Open a read/write connection with explicit transaction control and durable commits."""
    conn = sqlite3.connect(
        str(path), timeout=busy_timeout_ms / 1000, isolation_level=None, check_same_thread=False
    )
    conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
    mode = conn.execute("PRAGMA journal_mode = WAL").fetchone()[0]
    if str(mode).lower() != "wal":
        conn.close()
        raise SchemaError("could not enable WAL journal mode")
    conn.execute("PRAGMA synchronous = FULL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA trusted_schema = OFF")
    return conn


def current_version(conn: sqlite3.Connection) -> int:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
    ).fetchone()
    if not exists:
        return 0
    row = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
    return int(row[0] or 0)


def migrate(conn: sqlite3.Connection) -> int:
    """Apply pending migrations atomically; refuse databases newer than this code."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        version = current_version(conn)
        if version > SCHEMA_VERSION:
            raise SchemaError("database schema is newer than this software")
        for number in range(version + 1, SCHEMA_VERSION + 1):
            name, sql = MIGRATIONS[number]
            for statement in (s.strip() for s in _split_sql(sql)):
                if statement:
                    conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (number, name, datetime.now(timezone.utc).isoformat()),
            )
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    return SCHEMA_VERSION


def _split_sql(sql: str) -> list[str]:
    """Split migration SQL on statement boundaries, keeping trigger bodies intact."""
    statements: list[str] = []
    buffer: list[str] = []
    for line in sql.strip().splitlines():
        buffer.append(line)
        candidate = "\n".join(buffer)
        if sqlite3.complete_statement(candidate):
            statements.append(candidate)
            buffer = []
    if buffer and "".join(buffer).strip():
        raise SchemaError("incomplete migration statement")
    return statements
