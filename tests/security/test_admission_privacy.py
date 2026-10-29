import io
import sqlite3
import traceback
from unittest.mock import Mock

import pytest

from pisentinel.edge.collector.ingest import (
    AdmissionRejected,
    ObservationAdmission,
    TrustedProducerContext,
)
from pisentinel.edge.evidence.canonical import parse_canonical
from pisentinel.edge.evidence.verify import verify_database
from pisentinel.edge.evidence.writer import EvidenceWriteError, EvidenceWriter, RecordRejected
from pisentinel.safe_logging import configure_logging
from tests.admission_helpers import CONTEXT, admitted_observation, make_policy

CANARY = "M2-PR1-Prohibited-Canary-9f8e7d"


def database_bytes(config):
    return b"".join(
        path.read_bytes()
        for suffix in ("", "-wal", "-shm")
        if (path := config.db_path.with_name(config.db_path.name + suffix)).exists()
    )


def diagnostic_text(exc):
    return str(exc) + repr(exc) + "".join(traceback.format_exception(exc))


def test_sensitive_and_free_text_metadata_never_reaches_writer_or_store(config, monkeypatch):
    stream = io.StringIO()
    configure_logging("DEBUG", stream)
    with EvidenceWriter(config) as writer:
        spy = Mock(wraps=writer.append_observation)
        monkeypatch.setattr(writer, "append_observation", spy)
        receipt = ObservationAdmission(writer, (make_policy(),)).admit(
            CONTEXT,
            admitted_observation(
                metadata={
                    "attempt": 1,
                    "password": CANARY,
                    "headers": {"authorization": CANARY, "cookie": CANARY},
                    "username": CANARY,
                    "note": CANARY,
                    "command": CANARY,
                    "path": CANARY,
                }
            ),
        )
        assert spy.call_args.args[0]["metadata"] == {"attempt": 1}
        assert CANARY not in repr(receipt)
        assert CANARY.encode() not in database_bytes(config)
    with sqlite3.connect(str(config.db_path)) as reader:
        content = reader.execute("SELECT canonical_json FROM evidence_records").fetchone()[0]
    payload = parse_canonical(content)
    assert payload["chain_format"] == "pisentinel.chain.v1"
    assert payload["body"]["schema_version"] == "pisentinel.event.v1"
    assert payload["body"]["metadata"] == {"attempt": 1}
    assert CANARY.encode() not in database_bytes(config)
    assert CANARY not in stream.getvalue()
    assert verify_database(config.db_path).intact


@pytest.mark.parametrize(
    "changes",
    [
        {"password": CANARY},
        {"event_id": CANARY + " !"},
        {"metadata": {"attempt": CANARY}},
        {"metadata": {CANARY: 1}},
        {"source_ip": CANARY},
    ],
)
def test_rejections_have_value_free_diagnostics(writer, config, changes):
    stream = io.StringIO()
    configure_logging("DEBUG", stream)
    with pytest.raises(AdmissionRejected) as caught:
        ObservationAdmission(writer, (make_policy(),)).admit(
            CONTEXT, admitted_observation(**changes)
        )
    assert CANARY not in diagnostic_text(caught.value)
    assert CANARY not in stream.getvalue()
    assert CANARY.encode() not in database_bytes(config)
    assert writer.head().count == 0


@pytest.mark.parametrize("field", ["event_id", "session_id"])
def test_recognized_secret_shapes_in_retained_identifiers_are_rejected(writer, field):
    secret = "ghp_" + "A" * 32
    with pytest.raises(AdmissionRejected) as caught:
        ObservationAdmission(writer, (make_policy(),)).admit(
            CONTEXT, admitted_observation(**{field: secret})
        )
    assert caught.value.category == "sensitive_value"
    assert secret not in diagnostic_text(caught.value)
    assert writer.head().count == 0


def test_explicitly_discarded_values_are_never_inspected_or_retained(writer, config):
    class DoNotInspect:
        def __repr__(self):
            raise AssertionError("discarded value inspected")

        __str__ = __repr__

    recursive = {}
    recursive["self"] = recursive
    policy = make_policy(discard_metadata=frozenset({"unknown", "recursive"}))
    ObservationAdmission(writer, (policy,)).admit(
        CONTEXT,
        admitted_observation(
            metadata={"attempt": 1, "unknown": DoNotInspect(), "recursive": recursive}
        ),
    )
    assert writer.head().count == 1 and verify_database(config.db_path).intact


def test_writer_error_chain_cannot_expose_database_error_text(config):
    stream = io.StringIO()
    configure_logging("DEBUG", stream)
    with EvidenceWriter(config) as writer:

        def fail(point):
            raise sqlite3.OperationalError(CANARY)

        writer._fault_hook = fail
        with pytest.raises(EvidenceWriteError) as caught:
            ObservationAdmission(writer, (make_policy(),)).admit(CONTEXT, admitted_observation())
        assert caught.value.failure_class == "OperationalError"
        assert CANARY not in diagnostic_text(caught.value)
        assert CANARY not in stream.getvalue()
        assert CANARY.encode() not in database_bytes(config)
        assert writer.head().count == 0


def test_writer_rejection_details_are_not_exposed():
    sink = Mock(spec=EvidenceWriter)
    sink.append_observation.side_effect = RecordRejected("duplicate_event_id", CANARY)
    with pytest.raises(RecordRejected) as caught:
        ObservationAdmission(sink, (make_policy(),)).admit(CONTEXT, admitted_observation())
    assert caught.value.category == "duplicate_event_id"
    assert CANARY not in diagnostic_text(caught.value)


def test_unexpected_programming_error_is_not_hidden_or_turned_into_receipt():
    sink = Mock(spec=EvidenceWriter)
    sink.append_observation.side_effect = RuntimeError("implementation fault")
    with pytest.raises(RuntimeError, match="implementation fault"):
        ObservationAdmission(sink, (make_policy(),)).admit(CONTEXT, admitted_observation())


def test_trusted_context_and_invalid_policy_do_not_echo_submitted_values():
    context = TrustedProducerContext(CANARY)
    assert CANARY not in repr(context)
    with pytest.raises(ValueError) as caught:
        make_policy(source_networks=(CANARY,))
    assert CANARY not in diagnostic_text(caught.value)
