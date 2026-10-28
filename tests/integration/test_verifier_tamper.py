import hashlib
import json
import os
import subprocess
import sys

import pytest

from pisentinel.edge.evidence.canonical import canonical_bytes, parse_canonical
from pisentinel.edge.evidence.chain import GENESIS_PREVIOUS_HASH, compute_record_hash
from pisentinel.edge.evidence.verify import VerifierError, main, verify_database
from pisentinel.edge.evidence.writer import EvidenceWriter
from tests.conftest import REPO_ROOT, make_config, observation, raw_conn


@pytest.fixture
def chain(config):
    """Six-record case: five observations then one derived assessment."""
    with EvidenceWriter(config) as w:
        receipts = [w.append_observation(observation(n)) for n in range(1, 6)]
        receipts.append(
            w.append_derived(
                "assessment", ["EVT-000002"], {"model_label": "x"}, record_id="REC-000006"
            )
        )
    return config, receipts


def ids(receipts, start):
    return [r.event_id for r in receipts[start - 1 :]]


def report_for(config, **kw):
    return verify_database(config.db_path, config.case_id, **kw).case(config.case_id)


def rechain(conn, case_id, start):
    """Recompute every hash from ``start`` onward (privileged full rewrite)."""
    prev = (
        GENESIS_PREVIOUS_HASH
        if start == 1
        else conn.execute(
            "SELECT current_hash FROM evidence_records WHERE case_id=? AND sequence=?",
            (case_id, start - 1),
        ).fetchone()[0]
    )
    for seq, content in conn.execute(
        "SELECT sequence, canonical_json FROM evidence_records WHERE case_id=? AND sequence>=? "
        "ORDER BY sequence",
        (case_id, start),
    ).fetchall():
        new = compute_record_hash(content, prev)
        conn.execute(
            "UPDATE evidence_records SET previous_hash=?, current_hash=? "
            "WHERE case_id=? AND sequence=?",
            (prev, new, case_id, seq),
        )
        prev = new
    return prev


def edit_payload(conn, case_id, seq, mutate):
    content = conn.execute(
        "SELECT canonical_json FROM evidence_records WHERE case_id=? AND sequence=?", (case_id, seq)
    ).fetchone()[0]
    payload = parse_canonical(content)
    mutate(payload)
    conn.execute(
        "UPDATE evidence_records SET canonical_json=? WHERE case_id=? AND sequence=?",
        (canonical_bytes(payload), case_id, seq),
    )


def test_intact_chain_verifies(chain):
    config, receipts = chain
    rep = report_for(config)
    assert rep.status == "intact" and rep.record_count == 6
    assert rep.head_hash == receipts[-1].current_hash and rep.affected_event_ids == []


def test_content_modification_detected_with_affected_descendants(chain):
    config, receipts = chain
    conn = raw_conn(config)
    edit_payload(
        conn, config.case_id, 3, lambda p: p["body"]["metadata"].update(username="attacker")
    )
    rep = report_for(config)
    assert rep.status == "broken"
    assert (rep.first_failure.sequence, rep.first_failure.check) == (3, "hash_mismatch")
    assert rep.first_failure.event_id == "EVT-000003"
    assert rep.affected_event_ids == ids(receipts, 3)


def test_column_modification_detected(chain):
    config, _ = chain
    raw_conn(config).execute("UPDATE evidence_records SET record_type='closure' WHERE sequence=2")
    rep = report_for(config)
    assert (rep.first_failure.sequence, rep.first_failure.check) == (2, "envelope_mismatch")


def test_replaced_hash_breaks_record_and_next_link(chain):
    config, receipts = chain
    raw_conn(config).execute(
        "UPDATE evidence_records SET current_hash=? WHERE sequence=4", ("b" * 64,)
    )
    rep = report_for(config)
    checks = [(f.sequence, f.check) for f in rep.failures]
    assert checks[0] == (4, "hash_mismatch") and (5, "link_mismatch") in checks
    assert rep.affected_event_ids == ids(receipts, 4)


@pytest.mark.parametrize(
    "column,value,check",
    [
        ("current_hash", "A" * 64, "invalid_hash"),
        ("current_hash", "z" * 64, "invalid_hash"),
        ("previous_hash", "Z" * 64, "invalid_previous_hash"),
    ],
)
def test_invalid_hash_format_detected(chain, column, value, check):
    config, _ = chain
    raw_conn(config).execute(f"UPDATE evidence_records SET {column}=? WHERE sequence=2", (value,))
    rep = report_for(config)
    assert (rep.first_failure.sequence, rep.first_failure.check) == (2, check)


def test_interior_deletion_detected(chain):
    config, receipts = chain
    raw_conn(config).execute("DELETE FROM evidence_records WHERE sequence=3")
    rep = report_for(config)
    checks = {(f.sequence, f.check) for f in rep.failures}
    assert {(4, "sequence_gap"), (4, "link_mismatch")} <= checks
    assert rep.first_failure.event_id == "EVT-000004"
    assert rep.affected_event_ids == ids(receipts, 4)


def test_genesis_deletion_detected(chain):
    config, _ = chain
    raw_conn(config).execute("DELETE FROM evidence_records WHERE sequence=1")
    rep = report_for(config)
    assert rep.first_failure.sequence == 2 and rep.status == "broken"


def test_insertion_detected(chain):
    config, receipts = chain
    conn = raw_conn(config)
    for seq in range(6, 2, -1):
        conn.execute("UPDATE evidence_records SET sequence=sequence+1 WHERE sequence=?", (seq,))
    prev = receipts[1].current_hash
    payload = {
        "chain_format": "pisentinel.chain.v1",
        "case_id": config.case_id,
        "sequence": 3,
        "record_type": "observation",
        "event_id": "EVT-FORGED",
        "recorded_at": "2026-09-16T00:00:00.000000Z",
        "body": {"event_id": "EVT-FORGED"},
    }
    content = canonical_bytes(payload)
    forged_hash = compute_record_hash(content, prev)
    conn.execute("UPDATE evidence_records SET previous_hash=? WHERE sequence=4", (forged_hash,))
    conn.execute(
        "INSERT INTO evidence_records VALUES (?,3,'observation','EVT-FORGED',?,?,?,?)",
        (config.case_id, payload["recorded_at"], content, prev, forged_hash),
    )
    rep = report_for(config)
    assert rep.first_failure.sequence == 4 and rep.first_failure.event_id == "EVT-000003"
    assert {f.check for f in rep.failures} >= {"envelope_mismatch", "hash_mismatch"}


def test_reordering_detected(chain):
    config, receipts = chain
    conn = raw_conn(config)
    conn.execute("UPDATE evidence_records SET sequence=1000 WHERE sequence=2")
    conn.execute("UPDATE evidence_records SET sequence=2 WHERE sequence=3")
    conn.execute("UPDATE evidence_records SET sequence=3 WHERE sequence=1000")
    rep = report_for(config)
    assert rep.first_failure.sequence == 2 and rep.first_failure.event_id == "EVT-000003"
    assert {f.check for f in rep.failures} >= {"envelope_mismatch", "link_mismatch"}
    assert rep.affected_event_ids == ["EVT-000003", "EVT-000002"] + ids(receipts, 4)


def test_noncanonical_bytes_detected_even_with_matching_hash(chain):
    config, _ = chain
    conn = raw_conn(config)
    content, prev = conn.execute(
        "SELECT canonical_json, previous_hash FROM evidence_records WHERE sequence=6"
    ).fetchone()
    pretty = json.dumps(json.loads(content), indent=1).encode()
    conn.execute(
        "UPDATE evidence_records SET canonical_json=?, current_hash=? WHERE sequence=6",
        (pretty, compute_record_hash(pretty, prev)),
    )
    rep = report_for(config)
    assert (rep.first_failure.sequence, rep.first_failure.check) == (6, "noncanonical_content")


def test_derived_reference_to_later_record_detected(chain):
    config, _ = chain
    conn = raw_conn(config)
    edit_payload(conn, config.case_id, 6, lambda p: p["body"].update(refers_to=["EVT-999999"]))
    rechain(conn, config.case_id, 6)
    rep = report_for(config)
    assert (rep.first_failure.sequence, rep.first_failure.check) == (6, "reference")


def test_moving_record_to_another_case_detected(chain):
    config, _ = chain
    raw_conn(config).execute("UPDATE evidence_records SET case_id='OTHER' WHERE sequence=5")
    report = verify_database(config.db_path)
    assert report.status == "broken"
    assert report.case("OTHER").first_failure.check == "sequence_gap"
    assert any(f.check == "envelope_mismatch" for f in report.case("OTHER").failures)
    assert report.case(config.case_id).first_failure.sequence == 6


def test_tail_truncation_is_undetected_without_independent_anchor(chain):
    config, receipts = chain
    raw_conn(config).execute("DELETE FROM evidence_records WHERE sequence=6")
    assert report_for(config).status == "intact"  # documented limitation
    rep = report_for(config, checkpoint=(6, receipts[5].current_hash))
    assert rep.first_failure.check == "anchor_missing_record"
    assert report_for(config, expected_count=6).first_failure.check == "anchor_count_mismatch"


def test_full_chain_recomputation_is_undetected_without_independent_anchor(chain):
    config, receipts = chain
    conn = raw_conn(config)
    edit_payload(
        conn, config.case_id, 2, lambda p: p["body"]["metadata"].update(username="rewritten")
    )
    rechain(conn, config.case_id, 2)
    assert report_for(config).status == "intact"  # documented limitation
    rep = report_for(config, checkpoint=(6, receipts[5].current_hash))
    assert rep.status == "broken" and rep.first_failure.check == "anchor_hash_mismatch"
    assert rep.anchor["checkpoint_matched"] is False
    assert set(rep.affected_event_ids) == {r.event_id for r in receipts}


def test_checkpoint_permits_later_appends(chain):
    config, receipts = chain
    with EvidenceWriter(config) as w:
        w.append_observation(observation(7))
    rep = report_for(config, checkpoint=(6, receipts[5].current_hash))
    assert rep.status == "intact" and rep.anchor["checkpoint_matched"] is True


def test_verifier_does_not_modify_database(chain):
    config, _ = chain
    path = config.db_path
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    verify_database(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_verifier_runs_while_writer_open(config):
    with EvidenceWriter(config) as w:
        w.append_observation(observation(1))
        assert report_for(config).status == "intact"


def test_verifier_errors(tmp_path, chain):
    with pytest.raises(VerifierError):
        verify_database(tmp_path / "missing.sqlite3")
    junk = tmp_path / "junk.sqlite3"
    junk.write_bytes(b"not a database")
    with pytest.raises(VerifierError):
        verify_database(junk)
    config, _ = chain
    with pytest.raises(VerifierError):
        verify_database(config.db_path, checkpoint=(1, "a" * 64))


def test_cli_exit_codes_and_json(chain, capsys):
    config, receipts = chain
    assert main(["--db", str(config.db_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "intact" and out["limitations"]
    assert (
        main(
            [
                "--db",
                str(config.db_path),
                "--case-id",
                config.case_id,
                "--checkpoint-sequence",
                "6",
                "--checkpoint-hash",
                "c" * 64,
            ]
        )
        == 1
    )
    capsys.readouterr()
    assert main(["--db", str(config.db_path) + ".missing"]) == 2


def test_verifier_is_standalone_and_runs_as_module(chain):
    config, _ = chain
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    code = (
        "import sys, pisentinel.edge.evidence.verify as v; "
        "bad = [m for m in sys.modules if m.startswith('pisentinel') and "
        "m.split('.')[-1] in ('writer', 'schema', 'config', 'db', 'health', 'safe_logging')]; "
        "assert not bad, bad"
    )
    subprocess.run([sys.executable, "-c", code], check=True, env=env)
    proc = subprocess.run(
        [sys.executable, "-m", "pisentinel.edge.evidence.verify", "--db", str(config.db_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0 and json.loads(proc.stdout)["status"] == "intact"


def test_multiple_cases_are_independent_chains(tmp_path):
    a, b = make_config(tmp_path, CASE_ID="CASE-A"), make_config(tmp_path, CASE_ID="CASE-B")
    with EvidenceWriter(a) as wa, EvidenceWriter(b) as wb:
        ra = wa.append_observation(observation(1))
        rb = wb.append_observation(observation(1))
    assert ra.previous_hash == rb.previous_hash == GENESIS_PREVIOUS_HASH
    report = verify_database(a.db_path)
    assert report.intact and [c.case_id for c in report.cases] == ["CASE-A", "CASE-B"]
