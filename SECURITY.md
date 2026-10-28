# PiSentinel security and deployment safety

**Phase 1 design only: none of these controls is claimed implemented or penetration-tested.** Authorized controlled-lab use only. Stable PS-* IDs/A01-A14 refer to PROJECT_PLAN.

## 1. Assets, adversaries and trust boundaries

Protect real management SSH/accounts/keys, Windows host, Pi OS, other network devices, source/model/config integrity, case availability/privacy/integrity, policy authority and any future provider keys. Submitted usernames/commands/paths/URLs/bodies/packet metadata/timestamps and AI output are untrusted. Synthetic services can accidentally receive real credentials: never retain them.

| Boundary / threat | Proposed controls | Required verification |
|---|---|---|
| Lab client -> decoy: exploit, arbitrary command, traversal, pivot | Maintained parser/library, no shell/exec/eval/host paths/SFTP/SCP/forwarding; finite virtual command/file/data handlers; separate least-privilege UID/process and reviewed egress isolation. | Real SSH/HTTP clients; metacharacter/traversal/forwarding/subsystem tests (PS-C03/C04). |
| Client -> evidence/logs: credentials, log forgery, size/format attacks | Boundary redaction/allowlist/bounds; no payload logging; structured log categories; UI text escaping. | Canary secrets absent from DB/logs/errors/exports/reports; newline/Unicode/XSS/size tests (PS-C02/C05). |
| Decoy -> writer: forged producer, tamper, flooding | Protected local IPC/producer identity, bounded envelope/queue/rate; writer-only evidence file permissions; atomic serialized append. | Unauthorized producer/file access, concurrency/crash/disk-full tests (PS-E01/E02/O02). |
| Stored evidence -> verifier: modification/deletion/reorder/full rewrite | Canonical chain, first-broken-link report, restrictive permissions, separate trusted checkpoints/backups; preserve originals. | Mutation matrix plus explicit rewrite/truncation limitation tests (PS-E03/E05/V06). |
| Data/model pipeline: poisoning/leakage/unsafe deserialize | Labels separate from features; grouped run/scenario splits; frozen pipeline; only trusted hashed artifacts, no arbitrary pickle/joblib uploads. | Leakage/provenance/schema/hash checks and real held-out metrics (PS-D03/ML01). |
| Case -> investigator: injection/exfiltration/fake verified status | Independent verification, bounded allowed fields, hostile content treated as data, no OS/browser/network tools, approved destination/budget only. | Tampered case/unknown ID/injected instruction/egress-off tests (PS-I01/I03/I04/U03). |
| AI -> report/policy: false facts/arbitrary action | Separate observations/inferences/hypotheses; citations plus semantic support checks; finite allowlisted executor, no direct AI actions. | Unsupported claims/free-form command/action bypass/fallback tests (PS-I02-I05/P01/P02). |
| Browser -> management: unauthorized read/control/stored XSS/CSRF | Loopback by default + approved SSH tunnel, distinct control/decoy service, auth/scopes, escaped content/pagination; no state-changing GET. | Auth/control isolation/XSS tests, TLS/CSRF review before LAN management (PS-UI01/UI02/Z01). |
| Workload -> 2 GB Pi: OOM/CPU/disk exhaustion | Bound sessions/requests/queues/records/cases, backpressure, optional-work timeout, disk reserve and visible rejection/loss/health. | Actual Pi load/long-run/degraded tests (PS-G02/O01-O03). |
| Executor -> real network: lockout/unsafe exposure/destruction | Synthetic changes inside existing approved services, TTL/cooldown/reset, app restriction/simulated isolation, management-path exclusion. | Scope/authorization/rollback/restart/safety-veto tests, no OS/firewall commands (PS-A03/A04/P01/P02). |

Local root/admin/kernel/hardware compromise and proof of real attacker intent are not solved. Native processes alone are not a sandbox. Lab realism, sensor coverage gaps and generalization limits must be reported; do not weaken machine security to make builds pass.

## 2. Evidence claims and privacy

M1 implementation status and tested negative guarantees (tail truncation, full-chain recomputation, trigger bypass): [docs/EVIDENCE_CHAIN.md](docs/EVIDENCE_CHAIN.md#limitations-do-not-overstate).

A SHA-256 chain detects inconsistent record/link changes **relative to the retained chain/checkpoint**. It is not encryption, access control, signature, immutable storage, completeness/origin proof or legal admissibility. A privileged adversary can recompute an entire unkeyed chain; tail truncation needs independently retained expected count/head. A checkpoint stored beside the DB is not independent. Never silently repair originals; label failed/unverified evidence in UI/exports/report. See ARCHITECTURE proposed format and limitation tests.

Persist privacy-filtered raw normalized observations before enrichment, with ingest sequence/source timestamps and clock-skew caveats. Keep model/SHAP/policy/AI separately versioned and linked; AI hypotheses are not facts. Restrict evidence/export/backup permissions. Owner must approve retention/case limits/disk budget (A13). No actual password/key/token/cookie/production data in Git or evidence. Runtime secrets in environment or protected files excluded from Git; secret-free examples only. M1 must add project-appropriate ignore/secret-scan rules before runtime data exists.

Raw-event requirements do not authorize full packet capture. Resolve A02 interface/header/payload/privilege/privacy before any sensor activation. Future external AI needs evidence minimization/anonymization, explicit model destination/retention/training/region review, spend cap and keys solely on trusted analysis host. No provider call or signup authorized now.

## 3. Lab isolation and response safety

RFC1918 addressing does not prove a safe separate lab. Obtain diagram, approved source hosts, capture interface and management path before any decoy binding/scans. Default development in-process; even local listener creation requires explicit approval under user rules. One SSH + one web decoy, never replace real management SSH or co-host control endpoints in decoy app. Ports/interfaces remain proposals until approved. No public exposure/router forwarding/published tunnel/firewall/route changes authorized.

Dedicated VLAN/subnet or equally reviewed isolation, least-privilege users and blocked sensitive-host/egress access are proposed prerequisites, not deployed controls. Confinement may need owner-approved network changes. A custom SSH library never makes host-shell execution safe; commands are interpreted only by synthetic handlers.

Finite vocabulary: observe, expose approved synthetic inventory/identity/tree/routes/dataset, app-level rate-limit/restrict, stop synthetic session, simulated isolate. Every change has scope, evidence, reason/confidence, TTL/cooldown and rollback. Safety veto precedes deception. Simulated isolation must be labelled; terminating a decoy session is not infrastructure isolation. No LLM root authority or report-text bypass.

## 4. Read-only inspection and actual target result

Supplied target: `pisentinel@192.168.1.3`, hostname `sentinel`, claimed Pi 4/2 GB. No OS/storage/version was inferred from username or transport reachability.

Attempted in Phase 1: SSH with `BatchMode=yes`, `StrictHostKeyChecking=yes`, `ConnectTimeout=8`, `ConnectionAttempts=1` and read-only inventory command (hostname/id/os-release/uname/word-size/free/df/tool availability/Python version). **Result: exit 255, `Permission denied (publickey,password)`. No remote inventory ran.** No key discovery/password retry/host-check downgrade followed. Endpoint response does not establish authenticated target identity or deployment permission.

Owner can arrange authorized normal SSH agent/key access, or run/share this non-sensitive read-only inventory (do not share keys/passwords):

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8 pisentinel@192.168.1.3 'hostname; id; cat /etc/os-release; uname -a; getconf LONG_BIT; free -m; df -h /; command -v python3 git systemctl; python3 --version'
```

Verify host fingerprint out of band via trusted administration; do not blindly accept unknown/changed keys. Do not paste passwords/private keys into repository/conversation. Authentication requires owner help, not bypasses. Later inventory can inspect ports/clock/service status after authorized access; never dump secret-bearing process environments/configs.

## 5. Future reproducible deployment and recovery procedure

**No step below has run on the Pi; installer/service scripts do not exist.**

1. Resolve A01/A02/A05/A12/A13. Authenticate target identity; read OS/64-bit architecture/Python/RAM/disk/clock/power/cooling/existing services/listeners without modifying them. Record differences from guide-recommended Raspberry Pi OS 64-bit. Never automatically reflash or change IP.
2. Verify local milestone tests/clean source, record commit/locks/config/model/schema hashes and exact proposed commands. Review ARM wheels, package age/advisories and platform compatibility without disabling security policies.
3. Prepare independent recoverable source/config/evidence backups. Secrets stay outside Git/protected channels. Use WAL-safe SQLite snapshot/backup; verify restore in a **new test location**. Local Git commit alone is not independent backup. Never overwrite existing config/evidence.
4. Present package/user/path/permission/capability/service/network changes and recovery commands for explicit approval, including privilege and side effects. SSH login is not installation approval. No sudo, service enablement, packet capability, listener/firewall change without this gate.
5. Deploy **one previously verified milestone** into versioned release location/venv, protected separate runtime data/secrets. Compare config without exposing values; preflight/migrations on safe copy first. Preserve previous release and plan forward/backward schema recovery.
6. Apply only approved minimal service changes/bindings. Run bounded authorized smoke and milestone tests **on Pi**; inspect actual output, not just SSH exit status. Failure remains failure.
7. Record CPU/RSS/system memory/peaks, latency/queues/loss/storage/offload bytes with workload/versions/sample interval; evaluate throttling/power where available. Defer optional work when unsafe, never conceal failures.
8. If health/resource gates fail: preserve logs/cases, label failed deployment, stop only newly approved services as authorized and select preserved previous release/config. No destructive migration/delete/restore-over-existing without separate approval. Verify recovery in new location before replacement.
9. Update status/traceability with exact command/environment/result/artifact; commit coherent verified local work. Ask before tagging/pushing/sharing release or changing network security. Repeat per milestone, never deploy an unverified whole stack.

## 6. Security acceptance and incident handling

Before authorized exposure: parser/confinement/auth/redaction/rate/rollback/independent-verifier/leakage tests and actual load measurements; document residual risks. Unexpected sensitive capture or exploit: stop affected new collection safely/as authorized, protect minimal evidence without propagating secrets, notify owner, add regression fix and review retention/remediation. Never erase original data to hide a failure. No external report/issue with private evidence or credentials without approval.
