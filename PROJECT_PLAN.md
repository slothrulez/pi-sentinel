# PiSentinel project plan

## 1. Authority and current gate

**Phase 1 only. Await owner review before implementation. No application feature exists yet.**

Primary specification: `PiSentinel-Master-Guide.pdf`, 23 physical PDF pages (cover included), SHA-256 `a5cde730f8d99d615e017fe15d138c1e6962b634b2cad5a06b9248e0e46e20ea`. All pages were text-read and visually reviewed, including diagrams, tables, sections 1-29 and appendices A-C. No additional appendix was present. Numbered lists continue across unrelated sections; their numbers are not requirement IDs. Inspection began in the 2026-10-28 session and continued after local midnight, 2026-10-29 (+05:30).

Guide core requirements, guide recommendations adopted as proposals, optional extensions, user constraints and proposed design choices are distinguished. Repeated statements share stable IDs; never renumber/reuse IDs. Documentation completion does not satisfy implementation requirements. Full planned acceptance/test/evidence mapping is in `docs/REQUIREMENTS_TRACEABILITY.md`.

Research question (§1.2): can adaptive, intent-driven deception plus tamper-evident reconstruction improve engagement and post-incident understanding on constrained edge hardware? The principal research comparison is **static versus adaptive deception** (§27). Improvement must be measured, not assumed.

## 2. Complete requirements inventory

**Origin:** G = guide core; R = guide recommendation, proposed adoption; U = user constraint. Mixed origins are explicit. **Priority:** P0 = safety/integrity/dependency gate; P1 = required functional/research/delivery capability; P2 = optional extension. All P1 work remains required for final completion. Milestone is the primary acceptance owner; ongoing controls apply earlier and later too. Inventory: 66 core/adopted/user requirements plus 10 optional extensions, implemented through 28 independently checkable planning/implementation subtasks. No row below is an implemented feature.

| Stable ID | Origin / priority | Requirement or adopted recommendation | Source (physical PDF pages) | Milestone |
|---|---|---|---|---|
| PS-G01 | G/P0 | Authorized defensive closed loop: observe, infer, explain, adapt, collect, reconstruct, investigate, respond; not merely honeypots or a dashboard. | pp. 1-5 §§1, 3-5; p. 19 §25 | M9 |
| PS-G02 | G/P0 | Core edge loop on Raspberry Pi 4 / 2 GB; measure CPU, RAM, latency, storage and network. | p. 1 scope; pp. 7, 15 §§7, 18 | M10 |
| PS-G03 | G/P0 | Offload training, large visualization and LLM; native MVP before selective containers. Exclude Pi deep training/large LLM, full SIEM, many honeypots, initial RL, blockchain and enterprise orchestration. | pp. 6-7, 15, 18-19 §§6.2, 7.2, 17-18, 25 | M10 |
| PS-F01 | R/P0 | Configuration, secret-free environment example, SQLite/Event schema, real health endpoint and visible failures. | p. 15 §19 week 1; p. 22 Apps. B-C | M1 |
| PS-F02 | G/P0 | Reproducible Pi setup, documented private network, source/config recovery and preserved management SSH. | pp. 15, 19-20 §§19, 26, 29 | M10 |
| PS-C01 | G/P1 | Collect network plus decoy events: connections, ports/services, timing, discovery and cross-service activity; independently observe scans. | pp. 4-5, 7 §§4-5, 8.1; p. 17 scenario A | M2 |
| PS-C02 | G+U/P0 | Stable bounded normalized schema: event ID, timestamp, source IP, destination service, type, action, metadata, session, severity, chain and assessment fields/references. | p. 9 §9; user data validation | M1 |
| PS-C03 | G/P1 | One real SSH-protocol synthetic decoy: usernames, failed/success-like states, duration, commands, file/path probes; no real shell. | pp. 7-8 §8.2; p. 17 scenarios B-C | M2 |
| PS-C04 | G/P1 | One web/API decoy with fake login/endpoints/data; URL/method/rate/status patterns and endpoint transitions. | p. 8 §8.3; p. 17 scenario D | M2 |
| PS-C05 | G+U/P0 | Synthetic accounts/records only; discard submitted passwords/tokens and unnecessary sensitive values before evidence/logging. | p. 5 §5.2; p. 18 §23; user security rules | M2 |
| PS-S01 | G/P1 | Behavioural sessions/windows grouped by source/session/time; one reproducible vector per defined window. | p. 8 §8.4; p. 10 §10 | M3 |
| PS-S02 | R/P1 | Features: connection_count, unique_ports, unique_services, failed_login_count, unique_usernames, command_count, session_duration, http_request_count, unique_urls, endpoint_count, file_access_count, db_like_request_count. | p. 10 §10.1 | M3 |
| PS-S03 | R/P1 | Sequence features service_transition_count and repeat_pattern_score; consistent request-rate/duration semantics for explanation examples. | pp. 10-11 §§10.1, 11.1 | M3 |
| PS-D01 | G/P1 | Own small labelled lab dataset: benign/scripted attacks, independent run metadata, start/end times and ground-truth stage sequence. | p. 10 §10.4; pp. 16, 19 §§19, 26 | M3 |
| PS-D02 | R/P1 | Suggested labels: benign, reconnaissance, automated_scanning, credential_attack, remote_access, file_discovery, data_discovery. | p. 10 §10.2 | M4 |
| PS-D03 | G+U/P0 | Train/validation/test independent by collection run/scenario; no overlapping-session/window or preprocessing leakage. | p. 16 §19 week 3; user evaluation rules | M4 |
| PS-ML01 | R/P1 | Reproducible scikit-learn RF baseline: n_estimators=50, max_depth=8, n_jobs=1, random_state=42, interpretable numeric features. | p. 10 §§10.3-10.4; pp. 14-15 §17 | M4 |
| PS-ML02 | G/P1 | Classifier probabilities/label/confidence; intent mapping with evidence IDs; predictions separate from facts. | p. 8 §§8.5-8.6; pp. 9-10 §§9-10 | M5 |
| PS-ML03 | G/P0 | Uncertain/novel/mixed behaviour falls back to observe and gather evidence, not unsupported escalation. | p. 18 §24; p. 19 §25 | M6 |
| PS-X01 | G/P1 | Real Tree SHAP on aggregated session/window RF decisions; positive and negative feature contributions. | pp. 8, 10-11 §§8.7, 11 | M5 |
| PS-X02 | G/P1 | Store machine-readable SHAP values with exact model/version/vector; human top contributors are not proof of intent. | p. 11 §§11.2-11.3; p. 20 §29 | M5 |
| PS-X03 | G/P0 | SHAP suspicious/on-demand, never per packet; bounded scheduling, defer/offload on pressure, measured Pi feasibility. | pp. 8, 11, 15, 18 §§8.7, 11.3, 18, 24 | M5 |
| PS-A01 | G/P1 | Deterministic deception state machine from stage, intent/confidence and risk before any learned policy. | pp. 11-12 §12 | M6 |
| PS-A02 | G/P1 | Actual adaptive synthetic inventory, usernames/admin-like surface, directory/files, extra API routes and database-like records. | pp. 11-12 §12.1; p. 17 scenarios B-E | M6 |
| PS-A03 | G/P0 | Action expiry, rollback, cooldowns and bounded transitions prevent oscillation. | p. 8 §8.8; pp. 16, 18, 20 §§19, 23-24, 29 | M6 |
| PS-A04 | G/P0 | Durable audit for every control decision: reason, confidence, evidence, action and result. | p. 12 §12.3; pp. 16, 18 §§19, 23 | M6 |
| PS-E01 | G+U/P0 | Persist timestamped raw normalized observations before enrichment; derived assessments stored separately. | pp. 8-9, 12-13 §§8.9, 9, 13.3; user evidence rules | M1 |
| PS-E02 | G/P0 | SQLite SHA-256 chain over canonical event JSON plus previous hash, stable linkage/order and atomic append. | p. 12 §13.1/diagram; p. 22 App. C steps 2-3 | M1 |
| PS-E03 | G+U/P0 | Recompute all hashes/links; report first broken record and affected IDs; deliberate tampering tests and honest limitations. | p. 12 §13.2; p. 17 scenario F; user integrity rules | M1 |
| PS-E04 | G/P1 | Export events.jsonl, case.json, timeline.json, attack_graph.json, integrity_report.json, shap.json, investigator_report.md; independent verification. | p. 13 §13.3; pp. 16, 19 §§19, 26 | M8 |
| PS-E05 | G/P0 | Broken-chain cases flagged, raw copy preserved, never sent as supposedly verified evidence to AI. | pp. 8, 13-14, 18 §§8.11, 15, 24 | M7 |
| PS-R01 | G/P1 | Ordered evidence-backed stage timeline, noise reduction and observed recon/SSH enumeration/credential/access/file/data progression. | p. 13 §14.1 | M7 |
| PS-R02 | G/P1 | Source -> service -> session -> action -> resource -> evidence graph, followed-event relations, JSON and visualization. | p. 13 §14.2; pp. 15, 19 §§17, 26 | M7 |
| PS-R03 | G/P0 | Timestamp normalization, monotonic sequence IDs, clock-skew/late-arrival handling without unsupported causal claims. | p. 18 §24 | M7 |
| PS-I01 | G/P0 | Trusted laptop/approved API investigator consumes only verified structured case JSON, timeline/graph, intent/confidence, SHAP and evidence. | pp. 1, 7, 13-14 scope/§§7, 15.1-15.2 | M8 |
| PS-I02 | G/P1 | AI report: observed facts, model assessment, SHAP rationale, progression, uncertainty/missing evidence, policy-bounded recommendation. | p. 14 §15.3 | M8 |
| PS-I03 | G/P0 | Every factual statement cites evidence IDs; predictions/hypotheses labelled; reject unsupported/unknown references; do not invent missing details. | p. 14 §15.4; p. 18 §24 | M8 |
| PS-I04 | G/P0 | No arbitrary AI shell/OS control; recommendations must pass finite policy/allowed executor. | pp. 5, 9, 14, 18 §§5, 8.12, 15.4, 16.1, 23 | M6 |
| PS-I05 | G/P1 | AI outage uses deterministic template from verified evidence, explicitly labelled non-AI fallback. | p. 18 §24 | M8 |
| PS-P01 | G/P0 | Low observe; medium deceive; high rate-limit/restrict; critical isolate/stop lab session while preserving evidence. | p. 14 §16 | M6 |
| PS-P02 | G+U/P0 | Explicit allowlist/safety limits/approved scope; simulated isolation unless separately authorized; management excluded. | pp. 5, 14, 18 §§5, 16.1, 23; user approvals | M6 |
| PS-UI01 | G/P1 | Live session/source, inferred intent/confidence, SHAP, decoy state, timeline/graph, integrity, response and audit view. | p. 9 §8.13; pp. 17-18 §22.1; p. 20 §29 | M9 |
| PS-UI02 | R/P1 | Adopt all eleven exact Appendix B GET APIs over real state: health, events, sessions, cases, explanations, integrity, state, policy and reports. | p. 22 App. B | M9 |
| PS-O01 | G/P1 | Observable CPU/RAM, feature-to-decision latency, storage and analysis-plane bytes, with workload/version context. | pp. 2-3, 15, 17 §§1.3, 18, 21 | M10 |
| PS-O02 | G+U/P0 | Bound input/concurrency/queues/cases/storage, rate-limit decoys, handle disk/writer/resource failure visibly. | pp. 15, 18 §§18, 23-24; user validation | M2 |
| PS-O03 | G/P0 | Slow SHAP/RAM/oscillation fallbacks preserve collection; explicit optional UI/container disablement or offload. | p. 18 §24 | M10 |
| PS-O04 | G+U/P0 | Reproducible install/service supervision/least privilege/backups and one verified approved Pi milestone at a time. | pp. 15-16, 19-20 §§19, 26, 29; user deployment | M10 |
| PS-V01 | G/P1 | All six baselines: static/adaptive; intent ML with/without behavioural features; ML with/without SHAP; rule-only/ML-assisted intent; raw/stage timeline; local-only/Pi+PC offload. | p. 16 §20.1 | M10 |
| PS-V02 | G/P1 | Fixed scenarios, repeated independent runs, fixed HW/SW per experiment, exact model/schema, outcomes/resource costs and failure cases. | p. 17 §20.2 | M10 |
| PS-V03 | G/P1 | Intent accuracy correct/labelled sessions; per-class and macro precision/recall/F1 against ground truth. | p. 17 §21 | M10 |
| PS-V04 | G/P1 | Stage accuracy correct reconstructed/labelled stages; timeline accuracy as order and temporal alignment. | p. 17 §21 | M10 |
| PS-V05 | G/P1 | Engagement time, meaningful interaction depth and adaptive assets reached. | p. 17 §21; p. 19 §27 | M10 |
| PS-V06 | G/P0 | Measured injected-modification detection and evidence completeness, with cryptographic limitations. | p. 2 §1.3; p. 17 §21/scenario F | M10 |
| PS-V07 | G/P1 | Evidence-linked report grounding/hallucination checks, SHAP attribution quality and analyst usefulness. | p. 2 §1.3; p. 17 §21 | M10 |
| PS-V08 | G/P1 | Average/peak Pi CPU/RSS, monotonic feature-to-decision time, bytes to analysis plane and storage overhead. | pp. 2-3, 15, 17 §§1.3, 18, 21 | M10 |
| PS-V09 | G/P1 | Execute A port scan, B SSH credential attack, C post-access discovery, D web enumeration, E multi-stage, F copy tampering. | p. 17 §22 | M10 |
| PS-V10 | G/P1 | Repeat full demo: health/scan/session/SSH/confidence/SHAP/adaptive files/data/timeline/graph/integrity/AI/policy/audit/copy tamper. | pp. 17-18 §22.1; p. 20 §29 | M10 |
| PS-Z01 | G/P0 | Private lab subnet/VLAN, controlled bindings; no production data or uncontrolled internet-facing honeypot/isolation. | p. 5 §5; p. 18 §23 | M2 |
| PS-Z02 | G/P0 | Back up before destructive tests; preserve original and failed/corrupt cases. | p. 18 §§23-24 | M7 |
| PS-T01 | G/P1 | Source modules, labelled dataset, versioned model/schema, evidence/verifier, reconstruction JSON/view and grounded report deliverables. | p. 19 §26; p. 20 §29; p. 22 App. A | M10 |
| PS-T02 | G/P1 | Architecture/setup/API/security/limitations docs, evaluation report, final presentation/viva and bounded scientific claims. | pp. 19-21 §§26-29 | M10 |
| PS-T03 | G/P0 | Source tagged/backed up; model/data/code provenance and reproducible hardware demo. | pp. 15, 20 §§17, 29 | M10 |
| PS-U01 | U/P0 | Phase 1 only: complete PDF/repo/environment review and six documents; stop for plan approval. | User FIRST TASK / PHASE 1 | M0 |
| PS-U02 | U/P0 | Prior approval for installs/deployment/listeners/firewall/security/system/privileged/destructive operations. | User security/deployment/working rules | M10 |
| PS-U03 | U/P0 | No unapproved paid/cloud dependency; secret separation; documented pinned compatible dependencies and costs. | User PHASE 2 / working rules | M8 |
| PS-U04 | U/P0 | Distinguish implementation/test execution/pass/fail/not-run/blocked/estimates/actual metrics; no fabricated or placeholder success. | User primary objective/testing | M10 |

### Optional extensions explicitly retained

| Stable ID | Extension | Source | Disposition |
|---|---|---|---|
| PS-OPT01 | Zeek/Suricata integration | p. 6 §6.1 | P2/deferred; independent lightweight scan telemetry still core PS-C01. |
| PS-OPT02 | More realistic profiles/additional synthetic apps | p. 6 §6.1 | P2/deferred; one SSH/web pair with adaptive content still core. |
| PS-OPT03 | PostgreSQL offload | p. 6 §6.1 | P2/deferred; SQLite MVP. |
| PS-OPT04 | Advanced uncertainty-aware model | p. 6 §6.1 | P2/deferred; confidence/observe fallback still required. |
| PS-OPT05 | Interactive explanation history | p. 6 §6.1 | P2/deferred; selected stored SHAP still required. |
| PS-OPT06 | Learned policy/contextual bandit | pp. 6, 12 §§6.1, 12.2 | P2/deferred; deterministic first. |
| PS-OPT07 | Signed export bundles | p. 6 §6.1 | P2/deferred; no signed/authenticity guarantee claimed. |
| PS-OPT08 | Advanced graph analytics/ATT&CK mapping | p. 6 §6.1 | P2/deferred; basic graph still required. |
| PS-OPT09 | RAG over larger case files | p. 6 §6.1; diagrams pp. 1, 7 | P2/deferred pending A04; bounded verified JSON proposed for MVP. |
| PS-OPT10 | Prometheus/Grafana on laptop | p. 6 §6.1 | P2/deferred; resource measurement/simple dashboard still core. |

§2 is navigation; §§3, 27-28 include explanatory motivation, viva and glossary. Concrete claims/limitations are covered by PS-G01/ML02/E02/E03/V01/V07/T02. Confidence 0.91, sample IDs/JSON and stage times are examples, not results/targets. Appendix A/B are suggestions adopted as proposals, not mandates to create empty skeletons. Section 19's week labels express guide sequencing, not our delivery estimate.

## 3. Proposed decisions, ambiguities and dependencies

These are proposals, not guide facts or approved deployment choices.

| ID | Issue and proposed resolution | Required decision / blocking point |
|---|---|---|
| A01 | Supplied 192.168.1.3 is a management address, not proof of isolation. Development defaults to in-process/local tests, no listeners. | Owner supplies approved attacker hosts, lab interface/subnet and sensitive-LAN separation before M2 traffic/deployment. |
| A02 | Two app decoys cannot observe probes of closed/unbound ports. Need minimal header-only capture or independent trusted network-sensor telemetry; generator labels are not sensor evidence. | Approve location/interface, privacy and privilege before PS-C01/scenario A. No capture/capability changes now. Missing sensor leaves work blocked. |
| A03 | Prefer maintained minimal SSH library (candidate AsyncSSH) with synthetic handlers over full Cowrie if measured memory/confinement justify it. | M2 security/ARM/dependency/resource review selects one. Banner-only TCP is insufficient; no host shell/forwarding/SFTP/SCP. |
| A04 | Diagrams pp. 1/7 say grounded RAG; §6.1 larger-case RAG is optional; §15 input is JSON. Propose bounded verified JSON context, no vector store. | Owner confirms MVP interpretation or expands M8 scope/cost/resource plan. |
| A05 | LLM model/provider, egress/data permissions and cost ceiling absent; PC is not assumed able to run a useful large model. | Owner chooses approved laptop model or provider/budget/fields before real M8 AI. No signup/call/subscription now. Templates do not satisfy AI. |
| A06 | Counts/repeats/load, confidence/risk and accuracy/latency thresholds, stage matching tolerances absent. | Preregister/review before M3 collection/M10 experiments; do not tune after test results. Resource guardrails below are proposals. |
| A07 | Suggested labels omit web/SSH enumeration used as stages elsewhere. | Propose seven behaviour labels plus explicit enumeration stage tags; freeze taxonomy/mixed-session labelling before M3. |
| A08 | IP is not identity; NAT/reconnect/cross-service windows, timeouts and case rotation unspecified. | Source+transport+time linkage with uncertainty; freeze bounded window and feature formulas at M3. |
| A09 | Canonical JSON/genesis/bytes/chain scope/checkpoint trust unspecified. | Review per-case chain and independently retained closure checkpoint proposal in ARCHITECTURE at M1; no anti-rewrite/signature claim. |
| A10 | §19 delays hashing/policy vs Appendix C/safety; §12 pseudocode checks high risk after some intent branches. | Propose hashing before collection and policy safety veto before adaptive action; high-risk limits precede deception. |
| A11 | “Without behavioural features”, local-only processing and analyst usefulness not operationally defined. | Review ablations in §5 before experiments. No SHAP accuracy-improvement claim; local-only never means Pi LLM/training. |
| A12 | Pi OS/architecture/storage/packages/power/cooling unknown; SSH auth failed. | Owner arranges authorized access or provides inventory before ARM locking/Pi deployment. No authentication retries/key discovery. |
| A13 | Retention/rotation/disk budget/case limits and independent backup/checkpoint destination unspecified. | Approve before continuous collection; no automatic evidence deletion. Stop/reject visibly at limits. |
| A14 | Guide recommends Git+GitHub; remote/backup destination and release approval absent. | Local Git now; owner approves independent backup, release tag and any push later. Local commit is not independent backup. |

Material review questions now: A01/A02 lab and sensor; A04 JSON-grounding interpretation; A05 AI/cost/data choice. Other choices can be refined safely within milestones but cannot silently redefine evaluation.

## 4. Dependency-aware milestones

Every task needs linked IDs, actual source changes, inspected tests/failure checks and environment evidence. Planned test paths are not existing tests. All implementation milestones are not started.

### M0 — specification and plan (current)

- M0.1: inspect repository/tooling, read all pages/tables/diagrams/appendices, record guide digest (PS-U01).
- M0.2: six documents, complete inventory/source mapping, proposed decisions (PS-U01).
- M0.3: consistency audit, record failed SSH honestly, local planning checkpoint if Git identity available, request owner review (PS-U01/U04).
- Exit: no application changes; all guide sources covered, blockers visible. **Owner approval required before M1.**

### M1 — local configuration and evidence foundation (first implementation)

Depends: approved M0; A09 format review. No Pi modification, install or listener needed.

- M1.1: Python packaging/test tooling, separate minimal edge/analysis dependency groups, bounded config and secret-free `.env.example` (PS-F01/U03).
- M1.2: versioned Event/raw schema, SQLite migrations, single transactional writer (PS-C02/E01).
- M1.3: canonical SHA-256 append-only chain, standalone verifier, tamper/concurrency/crash tests (PS-E02/E03).
- M1.4: actual health model/FastAPI health route tested in-process; DB/schema/writer failure injection, secret/log review (PS-F01/U04).

Acceptance: valid config loads; unsafe/invalid settings fail without secret echoes/import-time binding. Bound Unicode/size/non-finite inputs. Persisted events survive reopen. Independent known-byte hashes match. Deliberate content/link/insertion/interior-deletion/reordering tests identify broken/affected IDs. Concurrency cannot fork chain; interrupted transaction leaves no half-record; intact chain verifies. Disclose unanchored tail truncation/full rewrite limits. Raw data remains unchanged by enrichment. Run unit/integration/security tests on Windows, record commands/results and commit coherent milestone. Pi tests remain not executed until separately approved deployment/access.

### M2 — controlled real decoys and collection

Depends: M1; A01/A02 before lab traffic; A03 SSH selection.

- M2.1: real SSH protocol synthetic auth/session, bounded username/command/path events, credential discard (PS-C03/C05).
- M2.2: fake web/API login/routes/files/data and event integration isolated from management (PS-C04/C05).
- M2.3: independent network adapter, normalized connection telemetry, input/rate/concurrency/disk limits (PS-C01/O02/Z01).
- Acceptance: actual SSH/HTTP clients produce persisted verified events; no shell/forwarding/traversal/credential retention; independent authorized scan observations; visible failure/backpressure. Missing sensor permission blocks completion. Listeners/client traffic require approval; fixtures do not establish Pi success.

### M3 — sessions, features and labelled traces

Depends: M2; A06-A08 protocol/taxonomy/windows frozen.

- M3.1: deterministic session/window/cross-service linking and complete §10.1 vector with sequence/rate semantics (PS-S01/S02/S03).
- M3.2: bounded benign and A-E scenario drivers; independent run IDs, known start/end/stage truth and provenance (PS-D01/D02).
- M3.3: separate raw/processed/labels, grouped partitions and leakage checks; no generator truth in model inputs (PS-D03).
- Acceptance: every feature matches hand-count fixtures; deterministic replay; actual labelled runs with independent manifests and no split overlap. Report collection counts/failures honestly.

### M4 — reproducible baseline model

Depends: M3; review Pi runtime compatibility when inventory available.

- M4.1: PC training with exact guide RF baseline, training-only preprocessing, artifact/schema/run/code hashes (PS-ML01/D02/D03).
- M4.2: bounded inference, missing/version mismatch handling, actual held-out metrics/confusion matrix (PS-ML01/V03).
- Acceptance: deterministic fixture plus collected-data training, class order/probabilities/schema checks, group independence, trusted artifacts only (no untrusted pickle loading); measured artifact size/CPU/RAM on named machine. Weak results remain visible.

### M5 — explainable intent

Depends: M4.

- M5.1: evidence-backed versioned behaviour-to-intent mapping (PS-ML02).
- M5.2: actual Tree SHAP with signed values/exact provenance, bounded suspicious/on-demand scheduler, actual Pi budget when approved (PS-X01/X02/X03).
- Acceptance: class/output-space/additivity and provenance tests; intent labelled inference; timeout preserves collection. Windows SHAP execution does not satisfy on-Pi feasibility: PS-X03 stays unverified until measured there.

### M6 — safe adaptive control and response

Depends: M2/M3/M5; approved scope.

- M6.1: finite policy/executor, four risk levels, confidence gate/high-risk veto, simulated isolation (PS-P01/P02/I04/ML03).
- M6.2: real adaptive content and static baseline; cooldown/expiry/rollback/restart/emergency reset and decision/result audit (PS-A01/A02/A03/A04).
- Acceptance: all state/action/denial paths tested; SSH/web clients see actual profile change, static condition does not. No new listener/firewall/root command; expiry/restart/reset restore safe baseline; failed/denied actions audited; untrusted model text cannot execute.

### M7 — verified case reconstruction

Depends: M1/M3/M5/M6.

- M7.1: verified snapshot, timestamp/sequence handling and supported timeline/stages (PS-R01/R03/E05/Z02).
- M7.2: bounded NetworkX graph/JSON and evidence relations, partial export manifest (PS-R02/E04).
- Acceptance: known skew/order/late-event fixtures and collected multi-stage case compared to independent ground truth; all stages/edges have provenance. Tampered cases visibly unverified, never “repaired”; original unchanged during copy-tamper tests.

### M8 — grounded investigation and complete export

Depends: M7/M5/M6; A04/A05 approval and actual model availability.

- M8.1: analysis-side independent verification, bounded JSON, prompt/schema, statement citations, support/injection checks, report provenance/separation (PS-I01/I02/I03).
- M8.2: explicit deterministic outage report, seven-artifact bundle/offline verifier (PS-I05/E04/U03).
- Acceptance: an actual approved model generates reviewed report from collected evidence, all §15.3 sections, no unsupported facts/unknown IDs/OS tools; tampered inputs rejected. Timeout yields labelled non-AI fallback. No provider/model means AI requirements remain blocked, not “done by template”.

### M9 — operator API/dashboard and closed loop

Depends: M1-M8; no unapproved exposure.

- M9.1: every Appendix B route over actual state, auth/pagination, simple HTML/JS timeline/graph/evidence UI with escaped untrusted content (PS-UI01/UI02).
- M9.2: real-client end-to-end flow, policy audit, browser/API/evidence consistency and security tests (PS-G01/UI01/U04).
- Acceptance: browser -> API -> durable observation -> session/model/SHAP -> adaptive assets -> case/graph/integrity -> actual report/policy. Missing/degraded states explicit, never simulated success. In-process API checks do not substitute for browser or Pi tests.

### M10 — approved Pi hardening, experiments and delivery

Depends: M9 and earlier gates; A06/A11-A14 resolved as applicable. Individually verified earlier milestones may be deployed using the same approval gates; M10 finalizes integration, not permission for an unverified whole-stack deployment.

- M10.1: reproducible native install/services, pinned ARM artifacts, independent source/config/data backup, stepwise approved rollout and recovery (PS-F02/O04/G03/T03).
- M10.2: actual Pi stress/resources/degraded modes, all six comparisons, A-F and repeated final demo (PS-G02/O01/O03/V01-V10).
- M10.3: versioned source/dataset/model/case/evaluation manifest, report/presentation/limitations, approved tag/backup verification (PS-T01/T02/T03/U02/U04).
- Acceptance: inspect and retain real Pi outputs, raw samples and failed runs. Every comparison measured or explicitly blocked; no final completion before all required gates. No push/live isolation/destructive maintenance without separate approval.

### Dependency order and guide reconciliation

**M0 approval -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M9 -> M10.** This conservative spine suits a small resource-constrained project; independent checks within a milestone do not bypass gates.

| Guide sequence | Mapping / justified clarification |
|---|---|
| §19 week 1 foundation/Pi/status shell | M1 local foundation; Pi setup only with inventory/backup/approval; full real UI later. |
| week 2 decoys/events | M2, chain already present per Appendix C. |
| week 3 data/features/RF | M3-M4. |
| week 4 SHAP/intent | M5; stored/API-ready results before full UI. |
| week 5 adaptation | M6, finite safety policy first. |
| week 6 evidence/reconstruction | Hashing advanced to M1; reconstruction/export M7-M8. |
| week 7 investigator | M8 after independent verification. |
| week 8 policy/integration | Safety policy advanced to M6; operator integration M9. |
| weeks 9-10 hardening/install | M10 plus failure checks in every increment. |
| weeks 11-12 experiments/report | M10 final evaluation; protocol/instrumentation start earlier. |
| App. C steps 1-20 | Config/Event/SQLite/hash -> SSH/web -> sessions/features/data/RF -> SHAP/intent/deception -> timeline/graph -> policy/API/UI/AI -> tests/evaluation all retained. Safety policy/tests deliberately earlier; minimal real health API early; AI before final integrated UI. |

## 5. Evaluation protocol to freeze before experiments

The guide defines comparisons/metrics, not a supplied dataset, run count, numeric accuracy target or established improvement. No public dataset is mandated. Training and expensive analysis run on the PC. Independent unit: collection run; keep related/overlapping windows, sessions and paired variants in the same split group. Hold out scenario families where feasible to test template generalization. Fit preprocessing/tune thresholds only on training/validation; freeze then test. Record seeds, class support, run IDs, model/feature/code/package/OS versions and failures. Review scenario counts/repeats/load and tolerances before collection; do not invent completed runs.

| Comparison (§20.1) | Proposed operationalization requiring A11 review |
|---|---|
| Static vs adaptive | Same starting assets, bounded response-sensitive driver, matched work budgets/seeds, independent repeated runs, randomized condition order. Content must visibly change, not merely a UI flag. |
| ML with/without behavioural features | Full session/sequence vector vs preregistered network-count-only ablation, same group splits/model budget. Exact ablation is proposed, not specified by PDF. |
| ML with/without SHAP | Same trained predictions/workload, explanations on/off; latency/resources plus blinded analyst comprehension/usefulness. SHAP is not expected to change predicted classes. |
| Rule-only vs ML-assisted intent | Frozen rules vs versioned RF-assisted mapping on same held-out sessions; uncertainty/decision traces retained. |
| Raw events vs reconstructed stages | Frozen raw-event ordering/display baseline vs stage summarizer against independent ground truth; preregister stage matching/timing tolerance. |
| Local-only vs Pi+PC offload | Compatible bounded edge SHAP/reconstruction profiles vs offload on matched workload. Training/large LLM off Pi in both. Stop unsafe local profile and report infeasibility instead of forcing OOM. |

Preserve every §21 definition/collection method:

- Intent accuracy = correct predicted intent / labelled sessions (scenario truth); per-class/macro precision/recall/F1 (scikit-learn).
- Stage accuracy = correct reconstructed stages / labelled stages (ground-truth sequence); timeline accuracy = order/temporal alignment (event timestamps vs script).
- Engagement time = time engaged with decoys (case timestamps); depth = meaningful interactions (event classification); decoys reached = adaptive assets touched (deception logs). Idle padding/repeated noise are not engagement.
- Integrity = injected modifications detected (tampering tests); grounding = factual statements linked to evidence IDs (validator). Separately check semantic support: citation presence is not truth.
- CPU = average/peak Pi CPU; RAM = average/peak resident memory (psutil candidate); latency = feature-to-decision time (monotonic timestamps); network = bytes to analysis plane (system/network counters).
- Also retain §1.3 evidence completeness, attribution quality/analyst usefulness and storage overhead. Define denominators, sample interval, CPU normalization, unsupported classes, timestamp uncertainty and failure inclusion. Supplement, never replace, with confusion matrices, latency percentiles and uncertainty intervals.

Proposed operational safety guardrail, **not a guide value or measured result**: >=300 MiB available system memory under the agreed workload; no OOM/sustained swap as evidence of capacity; at most one optional explanation worker. Traffic/case-size/latency/accuracy gates require review. Exact analyst protocol may require willing participants; if unavailable, report usefulness evaluation blocked, not fabricate feedback.

## 6. Milestone evidence and review policy

Identify IDs/dependencies/acceptance before each increment. Prefer a failing test before fixing a bug. Implement smallest coherent behaviour, run unit/integration/security/E2E checks as appropriate, measure where relevant, review limits/secrets/failures. Update status and traceability with exact source, command/environment/result/artifact evidence. Commit coherent verified increments; mark unrun tests honestly. Do not proceed past unsatisfied dependencies. No directory skeleton, stub API, fake model/report or documentation-only feature is complete. Blocked work remains visible with next owner action/alternative.

This plan authorizes no remote install, new listener, firewall/system/security change, paid/cloud usage or destructive operation. Phase 1 ends with review request, not automatic implementation.
