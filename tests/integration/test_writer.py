import os
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from pisentinel.config import Config
from pisentinel.edge import db
from pisentinel.edge.evidence.chain import GENESIS_PREVIOUS_HASH
from pisentinel.edge.evidence.verify import verify_database
from pisentinel.edge.evidence.writer import EvidenceWriteError, EvidenceWriter, RecordRejected
from tests.conftest import REPO_ROOT, make_config, observation

CHILD = Path(__file__).with_name("writer_child.py")


def rows(config: Config):
    conn = sqlite3.connect(str(config.db_path))
    try:
        return conn.execute(
            "SELECT sequence, event_id, previous_hash, current_hash, canonical_json "
            "FROM evidence_records WHERE case_id = ? ORDER BY sequence",
            (config.case_id,),
        ).fetchall()
    finally:
        conn.close()


def assert_intact(config: Config, count: int):
    report = verify_database(config.db_path, config.case_id)
    assert report.intact, report.to_dict()
    assert report.case(config.case_id).record_count == count
    seqs = [r[0] for r in rows(config)]
    assert seqs == list(range(1, count + 1))


def run_child(mode, config, prefix, count, **kw):
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    return subprocess.Popen(
        [sys.executable, str(CHILD), mode, str(config.db_path), prefix, str(count)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        **kw,
    )


def test_append_links_genesis_and_acknowledges(writer, config):
    first = writer.append_observation(observation(1))
    second = writer.append_observation(observation(2))
    assert first.sequence == 1 and first.previous_hash == GENESIS_PREVIOUS_HASH
    assert second.sequence == 2 and second.previous_hash == first.current_hash
    head = writer.head()
    assert (head.count, head.last_sequence, head.head_hash) == (2, 2, second.current_hash)
    assert_intact(config, 2)


def test_restart_recovers_committed_head_and_continues(config):
    with EvidenceWriter(config) as w:
        for n in range(1, 4):
            last = w.append_observation(observation(n))
    with EvidenceWriter(config) as w:
        head = w.head()
        assert (head.count, head.head_hash) == (3, last.current_hash)
        nxt = w.append_observation(observation(4))
        assert nxt.sequence == 4 and nxt.previous_hash == last.current_hash
    assert_intact(config, 4)


def test_raw_observation_unchanged_by_enrichment(writer, config):
    writer.append_observation(observation(1))
    before = rows(config)[0][4]
    writer.append_derived("session_association", ["EVT-000001"], {"behaviour_session": "B-1"})
    writer.append_derived("assessment", ["EVT-000001"], {"model_label": "credential_attack"})
    after = rows(config)
    assert after[0][4] == before and len(after) == 3
    assert_intact(config, 3)


def test_enrichment_requires_previously_committed_record(writer, config):
    with pytest.raises(RecordRejected) as info:
        writer.append_derived("assessment", ["EVT-999999"], {"model_label": "x"})
    assert info.value.category == "unknown_reference"
    assert writer.head().count == 0


def test_append_only_triggers_block_application_update_and_delete(writer, config):
    writer.append_observation(observation(1))
    conn = sqlite3.connect(str(config.db_path))
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute("UPDATE evidence_records SET event_id = 'X'")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute("DELETE FROM evidence_records")
    conn.close()


def test_database_constraint_makes_fork_unrepresentable(writer, config):
    r = writer.append_observation(observation(1))
    conn = sqlite3.connect(str(config.db_path))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO evidence_records VALUES "
            "(?, 2, 'observation', 'EVT-F', 't', x'7b7d', ?, ?)",
            (config.case_id, GENESIS_PREVIOUS_HASH, "a" * 64),
        )
    conn.close()
    assert r.sequence == 1


def test_duplicate_event_id_rejected_without_changing_chain(writer):
    writer.append_observation(observation(1))
    head = writer.head()
    with pytest.raises(RecordRejected) as info:
        writer.append_observation(observation(1))
    assert info.value.category == "duplicate_event_id"
    assert writer.head() == head and writer.state.rejected == 1 and writer.state.failed == 0


def test_oversized_record_rejected(tmp_path):
    config = make_config(tmp_path, MAX_RECORD_BYTES="1024")
    with EvidenceWriter(config) as w:
        with pytest.raises(RecordRejected) as info:
            w.append_observation(observation(1, metadata={"command": "x" * 2000}))
        assert info.value.category == "record_too_large"
        assert w.head().count == 0


def test_invalid_observation_rejected_before_persistence(writer):
    with pytest.raises(RecordRejected):
        writer.append_observation(observation(1, source_ip="not-an-ip"))
    assert writer.head().count == 0
    assert writer.state.rejections_by_category == {"invalid_observation": 1}


@pytest.mark.parametrize("point", ["after_insert", "before_commit"])
def test_failed_write_rolls_back_is_visible_and_not_acknowledged(config, point):
    def hook(p):
        if p == point:
            raise sqlite3.OperationalError("disk I/O error")

    with EvidenceWriter(config) as w:
        good = w.append_observation(observation(1))
        w._fault_hook = hook
        with pytest.raises(EvidenceWriteError) as info:
            w.append_observation(observation(2))
        assert "NOT persisted" in str(info.value)
        assert w.state.failed == 1 and w.state.consecutive_failures == 1
        assert w.state.last_failure_class == "OperationalError"
        assert w.head().head_hash == good.current_hash
        w._fault_hook = None
        retry = w.append_observation(observation(2))
        assert retry.sequence == 2 and w.state.consecutive_failures == 0
    assert_intact(config, 2)


def test_disk_full_failure_leaves_no_partial_record(config):
    with EvidenceWriter(config) as w:
        w.append_observation(observation(1))
        conn = w._conn
        pages = conn.execute("PRAGMA page_count").fetchone()[0]
        conn.execute(f"PRAGMA max_page_count = {pages + 1}")
        acked = 1
        with pytest.raises(EvidenceWriteError) as info:
            for n in range(2, 500):
                w.append_observation(observation(n, metadata={"command": "y" * 2000}))
                acked += 1
        assert info.value.failure_class == "OperationalError"
        assert w.state.failed == 1
        assert w.head().count == acked
    assert_intact(config, acked)


def test_read_only_database_write_fails_visibly(config):
    with EvidenceWriter(config) as w:
        w._conn.execute("PRAGMA query_only = ON")
        with pytest.raises(EvidenceWriteError):
            w.append_observation(observation(1))
        assert w.state.consecutive_failures == 1


def test_writer_not_open_refuses(config):
    w = EvidenceWriter(config)
    with pytest.raises(EvidenceWriteError) as info:
        w.append_observation(observation(1))
    assert info.value.failure_class == "writer_not_open"


def test_newer_schema_refused(config):
    EvidenceWriter(config).open().close()
    conn = sqlite3.connect(str(config.db_path))
    conn.execute("INSERT INTO schema_migrations VALUES (99, 'future', 'x')")
    conn.commit()
    conn.close()
    with pytest.raises(EvidenceWriteError) as info:
        EvidenceWriter(config).open()
    assert info.value.failure_class == "open_SchemaError"


def test_migration_is_idempotent(config):
    for _ in range(2):
        EvidenceWriter(config).open().close()
    conn = sqlite3.connect(str(config.db_path))
    assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
    assert db.current_version(conn) == db.SCHEMA_VERSION
    conn.close()


@pytest.mark.parametrize("point", ["after_insert", "before_commit"])
def test_interrupted_process_leaves_no_half_record(config, point):
    with EvidenceWriter(config) as w:
        before = w.append_observation(observation(1))
    proc = run_child(f"crash_{point}", config, "CRASH", 1)
    out, err = proc.communicate(timeout=60)
    assert proc.returncode == 17, err
    assert "ACK" not in out
    with EvidenceWriter(config) as w:
        assert w.head().head_hash == before.current_hash and w.head().count == 1
        w.append_observation(observation(2))
    assert_intact(config, 2)


@pytest.mark.slow
def test_killed_writer_keeps_every_acknowledged_record(config):
    EvidenceWriter(config).open().close()
    proc = run_child("loop", config, "KILL", 100000)
    acks = []
    deadline = time.monotonic() + 60
    while len(acks) < 50 and time.monotonic() < deadline:
        line = proc.stdout.readline()
        if line.startswith("ACK"):
            acks.append(line.split())
    proc.kill()
    proc.communicate(timeout=60)
    assert len(acks) >= 50
    stored = {r[0]: (r[1], r[3]) for r in rows(config)}
    for _, seq, event_id, current_hash in acks:
        assert stored[int(seq)] == (event_id, current_hash)
    assert_intact(config, len(stored))


def test_concurrent_threads_sharing_one_writer_do_not_fork(writer, config):
    def work(t):
        for i in range(25):
            writer.append_observation(observation(t * 1000 + i))

    threads = [threading.Thread(target=work, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert_intact(config, 200)


def test_concurrent_writers_with_separate_connections_do_not_fork(config):
    EvidenceWriter(config).open().close()
    errors = []

    def work(t):
        try:
            with EvidenceWriter(config) as w:
                for i in range(25):
                    w.append_observation(observation(t * 1000 + i))
        except Exception as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=work, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert_intact(config, 100)


@pytest.mark.slow
def test_concurrent_processes_do_not_fork(config):
    EvidenceWriter(config).open().close()
    procs = [run_child("loop", config, f"P{p}", 40) for p in range(4)]
    acked = set()
    for proc in procs:
        out, err = proc.communicate(timeout=120)
        assert proc.returncode == 0, err
        acked |= {tuple(line.split()[1:]) for line in out.splitlines() if line.startswith("ACK")}
    assert len(acked) == 160
    stored = {(str(r[0]), r[1], r[3]) for r in rows(config)}
    assert acked == stored
    prev = [r[2] for r in rows(config)]
    assert len(set(prev)) == len(prev)
    assert_intact(config, 160)
