import pytest

from pisentinel.edge.schema import (
    EVENT_SCHEMA_VERSION,
    MAX_METADATA_STRING_CHARS,
    MAX_USERNAME_CHARS,
    ValidationError,
    build_derived_body,
    build_observation_body,
)
from tests.conftest import observation


def test_guide_section_9_example_maps_to_observation_body():
    body = build_observation_body(
        observation(231, event_id="EVT-000231", metadata={"username": "admin"})
    )
    assert body["schema_version"] == EVENT_SCHEMA_VERSION
    assert body["event_id"] == "EVT-000231"
    assert body["timestamp"] == "2026-09-16T14:22:01+05:30"
    assert body["timestamp_utc"] == "2026-09-16T08:52:01.000000Z"
    assert body["metadata"] == {"username": "admin"}
    for key in (
        "source_ip",
        "destination_service",
        "event_type",
        "action",
        "session_id",
        "severity",
    ):
        assert key in body
    for derived in (
        "previous_hash",
        "current_hash",
        "model_label",
        "confidence",
        "shap_summary",
        "response_action",
    ):
        assert derived not in body


def test_ipv6_is_normalized_and_z_suffix_accepted():
    body = build_observation_body(
        observation(1, source_ip="2001:DB8:0:0::1", timestamp="2026-09-16T08:00:00.5Z")
    )
    assert body["source_ip"] == "2001:db8::1"
    assert body["timestamp_utc"] == "2026-09-16T08:00:00.500000Z"


def test_credentials_are_discarded_and_counted():
    body = build_observation_body(
        observation(
            1,
            metadata={
                "username": "root",
                "password": "hunter2",
                "api_key": "k",
                "session_cookie": "c",
                "headers": {"authorization": "Basic Zm9vOmJhcg==", "user_agent": "curl"},
                "command": "Bearer abcdefghijklmnop",
                "note": "fine",
            },
        )
    )
    meta = body["metadata"]
    assert set(meta) == {"username", "headers", "command", "note"}
    assert meta["headers"] == {"user_agent": "curl"}
    assert meta["command"] is None
    assert body["discarded_sensitive_values"] == 5


@pytest.mark.parametrize(
    "overrides,field",
    [
        ({"event_id": ""}, "event_id"),
        ({"event_id": "x" * 65}, "event_id"),
        ({"event_id": "EVT 1"}, "event_id"),
        ({"timestamp": "2026-09-16T14:22:01"}, "timestamp"),
        ({"timestamp": "2026-13-16T14:22:01Z"}, "timestamp"),
        ({"timestamp": "yesterday"}, "timestamp"),
        ({"timestamp": 1700000000}, "timestamp"),
        ({"source_ip": "999.1.1.1"}, "source_ip"),
        ({"source_ip": "example.com"}, "source_ip"),
        ({"destination_service": "SSH"}, "destination_service"),
        ({"event_type": "auth failure"}, "event_type"),
        ({"action": "x" * 65}, "action"),
        ({"severity": "urgent"}, "severity"),
        ({"session_id": "S/1"}, "session_id"),
        ({"source_port": 0}, "source_port"),
        ({"destination_port": 70000}, "destination_port"),
        ({"destination_port": True}, "destination_port"),
        ({"metadata": []}, "metadata"),
        ({"metadata": {"score": 0.5}}, "metadata.score"),
        ({"metadata": {"score": float("nan")}}, "metadata.score"),
        ({"metadata": {"n": 2**60}}, "metadata.n"),
        ({"metadata": {"Bad-Key": 1}}, "metadata"),
        ({"metadata": {"username": "u" * (MAX_USERNAME_CHARS + 1)}}, "metadata.username"),
        ({"metadata": {"command": "c" * (MAX_METADATA_STRING_CHARS + 1)}}, "metadata.command"),
        ({"metadata": {"text": "\ud800"}}, "metadata.text"),
        ({"metadata": {"a": {"b": {"c": {"d": 1}}}}}, "metadata.a.b.c"),
        ({"metadata": {f"k{i}": i for i in range(33)}}, "metadata"),
        ({"metadata": {"items": list(range(33))}}, "metadata.items"),
        ({"unexpected": 1}, "observation"),
    ],
)
def test_invalid_observations_rejected(overrides, field):
    with pytest.raises(ValidationError) as info:
        build_observation_body(observation(1, **overrides))
    assert info.value.field == field


def test_missing_required_field():
    obs = observation(1)
    del obs["source_ip"]
    with pytest.raises(ValidationError) as info:
        build_observation_body(obs)
    assert info.value.field == "source_ip"


def test_unicode_text_is_preserved_not_normalized():
    body = build_observation_body(observation(1, metadata={"path": "/cafe\u0301/日本"}))
    assert body["metadata"]["path"] == "/cafe\u0301/日本"


def test_derived_body_validation():
    body = build_derived_body("assessment", ["EVT-1"], {"model_label": "x", "token": "t"})
    assert body["refers_to"] == ["EVT-1"] and body["data"] == {"model_label": "x"}
    assert body["discarded_sensitive_values"] == 1
    for args in [
        ("observation", ["EVT-1"], {}),
        ("assessment", [], {}),
        ("assessment", "EVT-1", {}),
        ("assessment", ["EVT-1", "EVT-1"], {}),
        ("assessment", ["EVT-1"], {"confidence": 0.91}),
    ]:
        with pytest.raises(ValidationError):
            build_derived_body(*args)
