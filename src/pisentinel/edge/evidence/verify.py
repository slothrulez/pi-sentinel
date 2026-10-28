"""Standalone evidence-chain verifier (PS-E03).

Depends only on the standard library plus ``canonical``/``chain`` (no writer code). Opens the
database read-only, recomputes every record hash from genesis, checks sequence, links, case
scope, canonical form, envelope/column agreement and reference ordering, and reports the first
broken record plus all affected descendants.

Without an independently retained checkpoint it cannot detect tail truncation or a fully
recomputed rewrite. See docs/EVIDENCE_CHAIN.md.

Usage::

    python -m pisentinel.edge.evidence.verify --db PATH [--case-id ID]
        [--checkpoint-sequence N --checkpoint-hash HEX] [--expected-count N]

Exit status: 0 intact, 1 broken/anchor mismatch, 2 usage or database error.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from pisentinel.edge.evidence.canonical import CanonicalizationError, parse_canonical
from pisentinel.edge.evidence.chain import (
    CHAIN_FORMAT,
    GENESIS_PREVIOUS_HASH,
    compute_record_hash,
    is_valid_hash,
)

VERIFIER_VERSION = "pisentinel.verify.v1"
MAX_REPORTED_FAILURES = 100
ENVELOPE_FIELDS = ("case_id", "sequence", "record_type", "event_id", "recorded_at")
LIMITATIONS = (
    "Unkeyed SHA-256 chain: not a signature; does not prove origin, completeness or "
    "legal admissibility.",
    "A party with write access can recompute the full chain; only an independently retained "
    "checkpoint (sequence + head hash) detects such a rewrite.",
    "Tail truncation (removal of the newest records) is undetectable without an independently "
    "retained expected count or checkpoint.",
    "A manifest or checkpoint stored beside the database is not independent anchoring.",
)


class VerifierError(RuntimeError):
    """The database could not be read as an evidence store."""


@dataclass
class Failure:
    sequence: int | None
    event_id: str | None
    check: str
    detail: str


@dataclass
class CaseReport:
    case_id: str
    status: str = "intact"
    record_count: int = 0
    first_sequence: int | None = None
    last_sequence: int | None = None
    head_hash: str = GENESIS_PREVIOUS_HASH
    first_failure: Failure | None = None
    failures: list[Failure] = field(default_factory=list)
    failure_count: int = 0
    affected_event_ids: list[str] = field(default_factory=list)
    anchor: dict[str, Any] | None = None


@dataclass
class VerificationReport:
    verifier: str
    chain_format: str
    status: str
    cases: list[CaseReport]
    limitations: tuple[str, ...] = LIMITATIONS

    @property
    def intact(self) -> bool:
        return self.status == "intact"

    def case(self, case_id: str) -> CaseReport:
        for item in self.cases:
            if item.case_id == case_id:
                return item
        raise KeyError(case_id)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _open_readonly(path: Path) -> sqlite3.Connection:
    path = Path(path)
    if not path.is_file():
        raise VerifierError("database file not found")
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, isolation_level=None)
        conn.execute("PRAGMA query_only = ON")
        conn.execute(
            "SELECT case_id, sequence, record_type, event_id, recorded_at, canonical_json, "
            "previous_hash, current_hash FROM evidence_records LIMIT 0"
        )
    except sqlite3.Error as exc:
        raise VerifierError(f"not a readable evidence database ({type(exc).__name__})") from None
    return conn


class _CaseWalker:
    def __init__(self, case_id: str) -> None:
        self.report = CaseReport(case_id=case_id)
        self.expected_sequence = 1
        self.previous_hash = GENESIS_PREVIOUS_HASH
        self.seen_ids: set[str] = set()
        self.event_ids: list[str] = []
        self.hash_by_sequence: dict[int, str] = {}
        self.first_failure_index: int | None = None

    def fail(self, sequence: Any, event_id: Any, check: str, detail: str) -> None:
        rep = self.report
        failure = Failure(
            sequence if isinstance(sequence, int) else None,
            event_id if isinstance(event_id, str) else None,
            check,
            detail,
        )
        rep.failure_count += 1
        if len(rep.failures) < MAX_REPORTED_FAILURES:
            rep.failures.append(failure)
        if rep.first_failure is None:
            rep.first_failure = failure
            self.first_failure_index = len(self.event_ids) - 1

    def visit(self, row: tuple[Any, ...]) -> None:
        case_id, sequence, record_type, event_id, recorded_at, content, prev, current = row
        self.event_ids.append(str(event_id))
        rep = self.report
        rep.record_count += 1
        if rep.first_sequence is None:
            rep.first_sequence = sequence
        rep.last_sequence = sequence

        if sequence != self.expected_sequence:
            kind = "sequence_gap" if isinstance(sequence, int) else "sequence_type"
            if isinstance(sequence, int) and sequence < self.expected_sequence:
                kind = "sequence_duplicate"
            self.fail(sequence, event_id, kind, f"expected sequence {self.expected_sequence}")
        if not is_valid_hash(prev):
            self.fail(sequence, event_id, "invalid_previous_hash", "not 64 lowercase hex chars")
        elif prev != self.previous_hash:
            self.fail(sequence, event_id, "link_mismatch", "previous_hash != prior current_hash")

        payload: Any = None
        if not isinstance(content, (bytes, bytearray)):
            self.fail(sequence, event_id, "content_type", "canonical_json is not a BLOB")
        else:
            try:
                payload = parse_canonical(bytes(content))
            except CanonicalizationError as exc:
                self.fail(sequence, event_id, "noncanonical_content", str(exc))
        if payload is not None:
            self._check_envelope(payload, row)

        if not is_valid_hash(current):
            self.fail(sequence, event_id, "invalid_hash", "not 64 lowercase hex chars")
        elif isinstance(content, (bytes, bytearray)):
            link = prev if is_valid_hash(prev) else self.previous_hash
            if compute_record_hash(bytes(content), link) != current:
                self.fail(sequence, event_id, "hash_mismatch", "recomputed hash differs")

        if event_id in self.seen_ids:
            self.fail(sequence, event_id, "duplicate_event_id", "event_id repeated in case")
        self.seen_ids.add(event_id)
        if isinstance(sequence, int):
            self.hash_by_sequence[sequence] = current
            self.expected_sequence = sequence + 1
        else:
            self.expected_sequence += 1
        self.previous_hash = current if is_valid_hash(current) else self.previous_hash
        rep.head_hash = current if isinstance(current, str) else rep.head_hash

    def _check_envelope(self, payload: Any, row: tuple[Any, ...]) -> None:
        case_id, sequence, record_type, event_id = row[0], row[1], row[2], row[3]
        if not isinstance(payload, dict):
            self.fail(sequence, event_id, "envelope_mismatch", "payload is not an object")
            return
        if payload.get("chain_format") != CHAIN_FORMAT:
            self.fail(sequence, event_id, "chain_format", "unsupported chain_format")
        for name, column in zip(ENVELOPE_FIELDS, row[:5], strict=True):
            if payload.get(name) != column:
                self.fail(sequence, event_id, "envelope_mismatch", f"{name} differs from column")
        if case_id != self.report.case_id:
            self.fail(sequence, event_id, "case_scope", "record outside case scope")
        body = payload.get("body")
        if not isinstance(body, dict):
            self.fail(sequence, event_id, "envelope_mismatch", "body is not an object")
            return
        if record_type == "observation":
            if body.get("event_id") != event_id:
                self.fail(sequence, event_id, "envelope_mismatch", "body event_id differs")
        else:
            refs = body.get("refers_to")
            if not isinstance(refs, list) or not refs:
                self.fail(sequence, event_id, "reference", "derived record lacks refers_to")
            else:
                for ref in refs:
                    if ref not in self.seen_ids:
                        self.fail(
                            sequence, event_id, "reference", "refers_to a later or missing record"
                        )
                        break

    def finish(self, checkpoint: tuple[int, str] | None, expected_count: int | None) -> CaseReport:
        rep = self.report
        if self.first_failure_index is not None:
            rep.affected_event_ids = self.event_ids[self.first_failure_index :]
        if checkpoint is not None or expected_count is not None:
            anchor: dict[str, Any] = {"independent_anchor_supplied": True}
            if checkpoint is not None:
                seq, expected_hash = checkpoint
                anchor["checkpoint_sequence"] = seq
                actual = self.hash_by_sequence.get(seq)
                if actual is None:
                    anchor["checkpoint_matched"] = False
                    self.fail(
                        seq,
                        None,
                        "anchor_missing_record",
                        "checkpoint sequence absent (truncation or deletion)",
                    )
                elif actual != expected_hash:
                    anchor["checkpoint_matched"] = False
                    self.fail(
                        seq,
                        None,
                        "anchor_hash_mismatch",
                        "head at checkpoint differs (rewrite or substitution)",
                    )
                    # Every record up to the checkpoint, and all descendants, is suspect.
                    rep.affected_event_ids = list(self.event_ids)
                else:
                    anchor["checkpoint_matched"] = True
            if expected_count is not None:
                anchor["expected_count"] = expected_count
                anchor["count_matched"] = rep.record_count == expected_count
                if rep.record_count != expected_count:
                    self.fail(
                        None,
                        None,
                        "anchor_count_mismatch",
                        f"found {rep.record_count} records, expected {expected_count}",
                    )
            rep.anchor = anchor
        if rep.failure_count:
            rep.status = "broken"
        return rep


def verify_database(
    path: Path | str,
    case_id: str | None = None,
    *,
    checkpoint: tuple[int, str] | None = None,
    expected_count: int | None = None,
) -> VerificationReport:
    """Verify every case (or one ``case_id``) in the evidence database at ``path``."""
    if (checkpoint is not None or expected_count is not None) and case_id is None:
        raise VerifierError("an anchor requires an explicit case_id")
    if checkpoint is not None and not is_valid_hash(checkpoint[1]):
        raise VerifierError("checkpoint hash must be 64 lowercase hex chars")
    conn = _open_readonly(Path(path))
    try:
        if case_id is None:
            case_ids = [
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT case_id FROM evidence_records ORDER BY case_id"
                )
            ]
        else:
            case_ids = [case_id]
        reports = []
        for cid in case_ids:
            walker = _CaseWalker(cid)
            rows = conn.execute(
                "SELECT case_id, sequence, record_type, event_id, recorded_at, canonical_json, "
                "previous_hash, current_hash FROM evidence_records WHERE case_id = ? "
                "ORDER BY sequence, rowid",
                (cid,),
            )
            for row in rows:
                walker.visit(row)
            reports.append(walker.finish(checkpoint, expected_count))
    except sqlite3.Error as exc:
        raise VerifierError(f"database read failed ({type(exc).__name__})") from None
    finally:
        conn.close()
    status = "broken" if any(r.status != "intact" for r in reports) else "intact"
    return VerificationReport(VERIFIER_VERSION, CHAIN_FORMAT, status, reports)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a PiSentinel evidence database.")
    parser.add_argument("--db", required=True, type=Path, help="SQLite evidence database")
    parser.add_argument("--case-id", help="verify only this case")
    parser.add_argument("--checkpoint-sequence", type=int, help="independently retained sequence")
    parser.add_argument("--checkpoint-hash", help="independently retained hash at that sequence")
    parser.add_argument("--expected-count", type=int, help="independently retained record count")
    args = parser.parse_args(argv)
    if (args.checkpoint_sequence is None) != (args.checkpoint_hash is None):
        parser.error("--checkpoint-sequence and --checkpoint-hash must be used together")
    checkpoint = None
    if args.checkpoint_sequence is not None:
        checkpoint = (args.checkpoint_sequence, args.checkpoint_hash)
    try:
        report = verify_database(
            args.db, args.case_id, checkpoint=checkpoint, expected_count=args.expected_count
        )
    except VerifierError as exc:
        print(json.dumps({"verifier": VERIFIER_VERSION, "status": "error", "error": str(exc)}))
        return 2
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.intact else 1


if __name__ == "__main__":
    sys.exit(main())
