# PiSentinel working instructions

## Gate and authority

- Owner authorized **M1 only** (2026-10-29). Do not start M2 or later milestones without separate approval. Read PROJECT_PLAN.md, PROJECT_STATUS.md and docs/REQUIREMENTS_TRACEABILITY.md first.
- Primary guide: PiSentinel-Master-Guide.pdf, 23 pages, SHA-256 a5cde730f8d99d615e017fe15d138c1e6962b634b2cad5a06b9248e0e46e20ea. Preserve guide/user data; reference physical PDF pages/sections/appendices.
- Stable PS-* IDs never renumber. Documentation/stubs/unrun tests never satisfy application acceptance. Record exact source, command, environment, inspected result/evidence in status/traceability.

## Safety/deployment

- Authorized defensive lab only. No new listeners/exposure/scans, Pi installs, sudo/services, firewall/security/IP changes, cloud/paid calls or destructive action without specific approval.
- Target supplied as sentinel / pisentinel@192.168.1.3, Pi 4/2 GB. Strict noninteractive SSH authentication failed; no inventory ran. Ask owner for authorized access; no key discovery/password retry/host-check downgrade.
- Synthetic decoys never execute host commands or expose real accounts/files. Drop credentials before logs/evidence. AI stays outside OS control path; finite policy/executor, limits and rollback required.
- Heavy training/graphs/LLM off Pi; budgets are not measurements. Never weaken security policies for build convenience.
- Local Git only, no push without explicit request. Separate runtime secrets/evidence. Local commit is not independent backup.

## Verified local environment and checks

- Windows 10 Pro 64-bit; repository D:\Projects\SENTINEL; Git Bash; Python 3.12.6, Git 2.46.0.windows.1, OpenSSH 9.8p1 and pdftotext available; ripgrep unavailable.
- Read-only Git Bash checks: `git status --short --branch`, `git diff --check`, `python --version`, `pdftotext -layout PiSentinel-Master-Guide.pdf -`, `sha256sum PiSentinel-Master-Guide.pdf`. PowerShell digest: `Get-FileHash .\PiSentinel-Master-Guide.pdf -Algorithm SHA256`.
- Project checks (M1): `uv sync --all-extras`, `uv run pytest -q`, `uv run ruff check src tests`, `uv run ruff format --check src tests`. Linux cloud VM used for M1; Windows run still owed.
- Chain format v1 vectors in `tests/vectors/chain_v1/` are frozen; any change needs a new chain format version.
- Planning audit: unique requirement definitions, every core/user/optional ID in traceability, all guide sections/appendices covered, local Markdown links valid, guide digest unchanged and Git whitespace check clean. Record actual audit result.
- Windows shell command payloads were truncated around 8 KiB during document drafting; use smaller batches and verify file tails/counts. A first oversized invocation failed without writing files; a partial planning-table write was repaired before audit.
- If new agent/tool configuration is requested later, use `.devin/`; no unrelated environment blueprint/config during Phase 1.
