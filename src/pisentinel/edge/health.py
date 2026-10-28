"""Real health model (PS-F01/PS-O02): database, schema, writer and storage status.

``healthy``: all components ok. ``degraded``: usable but a limit is near (e.g. free space below
the configured reserve). ``unavailable``: evidence cannot currently be persisted. The full
chain is not re-verified here (that is an explicit verifier operation).
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from typing import Any

from pisentinel.config import Config
from pisentinel.edge import db
from pisentinel.edge.evidence.writer import EvidenceWriter

HEALTHY, DEGRADED, UNAVAILABLE = "healthy", "degraded", "unavailable"
_RANK = {HEALTHY: 0, DEGRADED: 1, UNAVAILABLE: 2}


def _database_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": UNAVAILABLE, "reason": "database_missing"}
    try:
        conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    except sqlite3.Error as exc:
        return {"status": UNAVAILABLE, "reason": "open_failed", "error_class": type(exc).__name__}
    try:
        version = db.current_version(conn)
    except sqlite3.Error as exc:
        return {"status": UNAVAILABLE, "reason": "read_failed", "error_class": type(exc).__name__}
    finally:
        conn.close()
    if version != db.SCHEMA_VERSION:
        return {
            "status": UNAVAILABLE,
            "reason": "schema_mismatch",
            "schema_version": version,
            "expected_schema_version": db.SCHEMA_VERSION,
        }
    return {"status": HEALTHY, "schema_version": version}


def _storage_status(path: Path, min_free_bytes: int) -> dict[str, Any]:
    probe = path.parent
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        free = shutil.disk_usage(probe).free
    except OSError as exc:
        return {"status": UNAVAILABLE, "reason": "stat_failed", "error_class": type(exc).__name__}
    status = HEALTHY if free >= min_free_bytes else DEGRADED
    return {"status": status, "free_bytes": free, "min_free_bytes": min_free_bytes}


def _writer_status(writer: EvidenceWriter | None) -> dict[str, Any]:
    if writer is None:
        return {"status": UNAVAILABLE, "reason": "writer_not_attached"}
    state = writer.state
    info: dict[str, Any] = {
        "appended": state.appended,
        "rejected": state.rejected,
        "failed": state.failed,
        "consecutive_failures": state.consecutive_failures,
        "last_failure_class": state.last_failure_class,
        "last_failure_at": state.last_failure_at,
    }
    if not state.open:
        info.update(status=UNAVAILABLE, reason="writer_not_open")
    elif state.consecutive_failures:
        info.update(status=UNAVAILABLE, reason="last_write_failed")
    else:
        info["status"] = HEALTHY
    return info


def check_health(config: Config, writer: EvidenceWriter | None) -> dict[str, Any]:
    components = {
        "database": _database_status(config.db_path),
        "writer": _writer_status(writer),
        "storage": _storage_status(config.db_path, config.min_free_bytes),
    }
    overall = max((c["status"] for c in components.values()), key=_RANK.__getitem__)
    return {"status": overall, "case_id": config.case_id, "components": components}
