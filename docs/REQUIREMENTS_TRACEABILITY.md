# PiSentinel requirements traceability

## Interpretation and evidence rules

Baseline: `../PiSentinel-Master-Guide.pdf`, 23 pages, SHA-256 `a5cde730f8d99d615e017fe15d138c1e6962b634b2cad5a06b9248e0e46e20ea`. References are physical PDF pages. Full requirement wording/origin/priority is in `../PROJECT_PLAN.md`; A01-A14 and architecture ADRs are proposals, not specification facts.

**Every test path below is planned, not an existing test. No application source has been created.** Tasks map to named milestones/subtasks in PROJECT_PLAN. After implementation, add exact source path/symbol, test command/node, environment, run date, inspected result and artifact/commit evidence. Separate tests created/executed/pass/fail/not-run, local/remote results, estimates and actual metrics. Never renumber IDs. Optional rows remain visible/deferred. Documentation does not satisfy application acceptance.

## Requirement -> task -> planned test -> acceptance -> actual evidence

| Stable ID | Source (physical pages) | Tasks | Planned test / check | Acceptance evidence required | Actual source / executed result |
|---|---|---|---|---|---|
| PS-G01 | pp. 1-5 §§1, 3-5; p. 19 §25 | M9.2 | `tests/e2e/test_closed_loop.py` | Real interaction traverses collection through response with linked evidence, not UI-only flags. | Not implemented; test not created/run; no source/completion evidence. |
| PS-G02 | p. 1 scope; pp. 7, 15 §§7, 18 | M10.2 | `tests/pi/test_resource_profile.py` | Actual Pi mean/peak samples and workload retained; no OOM/unexplained loss at agreed load. | Not implemented; test not created/run; no source/completion evidence. |
| PS-G03 | pp. 6-7, 15, 18-19 §§6.2, 7.2, 17-18, 25 | M10.1 | `tests/pi/test_deployment_profile.py` | Process/package inventory confirms approved lightweight edge and offloaded work/exclusions. | Not implemented; test not created/run; no source/completion evidence. |
| PS-F01 | p. 15 §19 week 1; p. 22 Apps. B-C | M1.1/M1.2/M1.4 | `tests/integration/test_foundation.py` | Invalid config and DB/writer failure visible; durable schema round-trip; no secrets/listeners by default. | Not implemented; test not created/run; no source/completion evidence. |
| PS-F02 | pp. 15, 19-20 §§19, 26, 29 | M10.1 | `tests/pi/test_install_recovery.py` | Approved reproducible install and new-location recovery verified on actual Pi. | Not implemented; test not created/run; no source/completion evidence. |
| PS-C01 | pp. 4-5, 7 §§4-5, 8.1; p. 17 scenario A | M2.3 | `tests/integration/test_network_sensor.py` | Independent real network observations cover multi-port scan; generator truth is not sensor input. | Not implemented; test not created/run; no source/completion evidence. |
| PS-C02 | p. 9 §9; user data validation | M1.2 | `tests/unit/test_event_schema.py` | All guide fields represented; bounded malformed/Unicode/non-finite input; enrichment cannot mutate observations. | Not implemented; test not created/run; no source/completion evidence. |
| PS-C03 | pp. 7-8 §8.2; p. 17 scenarios B-C | M2.1 | `tests/integration/test_ssh_decoy.py` | Standard SSH client reaches synthetic auth/session/commands/files; no shell/filesystem/forwarding escape. | Not implemented; test not created/run; no source/completion evidence. |
| PS-C04 | p. 8 §8.3; p. 17 scenario D | M2.2 | `tests/integration/test_web_decoy.py` | Actual HTTP probes yield persisted events and synthetic responses; traversal/oversize/control access denied. | Not implemented; test not created/run; no source/completion evidence. |
| PS-C05 | p. 5 §5.2; p. 18 §23; user security rules | M2.1/M2.2 | `tests/security/test_sensitive_input.py` | Canary password/token absent in DB/logs/errors/bundles/reports after real submitted input. | Not implemented; test not created/run; no source/completion evidence. |
| PS-S01 | p. 8 §8.4; p. 10 §10 | M3.1 | `tests/unit/test_sessions.py` | Timeout/boundary/concurrent source/restart/cross-service fixtures give deterministic uncertain linkage. | Not implemented; test not created/run; no source/completion evidence. |
| PS-S02 | p. 10 §10.1 | M3.1 | `tests/unit/test_features.py` | Every listed feature matches manual counts with units/window/missing-data semantics. | Not implemented; test not created/run; no source/completion evidence. |
| PS-S03 | pp. 10-11 §§10.1, 11.1 | M3.1 | `tests/unit/test_sequence_features.py` | Transition/repetition/rate fixtures match frozen formulas; missing sensor not silently observed zero. | Not implemented; test not created/run; no source/completion evidence. |
| PS-D01 | p. 10 §10.4; pp. 16, 19 §§19, 26 | M3.2 | `tests/integration/test_dataset_provenance.py` | Actual independent runs retain labels/time/stage/provenance apart from inference input. | Not implemented; test not created/run; no source/completion evidence. |
| PS-D02 | p. 10 §10.2 | M3.2/M4.1 | `tests/unit/test_label_contract.py` | Seven-label mapping and SSH/web stage tags explicit; unsupported/mixed labels not fabricated. | Not implemented; test not created/run; no source/completion evidence. |
| PS-D03 | p. 16 §19 week 3; user evaluation rules | M3.3/M4.1 | `tests/security/test_dataset_leakage.py` | Group-disjoint manifests and training-only fit assertions; no final-test tuning. | Not implemented; test not created/run; no source/completion evidence. |
| PS-ML01 | p. 10 §§10.3-10.4; pp. 14-15 §17 | M4.1/M4.2 | `tests/integration/test_model_pipeline.py` | Actual versioned training artifact, class probabilities and held-out metrics; Pi compatibility separate. | Not implemented; test not created/run; no source/completion evidence. |
| PS-ML02 | p. 8 §§8.5-8.6; pp. 9-10 §§9-10 | M5.1 | `tests/unit/test_intent.py` | Assessment links exact model/vector/schema/evidence; inference distinguished from fact. | Not implemented; test not created/run; no source/completion evidence. |
| PS-ML03 | p. 18 §24; p. 19 §25 | M6.1 | `tests/security/test_uncertain_policy.py` | Low confidence/missing features/corrupt model cannot trigger unsupported containment; audit fallback. | Not implemented; test not created/run; no source/completion evidence. |
| PS-X01 | pp. 8, 10-11 §§8.7, 11 | M5.2 | `tests/integration/test_shap.py` | Real TreeExplainer class/output alignment, signed contributions and numerical additivity tolerance checked. | Not implemented; test not created/run; no source/completion evidence. |
| PS-X02 | p. 11 §§11.2-11.3; p. 20 §29 | M5.2 | `tests/unit/test_explanation_provenance.py` | Stored explanation reproduces exact vector/model/class/base value/contributions. | Not implemented; test not created/run; no source/completion evidence. |
| PS-X03 | pp. 8, 11, 15, 18 §§8.7, 11.3, 18, 24 | M5.2 | `tests/pi/test_explanation_budget.py` | Actual Pi import/latency/peak memory measured; timeout/pressure defers visibly and preserves collection. | Not implemented; test not created/run; no source/completion evidence. |
| PS-A01 | pp. 11-12 §12 | M6.2 | `tests/unit/test_deception_states.py` | Recon/SSH enumeration/credential/web/data/high-risk/fallback state tests cover table and veto. | Not implemented; test not created/run; no source/completion evidence. |
| PS-A02 | pp. 11-12 §12.1; p. 17 scenarios B-E | M6.2 | `tests/integration/test_adaptive_assets.py` | Client sees real synthetic next asset; static mode unchanged; no automatic new sockets. | Not implemented; test not created/run; no source/completion evidence. |
| PS-A03 | p. 8 §8.8; pp. 16, 18, 20 §§19, 23-24, 29 | M6.2 | `tests/unit/test_action_lifecycle.py` | Fake-clock TTL/cooldown, restart and emergency reset restore safe baseline. | Not implemented; test not created/run; no source/completion evidence. |
| PS-A04 | p. 12 §12.3; pp. 16, 18 §§19, 23 | M6.1/M6.2 | `tests/integration/test_decision_audit.py` | Allowed/denied/failed/expired actions linked to durable decision/result; unauditable changes fail closed. | Not implemented; test not created/run; no source/completion evidence. |
| PS-E01 | pp. 8-9, 12-13 §§8.9, 9, 13.3; user evidence rules | M1.2/M1.3 | `tests/integration/test_raw_before_enrichment.py` | Acknowledged raw data survives worker failure/reopen and remains unchanged by enrichment. | Not implemented; test not created/run; no source/completion evidence. |
| PS-E02 | p. 12 §13.1/diagram; p. 22 App. C steps 2-3 | M1.3 | `tests/unit/test_hash_chain.py` | Independent known-byte fixtures and concurrent transactions verify deterministic atomic nonforking chain. | Not implemented; test not created/run; no source/completion evidence. |
| PS-E03 | p. 12 §13.2; p. 17 scenario F; user integrity rules | M1.3 | `tests/security/test_tamper_detection.py` | Modify/link/insert/delete/reorder tests identify break/affected IDs; rewrite/truncation limits explicitly tested. | Not implemented; test not created/run; no source/completion evidence. |
| PS-E04 | p. 13 §13.3; pp. 16, 19 §§19, 26 | M7.2/M8.2 | `tests/integration/test_case_export.py` | Collected completed case includes seven genuine consistent artifacts and standalone offline verification. | Not implemented; test not created/run; no source/completion evidence. |
| PS-E05 | pp. 8, 13-14, 18 §§8.11, 15, 24 | M7.1 | `tests/security/test_integrity_failure.py` | Tampered case inspectable only as unverified; verified-only/LLM paths reject without repairing original. | Not implemented; test not created/run; no source/completion evidence. |
| PS-R01 | p. 13 §14.1 | M7.1 | `tests/unit/test_timeline.py` | Known and collected stage sequences match supported truth; missing stages not invented. | Not implemented; test not created/run; no source/completion evidence. |
| PS-R02 | p. 13 §14.2; pp. 15, 19 §§17, 26 | M7.2 | `tests/unit/test_attack_graph.py` | Graph relations resolve to evidence or marked inference; JSON/view agree without unsupported causality. | Not implemented; test not created/run; no source/completion evidence. |
| PS-R03 | p. 18 §24 | M7.1 | `tests/unit/test_event_ordering.py` | Equal/backward times, late arrivals/restarts preserve ingest order and visible clock uncertainty. | Not implemented; test not created/run; no source/completion evidence. |
| PS-I01 | pp. 1, 7, 13-14 scope/§§7, 15.1-15.2 | M8.1 | `tests/security/test_investigator_input.py` | Independent local verification rejects tamper/unknown references; bounded permitted evidence only, no credentials/tools. | Not implemented; check not created/run; no source/completion evidence. |
| PS-I02 | p. 14 §15.3 | M8.1 | `tests/integration/test_investigator_report.py` | Actual approved model generates all six sections from collected case, stored separately with provenance. | Not implemented; check not created/run; no source/completion evidence. |
| PS-I03 | p. 14 §15.4; p. 18 §24 | M8.1 | `tests/security/test_report_grounding.py` | Unknown IDs/unsupported factual claims/prompt injection rejected or flagged; semantic review distinct from citation count. | Not implemented; check not created/run; no source/completion evidence. |
| PS-I04 | pp. 5, 9, 14, 18 §§5, 8.12, 15.4, 16.1, 23 | M6.1 | `tests/security/test_no_ai_execution.py` | No OS/shell/tool execution interface; free-form/unknown recommendations cannot become actions. | Not implemented; check not created/run; no source/completion evidence. |
| PS-I05 | p. 18 §24 | M8.2 | `tests/integration/test_ai_outage.py` | Timeout/network/schema failure yields explicitly non-AI cited template, never counted as actual LLM result. | Not implemented; check not created/run; no source/completion evidence. |
| PS-P01 | p. 14 §16 | M6.1 | `tests/unit/test_risk_policy.py` | Four risk levels/confidence/context/veto tested; simulated isolation explicit, OS state changes disabled by default. | Not implemented; check not created/run; no source/completion evidence. |
| PS-P02 | pp. 5, 14, 18 §§5, 16.1, 23; user approvals | M6.1 | `tests/security/test_action_authorization.py` | Out-of-scope targets/actions denied, management excluded; real app restrictions work without firewall changes. | Not implemented; check not created/run; no source/completion evidence. |
| PS-UI01 | p. 9 §8.13; pp. 17-18 §22.1; p. 20 §29 | M9.1/M9.2 | `tests/e2e/test_operator_case.py` | Actual case visible end-to-end, untrusted fields escaped, missing/degraded states no fake green success. | Not implemented; check not created/run; no source/completion evidence. |
| PS-UI02 | p. 22 App. B | M9.1 | `tests/integration/test_api_contract.py` | All eleven exact routes return genuine bounded authorized state; no stubs or success for missing data. | Not implemented; check not created/run; no source/completion evidence. |
| PS-O01 | pp. 2-3, 15, 17 §§1.3, 18, 21 | M10.2 | `tests/pi/test_measurement_pipeline.py` | Actual sampled CPU/RSS/system memory/latency/disk/network with units/workload/interval/versions. | Not implemented; check not created/run; no source/completion evidence. |
| PS-O02 | pp. 15, 18 §§18, 23-24; user validation | M2.3 | `tests/security/test_resource_limits.py` | Load/oversize/writer-down/disk-full expose errors/counters and cannot ack unpersisted evidence. | Not implemented; check not created/run; no source/completion evidence. |
| PS-O03 | p. 18 §24 | M10.2 | `tests/integration/test_degraded_modes.py` | Pressure/slow SHAP defers optional work visibly with cooldowns while preserving core safety/collection. | Not implemented; check not created/run; no source/completion evidence. |
| PS-O04 | pp. 15-16, 19-20 §§19, 26, 29; user deployment | M10.1 | `tests/pi/test_milestone_rollout.py` | Approved commands/backups, per-milestone Pi tests and recoverable previous release verified. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V01 | p. 16 §20.1 | M10.2 | `tests/evaluation/test_comparison_protocol.py` | All six frozen comparison manifests and actual outputs, or explicit unresolved blockers; no substituted study. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V02 | p. 17 §20.2 | M10.2 | `tests/evaluation/test_run_manifest.py` | Repeated independent runs retain seeds/versions/raw evidence/failures and reproducible metrics. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V03 | p. 17 §21 | M4.2/M10.2 | `tests/evaluation/test_classification_metrics.py` | Actual group-held-out intent accuracy/per-class/macro metrics, support/confusion matrix and zero-support policy. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V04 | p. 17 §21 | M10.2 | `tests/evaluation/test_reconstruction_metrics.py` | Frozen matching/order/timing rules compare reconstructed stages against independent ground truth. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V05 | p. 17 §21; p. 19 §27 | M10.2 | `tests/evaluation/test_engagement_metrics.py` | Matched response-sensitive static/adaptive runs measure genuine time/depth/assets without idle-padding bias. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V06 | p. 2 §1.3; p. 17 §21/scenario F | M1.3/M10.2 | `tests/evaluation/test_integrity_metrics.py` | Mutation matrix and independent expected-event ledger yield measured detection/completeness and disclosed limitations. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V07 | p. 2 §1.3; p. 17 §21 | M10.2 | `tests/evaluation/test_grounding_metrics.py` | Citation coverage vs semantic support separated; SHAP fidelity/usefulness protocol executed or explicitly blocked. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V08 | pp. 2-3, 15, 17 §§1.3, 18, 21 | M10.2 | `tests/evaluation/test_resource_metrics.py` | Real Pi average/peak CPU/RSS, monotonic latency and offload/storage bytes with workload/sampling definition. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V09 | p. 17 §22 | M10.2 | `tests/e2e/test_scenarios_a_to_f.py` | Each actual authorized A-F run has observed inputs/expected outcome/inspected evidence; tamper only disposable copy. | Not implemented; check not created/run; no source/completion evidence. |
| PS-V10 | pp. 17-18 §22.1; p. 20 §29 | M10.2 | `tests/e2e/test_final_demo.py` | Full guide demo repeated with saved actual run evidence; missing model/sensor/access remains incomplete. | Not implemented; check not created/run; no source/completion evidence. |
| PS-Z01 | p. 5 §5; p. 18 §23 | M2.3 | `tests/security/test_lab_scope.py` | Approved topology/interface/source allowlist before listeners/scans; private IP not accepted as isolation proof. | Not implemented; check not created/run; no source/completion evidence. |
| PS-Z02 | p. 18 §§23-24 | M7.1 | `tests/security/test_case_preservation.py` | Tamper tests touch new copies, original digest unchanged; backup restores only to new approved location. | Not implemented; check not created/run; no source/completion evidence. |
| PS-T01 | p. 19 §26; p. 20 §29; p. 22 App. A | M10.3 | `tests/evaluation/test_release_artifacts.py` | Release references real source/dataset/model/case/verifier/views/report artifacts with hashes and successful checks. | Not implemented; check not created/run; no source/completion evidence. |
| PS-T02 | pp. 19-21 §§26-29 | M10.3 | `tests/evaluation/test_final_package.py` | Docs/report/presentation cite actual results/failures/limits, not legal authenticity or proven-intent claims. | Not implemented; check not created/run; no source/completion evidence. |
| PS-T03 | pp. 15, 20 §§17, 29 | M10.1/M10.3 | `tests/evaluation/test_release_recovery.py` | Approved local tag and independent backup recoverability verified; no unauthorized push. | Not implemented; check not created/run; no source/completion evidence. |
| PS-U01 | User FIRST TASK / PHASE 1 | M0.1/M0.2/M0.3 | `Planning document audit` | Six requested documents, complete PDF review, local inventory and blocked SSH honest; no application implementation. | Planning documents/read-only local inspection complete; 29-check local audit PASS, details in PROJECT_STATUS. SSH inventory blocked/auth failed. Owner approval pending; no application source. |
| PS-U02 | User security/deployment/working rules | M10.1 and every milestone | `Approval/command log review` | Every privileged/network/system/destructive action separately approved; read-only access never implies deployment permission. | Not implemented; check not created/run; no source/completion evidence. |
| PS-U03 | User PHASE 2 / working rules | M1.1/M8.2 | `tests/security/test_dependency_and_secret_policy.py` | Reviewed compatible locked dependencies and approved AI destination/cost/data policy; offline core, no secret source. | Not implemented; check not created/run; no source/completion evidence. |
| PS-U04 | User primary objective/testing | M0.3 and every milestone | `Milestone evidence review` | Each implementation claim has inspected command/environment/source/test evidence; unrun/failed/blocked explicit. | Not implemented; check not created/run; no source/completion evidence. |

## Optional requirement disposition

All optional rows are P2, deferred/not implemented/not tested; required core variants remain required.

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

## Full source coverage ledger

Reading coverage is specification analysis, **not application completion**. All entries read; visual review covered all pages in contact sheets, with full-resolution architecture/metrics/failure tables as needed.

| Physical pages | Source | Captured by / extraction notes |
|---|---|---|
| 1 | Cover scope and architecture diagram | PS-G01/G02/G03/C01/E02/I01/P01; A04. Network+decoys, ML+rules+SHAP, SQLite/SHA-256, reconstruction, laptop/API “grounded RAG”, closed-loop arrows visually recovered (diagram absent from extracted text). |
| 2-3 | §1 overview/research/contribution table | PS-G01/V01/V06/V07/V08/T02. Edge-overhead row continues p. 3; claims require experiments, not assumed improvement. |
| 3 | §2 navigation | No independent feature; listed §§3-29 all present. |
| 4 | §§3-4 gap table and eleven-step loop | PS-G01/C01/S01/ML02/X01/A01/E01/R01/I01/P01. Forensic capture part of loop. |
| 5 | Adaptive loop diagram; §5 lab/threat boundaries | PS-Z01/C01/C03/C04/C05/S03/I04/P02. Synthetic controlled environment, no unrestricted AI/root/production data. |
| 6 | §6 minimum/optional scope table and exclusions | PS-G03 and PS-OPT01-OPT10. Core graph also required by §§14/26/29 even though §6 table only names timeline. |
| 7 | §7 architecture/flow/three-plane table; §§8.1-8.2 | PS-G01/G02/G03/C01/C03; A03/A04/A10. Diagram arrows and edge/analysis/presentation responsibilities checked. |
| 8 | §§8.3-8.11 module responsibilities/outputs | PS-C04/S01/ML01/ML02/X01/A01/A03/E01/R01/R02/I01. Action expiry/rollback and prediction/fact distinction retained. |
| 9 | §§8.12-8.13, §9 schema/example | PS-P02/UI01/C02/E01/ML02/X02/A04. All guide fields retained via immutable observation plus joined derived records. |
| 10 | §10 features/labels/RF/dataset; §11 start/example | PS-S02/S03/D01/D02/D03/ML01/X01. Exact RF example adopted; labels remain suggested taxonomy. |
| 11 | §11 continuation/pipeline/limits; §12 loop/state table | PS-X01/X02/X03/A01/A02; A07. Signed values/model+vector version, no per-packet SHAP or intent proof. |
| 12 | §12 continuation/pseudocode; §13 chain diagram/design/verify | PS-A01/A03/A04/E02/E03/P01; A09/A10. High-risk table continuation and non-reset list numbering accounted for. |
| 13 | §13.3 seven artifacts; §14 timeline/graph; §15 role/input start | PS-E04/R01/R02/I01. All filenames/graph relationships retained; input JSON continues p. 14. |
| 14 | §15 input/report/guardrails; §16 risk table; §17 stack start | PS-I01/I02/I03/I04/P01/P02/ML01/UI02; A03/A05. All four risk levels and finite executor retained. |
| 15 | §17 stack end; §18 budget; §19 weeks 1-2 | PS-G02/G03/F01/F02/C03/C04/X03/O01; A12. Approximate budgets are estimates only. |
| 16 | §19 weeks 3-12; §20.1 six comparisons | PS-D01/D03/ML01/X01/A01/E04/R01/I02/P01/O04/V01/T02. Guide week labels are not our time estimate. |
| 17 | §20.2 protocol; §21 metrics; §22 scenarios/demo start | PS-V02-V10/O01. Full-resolution table checked: every metric/collection pair retained; no numeric thresholds supplied. |
| 18 | §22 demo end; §23 safety; §24 eight fallbacks; §25 start | PS-V10/Z01/Z02/O02/O03/ML03/A03/E05/R03/I03/I05/G03. Full-resolution table checked: uncertainty, slow SHAP, RAM, oscillation, hallucination, broken chain, skew, AI outage. |
| 19 | §25 end; §26 deliverables; §27 viva | PS-G01/G03/ML02/T01/T02/V01/E03/I04. Main research variable and limits on claims preserved. |
| 20-21 | §27 limitation; §28 glossary; §29 final checklist | PS-T01/T02/T03 and crosswalk below. Final report/presentation continues p. 21. |
| 22 | App. A structure; App. B eleven GET routes; App. C first five steps | PS-T01/UI02/F01/C02/E02/C03/C04. Suggestions vs mandatory requirements explicit. |
| 23 | App. C remaining steps 6-20 | M3-M10 and A10. No omitted coding-order item; tests and safety policy advanced deliberately. |

No PDF page/diagram/table/appendix was inaccessible. The guide does **not** supply runnable source/tests, actual dataset/model, exact network sensor, run counts, numeric quality/latency thresholds, canonicalization/genesis/anchor rules, AI provider/cost or target OS/access credentials. These cannot be extracted/verified as if present; A01-A14 retain the gaps.

## §29 final-checklist crosswalk

All application checklist items remain **not implemented/not verified**.

| Checklist item | Stable IDs |
|---|---|
| Pi reproducible; private lab documented | PS-F02/O04/Z01 |
| SSH/web work | PS-C03/C04/C05 |
| Normalized events; sessions work | PS-C02/S01/S02/S03 |
| Labelled dataset; baseline ML measured | PS-D01/D02/D03/ML01/V03 |
| Suspicious SHAP stored; confidence displayed | PS-X01/X02/X03/ML02/UI01 |
| Adaptive rules/cooldowns | PS-A01/A02/A03/A04 |
| Hash chain implemented/verified | PS-E01/E02/E03/E05 |
| Timeline/graph generated | PS-R01/R02/R03 |
| Grounded AI report | PS-I01/I02/I03/I05/E04 |
| No arbitrary AI commands | PS-I04/P01/P02 |
| End-to-end dashboard | PS-UI01/UI02/G01 |
| Resource usage measured | PS-G02/O01/V08 |
| Static/adaptive experiment | PS-V01/V02/V05 |
| Failure cases documented | PS-O03/U04/T02 |
| Final demo repeated | PS-V09/V10 |
| Source tagged/backed up | PS-T03 |
| Final report/presentation | PS-T02 |

## Phase 1 evidence boundary

Only PS-U01 planning deliverables can be accepted here after audit. PDF reading/digest, local tooling, rendered-page review and failed SSH are in PROJECT_STATUS. No audit may turn application/ML/AI/UI/deployment/evaluation IDs into complete. Populate exact source/test/measurement evidence only when it actually exists and was inspected.
