"""Child process used by crash/concurrency tests. Prints one ACK line per committed record."""

import os
import sys

from pisentinel.config import load_config
from pisentinel.edge.evidence.writer import EvidenceWriter


def obs(event_id: str) -> dict:
    return {
        "event_id": event_id,
        "timestamp": "2026-09-16T14:22:01+05:30",
        "source_ip": "10.10.0.20",
        "destination_service": "ssh",
        "event_type": "auth_failure",
        "action": "login_attempt",
        "metadata": {"username": "admin"},
    }


def main() -> None:
    mode, db_path, prefix, count = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    config = load_config(
        {
            "PISENTINEL_DB_PATH": db_path,
            "PISENTINEL_CASE_ID": "CASE-TEST",
            "PISENTINEL_SQLITE_BUSY_TIMEOUT_MS": "60000",
        }
    )

    def hook(point: str) -> None:
        if mode == f"crash_{point}":
            os._exit(17)  # simulate power loss / kill: no rollback, no cleanup

    writer = EvidenceWriter(config, fault_hook=hook).open()
    print("READY", flush=True)
    for i in range(count):
        receipt = writer.append_observation(obs(f"{prefix}-{i:05d}"))
        print(f"ACK {receipt.sequence} {receipt.event_id} {receipt.current_hash}", flush=True)
    writer.close()


if __name__ == "__main__":
    main()
