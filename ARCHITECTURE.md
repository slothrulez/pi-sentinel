# PiSentinel architecture — proposed, not implemented

## 1. Boundaries and placement

Authority: guide cover/§§7-18, appendices A-C and user safety requirements. IDs/A01-A14 are in PROJECT_PLAN. Preserve the guide's **edge**, **analysis**, **presentation** planes and module terminology. All choices here await review/measurement.

| Component / plane | Placement and interface | Proposed implementation and constraints |
|---|---|---|
| SSH honeypot / edge | Pi, separate unprivileged process | Evaluate minimal maintained SSH library (candidate AsyncSSH) vs Cowrie; actual SSH protocol, virtual handlers, one instance/capped sessions, no shell/forwarding/SFTP/SCP/host files. Not selected/installed yet. |
| Web/API honeypot / edge | Pi, separate unprivileged process from management | Small FastAPI candidate with synthetic routes/content/profile; no client-driven host file/SQL operations. |
| Network observation / edge input | Approved narrow sensor/helper or independently trusted sensor | Connection/header metadata only, no payload. Capture privilege/location unresolved A02; no broad-root application. Missing sensor leaves scanning requirement incomplete. |
| Collector + evidence writer / edge | Pi core | Bounded validated local IPC, one serialized SQLite writer; only writer owns DB, decoys lack DB/control credentials. |
| Session builder + features / edge | Pi core | Incremental bounded windows over persisted observations, complete interpretable feature schema. No unbounded history scan per request. |
| Behaviour classifier + intent / edge | Pi core, single inference lane | Small scikit-learn RF baseline (50 trees, depth 8, one job, seed 42), finite intent mapping. Training never on Pi. |
| SHAP / edge with analysis fallback | Pi suspicious/on-demand; max one optional worker; trusted PC fallback | Real TreeExplainer bound to exact assessment. Timeout/defer optional work without losing collection; actual Pi peak/import cost must be measured. |
| Adaptive deception + policy / edge | Pi core | Deterministic state machine, confidence/risk safety veto, finite executor, TTL/cooldown/rollback; synthetic content changes inside approved services, never new sockets/firewall rules. |
| Evidence + independent verifier | Pi SQLite; offline verification on PC | Atomic immutable chain; read snapshots, restrictive permissions, independent closure checkpoints/backups. No DB/queue daemon. |
| Timeline + attack graph | Small bounded cases on Pi; large graphs/rendering PC/browser | Stage reducer + NetworkX candidate, graph JSON, pagination/case limits. Heavy analysis offloaded. |
| Model training + evaluation / analysis | Windows PC or approved trusted analysis machine | scikit-learn grouped pipeline, run manifests, dataset/code/model hashes. Bounded classical training; PC large-LLM capacity not assumed. |
| AI investigator / analysis | Trusted PC or approved provider | Re-verified bounded structured JSON, no OS tools, output/citation validation; separate labelled template fallback. No mandatory cloud to collect/control. |
| API + dashboard / presentation | Read API/static HTML/JS in core; browser on PC | FastAPI candidate, one HTTP worker, bounded queries/polling. No Node/React runtime or full monitoring stack on Pi. Management loopback + approved SSH tunnel proposed. |
| Service supervision | Native Pi units after approval | Least-privilege processes/protected data dirs; selective containers only after native benchmarks/confinement review. No service changes now. |

This is a **modular edge application with isolated decoy processes**, not unnecessary microservices. FastAPI/scikit-learn/SHAP/NetworkX are guide-recommended candidates; no library is assumed installed. Exact versions, security advisories, release age and ARM wheels must be reviewed/pinned during implementation. Prefer standard-library SQLite/JSON/hashlib when sufficient; avoid Redis/Kafka/PostgreSQL/vector stores/orchestration for MVP.

## 2. Data and control flow

```text
Authorized clients -> SSH/web decoys --------+
Approved independent network sensor --------+-> bounded validation/redaction
                                                      |
                                      atomic raw normalized observation append
                                                      |
                                              SQLite evidence chain
                                                      |
                                         sessions -> feature vector
                                                      |
                                        RF -> probability -> intent
                                                      +-> on-demand SHAP
                                                      |
                                      policy safety veto + deception state machine
                                                      |
                                      audit decision -> finite synthetic executor
                                                      |
                                        append result -> next observation

Verified snapshot -> timeline/graph/SHAP/policy -> full case bundle
    -> independent PC verification -> bounded JSON -> AI -> citation/support review
    -> separate derived report -> operator UI
Operator UI -> authenticated read API -> actual persisted/derived state
AI recommendation -> finite policy validation, never OS/shell execution
```

§7.1 draws evidence after adaptation as logical flow. Appendix C/forensic safety require raw observation persistence **before** enrichment/control: append observations first, derived assessments/decisions/results afterward. The control loop never waits for an LLM; report generation is asynchronous/explicit analysis. Policy constrains every action before execution even though §12 pseudocode checks high risk late.

## 3. Proposed versioned contracts

### Observation and guide §9 fields

Raw observation: schema version, event ID, case ID, durable ingest sequence, source-observed timestamp and normalized UTC ingest timestamp, source IP, transport ID, destination port/service, event type/action, bounded allowlisted metadata and severity basis. Preserve original time offset/source where provided. A transport session reference may be known on ingress; later behavioural-session membership is a separate append, not a mutation. IP is an endpoint observation, not personal identity.

`previous_hash/current_hash` belong in chain envelope; §9 `model_label/confidence/shap_summary/response_action` are linked derived assessment/decision records joined in the API's versioned event view. All guide fields remain representable; already-hashed raw input is never rewritten when models, session correlation or policy change. Ground-truth labels belong in separate training/evaluation manifests, not inference inputs.

“Raw” means **raw normalized privacy-filtered observations** per §13.3 `events.jsonl`, not lossless packets/passwords/request bodies. Discard passwords/tokens at boundary; apply secret/length/character checks to usernames/paths/commands too. Prefer counts/flags to unnecessary values. Log rejection categories, not rejected payload. Packet/raw-log retention needs a separate scope/privacy decision, not implied permission.

Initial limits proposed for M1/M2 review, not guide values/tested capacity: 16 KiB normalized record, 256-character username, 2 KiB command/path, 8 KiB HTTP body only where necessary (never generically logged); bounded fields/nesting/session counts/queues/rates. Configurable safe upper bounds and exact failure behaviour required. Do not log headers/cookies/authorization/query secrets or stack-local credential values.

### Sessions, features, assessments and control

- `SessionSummary`: source/scope/transport links, start/end/idle-window rules, ordered evidence IDs, missing-source flags and correlation uncertainty.
- `FeatureVector`: schema version, ordered numeric names/values/units, window bounds, evidence IDs/extractor version; complete §10.1 families. Rate/short-duration examples map to declared numeric features, not invented display labels.
- `Assessment`: trusted model hash/version, training manifest, exact vector, class-ordered probabilities, behaviour/confidence semantics, inferred intent and supporting IDs. RF probabilities are not calibrated certainty or proof of intent; calibration would require separate measurement.
- `Explanation`: assessment/model/vector reference, SHAP method/library/output space/class, base value and full signed contributions/top positive/negative features plus measured cost. Failure means unavailable, not zero attribution.
- `Decision/Result`: policy/state versions, evidence/assessment references, risk/confidence/context, requested/approved action/denial/reason, prior/next synthetic state, scope, TTL/cooldown, rollback token and actual result.
- `TimelineStage/Graph`: explicit observed/inferred relation kinds with evidence references. Time adjacency is not causal proof; model hypotheses are not observed actions.

### Hash-chain format (A09; review/freeze/test at M1)

M1 implemented this as chain format v1; exact rules, vectors and tested limits: [docs/EVIDENCE_CHAIN.md](docs/EVIDENCE_CHAIN.md).

Per bounded collection case/run, one writer assigns strictly increasing durable sequences. Concurrent sessions may share a case. Case time/size limits and closure/rotation never imply deletion. Records distinguish observation, session-association, assessment, explanation, decision, result and closure; derived records are not counted as raw interactions.

Proposed format v1 matching §13.1:

```text
content = versioned payload including case_id, sequence, record_type, event_id
canonical_event_json = UTF-8 JSON(content), sorted keys, compact separators,
                       no duplicate keys / NaN / Infinity / ambiguous numbers
previous_hash = prior record SHA-256 lowercase 64-char hex, or 64 zeroes at genesis
current_hash = SHA256(canonical_event_json_bytes || ASCII(previous_hash)).hexdigest()
```

Hash fields are excluded from content to avoid self-hashing/double inclusion. Define number/time/Unicode rules and independent known-byte fixtures before claiming cross-platform canonicalization. A single transaction inserts record/advances head; acknowledge only after commit. Parameterized SQL, durability, concurrent reads and WAL-safe SQLite backup need tests; copying just a live DB without WAL handling is unsafe.

Verifier starts at genesis, checks hashes/links/sequence/case scope, and reports first failure plus affected descendants. Closed-case manifest contains count, first/last sequence, head, scope, versions and artifact digests. A **separately retained trusted checkpoint** on the analysis machine reveals truncation/substitution relative to it. Manifest beside DB is not independent anchoring. Export full case chain, not an unverifiable filtered subset. Redacted/subset exports are labelled derivatives with weaker guarantees.

**Limits:** unkeyed chaining cannot establish origin, completeness, legal admissibility, prevent privileged modification, detect a fully recomputed rewrite, or detect tail truncation without independent expected length/head. It is not a signature/encryption/access-control mechanism. PS-OPT07 signatures remain optional, not claimed. Permission separation, protected independent backups/checkpoints and explicit negative-guarantee tests remain necessary.

### Persistence and backpressure

Writer owns cases/chain/migrations; read-side indexed projections can be rebuilt, originals cannot be edited. Proposed IPC: protected Unix-domain socket on Pi, authenticated local/in-process equivalent in Windows tests. Typed size-limited envelopes and authorized producer UIDs; concrete Windows-compatible adapter selected in M1/M2. No unauthenticated exposed ingestion API.

Ack only after durable commit. Bound queues/cache/storage. Writer/disk-full failure returns visible unhealthy/degraded state and rejects/closes new decoy interactions as necessary with loss/rejection counters; never claim unpersisted evidence was saved. Optional model/SHAP/report/UI yields before collection. No unapproved automatic evidence deletion. Restart recovers committed sequence and resets unknown/expired synthetic state with audited reconciliation.

## 4. Operator and analysis interfaces

All eleven Appendix B GET routes are **planned**, not implemented:

| Route | Actual source / semantics |
|---|---|
| `/health` | Writer/schema/storage/worker status, distinguish healthy/degraded/unavailable. |
| `/events` | Bounded paginated observation view with linked enrichment. |
| `/sessions` | Bounded session summaries. |
| `/sessions/{id}` | Scope, features, behaviour, inferred intent and evidence. |
| `/explanations/{id}` | Exact SHAP record or explicit not-generated/failed state. |
| `/cases/{id}` | Scope, provenance, versions and case state. |
| `/cases/{id}/timeline` | Supported stage sequence/evidence/uncertainty. |
| `/cases/{id}/integrity` | Actual verified range/head/result/check time. |
| `/decoy/state` | Actual current profile/TTL/cooldown/rollback state. |
| `/policy/decision` | Scoped audited decision and outcome. |
| `/reports/{id}` | Validated stored AI report or clearly non-AI template. |

GET must not perform control changes. Expensive verification is explicit or bounded/cached with verified-head freshness. Report generation/case closure/reset may initially be approved local CLI operations; future POST control APIs require auth/CSRF/scope review. No arbitrary command endpoint. Management loopback by default through approved SSH forwarding; any LAN access needs reviewed auth/TLS/interface design. Distinct decoy/real administrative SSH/control bindings; ports/interfaces require A01 approval.

Bundle (§13.3): `events.jsonl`, `case.json`, `timeline.json`, `attack_graph.json`, `integrity_report.json`, `shap.json`, `investigator_report.md`. Versioned manifest includes hashes/provenance/scope/verification boundary. Investigator input follows §15.2 `case_id`, `integrity`, `timeline`, `attack_graph`, `intent`, `shap`, `evidence`; independently verify records/derived provenance rather than trusting a supplied `status: verified` string. Derived artifacts require recomputation or explicit provenance/digest checks. AI assertions stay separate from raw evidence.

## 5. Hardware feasibility — estimates, not measured results

Guide §18 approximate **MB** ranges (not measurements):

| Component | Guide budget | Proposed discipline |
|---|---|---|
| Minimal 64-bit OS | 300-500 MB | Verify actual OS/background services; do not reflash without approval. |
| Collector/API | 50-150 MB | One core process/HTTP worker, bounded queue. |
| SQLite | 20-100 MB | Embedded; limited cache/queries, not a daemon. |
| SSH honeypot | 100-250 MB | One protocol implementation, capped sessions. |
| Web honeypot | 30-100 MB | One synthetic app, no full stack/real DB. |
| ML inference | 50-150 MB | One job; measure import/resident forest/native library cost. |
| SHAP transient | 100-300 MB | Max one optional worker, timeout/defer/offload. |
| Dashboard server | 50-150 MB | Share API/static hosting; PC/browser heavy rendering. |
| Heavy analysis | Offloaded | No Pi training/LLM. |

Naive sum: 600-1400 MB without SHAP, 700-1700 MB including it. Categories overlap in shared processes and may underestimate native/transient peaks: this does **not** prove 2 GB feasibility. Proposed guardrail (not guide mandate/result): >=300 MiB available system memory during agreed workload, no OOM/sustained swap as capacity evidence, bounded queues/storage. Measure RSS/PSS if available, total/available memory, CPU average/peak, temperature/throttling, startup/import peaks, concurrent SSH+HTTP+SHAP, latency, disk growth and long-run drift on actual Pi. No resource benchmark ran in Phase 1.

If budgets fail: defer/offload SHAP and large graphs first; cap workload; version/evaluate any model reduction; avoid containers; disable optional UI hosting. Preserve capture and safe local policy. Offload latency/network cost must be measured. Inspected Windows PC has 7.88 GiB RAM, i5-6200U/four logical processors: bounded classical training is plausible but still requires measurement; large local LLM is not assumed practical.

## 6. Repository and deployment model

Preserve Appendix A logical names when implementing: `edge/{collector,decoys/ssh,decoys/web,features,model,explain,deception,evidence,reconstruction,policy,api}`, `analysis/{training,shap_reports,graphs,investigator}`, `dashboard`, `scenarios`, `data/{raw,processed,cases}`, `docs`, `scripts`. No empty feature tree now. Test groups: unit/integration/security/e2e/pi/evaluation. Packaging may consolidate shared code, not create a process per module.

Native Windows development and separate Linux/ARM verification; source/config templates versioned, runtime secrets/evidence separate and protected. Lock minimal dependency groups and artifact hashes. Approved reproducible native Pi install/services first, containers only if measurements/confinement justify them. Apply one locally verified milestone at a time with target inventory, independent backups, exact-command approval, actual Pi tests and rollback; see SECURITY. Reflashing/static-IP/firewall/capability/package/service changes are never automatic prerequisites we may perform without approval.

## 7. Proposed decision records

- ADR-01: guide's three planes retained; no unapproved cloud requirement.
- ADR-02: modular native core + separate least-privilege decoys, no heavyweight infrastructure.
- ADR-03: immutable sanitized observations before enrichment; guide event view joins derived records.
- ADR-04: versioned per-case chain, independent verifier/checkpoints and explicit rewrite/truncation limits.
- ADR-05: policy safety veto before deterministic deception; LLM outside control path.
- ADR-06: actual SSH/HTTP protocols and independent scan observations, no banner/mock substitute.
- ADR-07: on-demand SHAP measured on Pi; bounded offload/degraded mode rather than assumed capacity.
- ADR-08: direct verified JSON context for MVP AI pending owner A04 interpretation of diagram “RAG”.
- ADR-09: simple HTML/JS, no Pi Node runtime/paid provider needed for collection and policy.

All decisions are proposed for review; material deviations require plan/traceability changes before implementation.
