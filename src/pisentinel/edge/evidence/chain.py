"""SHA-256 hash chain primitives (chain format v1, guide section 13.1).

``current_hash = SHA256(canonical_event_json_bytes || ASCII(previous_hash)).hexdigest()``

The genesis record's ``previous_hash`` is 64 ASCII zeroes. Hash fields are never part of the
hashed content. This is an unkeyed integrity chain, not a signature: see
``docs/EVIDENCE_CHAIN.md`` for what it can and cannot show.
"""

from __future__ import annotations

import hashlib
import re

CHAIN_FORMAT = "pisentinel.chain.v1"
GENESIS_PREVIOUS_HASH = "0" * 64
HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def is_valid_hash(value: object) -> bool:
    """True for a lowercase 64-character hexadecimal SHA-256 digest string."""
    return isinstance(value, str) and HASH_PATTERN.match(value) is not None


def compute_record_hash(canonical_json: bytes, previous_hash: str) -> str:
    """Compute a record's ``current_hash`` from its canonical bytes and the previous hash."""
    if not isinstance(canonical_json, (bytes, bytearray)):
        raise TypeError("canonical_json must be bytes")
    if not is_valid_hash(previous_hash):
        raise ValueError("previous_hash must be 64 lowercase hexadecimal characters")
    return hashlib.sha256(bytes(canonical_json) + previous_hash.encode("ascii")).hexdigest()
