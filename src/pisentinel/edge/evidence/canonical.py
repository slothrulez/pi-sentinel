"""Canonical JSON serialization for evidence records (chain format v1).

Rules (frozen by the known-byte vectors in ``tests/vectors/chain_v1``):

* UTF-8 output, no BOM, no insignificant whitespace (separators ``,`` and ``:``).
* Object keys are ASCII ``[a-z][a-z0-9_]{0,63}`` and are emitted in byte order, which for this
  key alphabet is identical to Unicode code point and UTF-16 code unit order.
* Allowed values: object, array, string, integer, ``true``, ``false``, ``null``.
* Floats, NaN and Infinity are rejected (no ambiguous number representation). Integers must lie
  within the IEEE-754 safe range ``[-(2**53 - 1), 2**53 - 1]``; booleans are not integers.
* Strings must be valid Unicode scalar sequences (lone surrogates are rejected). Non-ASCII text
  is emitted as raw UTF-8. Only ``"``, ``\\`` and U+0000..U+001F are escaped, using the short
  escapes ``\\b \\f \\n \\r \\t`` where defined and lowercase ``\\u00xx`` otherwise. Text is not
  Unicode-normalized: different code point sequences produce different bytes.
* Nesting depth is bounded.

Parsing (``parse_canonical``) rejects duplicate keys, floats, NaN/Infinity and any input whose
re-serialization differs from the supplied bytes.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

MAX_SAFE_INTEGER = 2**53 - 1
MAX_DEPTH = 8
KEY_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented canonically. Messages never include values."""


def _check(value: Any, depth: int, path: str) -> None:
    if depth > MAX_DEPTH:
        raise CanonicalizationError(f"nesting deeper than {MAX_DEPTH} at {path}")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise CanonicalizationError(f"integer outside safe range at {path}")
        return
    if isinstance(value, float):
        raise CanonicalizationError(f"floating-point number not permitted at {path}")
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            raise CanonicalizationError(f"invalid Unicode (surrogate) at {path}") from None
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or not KEY_PATTERN.match(key):
                raise CanonicalizationError(f"invalid object key at {path}")
            _check(item, depth + 1, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for index, item in enumerate(value):
            _check(item, depth + 1, f"{path}[{index}]")
        return
    raise CanonicalizationError(f"unsupported type {type(value).__name__} at {path}")


def canonical_bytes(value: Any) -> bytes:
    """Return the canonical UTF-8 JSON encoding of ``value``."""
    _check(value, 0, "$")
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return text.encode("utf-8")


def _reject_constant(name: str) -> Any:
    raise CanonicalizationError("NaN/Infinity not permitted")


def _reject_float(text: str) -> Any:
    raise CanonicalizationError("floating-point number not permitted")


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise CanonicalizationError("duplicate object key")
        result[key] = item
    return result


def parse_canonical(data: bytes) -> Any:
    """Parse canonical bytes, rejecting anything that is not exactly canonical."""
    if not isinstance(data, (bytes, bytearray)):
        raise CanonicalizationError("canonical data must be bytes")
    data = bytes(data)
    if data.startswith(b"\xef\xbb\xbf"):
        raise CanonicalizationError("byte order mark not permitted")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise CanonicalizationError("not valid UTF-8") from None
    try:
        value = json.loads(
            text,
            object_pairs_hook=_no_duplicates,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except CanonicalizationError:
        raise
    except (ValueError, RecursionError):
        raise CanonicalizationError("not valid JSON") from None
    if canonical_bytes(value) != data:
        raise CanonicalizationError("bytes are not in canonical form")
    return value
