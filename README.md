# PiSentinel

**Adaptive Cyber Deception and Explainable Autonomous Digital Forensics Platform for Edge Devices**

Authorized defensive research loop: observe controlled SSH/web/network interactions, classify session behaviour, explain predictions with SHAP, adapt synthetic assets, preserve tamper-evident evidence, reconstruct timeline/graph, and produce grounded investigation with finite policy-controlled responses.

## Current state

**Phase 1 planning only. No application, decoy, API, model, dashboard, installer or project test suite is implemented. No measured detection/evaluation/resource results exist.** Complete 23-page `PiSentinel-Master-Guide.pdf`, including diagrams/tables/appendices, reviewed. Owner approval required before M1 coding.

Target: Raspberry Pi 4 / 2 GB. Development: Windows. Supplied Pi hostname/user/address: `sentinel`, `pisentinel`, `192.168.1.3`. Read-only SSH inventory authentication failed; OS/storage/packages/resource headroom unknown. No remote inventory/test/install/configuration change ran.

## Read first

- [Project plan](PROJECT_PLAN.md): complete inventory, priorities, ambiguities, granular milestones/dependencies/acceptance.
- [Actual project status](PROJECT_STATUS.md): checks/results/failures, blockers and remaining work.
- [Architecture](ARCHITECTURE.md): planes/modules/contracts, evidence design and hardware feasibility estimates.
- [Security](SECURITY.md): threat model, trust boundaries, approvals and future deployment/recovery.
- [Requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md): stable IDs/sources/planned tests/actual evidence.
- [Persistent project instructions](AGENTS.md): safe contribution and verification conventions.

## Initial setup — inspect, do not install yet

Planning documents need no application dependencies. From PowerShell in this existing repository:

```powershell
Get-ChildItem -Force
git status --short --branch
python --version
git --version
ssh -V
Get-FileHash .\PiSentinel-Master-Guide.pdf -Algorithm SHA256
```

Expected guide SHA-256: `a5cde730f8d99d615e017fe15d138c1e6962b634b2cad5a06b9248e0e46e20ea`.
Inspected local Python: 3.12.6 (**not yet an approved Pi runtime**). Git 2.46.0.windows.1, OpenSSH 9.8p1, `pdftotext` available; pytest importable but no project tests exist. Ripgrep unavailable; use file listings/Python/search alternatives. No tooling install needed for plan review.

No `pyproject.toml`, dependency lock, `.env.example`, application/start command or install script exists yet. Do not run invented `pip install -r ...` or deployment commands. After approval M1 adds reproducible packaging/config/SQLite/Event/chain/verifier/real in-process health tests and reviewed pinned dependency groups. Record exact setup/test commands from actual execution, not guesses. Keep runtime secrets/case data out of Git.

## Pi access and authorization

See [read-only inventory and actual failure](SECURITY.md#4-read-only-inspection-and-actual-target-result). Arrange normal authorized key/agent access, or share the documented inventory's non-sensitive output. Do not share keys/passwords or disable host verification. Private-IP reachability is not isolation or deployment authorization.

No package, firewall/system setting, service, IP or listener binding changed. Future deployment requires lab/sensor design, independent recoverable backups, exact privileged-command approval and actual per-milestone Pi tests. Training/heavy visualization/LLM stay off Pi; no paid API/cloud integration selected/authorized.

## Next increment

**M1 — local configuration and immutable evidence foundation, after plan review.** Acceptance: bounded secret-safe config/Event schema; durable atomic SQLite append; deterministic SHA-256 chain/independent verifier; deliberate corruption/concurrency/crash tests; raw-before-enrichment; actual health failures tested in-process; honest chain limits. No Pi modification or network exposure required.

## Scientific/security limits

Intent is inferred, not proven. Chaining is tamper-evident within stated trust boundary, not signed immutable/legal evidence. Synthetic lab results cannot establish real-world generalization. Documents, unrun tests, templates and estimated budgets are not completed features, actual AI outputs or measured metrics.
