from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from pisentinel.edge.collector.ingest import (
    AdmissionRejected,
    ObservationAdmission,
    TrustedProducerContext,
)
from pisentinel.edge.evidence.writer import AppendReceipt, EvidenceWriter
from tests.admission_helpers import CONTEXT, admitted_observation, make_policy


@pytest.fixture
def sink():
    return Mock(spec=EvidenceWriter)


@pytest.fixture
def admission(sink):
    return ObservationAdmission(sink, (make_policy(),))


def test_accepts_only_through_writer_and_returns_its_exact_receipt(admission, sink):
    receipt = AppendReceipt("CASE-TEST", 1, "observation", "EVT-000001", "0" * 64, "a" * 64)
    sink.append_observation.return_value = receipt
    raw = admitted_observation()
    assert admission.admit(CONTEXT, raw) is receipt
    sink.append_observation.assert_called_once_with(raw)
    sink.append_derived.assert_not_called()


def test_default_policy_denies_all(sink):
    with pytest.raises(AdmissionRejected, match="unauthorized_producer"):
        ObservationAdmission(sink).admit(CONTEXT, admitted_observation())
    sink.append_observation.assert_not_called()


@pytest.mark.parametrize(
    "context",
    [
        None,
        "synthetic-auth",
        {"producer_id": "synthetic-auth"},
        TrustedProducerContext("other"),
        TrustedProducerContext([]),
        TrustedProducerContext(""),
    ],
)
def test_requires_explicit_registered_context(sink, admission, context):
    with pytest.raises(AdmissionRejected):
        admission.admit(context, admitted_observation())
    sink.append_observation.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"source_ip": "10.10.0.21"},
        {"source_ip": "::ffff:10.10.0.20"},
        {"destination_service": "web"},
        {"event_type": "auth_success"},
        {"action": "execute_command"},
    ],
)
def test_out_of_policy_inputs_never_reach_writer(admission, sink, changes):
    with pytest.raises(AdmissionRejected):
        admission.admit(CONTEXT, admitted_observation(**changes))
    sink.append_observation.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"event_id": ""},
        {"event_id": "x" * 65},
        {"source_ip": "example.com"},
        {"source_ip": "2001:db8::1%eth0"},
        {"timestamp": "yesterday"},
        {"timestamp": "2026-01-01T00:00:00"},
        {"timestamp": "0001-01-01T00:00:00+23:00"},
        {"source_port": True},
        {"destination_port": 65536},
        {"severity": "urgent"},
        {"session_id": []},
        {"action": []},
        {"metadata": []},
        {"metadata": None},
        {"metadata": {"Bad-Key": 1}},
        {"metadata": {1: 1}},
        {"metadata": {f"k{i}": i for i in range(33)}},
        {"metadata": {"attempt": True}},
        {"metadata": {"attempt": -1}},
        {"metadata": {"attempt": 2**53}},
        {"metadata": {"attempt": 1.0}},
        {"metadata": {"attempt": float("nan")}},
        {"metadata": {"attempt": float("inf")}},
        {"metadata": {"attempt": "1"}},
        {"metadata": {"attempt": [1]}},
        {"metadata": {"attempt": {"value": 1}}},
        {"metadata": {"attempt": None}},
        {"metadata": {"unknown": 1}},
        {"unexpected": 1},
        {"producer_id": "synthetic-auth"},
        {"case_id": "CASE-FORGED"},
        {"previous_hash": "a" * 64},
        {"chain_format": "pisentinel.chain.v2"},
        {"schema_version": "pisentinel.event.v2"},
        {"record_type": "assessment"},
        {"refers_to": ["EVT-1"]},
        {"confidence": 10000},
        {"model_label": "credential_attack"},
    ],
)
def test_malformed_or_unexpected_input_never_reaches_writer(admission, sink, changes):
    with pytest.raises(AdmissionRejected):
        admission.admit(CONTEXT, admitted_observation(**changes))
    sink.append_observation.assert_not_called()


@pytest.mark.parametrize("raw", [None, [], "event", 1, {}, {1: "x"}])
def test_non_observations_never_reach_writer(admission, sink, raw):
    with pytest.raises(AdmissionRejected):
        admission.admit(CONTEXT, raw)
    sink.append_observation.assert_not_called()


def test_normalizes_ipv6_without_inferring_or_enriching(admission, sink):
    admission.admit(CONTEXT, admitted_observation(source_ip="2001:DB8:0:0::1"))
    actual = sink.append_observation.call_args.args[0]
    assert actual["source_ip"] == "2001:db8::1"
    assert "confidence" not in actual and "model_label" not in actual


def test_optional_fields_remain_optional(admission, sink):
    raw = admitted_observation()
    for field in ("metadata", "severity", "session_id"):
        raw.pop(field)
    admission.admit(CONTEXT, raw)
    actual = sink.append_observation.call_args.args[0]
    assert actual["metadata"] == {}
    assert "severity" not in actual and "session_id" not in actual


def test_upper_integer_and_port_boundaries_are_accepted(admission, sink):
    admission.admit(
        CONTEXT,
        admitted_observation(
            metadata={"attempt": 2**53 - 1}, source_port=1, destination_port=65535
        ),
    )
    actual = sink.append_observation.call_args.args[0]
    assert actual["metadata"] == {"attempt": 2**53 - 1}
    assert (actual["source_port"], actual["destination_port"]) == (1, 65535)


def test_policies_do_not_union_permissions_across_producers(sink):
    other = make_policy(producer_id="other", source_networks=("10.10.0.21/32",))
    admission = ObservationAdmission(sink, (make_policy(), other))
    raw = admitted_observation(source_ip="10.10.0.21")
    with pytest.raises(AdmissionRejected, match="unauthorized_source"):
        admission.admit(CONTEXT, raw)
    sink.append_observation.assert_not_called()
    admission.admit(TrustedProducerContext("other"), raw)
    sink.append_observation.assert_called_once()


@pytest.mark.parametrize("source", ["10.10.0.19", "10.10.0.24"])
def test_cidr_neighbors_are_not_implicitly_authorized(sink, source):
    policy = make_policy(source_networks=("10.10.0.20/30",))
    with pytest.raises(AdmissionRejected, match="unauthorized_source"):
        ObservationAdmission(sink, (policy,)).admit(CONTEXT, admitted_observation(source_ip=source))
    sink.append_observation.assert_not_called()


def test_metadata_is_minimized_to_explicit_integer_counters(admission, sink):
    raw = admitted_observation(metadata={"attempt": 0, "username": "admin", "note": "discard"})
    admission.admit(CONTEXT, raw)
    actual = sink.append_observation.call_args.args[0]
    assert actual["metadata"] == {"attempt": 0}
    assert actual is not raw and actual["metadata"] is not raw["metadata"]
    assert raw["metadata"] == {"attempt": 0, "username": "admin", "note": "discard"}


def test_no_counter_is_retained_without_explicit_allowlist(sink):
    policy = make_policy(metadata_counters=frozenset(), discard_metadata=frozenset({"attempt"}))
    ObservationAdmission(sink, (policy,)).admit(CONTEXT, admitted_observation())
    assert sink.append_observation.call_args.args[0]["metadata"] == {}


@pytest.mark.parametrize(
    "changes",
    [
        {"producer_id": ""},
        {"producer_id": []},
        {"destination_service": "SSH"},
        {"source_networks": ()},
        {"source_networks": ["10.10.0.20/32"]},
        {"source_networks": ("not-a-network",)},
        {"source_networks": ("10.10.0.20/24",)},
        {"source_networks": ("fe80::%eth0/64",)},
        {"source_networks": ("10.10.0.20/32",) * 33},
        {"event_types": frozenset()},
        {"event_types": {"auth_failure"}},
        {"event_types": frozenset({"Auth Failure"})},
        {"actions": frozenset()},
        {"actions": frozenset({"run shell"})},
        {"metadata_counters": frozenset({"password"})},
        {"metadata_counters": frozenset({"otp_value"})},
        {"metadata_counters": frozenset({"Bad-Key"})},
        {"discard_metadata": {"password"}},
        {"discard_metadata": frozenset({"Bad-Key"})},
        {"discard_metadata": frozenset({"attempt"})},
    ],
)
def test_invalid_policy_fails_closed(changes):
    with pytest.raises(ValueError, match="invalid admission policy"):
        make_policy(**changes)


def test_policy_registry_is_snapshotted_and_immutable(sink):
    policy = make_policy()
    policies = [policy]
    admission = ObservationAdmission(sink, policies)
    policies.clear()
    admission.admit(CONTEXT, admitted_observation())
    sink.append_observation.assert_called_once()
    with pytest.raises(FrozenInstanceError):
        policy.destination_service = "web"
    with pytest.raises(FrozenInstanceError):
        CONTEXT.producer_id = "other"


def test_duplicate_producer_policies_are_not_silently_overridden(sink):
    with pytest.raises(ValueError, match="invalid admission policy"):
        ObservationAdmission(sink, (make_policy(), make_policy()))


@pytest.mark.parametrize("policies", [(object(),), "not-policies", (make_policy(),) * 33])
def test_invalid_registry_is_rejected(sink, policies):
    with pytest.raises(ValueError, match="invalid admission policy"):
        ObservationAdmission(sink, policies)
