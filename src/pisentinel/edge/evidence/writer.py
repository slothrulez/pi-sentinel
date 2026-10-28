"""Single serialized, transactional evidence writer (PS-E01/PS-E02, ARCHITECTURE.md section 3).

Each append runs in one ``BEGIN IMMEDIATE`` transaction: read the case head, validate, compute
the hash, insert, commit. A receipt is returned only after ``COMMIT`` succeeds. A thread lock
serializes callers within a process; SQLite's write lock serializes processes, so concurrent
writers cannot fork the chain. Any failure rolls back and is counted and logged by category.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pisentinel.config import Config
from pisentinel.edge import db
from pisentinel.edge.evidence.canonical import CanonicalizationError, canonical_bytes
from pisentinel.edge.evidence.chain import (
    CHAIN_FORMAT,
    GENESIS_PREVIOUS_HASH,
    compute_record_hash,
)
from pisentinel.edge.schema import (
    OBSERVATION,
    ValidationError,
    build_derived_body,
    build_observation_body,
    format_utc,
)
from pisentinel.safe_logging import log_event

LOGGER = logging.getLogger("pisentinel.edge.writer")


class RecordRejected(ValueError):
    """Input was refused before persistence (validation, size, duplicate, bad reference)."""

    def __init__(self, category: str, detail: str = "") -> None:
        self.category = category
        super().__init__(f"{category}: {detail}" if detail else category)


class EvidenceWriteError(RuntimeError):
    """Persistence failed; nothing was acknowledged. ``failure_class`` is safe to log."""

    def __init__(self, failure_class: str) -> None:
        self.failure_class = failure_class
        super().__init__(f"evidence write failed ({failure_class}); record NOT persisted")


@dataclass(frozen=True)
class AppendReceipt:
    case_id: str
    sequence: int
    record_type: str
    event_id: str
    previous_hash: str
    current_hash: str


@dataclass(frozen=True)
class ChainHead:
    case_id: str
    count: int
    last_sequence: int
    head_hash: str


@dataclass
class WriterState:
    open: bool = False
    appended: int = 0
    rejected: int = 0
    failed: int = 0
    consecutive_failures: int = 0
    last_failure_class: str | None = None
    last_failure_at: str | None = None
    rejections_by_category: dict[str, int] = field(default_factory=dict)


FaultHook = Callable[[str], None]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceWriter:
    """Owns the evidence database connection; the only component that appends records."""

    def __init__(
        self,
        config: Config,
        *,
        clock: Callable[[], datetime] = _utc_now,
        fault_hook: FaultHook | None = None,
    ) -> None:
        self.config = config
        self.case_id = config.case_id
        self._clock = clock
        self._fault_hook = fault_hook
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self.state = WriterState()

    # -- lifecycle -------------------------------------------------------------------------
    def open(self) -> EvidenceWriter:
        with self._lock:
            if self._conn is not None:
                return self
            try:
                db.prepare_db_file(self.config.db_path)
                conn = db.connect(self.config.db_path, self.config.sqlite_busy_timeout_ms)
                try:
                    db.migrate(conn)
                except BaseException:
                    conn.close()
                    raise
            except (OSError, sqlite3.Error, db.SchemaError) as exc:
                self._record_failure("open_" + type(exc).__name__)
                raise EvidenceWriteError("open_" + type(exc).__name__) from exc
            self._conn = conn
            self.state.open = True
        log_event(LOGGER, logging.INFO, "writer_opened", case_id=self.case_id)
        return self

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
            self.state.open = False

    def __enter__(self) -> EvidenceWriter:
        return self.open()

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- queries ---------------------------------------------------------------------------
    def head(self) -> ChainHead:
        with self._lock:
            conn = self._require_conn()
            return self._read_head(conn)

    def _read_head(self, conn: sqlite3.Connection) -> ChainHead:
        row = conn.execute(
            "SELECT COUNT(*), MAX(sequence) FROM evidence_records WHERE case_id = ?",
            (self.case_id,),
        ).fetchone()
        count, last = int(row[0]), int(row[1] or 0)
        head_hash = GENESIS_PREVIOUS_HASH
        if last:
            head_hash = conn.execute(
                "SELECT current_hash FROM evidence_records WHERE case_id = ? AND sequence = ?",
                (self.case_id, last),
            ).fetchone()[0]
        return ChainHead(self.case_id, count, last, head_hash)

    # -- appends ---------------------------------------------------------------------------
    def append_observation(self, raw: Mapping[str, Any]) -> AppendReceipt:
        """Validate, privacy-filter and durably append a raw observation."""
        try:
            body = build_observation_body(raw)
        except ValidationError as exc:
            self._record_rejection("invalid_observation", field_name=exc.field, reason=exc.reason)
            raise RecordRejected("invalid_observation", f"{exc.field}: {exc.reason}") from None
        return self._append(OBSERVATION, body["event_id"], body, ())

    def append_derived(
        self,
        record_type: str,
        refers_to: Sequence[str],
        data: Mapping[str, Any],
        record_id: str | None = None,
    ) -> AppendReceipt:
        """Append a derived record referencing already-committed records (never rewriting them)."""
        try:
            body = build_derived_body(record_type, refers_to, data)
        except ValidationError as exc:
            self._record_rejection("invalid_derived", field_name=exc.field, reason=exc.reason)
            raise RecordRejected("invalid_derived", f"{exc.field}: {exc.reason}") from None
        rid = record_id or f"REC-{uuid.uuid4().hex}"
        return self._append(record_type, rid, body, tuple(body["refers_to"]))

    def _append(
        self, record_type: str, event_id: str, body: dict[str, Any], refers_to: tuple[str, ...]
    ) -> AppendReceipt:
        with self._lock:
            conn = self._require_conn()
            try:
                conn.execute("BEGIN IMMEDIATE")
                receipt = self._append_in_transaction(conn, record_type, event_id, body, refers_to)
                self._fault("before_commit")
                conn.execute("COMMIT")
            except RecordRejected as exc:
                self._rollback(conn)
                self._record_rejection(exc.category)
                raise
            except BaseException as exc:
                self._rollback(conn)
                failure_class = type(exc).__name__
                self._record_failure(failure_class)
                if isinstance(exc, (sqlite3.Error, OSError)):
                    raise EvidenceWriteError(failure_class) from exc
                raise
            self.state.appended += 1
            self.state.consecutive_failures = 0
        log_event(
            LOGGER,
            logging.DEBUG,
            "record_appended",
            case_id=receipt.case_id,
            sequence=receipt.sequence,
            record_type=record_type,
        )
        return receipt

    def _append_in_transaction(
        self,
        conn: sqlite3.Connection,
        record_type: str,
        event_id: str,
        body: dict[str, Any],
        refers_to: tuple[str, ...],
    ) -> AppendReceipt:
        head = self._read_head(conn)
        exists = conn.execute(
            "SELECT 1 FROM evidence_records WHERE case_id = ? AND event_id = ?",
            (self.case_id, event_id),
        ).fetchone()
        if exists:
            raise RecordRejected("duplicate_event_id")
        for ref in refers_to:
            found = conn.execute(
                "SELECT 1 FROM evidence_records WHERE case_id = ? AND event_id = ?",
                (self.case_id, ref),
            ).fetchone()
            if not found:
                raise RecordRejected("unknown_reference")
        sequence = head.last_sequence + 1
        recorded_at = format_utc(self._clock())
        payload = {
            "chain_format": CHAIN_FORMAT,
            "case_id": self.case_id,
            "sequence": sequence,
            "record_type": record_type,
            "event_id": event_id,
            "recorded_at": recorded_at,
            "body": body,
        }
        try:
            content = canonical_bytes(payload)
        except CanonicalizationError:
            raise RecordRejected("not_canonicalizable") from None
        if len(content) > self.config.max_record_bytes:
            raise RecordRejected("record_too_large", f"limit {self.config.max_record_bytes} bytes")
        current_hash = compute_record_hash(content, head.head_hash)
        conn.execute(
            "INSERT INTO evidence_records (case_id, sequence, record_type, event_id, "
            "recorded_at, canonical_json, previous_hash, current_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                self.case_id,
                sequence,
                record_type,
                event_id,
                recorded_at,
                content,
                head.head_hash,
                current_hash,
            ),
        )
        self._fault("after_insert")
        return AppendReceipt(
            self.case_id, sequence, record_type, event_id, head.head_hash, current_hash
        )

    # -- helpers ---------------------------------------------------------------------------
    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._record_failure("writer_not_open")
            raise EvidenceWriteError("writer_not_open")
        return self._conn

    def _fault(self, point: str) -> None:
        if self._fault_hook is not None:
            self._fault_hook(point)

    @staticmethod
    def _rollback(conn: sqlite3.Connection) -> None:
        try:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass

    def _record_rejection(self, category: str, **fields: Any) -> None:
        self.state.rejected += 1
        counts = self.state.rejections_by_category
        counts[category] = counts.get(category, 0) + 1
        log_event(LOGGER, logging.WARNING, "record_rejected", category=category, **fields)

    def _record_failure(self, failure_class: str) -> None:
        self.state.failed += 1
        self.state.consecutive_failures += 1
        self.state.last_failure_class = failure_class
        self.state.last_failure_at = format_utc(_utc_now())
        log_event(
            LOGGER,
            logging.ERROR,
            "evidence_write_failed",
            failure_class=failure_class,
            persisted=False,
        )
