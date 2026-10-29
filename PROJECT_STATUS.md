# PiSentinel project status

## Snapshot

- **Phase:** M1 implemented, with recorded Linux cloud VM results and owner-verified Windows results (owner authorized M1 only, 2026-10-29). M2+ not authorized.
- **Inspection:** session 2026-10-28, continued after local midnight 2026-10-29 (+05:30).
- **Baseline:** 23-page guide SHA-256 `a5cde730f8d99d615e017fe15d138c1e6962b634b2cad5a06b9248e0e46e20ea`.
- **Initial repository:** D:\Projects\SENTINEL, branch main, no commits/tracked files; only user PDF. No existing app/rules found in repository or checked parent AGENTS paths.
- **Application features:** M1 only (config, Event schema, SQLite writer, hash chain, verifier, health). **Project tests:** 164 passed on Linux; owner-verified Windows Python 3.12.6 run: 164 passed, 0 failed, 1 Starlette deprecation warning, 17.30 seconds. **Pi inventory/tests:** not executed. **Research/resource evaluation results:** none.
- **Hardware:** proposed budgets, not actual Pi measurements.

## Task status

| Task / milestone | Status | Evidence / next gate |
|---|---|---|
| M0.1 repository/tooling/full guide review | Completed (inspection only) | Text of all pages; six contact sheets cover all 23 rendered pages, full-resolution pp. 1/17/18 checked; guide hash recorded. |
| M0.2 six requested documents + persistent instructions | Completed (planning documents only) | Inventory/plan/status/architecture/security/README/traceability and AGENTS.md; not application completion. |
| M0.3 consistency audit/Git checkpoint | Completed (local planning only) | 29 audit checks and staged whitespace review PASS; initial planning commit `3c7e5f9` inspected, working tree clean afterward. Owner approval still required before M1. |
| Read-only target inventory | Blocked: authentication | Strict batch SSH exited 255, permission denied; no remote command ran. Owner authorized access/inventory needed. |
| M1 local config/evidence foundation | Implemented; Linux results recorded; Windows test run verified by owner | See Linux and Windows verification below; implementation branch `devin/1793215090-m1-evidence-foundation`. Pi tests not executed. |
| M2 real decoys/collection | Not started | M1 and approved topology/sensor/library A01-A03. |
| M3 sessions/features/dataset | Not started | M2 and taxonomy/windows/protocol A06-A08 frozen. |
| M4 baseline RF | Not started | Actual independent labelled runs and leakage checks. |
| M5 explainable intent | Not started | M4 and actual Pi SHAP budget unverified. |
| M6 adaptive control/policy | Not started | M2/M3/M5, approved scope and finite executor. |
| M7 case reconstruction | Not started | Evidence/features/assessment/action provenance. |
| M8 investigator/export | Not started; future AI choice blocked | M7/M5/M6 and actual approved model/context/cost A04/A05. |
| M9 operator API/dashboard/closed loop | Not started | Genuine upstream state, no success mockups. |
| M10 approved Pi rollout/evaluation/delivery | Not started | Auth/backup/approvals/protocol and earlier acceptance gates. |

## Checks actually performed

| Check | Method / environment | Inspected result |
|---|---|---|
| Repository inventory | Git Bash pwd/ls/file listing/git status/ls-files/log | Only PDF; no prior commits on main. Initial git log failed because no initial commit, not lost history. |
| Search tool | rg attempt / command availability | rg unavailable; switched to directory listings/Python/text tools. No install. |
| Guide extraction | pdftotext -layout, page inventory and bounded range reads | All 23 pages/1,136 extracted lines read. Missing p. 7 and truncated module text explicitly recovered/read. |
| Guide digest | sha256sum | Matches baseline above. |
| Visual guide review | Built-in Windows.Data.Pdf + existing Pillow | All pages rendered/reviewed; diagrams missing from extraction recovered visually, tables checked. No new software installed. |
| Renderer recovery | Initial WinRT reflection failed; corrected generic-method selection | Second stop-on-error command rendered all 23 pages; file list inspected. This is reading utility work, not application tests. |
| Python/tool inventory | python --version, py -0p, git --version, ssh -V, node --version, import checks | Python 3.12.6; Git 2.46.0.windows.1; OpenSSH 9.8p1; Node 24.17.0 present, not selected for Pi. pytest/Pillow/PyYAML importable; no project environment created. |
| Local hardware | PowerShell CIM/Get-PSDrive | Windows 10 Pro 10.0.19045/64-bit; 7.88 GiB RAM; i5-6200U/4 logical processors; D free 62,501,351,424 bytes at inspection. Local facts, not Pi/project benchmarks. |
| SSH inventory attempt | BatchMode, strict host checking, 8-second timeout, one connection attempt to pisentinel@192.168.1.3 | Exit 255: Permission denied (publickey,password). Endpoint responded; target OS/identity inventory did not run. No auth retry/device change. |
| Document write recovery | Oversized command failed, subsequent command truncated at shell payload limit | Inspected partial file, repaired only newly created planning file and continued in bounded writes; final audit verified complete core and optional tables. |
| Application unit/integration/security/E2E | M1 tests recorded on Linux and Windows; later-milestone E2E not implemented | See Linux verification and owner-verified Windows results below. Later-milestone test paths remain planned, not executed. |
| Pi tests/load | Not executed | Auth failed; deployment not authorized. |
| ML/SHAP/AI/evaluation | Not implemented/executed | No dataset/model/metrics/provider calls. |
| Final documentation audit | Executed locally with inline Python assertions | PASS: 29 checks; 76 unique IDs (66 core/adopted/user + 10 optional), exact traceability set, 28 defined subtasks, M0-M10, A01-A14, links/anchor/fences, 11 routes, 14 features, seven artifacts, authorized file set and unchanged PDF. This is a documentation audit, not application tests. |
| Final Git/whitespace review | Executed locally | Staged `git diff --cached --check` PASS; eight staged paths reviewed, original guide digest unchanged in index; targeted document key-pattern check had no matches (not exhaustive). Existing Git LF/CRLF warning was informational; no Git configuration changed. |

Temporary visual aids are outside repository at C:\Users\HP\AppData\Local\Temp\pisentinel-guide-review-a5cde730; not deliverables/independent backups. Source PDF never replaced. Tests/verification utilities used to inspect documents are not a PiSentinel test suite.

## Blockers and remaining work

| ID | Blocker / risk | Impact and next action |
|---|---|---|
| B01 | M1 authorized; M2 approval absent | M1 Windows test result recorded below. Do not start M2 until owner separately approves; Pi testing remains unexecuted. |
| B02 | SSH auth failed (A12) | Cannot verify Pi OS/architecture/storage/packages/resources. Owner arranges authorized access or shares read-only inventory; no credential search/retry. |
| B03 | Lab topology/source allowlist/sensor absent (A01/A02) | No listeners/scans; multi-port observation/scenario A blocked until independent sensor/privacy/privilege design approved. |
| B04 | LLM/context/cost/data choice absent (A04/A05) | Actual AI cannot be replaced with template. Need approved model and interpretation of “grounded RAG”; no cloud call made. |
| B05 | Counts/thresholds/ablations/taxonomy/windows not frozen (A06-A08/A11) | Freeze before collection/evaluation; no numeric accuracy/latency claim available. |
| B06 | Chain/retention/checkpoint/backup details pending (A09/A13/A14) | Approve format/independent recovery destination before continuous collection/release. |
| B07 | 2 GB/ARM feasibility unmeasured | Guide ranges overlap/are estimates. Actual Pi imports/peaks/load and bounded service selection required. |

Security risks: hostile SSH/HTTP parsers, accidental sensitive capture, pivoting without isolation, resource/disk exhaustion, unanchored chain rewrite/truncation, prompt injection/unsupported cited claims, train/test leakage/unsafe model loading, privileged sensor design and management lockout. SECURITY defines **proposed** mitigations, not deployed controls.

## M1 scope (implemented; see verification below)

**M1 local config + immutable evidence foundation.** Bounded secret-safe settings/Event schema, transactional SQLite writer, deterministic chain/independent verifier, deliberate corruption/concurrency/crash tests, raw-before-enrichment persistence and actual in-process health. Read full acceptance in PROJECT_PLAN before coding. No Pi changes/listeners/AI cost necessary. Establish reproducible project dependency/test commands only after approval, rather than treating global pytest as project setup.

## Completion accounting

PS-U01 planning documents and the 29-check consistency audit are complete; the executed local Git checkpoint is recorded below. M1 was subsequently authorized and implemented; its Linux results and owner-verified Windows results are recorded below. Later-milestone requirements remain incomplete, Pi testing has not occurred, and M2 requires separate approval. A local planning Git checkpoint is not an independent backup, release tag, Pi deployment or completed research requirement. No push is authorized for this documentation update.

## Audit tooling recovery

The first Phase 1 audit invocation had a Python quoting syntax error and did not execute checks. The next audit found its own incorrect assumption that optional and core tables had identical column counts. Corrected validator uses their distinct four/five/six-column contracts; final inspected run passed all 29 checks. No application tests existed during that planning audit; subsequent M1 test results are recorded below.

## Executed Git checkpoint

Initial planning checkpoint: `3c7e5f93856fc8c024bf3bc00b3fab8146546879` — guide + six requested documents + AGENTS.md. Commit succeeded; inspected `git status --short --branch` showed clean `main` afterward. No push/tag/remote backup/deployment occurred. This follow-up status record documents the actual result; Git history identifies the status-record commit separately.

## M1 Linux verification (2026-10-29)

Environment: Devin Linux cloud VM (Ubuntu 22.04, x86_64), not Windows, not the Pi. `uv` 0.9.5; CPython 3.12.12 (project venv), 3.10.12 and 3.11.14 (extra venvs); SQLite 3.50.4 (3.12) / 3.37.2 (system 3.10). Locked (`uv.lock`): fastapi 0.141.1, starlette 1.10.0 (1.7.0 on Python 3.10), pydantic 2.14.1, pytest 9.1.1, httpx 0.28.1, ruff 0.16.9.

| Check | Command | Actual result |
|---|---|---|
| Setup | `uv sync --all-extras` | Environment created from `uv.lock`. |
| Full suite (3.12) | `uv run pytest -q` | 164 passed, 1 warning (Starlette TestClient httpx deprecation, third-party). |
| Full suite (3.10, 3.11) | `pytest -q` in separate uv venvs | 164 passed each. |
| Repeat integration/crash/concurrency | `pytest -q tests/integration` x10 | 10/10 runs: 53 passed. |
| Lint/format | `uv run ruff check src tests`; `uv run ruff format --check src tests` | All checks passed; formatted. |
| Vectors | `sha256sum` over `record_N.canonical.json` + previous hash (coreutils) | Matches `tests/vectors/chain_v1/expected.json` and Python. |
| Guide digest | `sha256sum PiSentinel-Master-Guide.pdf` | Unchanged baseline. |

M1 acceptance (PROJECT_PLAN): valid config loads / unsafe settings fail without echo or import-time binding: **met**. Unicode/size/non-finite bounds: **met**. Persisted events survive reopen: **met**. Independent known-byte hashes: **met**. Content/link/insertion/interior-deletion/reordering identify broken and affected IDs: **met**. Concurrency (threads, separate connections, 4 processes) cannot fork; interrupted transaction (process exit before commit, SIGKILL mid-loop) leaves no half record; intact chain verifies: **met**. Tail truncation / full rewrite limits disclosed and tested as negative guarantees: **met** (`docs/EVIDENCE_CHAIN.md`). Raw unchanged by enrichment: **met**. Real in-process health with DB/schema/writer/storage failures: **met** (no listener). The detailed results in this paragraph were recorded for Linux. The Windows test-execution requirement is now **met by the owner's verified Python 3.12.6 run** documented separately below; platform-specific Linux checks are not independently claimed for Windows. Pi tests: not executed by design.

M1 assumptions (proposals, reviewable; not guide facts):
- Severity vocabulary `info/low/medium/high/critical` (guide shows only `medium`).
- Canonical form forbids floats; guide `confidence` 0.91 must later be encoded (e.g. integer basis points) by its owning milestone. Open decision for M4/M5.
- Object keys restricted to ASCII lowercase; timestamps RFC 3339 with explicit offset, original kept plus `timestamp_utc`; writer assigns `recorded_at` (UTC).
- One chain per case shared by observations and derived records; derived record content schemas deferred to their milestones.
- Metadata: generic bounded structure plus credential-key denylist and secret-shape value filter (count kept). Per-service allowlists and the producer IPC adapter (A03/M2) are deferred; M1 exposes an in-process writer API only.
- Evidence core is stdlib-only; FastAPI is an optional `api` extra used only for `GET /health`, never served in M1.

Open decisions carried forward: A09 format review/freeze, checkpoint retention location and WAL-aware backup (A13/A14), float encoding. The previously outstanding Windows test run is recorded below.

## M1 Windows verification (2026-10-29)

Environment: Windows, Python 3.12.6. Evidence source: the owner's verified command results supplied on 2026-10-29. The application commands were not rerun for this documentation-only update; no additional Windows package/tool versions or lint/format results were supplied.

| Check | Command | Verified Windows result |
|---|---|---|
| Setup | `uv sync --all-extras` | Succeeded. |
| Full M1 test suite | `uv run pytest -q` | 164 passed, 0 failed, 1 Starlette deprecation warning, in 17.30 seconds. |

This closes the previously owed Windows test-execution check, not the warning: it remains recorded and no fix or dependency change is claimed. No Raspberry Pi inventory, tests, deployment or resource measurements occurred. No application code or dependencies were changed for this update. M2 and later milestones remain unstarted and require separate authorization.

Documentation-only update checks: inline Python audit **PASS (31 checks)** for exact results/provenance, retained requirement IDs and partial scope, unchanged Linux results, Markdown structure/links, unchanged guide digest, and two-file-only changes on the new documentation branch. `git diff --check`: **PASS**. Application test commands were not rerun.
