import sqlite3
import traceback
from contextlib import closing
from dataclasses import replace
from unittest.mock import Mock

import pytest

from pisentinel.edge.collector.ingest import AdmissionRejected, ObservationAdmission
from pisentinel.edge.evidence.verify import verify_database
from pisentinel.edge.evidence.writer import EvidenceWriteError, EvidenceWriter, RecordRejected
from tests.admission_helpers import CONTEXT, admitted_observation, make_policy


def test_authorized_observation_is_committed_before_receipt_and_verifies_after_reopen(config):
    with EvidenceWriter(config) as writer:
        admission = ObservationAdmission(writer, (make_policy(),))
        receipt = admission.admit(CONTEXT, admitted_observation())
        with sqlite3.connect(str(config.db_path)) as reader:
            row = reader.execute(
                "SELECT sequence, event_id, previous_hash, current_hash FROM evidence_records"
            ).fetchone()
        assert row == (
            receipt.sequence,
            receipt.event_id,
            receipt.previous_hash,
            receipt.current_hash,
        )
    with EvidenceWriter(config) as reopened:
        assert reopened.head().head_hash == receipt.current_hash
        second = ObservationAdmission(reopened, (make_policy(),)).admit(
            CONTEXT, admitted_observation(2)
        )
        assert second.previous_hash == receipt.current_hash and second.sequence == 2
    report = verify_database(config.db_path, config.case_id)
    assert report.intact and report.case(config.case_id).record_count == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"source_ip": "10.10.0.21"},
        {"destination_service": "web"},
        {"event_type": "auth_success"},
        {"password": "not-allowed"},
        {"metadata": {"attempt": "not-an-integer"}},
    ],
)
def test_denials_do_not_call_writer_or_change_store(writer, config, monkeypatch, changes):
    spy = Mock(wraps=writer.append_observation)
    monkeypatch.setattr(writer, "append_observation", spy)
    head = writer.head()
    with pytest.raises(AdmissionRejected):
        ObservationAdmission(writer, (make_policy(),)).admit(
            CONTEXT, admitted_observation(**changes)
        )
    spy.assert_not_called()
    assert writer.head() == head
    assert writer.state.appended == writer.state.rejected == writer.state.failed == 0
    assert verify_database(config.db_path).intact


@pytest.mark.parametrize("point", ["after_insert", "before_commit"])
def test_failed_transaction_never_returns_receipt_and_can_be_retried(config, point):
    with EvidenceWriter(config) as writer:
        admission = ObservationAdmission(writer, (make_policy(),))
        first = admission.admit(CONTEXT, admitted_observation())

        def fail(at):
            if at == point:
                raise sqlite3.OperationalError("simulated I/O failure")

        writer._fault_hook = fail
        with pytest.raises(EvidenceWriteError) as caught:
            admission.admit(CONTEXT, admitted_observation(2))
        assert caught.value.failure_class == "OperationalError"
        assert writer.head().head_hash == first.current_hash
        assert writer.state.failed == writer.state.consecutive_failures == 1
        report = verify_database(config.db_path, config.case_id)
        assert report.case(config.case_id).record_count == 1
        writer._fault_hook = None
        second = admission.admit(CONTEXT, admitted_observation(2))
        assert second.sequence == 2 and writer.state.consecutive_failures == 0
    assert verify_database(config.db_path).intact


def test_actual_commit_failure_rolls_back_without_receipt_and_recovers(config):
    with EvidenceWriter(config) as writer:
        admission = ObservationAdmission(writer, (make_policy(),))
        first = admission.admit(CONTEXT, admitted_observation())
        head = writer.head()
        conn = writer._conn
        transactions = []

        def authorize(operation, argument, _second, _database, _trigger):
            if operation == sqlite3.SQLITE_TRANSACTION:
                transactions.append(argument)
                if argument == "COMMIT":
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        conn.set_authorizer(authorize)
        receipt = None
        try:
            with pytest.raises(EvidenceWriteError) as caught:
                receipt = admission.admit(CONTEXT, admitted_observation(2))
            assert receipt is None
            assert transactions == ["BEGIN", "COMMIT", "ROLLBACK"]
            assert caught.value.failure_class == "DatabaseError"
            assert str(caught.value) == (
                "evidence write failed (DatabaseError); record NOT persisted"
            )
            assert caught.value.__cause__ is None and caught.value.__suppress_context__
            assert "not authorized" not in "".join(traceback.format_exception(caught.value))
            assert not conn.in_transaction
            assert writer.head() == head
            assert writer.state.appended == 1
            assert writer.state.failed == writer.state.consecutive_failures == 1
            with closing(sqlite3.connect(str(config.db_path))) as reader:
                rows = reader.execute(
                    "SELECT event_id, current_hash FROM evidence_records ORDER BY sequence"
                ).fetchall()
            assert rows == [(first.event_id, first.current_hash)]
        finally:
            # A callable reset also supports Python 3.10's authorizer API.
            conn.set_authorizer(lambda *_args: sqlite3.SQLITE_OK)

        second = admission.admit(CONTEXT, admitted_observation(2))
        assert second.sequence == 2 and second.previous_hash == first.current_hash
        assert writer.state.consecutive_failures == 0
    assert writer._conn is None and not writer.state.open
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        conn.execute("SELECT 1")
    report = verify_database(config.db_path, config.case_id)
    assert report.intact and report.case(config.case_id).record_count == 2


def test_duplicate_id_remains_explicit_writer_rejection(writer):
    admission = ObservationAdmission(writer, (make_policy(),))
    first = admission.admit(CONTEXT, admitted_observation())
    with pytest.raises(RecordRejected) as caught:
        admission.admit(CONTEXT, admitted_observation())
    assert caught.value.category == "duplicate_event_id"
    assert writer.head().count == 1 and writer.head().head_hash == first.current_hash


def test_closed_writer_never_produces_success(config):
    with pytest.raises(EvidenceWriteError, match="writer_not_open"):
        ObservationAdmission(EvidenceWriter(config), (make_policy(),)).admit(
            CONTEXT, admitted_observation()
        )
    assert not config.db_path.exists()


def test_read_only_write_failure_is_not_acknowledged(writer, config):
    writer._conn.execute("PRAGMA query_only = ON")
    with pytest.raises(EvidenceWriteError):
        ObservationAdmission(writer, (make_policy(),)).admit(CONTEXT, admitted_observation())
    assert writer.head().count == 0 and writer.state.failed == 1
    assert verify_database(config.db_path).intact


def test_busy_database_failure_is_not_acknowledged(config):
    config = replace(config, sqlite_busy_timeout_ms=100)
    with EvidenceWriter(config) as writer:
        locker = sqlite3.connect(str(config.db_path), isolation_level=None)
        try:
            locker.execute("BEGIN IMMEDIATE")
            with pytest.raises(EvidenceWriteError):
                ObservationAdmission(writer, (make_policy(),)).admit(
                    CONTEXT, admitted_observation()
                )
        finally:
            locker.execute("ROLLBACK")
            locker.close()
        assert writer.head().count == 0 and writer.state.failed == 1
    assert verify_database(config.db_path).intact


def test_envelope_size_limit_remains_writer_owned(config):
    config = replace(config, max_record_bytes=1024)
    counters = {f"counter_{n:02}": 2**53 - 1 for n in range(32)}
    policy = make_policy(metadata_counters=frozenset(counters))
    with EvidenceWriter(config) as writer:
        with pytest.raises(RecordRejected) as caught:
            ObservationAdmission(writer, (policy,)).admit(
                CONTEXT, admitted_observation(metadata=counters)
            )
        assert caught.value.category == "record_too_large"
        assert writer.head().count == 0


def test_sqlite_full_keeps_only_committed_receipts(config):
    with EvidenceWriter(config) as writer:
        pages = writer._conn.execute("PRAGMA page_count").fetchone()[0]
        writer._conn.execute(f"PRAGMA max_page_count = {pages + 1}")
        admission = ObservationAdmission(writer, (make_policy(),))
        receipts = []
        with pytest.raises(EvidenceWriteError):
            for n in range(1, 1000):
                receipts.append(admission.admit(CONTEXT, admitted_observation(n)))
        assert writer.head().count == len(receipts)
        assert writer.state.failed == 1
    report = verify_database(config.db_path, config.case_id)
    assert report.intact and report.case(config.case_id).record_count == len(receipts)
