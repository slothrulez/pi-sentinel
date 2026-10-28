from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from pisentinel.config import Config, load_config
from pisentinel.edge.evidence.writer import EvidenceWriter

REPO_ROOT = Path(__file__).resolve().parents[1]


def make_config(tmp_path: Path, **overrides: str) -> Config:
    env = {
        "PISENTINEL_DB_PATH": str(tmp_path / "cases" / "evidence.sqlite3"),
        "PISENTINEL_CASE_ID": "CASE-TEST",
        "PISENTINEL_MIN_FREE_BYTES": "0",
    }
    env.update({f"PISENTINEL_{k}": v for k, v in overrides.items()})
    return load_config(env)


def observation(n: int, **overrides: Any) -> dict[str, Any]:
    obs: dict[str, Any] = {
        "event_id": f"EVT-{n:06d}",
        "timestamp": "2026-09-16T14:22:01+05:30",
        "source_ip": "10.10.0.20",
        "destination_service": "ssh",
        "event_type": "auth_failure",
        "action": "login_attempt",
        "metadata": {"username": "admin", "attempt": n},
        "session_id": "S-014",
        "severity": "medium",
    }
    obs.update(overrides)
    return obs


def raw_conn(config: Config) -> sqlite3.Connection:
    """Direct DB access simulating a privileged party (append-only triggers dropped)."""
    conn = sqlite3.connect(str(config.db_path), isolation_level=None)
    conn.execute("DROP TRIGGER IF EXISTS evidence_records_no_update")
    conn.execute("DROP TRIGGER IF EXISTS evidence_records_no_delete")
    return conn


@pytest.fixture
def config(tmp_path: Path) -> Config:
    return make_config(tmp_path)


@pytest.fixture
def writer(config: Config) -> Iterator[EvidenceWriter]:
    w = EvidenceWriter(config).open()
    yield w
    w.close()
