# Evidence chain v1 (M1)

Implements guide §13.1 (p. 12) `current_hash = SHA256(canonical_event_json + previous_hash)` and the A09 proposal in [ARCHITECTURE.md](../ARCHITECTURE.md#hash-chain-format-a09-reviewfreezetest-at-m1). Code: `src/pisentinel/edge/evidence/`.

## Format

| Item | Rule |
|---|---|
| Scope | One chain per `case_id`; sequences start at 1 and increase by 1. Raw observations and derived records (`session_association`, `assessment`, `explanation`, `decision`, `result`, `closure`) share the case chain. |
| Hashed content | `{"chain_format":"pisentinel.chain.v1","case_id","sequence","record_type","event_id","recorded_at","body"}`. `previous_hash`/`current_hash` are never inside the content. |
| Canonical JSON | UTF-8, no BOM, separators `,` `:`, keys sorted; keys restricted to ASCII `[a-z][a-z0-9_]{0,63}` (so byte, code point and UTF-16 order agree). Strings raw UTF-8 except `"` `\` and U+0000-U+001F (short escapes `\b \f \n \r \t`, otherwise lowercase `\u00xx`); no Unicode normalization. Integers only, within ±(2^53-1); floats/NaN/Infinity rejected. Max depth 8. Parsing rejects duplicate keys and any non-canonical bytes. |
| Genesis | `previous_hash` = 64 ASCII `0`. |
| Hash | `current_hash = sha256(canonical_bytes + ascii(previous_hash))`, lowercase 64-hex. |
| Vectors | `tests/vectors/chain_v1/` frozen bytes; expected hashes computed with coreutils `sha256sum`, independent of Python `hashlib`. |

## Writer guarantees (tested)

- One `BEGIN IMMEDIATE` transaction reads the head, inserts and commits; the receipt is returned only after `COMMIT`. WAL + `synchronous=FULL`.
- In-process lock plus the SQLite write lock serialize writers; `UNIQUE(case_id, previous_hash)` and `PRIMARY KEY(case_id, sequence)` make a fork unrepresentable.
- Failure (I/O error, disk full, read-only, closed writer) rolls back, increments counters, marks health `unavailable` and raises `EvidenceWriteError` ("NOT persisted"). Validation/size/duplicate/reference problems raise `RecordRejected` before anything is written.
- Derived records may reference only already-committed records in the case; observation rows are never updated. Append-only triggers block accidental `UPDATE`/`DELETE` from application connections.
- Killing the process before commit leaves no half record; reopening recovers the committed head.

## Verifier

```sh
python -m pisentinel.edge.evidence.verify --db PATH [--case-id ID] \
    [--checkpoint-sequence N --checkpoint-hash HEX] [--expected-count N]
```

Read-only (`mode=ro`, `query_only`). Imports only `canonical`/`chain` and the standard library. Checks per record from genesis: sequence continuity, `previous_hash` format and link, canonical form, envelope/column agreement and case scope, `current_hash` format and recomputation, duplicate IDs, derived references to earlier records. Reports `first_failure`, up to 100 `failures`, and `affected_event_ids` (first broken record and every descendant). Exit 0 intact, 1 broken, 2 error. Failure details never echo record content.

## Limitations (do not overstate)

1. **Not a signature.** Unkeyed SHA-256 does not prove who wrote a record, completeness, legal admissibility, or access control. PS-OPT07 signatures are not implemented.
2. **Full-chain recomputation is undetectable on its own.** Anyone able to write the database can edit a record and recompute every later hash; the verifier then reports `intact` (`test_full_chain_recomputation_is_undetected_without_independent_anchor`). Only a checkpoint (sequence + head hash) retained somewhere the writer cannot modify exposes it.
3. **Tail truncation is undetectable on its own.** Deleting the newest records leaves a valid shorter chain (`test_tail_truncation_is_undetected_without_independent_anchor`). An independently retained checkpoint or expected count detects it.
4. **A checkpoint stored beside the database is not independent.** It can be rewritten together with the database. Where to retain checkpoints (analysis machine, offline media) is an open decision (A13/A14).
5. **Triggers are not a security boundary.** A privileged party can drop them; tests do exactly this to simulate tampering.
6. **Privacy filtering is pattern-based.** Credential key names and secret-shaped values are discarded before hashing, but unrecognised secrets in free text could still be persisted. Per-service metadata allowlists belong to M2 decoys.
7. **Never silently repair evidence.** A broken chain is reported, not fixed; corrections must be new records or a new case.
8. Copying a live WAL database file alone is not a safe backup; WAL-aware backup is not implemented in M1.
