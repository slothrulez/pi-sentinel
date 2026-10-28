# PiSentinel

**Adaptive Cyber Deception and Explainable Autonomous Digital Forensics Platform for Edge Devices**

Authorized defensive research loop: observe controlled SSH/web/network interactions, classify session behaviour, explain predictions with SHAP, adapt synthetic assets, preserve tamper-evident evidence, reconstruct timeline/graph, and produce grounded investigation with finite policy-controlled responses.

## Current state

**M1 (configuration + evidence foundation) is implemented and tested on Linux; nothing from M2 onward (decoys, models, dashboard, installer) exists. No measured detection/evaluation/resource results exist.** Complete 23-page `PiSentinel-Master-Guide.pdf`, including diagrams/tables/appendices, reviewed. Owner approval required before M1 coding.

Target: Raspberry Pi 4 / 2 GB. Development: Windows. Supplied Pi hostname/user/address: `sentinel`, `pisentinel`, `192.168.1.3`. Read-only SSH inventory authentication failed; OS/storage/packages/resource headroom unknown. No remote inventory/test/install/configuration change ran.

## Read first

- [Project plan](PROJECT_PLAN.md): complete inventory, priorities, ambiguities, granular milestones/dependencies/acceptance.
- [Actual project status](PROJECT_STATUS.md): checks/results/failures, blockers and remaining work.
- [Architecture](ARCHITECTURE.md): planes/modules/contracts, evidence design and hardware feasibility estimates.
- [Security](SECURITY.md): threat model, trust boundaries, approvals and future deployment/recovery.
- [Requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md): stable IDs/sources/planned tests/actual evidence.
- [Persistent project instructions](AGENTS.md): safe contribution and verification conventions.

## Development setup (M1)

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10+. Dependencies are pinned in `pyproject.toml` and locked in `uv.lock`; the evidence core uses only the standard library.

```sh
uv sync --all-extras          # create .venv from the lock file
uv run pytest -q              # unit, integration, security tests
uv run ruff check src tests
uv run python -m pisentinel.edge.evidence.verify --db data/cases/pisentinel.sqlite3
```

Configuration: copy `.env.example` to `.env` (git-ignored); see `src/pisentinel/config.py`. Evidence databases live under `data/` (git-ignored). Chain format and limitations: [docs/EVIDENCE_CHAIN.md](docs/EVIDENCE_CHAIN.md). No network service is started by any M1 code.

Expected guide SHA-256: `a5cde730f8d99d615e017fe15d138c1e6962b634b2cad5a06b9248e0e46e20ea`.

## Pi access and authorization

See [read-only inventory and actual failure](SECURITY.md#4-read-only-inspection-and-actual-target-result). Arrange normal authorized key/agent access, or share the documented inventory's non-sensitive output. Do not share keys/passwords or disable host verification. Private-IP reachability is not isolation or deployment authorization.

No package, firewall/system setting, service, IP or listener binding changed. Future deployment requires lab/sensor design, independent recoverable backups, exact privileged-command approval and actual per-milestone Pi tests. Training/heavy visualization/LLM stay off Pi; no paid API/cloud integration selected/authorized.

## Next increment

**M2 — real decoys/collection, requires separate owner approval and A01-A03 decisions.** M1 delivered: bounded secret-safe config/Event schema; durable atomic SQLite append; deterministic SHA-256 chain/independent verifier; deliberate corruption/concurrency/crash tests; raw-before-enrichment; actual health failures tested in-process; honest chain limits. No Pi modification or network exposure required.

## Scientific/security limits

Intent is inferred, not proven. Chaining is tamper-evident within stated trust boundary, not signed immutable/legal evidence. Synthetic lab results cannot establish real-world generalization. Documents, unrun tests, templates and estimated budgets are not completed features, actual AI outputs or measured metrics.
