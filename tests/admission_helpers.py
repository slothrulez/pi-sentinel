"""Explicit synthetic policies/observations for in-process admission tests; no traffic."""

from dataclasses import replace

from pisentinel.edge.collector.ingest import ProducerPolicy, TrustedProducerContext
from tests.conftest import observation

CONTEXT = TrustedProducerContext("synthetic-auth")


def make_policy(**changes):
    policy = ProducerPolicy(
        producer_id="synthetic-auth",
        source_networks=("10.10.0.20/32", "2001:db8::/32"),
        destination_service="ssh",
        event_types=frozenset({"auth_failure"}),
        actions=frozenset({"login_attempt"}),
        metadata_counters=frozenset({"attempt"}),
        discard_metadata=frozenset({"username", "password", "headers", "note", "command", "path"}),
    )
    return replace(policy, **changes)


def admitted_observation(n=1, **changes):
    return observation(n, **{"metadata": {"attempt": n}, **changes})
