import io
import re
import sqlite3
import subprocess

import pytest

from pisentinel.edge.evidence.verify import verify_database
from pisentinel.edge.evidence.writer import EvidenceWriter, RecordRejected
from pisentinel.safe_logging import configure_logging
from tests.conftest import REPO_ROOT, observation, raw_conn

SECRET = "hunter2-SuperSecretValue-9f8e7d"


@pytest.fixture
def log_stream():
    stream = io.StringIO()
    configure_logging("DEBUG", stream)
    return stream


def all_db_bytes(config):
    data = b""
    for suffix in ("", "-wal", "-shm"):
        path = config.db_path.with_name(config.db_path.name + suffix)
        if path.exists():
            data += path.read_bytes()
    return data


def test_credentials_never_reach_evidence_or_logs(config, log_stream):
    with EvidenceWriter(config) as w:
        receipt = w.append_observation(
            observation(
                1,
                metadata={
                    "username": "root",
                    "password": SECRET,
                    "headers": {"cookie": SECRET},
                    "command": f"curl -H 'Authorization: Bearer {SECRET}'",
                },
            )
        )
        assert SECRET not in repr(receipt)
        assert SECRET.encode() not in all_db_bytes(config)
    assert SECRET.encode() not in all_db_bytes(config)
    assert SECRET not in log_stream.getvalue()


def test_rejection_logs_category_not_value(config, log_stream):
    with EvidenceWriter(config) as w:
        with pytest.raises(RecordRejected) as info:
            w.append_observation(observation(1, event_id=SECRET + " !"))
        with pytest.raises(RecordRejected):
            w.append_observation(observation(2, metadata={"x": SECRET * 200}))
    assert SECRET not in str(info.value)
    output = log_stream.getvalue()
    assert SECRET not in output and "invalid_observation" in output and "event_id" in output


def test_sql_metacharacters_stored_literally(config):
    payload = "'; DROP TABLE evidence_records; --"
    with EvidenceWriter(config) as w:
        w.append_observation(observation(1, metadata={"command": payload}))
        w.append_observation(observation(2))
    assert verify_database(config.db_path).intact
    content = (
        sqlite3.connect(str(config.db_path))
        .execute("SELECT canonical_json FROM evidence_records WHERE sequence=1")
        .fetchone()[0]
    )
    assert payload.encode() in content


def test_verifier_report_does_not_echo_record_content(config):
    with EvidenceWriter(config) as w:
        w.append_observation(observation(1, metadata={"note": "visible-marker-123"}))
    raw_conn(config).execute("UPDATE evidence_records SET current_hash=?", ("d" * 64,))
    report = verify_database(config.db_path)
    assert not report.intact and "visible-marker-123" not in repr(report.to_dict())


def test_repository_hygiene():
    ignore = (REPO_ROOT / ".gitignore").read_text()
    for pattern in (".env", "*.sqlite3", "data/", "*.key"):
        assert pattern in ignore.splitlines()
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert not [p for p in tracked if re.search(r"(^|/)\.env$|\.sqlite3$|\.db$|\.pem$", p)]
    example = (REPO_ROOT / ".env.example").read_text()
    assert not re.search(r"(?i)(password|token|secret|api_key)\s*=", example)


def test_source_opens_no_network_listener():
    source = "\n".join(p.read_text() for p in (REPO_ROOT / "src").rglob("*.py"))
    for marker in (
        "uvicorn",
        ".listen(",
        ".bind(",
        "socketserver",
        "http.server",
        "import socket",
        "requests.",
        "openai",
    ):
        assert marker not in source
