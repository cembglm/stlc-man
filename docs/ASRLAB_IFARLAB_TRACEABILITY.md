# ASRLab IFARLAB Traceability Contract

This implementation adds an evidence-driven boundary between STLC Manager and IFARLAB without moving Gazebo orchestration, ROS recording, metric extraction, or robot control into STLC Manager.

## Architecture

The existing `session_history` workflow remains operational. New append-only collections provide stable integration records:

- `requirement_sets`: immutable complete requirement-set revisions and their content hashes.
- `traceability_submissions`: generated code, manifest revisions, generation provenance, and code-quality provenance.
- `ifarlab_result_deliveries`: every unique received payload, link status, and evaluations. Repeated identical delivery hashes are idempotent.
- `verification_verdicts`: append-only deterministic test verdict records.
- `traceability_events`: lifecycle audit events for requirement sets, submissions, and result receipt.

Generated test results also retain a `traceability_manifest` inside the legacy generation result. Missing upstream requirement links and model fields are recorded as `not_recorded` or `null`; they are never fabricated.

## Canonical hashing

`contract_sha256` is calculated over the exact bytes of `config/ifarlab_contract_v1.json`; both laboratories must distribute and hash that same file without reformatting it. Other normalized payload fingerprints use sorted object keys, compact separators, UTF-8, no BOM, no trailing newline, ISO-8601 datetimes, and JSON numeric values. `code_sha256` is calculated over the exact UTF-8 bytes exported as the Python test file. The active contract and its hash are available from `GET /api/integrations/ifarlab/v1/contract`.

## API

All endpoints reuse the existing `X-API-Key` or Bearer authentication policy when `API_AUTH_ENABLED=true`.

- `POST /api/integrations/ifarlab/v1/requirements` validates and records a complete requirement set.
- `GET /api/integrations/ifarlab/v1/requirements.json` exports the current or requested version, including uncovered requirements.
- `POST /api/integrations/ifarlab/v1/submissions` builds and validates a manifest against Python AST, requirement IDs, test-case IDs, code hash, and contract hash.
- `GET /api/integrations/ifarlab/v1/submissions/{id}/manifest.json` exports the authoritative manifest.
- `GET /api/integrations/ifarlab/v1/submissions/{id}/test.py` exports exact code and its hash.
- `POST /api/integrations/ifarlab/v1/results` validates, links, stores, and deterministically evaluates IFARLAB results. Unknown or mismatched records remain stored with `unlinked` or `rejected` status.
- `POST /api/integrations/ifarlab/v1/inbox/{package_name}/import` safely imports an SSH-delivered `<submission_id>__<run_id>.result.tar` from `IFARLAB_INBOX_DIR`. It rejects traversal paths, links, unexpected members, oversized payloads, invalid JSON, and identifier mismatches; it never executes package contents.
- `GET /api/integrations/ifarlab/v1/traceability` returns coverage, verification, requirement states, matrix rows, evidence, and rule details for the React dashboard.

FastAPI publishes the full schemas and realistic field constraints in `/docs` and `/openapi.json`.

## Verdict and aggregation rules

Execution validity is evaluated before product behavior. Missing evidence or measurements, timeouts, reset failures, infrastructure failures, invalid environments, and untrustworthy runs produce `INCONCLUSIVE`. Rules use only `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, and `not_in`; numerical comparisons use `Decimal` and never `eval()` or an LLM.

For valid runs, a code-quality failure, failed rule, generated assertion, or independent robot verdict produces `FAIL`. A result becomes `PASS` only when code quality and all applicable checks pass. `rtf_min < 0.7`, missing MoveIt collision evidence, missing evidence, exit 3/64, reset failure, and unavailable required measurements produce `INCONCLUSIVE`. Disagreement is retained as a contradiction. IFARLAB's returned verdict remains authoritative; the STLC verdict is stored as an independent re-evaluation and disagreements are flagged. Requirement aggregation applies `STALE > FAIL > NOT_VERIFIED > PASS`, with `NOT_COVERED` when no test case is linked. Coverage and verification use the complete current requirement set as separate denominators.

## Pending integration decisions

Final human verdict approval, the override and supersession workflow, migration-time warning behavior for contract mismatches, the final measured RTF threshold, the supported unit-conversion table, and operational deployment of the restricted Windows OpenSSH inbox account remain open decisions. The primary return transport is the SSH-delivered result package defined above; the authenticated HTTP endpoint remains available for controlled integrations. Historical records are not automatically rewritten when these decisions change.
