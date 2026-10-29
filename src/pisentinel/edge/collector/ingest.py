"""Default-deny admission before the unchanged M1 evidence writer (M2-A PR1).

Host code constructs the producer context and immutable policies, never the observation payload.
This is not authentication or a sandbox against malicious code in the same process. A producer
is bound to one service and explicit source networks, event types and actions.

Metadata is projected onto explicitly allowlisted non-negative integer counters. Explicitly
allowlisted discard fields are removed without inspecting their values; unknown fields are rejected.
Free text/nesting is never retained by this boundary.
The M1 schema validates the projected observation before the writer is called. Envelope-size,
duplicate-ID and persistence checks remain the writer's responsibility. No retries are performed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network
from typing import Any

from pisentinel.edge.evidence.canonical import MAX_SAFE_INTEGER
from pisentinel.edge.evidence.writer import (
    AppendReceipt,
    EvidenceWriteError,
    EvidenceWriter,
    RecordRejected,
)
from pisentinel.edge.schema import (
    CREDENTIAL_KEY_PATTERN,
    ID_PATTERN,
    MAX_METADATA_KEYS,
    METADATA_KEY_PATTERN,
    OBSERVATION_FIELDS,
    SERVICE_PATTERN,
    TOKEN_PATTERN,
    build_observation_body,
)
from pisentinel.safe_logging import looks_like_secret

MAX_POLICIES = 32
MAX_POLICY_ITEMS = 32


class AdmissionRejected(ValueError):
    """Refusal before calling the writer; category contains no submitted values."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(f"observation admission rejected ({category})")


@dataclass(frozen=True, repr=False)
class TrustedProducerContext:
    """Caller-supplied host context, separate from untrusted observation fields."""

    producer_id: str


@dataclass(frozen=True, repr=False)
class ProducerPolicy:
    """One explicit producer/service policy; empty registry means deny all."""

    producer_id: str
    source_networks: tuple[str, ...]
    destination_service: str
    event_types: frozenset[str]
    actions: frozenset[str]
    metadata_counters: frozenset[str] = frozenset()
    discard_metadata: frozenset[str] = frozenset()
    _networks: tuple[IPv4Network | IPv6Network, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        valid = (
            type(self.producer_id) is str
            and ID_PATTERN.fullmatch(self.producer_id)
            and not looks_like_secret(self.producer_id)
            and type(self.destination_service) is str
            and SERVICE_PATTERN.fullmatch(self.destination_service)
            and type(self.source_networks) is tuple
            and 1 <= len(self.source_networks) <= MAX_POLICY_ITEMS
        )
        if not valid:
            raise ValueError("invalid admission policy")
        for values, minimum in (
            (self.event_types, 1),
            (self.actions, 1),
            (self.metadata_counters, 0),
            (self.discard_metadata, 0),
        ):
            if (
                type(values) is not frozenset
                or not minimum <= len(values) <= MAX_POLICY_ITEMS
                or any(type(v) is not str or not TOKEN_PATTERN.fullmatch(v) for v in values)
            ):
                raise ValueError("invalid admission policy")
        if any(CREDENTIAL_KEY_PATTERN.search(key) for key in self.metadata_counters):
            raise ValueError("invalid admission policy")
        if self.metadata_counters & self.discard_metadata:
            raise ValueError("invalid admission policy")
        networks = []
        for text in self.source_networks:
            if type(text) is not str or len(text) > 64 or "%" in text:
                raise ValueError("invalid admission policy")
            try:
                networks.append(ip_network(text, strict=True))
            except ValueError:
                raise ValueError("invalid admission policy") from None
        object.__setattr__(self, "_networks", tuple(networks))


class ObservationAdmission:
    """Validate/minimize, then return only the writer's committed receipt.

    Policies are supplied by trusted host code, not discovered from environment/input. The
    registry is snapshotted; duplicate producer IDs fail rather than override permissions.
    """

    def __init__(
        self,
        writer: EvidenceWriter,
        policies: tuple[ProducerPolicy, ...] | list[ProducerPolicy] = (),
    ) -> None:
        if type(policies) not in (tuple, list) or len(policies) > MAX_POLICIES:
            raise ValueError("invalid admission policy")
        self._policies: dict[str, ProducerPolicy] = {}
        for policy in policies:
            if type(policy) is not ProducerPolicy or policy.producer_id in self._policies:
                raise ValueError("invalid admission policy")
            self._policies[policy.producer_id] = policy
        self._writer = writer

    def admit(self, context: TrustedProducerContext, raw: object) -> AppendReceipt:
        """Reject invalid input without writer calls; persistence errors never become receipts."""
        if (
            type(context) is not TrustedProducerContext
            or type(context.producer_id) is not str
            or not ID_PATTERN.fullmatch(context.producer_id)
        ):
            raise AdmissionRejected("invalid_context")
        policy = self._policies.get(context.producer_id)
        if policy is None:
            raise AdmissionRejected("unauthorized_producer")
        if type(raw) is not dict:
            raise AdmissionRejected("invalid_observation")
        if any(type(key) is not str or key not in OBSERVATION_FIELDS for key in raw):
            raise AdmissionRejected("unexpected_field")
        candidate = raw.copy()
        candidate["metadata"] = self._metadata(policy, candidate.get("metadata", {}))
        if any(
            type(value) not in (str, int, type(None))
            for key, value in candidate.items()
            if key != "metadata"
        ):
            raise AdmissionRejected("invalid_observation")
        try:
            body = build_observation_body(candidate)
        except (ValueError, TypeError, OverflowError):
            raise AdmissionRejected("invalid_observation") from None
        if any(looks_like_secret(value) for value in body.values() if type(value) is str):
            raise AdmissionRejected("sensitive_value")
        if "%" in body["source_ip"]:
            raise AdmissionRejected("invalid_source")
        source = ip_address(body["source_ip"])
        if not any(source in network for network in policy._networks):
            raise AdmissionRejected("unauthorized_source")
        if body["destination_service"] != policy.destination_service:
            raise AdmissionRejected("disallowed_service")
        if body["event_type"] not in policy.event_types:
            raise AdmissionRejected("disallowed_event_type")
        if body["action"] not in policy.actions:
            raise AdmissionRejected("disallowed_action")
        normalized = {key: value for key, value in body.items() if key in OBSERVATION_FIELDS}
        try:
            return self._writer.append_observation(normalized)
        except EvidenceWriteError as exc:
            # Do not expose a chained SQLite/OSError message through the admission boundary.
            raise EvidenceWriteError(exc.failure_class) from None
        except RecordRejected as exc:
            raise RecordRejected(exc.category) from None

    @staticmethod
    def _metadata(policy: ProducerPolicy, metadata: Any) -> dict[str, int]:
        if type(metadata) is not dict or len(metadata) > MAX_METADATA_KEYS:
            raise AdmissionRejected("invalid_metadata")
        counters: dict[str, int] = {}
        for key in metadata:
            if type(key) is not str or not METADATA_KEY_PATTERN.fullmatch(key):
                raise AdmissionRejected("invalid_metadata")
            if key in policy.metadata_counters:
                value = metadata[key]
                if type(value) is not int or not 0 <= value <= MAX_SAFE_INTEGER:
                    raise AdmissionRejected("invalid_metadata")
                counters[key] = value
            elif key not in policy.discard_metadata:
                raise AdmissionRejected("unexpected_metadata")
        return counters
