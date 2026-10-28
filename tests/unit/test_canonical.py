import hashlib
import json
import math

import pytest

from pisentinel.edge.evidence.canonical import (
    MAX_SAFE_INTEGER,
    CanonicalizationError,
    canonical_bytes,
    parse_canonical,
)
from pisentinel.edge.evidence.chain import (
    GENESIS_PREVIOUS_HASH,
    compute_record_hash,
    is_valid_hash,
)
from tests.conftest import REPO_ROOT

VECTORS = REPO_ROOT / "tests" / "vectors" / "chain_v1"


def load_vectors():
    inputs = json.loads((VECTORS / "inputs.json").read_text(encoding="utf-8"))["inputs"]
    expected = json.loads((VECTORS / "expected.json").read_text(encoding="utf-8"))
    return inputs, expected


def test_known_byte_vectors_match_canonical_bytes_and_independent_hashes():
    inputs, expected = load_vectors()
    assert expected["genesis_previous_hash"] == GENESIS_PREVIOUS_HASH
    previous = GENESIS_PREVIOUS_HASH
    for value, record in zip(inputs, expected["records"], strict=True):
        frozen = (VECTORS / record["file"]).read_bytes()
        assert canonical_bytes(value) == frozen
        assert parse_canonical(frozen) == value
        assert record["previous_hash"] == previous
        assert compute_record_hash(frozen, previous) == record["current_hash"]
        previous = record["current_hash"]


def test_vector_bytes_have_no_trailing_newline_or_bom():
    _, expected = load_vectors()
    for record in expected["records"]:
        data = (VECTORS / record["file"]).read_bytes()
        assert not data.endswith(b"\n") and not data.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in data


def test_hash_formula_is_sha256_of_content_then_ascii_previous_hash():
    content = b'{"a":1}'
    assert (
        compute_record_hash(content, GENESIS_PREVIOUS_HASH)
        == hashlib.sha256(content + b"0" * 64).hexdigest()
    )


def test_key_order_whitespace_and_unicode_rules():
    expected = '{"a":[true,null,"é"],"b":1}'.encode()
    assert canonical_bytes({"b": 1, "a": [True, None, "é"]}) == expected
    assert canonical_bytes({"a": "\n\t\x00\x1f\x7f"}) == b'{"a":"\\n\\t\\u0000\\u001f\x7f"}'
    assert canonical_bytes("😀") == '"😀"'.encode()


def test_deterministic_regardless_of_insertion_order():
    a = {"x": 1, "y": {"b": 2, "a": 3}}
    b = {"y": {"a": 3, "b": 2}, "x": 1}
    assert canonical_bytes(a) == canonical_bytes(b)


@pytest.mark.parametrize("value", [1.5, 0.0, math.nan, math.inf, -math.inf, {"a": 1.0}])
def test_rejects_floats_and_non_finite(value):
    with pytest.raises(CanonicalizationError):
        canonical_bytes(value)


@pytest.mark.parametrize("value", [MAX_SAFE_INTEGER + 1, -MAX_SAFE_INTEGER - 1, 10**30])
def test_rejects_unsafe_integers(value):
    with pytest.raises(CanonicalizationError):
        canonical_bytes(value)


@pytest.mark.parametrize(
    "value",
    [{"A": 1}, {"1a": 1}, {"a-b": 1}, {"é": 1}, {1: 2}, "\ud800", b"bytes", {"a": object()}],
)
def test_rejects_bad_keys_surrogates_and_types(value):
    with pytest.raises(CanonicalizationError):
        canonical_bytes(value)


def test_rejects_excess_depth():
    deep: object = 1
    for _ in range(10):
        deep = [deep]
    with pytest.raises(CanonicalizationError):
        canonical_bytes(deep)


@pytest.mark.parametrize(
    "data",
    [
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":1.0}',
        b'{"a":1e3}',
        b'{"b":1,"a":2}',
        b'{"a": 1}',
        b'\xef\xbb\xbf{"a":1}',
        b'{"a":"\\u00e9"}',
        b"\xff",
        b'{"a":1}\n',
        b"not json",
    ],
)
def test_parse_rejects_non_canonical_input(data):
    with pytest.raises(CanonicalizationError):
        parse_canonical(data)


def test_hash_validation():
    assert is_valid_hash("a" * 64)
    for bad in ["A" * 64, "a" * 63, "g" * 64, None, 1, "a" * 65]:
        assert not is_valid_hash(bad)
    with pytest.raises(ValueError):
        compute_record_hash(b"{}", "A" * 64)
    with pytest.raises(TypeError):
        compute_record_hash("{}", GENESIS_PREVIOUS_HASH)
