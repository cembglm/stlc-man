# KPI 3.4 Requirement Coverage Engine

## Purpose and claim boundary

This engine measures MATISSE KPI 3.4 as the percentage of applicable functional and non-functional requirements with valid execution evidence from a registered Digital Twin. It does not treat mapped tests, generated code, Docker execution, simulation, mock execution, or passing local unit tests as Digital Twin coverage.

The implementation produces scoped technical measurements. It does not establish a universal MATISSE achievement claim. The included fixture is synthetic and must never be reported as project evidence.

## Architecture

The implementation extends the existing traceability architecture:

1. `RequirementSet` stores stable, versioned requirements in `requirement_sets`.
2. Native and external generated code use `SubmissionManifest` records in `traceability_submissions`.
3. A `ManifestTest` links requirement versions to scenario, test case, Python function and exact code hash.
4. External deliveries remain append-only in `ifarlab_result_deliveries`.
5. The existing deterministic verdict engine writes `verification_verdicts`.
6. `RequirementCoverageService` joins those existing collections and calculates every coverage stage.
7. Explicit snapshots are stored in `requirement_coverage_snapshots`; dynamic GET requests do not mutate history.
8. Dashboard and machine-readable report endpoints call the same aggregation service.

No second requirement or verdict collection was introduced.

## Data models

### Requirements

Each requirement has:

- stable `id` and `version`;
- `type`: `functional`, `non_functional`, or explicit `unclassified`;
- description in `text`;
- acceptance criteria;
- source artifact/reference and optional SHA-256;
- related Digital Twin identifiers;
- `active`, `superseded`, or `retired` status;
- applicability, timestamps and superseded-version metadata.

Saving a new requirement set preserves earlier sets. Only the selected/current active applicable versions enter a denominator. Superseded versions remain historically queryable but are excluded from the current denominator.

### Traceability chain

The authoritative chain is:

`Requirement(version) → Scenario → Test Case → Test Function/Code SHA-256 → Execution/Run → Deterministic Verdict`

`ManifestTest` contains `scenario_id`, `test_case_id`, `function`, requirement IDs and optional expected requirement versions. `SubmissionManifest` adds requirement-set, project and session scope. A version mismatch marks a chain stale; a missing scenario ID leaves it unmapped. Unknown/inactive requirement links are reported as orphans.

### Execution environment

Execution scope is one of:

- `digital_twin`
- `physical_twin`
- `local`
- `simulation`
- `mock`
- `unknown`

A record qualifies as Digital Twin evidence only when it explicitly contains:

- `scope: digital_twin`;
- `environment_id`;
- `digital_twin_id`;
- `registry_reference` or `provenance_sha256`;
- linked delivery and exact requirement-set/code identity;
- execution evidence;
- a valid deterministic `PASS` or `FAIL` verdict.

An arbitrary environment ID is insufficient. Skipped, blocked, timed-out, not-executed, infrastructure-invalid, rejected, unlinked, stale, missing-evidence and inconclusive runs do not qualify.

## Coverage semantics

| Stage | Definition |
|---|---|
| Mapped | A valid requirement version is explicitly linked through a scenario to a test case. |
| Generated | A mapped case has exact generated code and a SHA-256 manifest. |
| Executable | Generated code has deterministic readiness evidence (`syntax=pass`, acceptable validator, `verdict=pass` or `pass_with_warnings`). |
| Executed DT | A linked test actually ran with valid evidence in a provenance-backed registered DT environment and produced deterministic PASS or FAIL. |
| Verified DT | Requirement-level aggregation of eligible DT evidence is PASS. Any valid FAIL prevents verification. |

Multiple cases or runs count a requirement once in each numerator. A failing valid DT execution counts as tested/executed coverage but not verified coverage. Contradictory PASS/FAIL evidence produces a failing requirement-level verification state.

## Formulas

Primary KPI:

```text
FR_DT_Coverage = functional requirements with valid DT execution / applicable active functional requirements × 100
NFR_DT_Coverage = non-functional requirements with valid DT execution / applicable active non-functional requirements × 100
```

Supplementary verification:

```text
FR_DT_Verified = functional requirements with PASS requirement verdict / applicable active functional requirements × 100
NFR_DT_Verified = non-functional requirements with PASS requirement verdict / applicable active non-functional requirements × 100
```

Targets are 100% FR and 80% NFR. A zero denominator returns `percentage: null` and `assessment: not_assessable`; it never returns a misleading 0% achievement.

## Native workflow integration

- Requirement analysis deterministically registers explicitly identified `FR`, `NFR`, and `REQ` lines as a versioned requirement set. It does not classify unidentified prose; persistence failure is reported without breaking the existing analysis response.
- The pipeline passes that structured requirement set to scenario generation, which preserves explicit upstream `RequirementIDs` and `RequirementsSetVersion`; it does not infer links from prose.
- Test-case generation inherits requirement identities from the selected scenario.
- Optimization's test-case model retains extra traceability fields, including requirement identities and set version, so deduplication cannot silently discard them.
- Code generation normalizes legacy/current field names, retains scenario and requirement identities, hashes exact code, performs deterministic readiness checks, and writes the existing traceability submission collection.
- Native MCP execution writes a non-authoritative trace event with the exact code hash and is explicitly ineligible until a qualified, linked DT evidence delivery exists.
- External/robot results continue through the deterministic verdict engine. Non-completed statuses are made inconclusive.

Removed/merged optimization cases remain visible in optimization provenance. KPI coverage is calculated from retained manifest mappings; if removal eliminates the last mapping for a requirement, that requirement becomes uncovered.

## API

All routes inherit the existing API-key dependency under `/api/integrations/ifarlab/v1`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/coverage` | Full KPI report, optional requirement type/stage/project/session/environment/DT filters |
| GET | `/coverage/functional` | FR executed and verified DT metrics |
| GET | `/coverage/non-functional` | NFR executed and verified DT metrics |
| GET | `/coverage/requirements/{requirement_id}` | Forward and reverse traceability drill-down |
| POST | `/coverage/snapshots` | Persist an explicit reproducible evaluation snapshot |
| GET | `/coverage/snapshots` | Historical snapshots |
| GET | `/coverage/gaps/{category}` | Uncovered, generated-unexecuted, failed/inconclusive, or stale requirements |
| GET | `/coverage/report` | Machine-readable KPI 3.4 report from the same aggregation service |

Example:

```http
GET /api/integrations/ifarlab/v1/coverage?requirements_set_version=demo-v1&environment_id=DT-ENV-1
X-API-Key: ...
```

Abbreviated response:

```json
{
  "engine_version": "1.0.0",
  "status": "assessed",
  "scope": {"requirements_set_version": "demo-v1", "environment_id": "DT-ENV-1"},
  "kpi": {
    "functional": {"covered": 1, "total_applicable": 2, "percentage": 50.0, "target_percentage": 100.0, "assessment": "not_achieved"},
    "non_functional": {"covered": 1, "total_applicable": 2, "percentage": 50.0, "target_percentage": 80.0, "assessment": "not_achieved"}
  },
  "verified": {
    "functional": {"covered": 1, "total_applicable": 2, "percentage": 50.0},
    "non_functional": {"covered": 0, "total_applicable": 2, "percentage": 0.0}
  }
}
```

## Dashboard and reporting

The React traceability dashboard displays separate FR and NFR DT-tested cards, supplementary verified coverage, targets, assessment status, evaluation time, filters, exclusions and a requirement-to-verdict drill-down. Empty denominators display “Not assessable.” JSON export returns the backend response without recomputing numbers in JavaScript.

`TestReportingService.get_kpi_3_4_section()` and the `/coverage/report` route delegate to `RequirementCoverageService`. The existing `/report` traceability response remains backward compatible. LLM prompts do not compute or rewrite KPI values.

## Synthetic demonstration dataset

`backend/tests/fixtures/kpi_3_4_synthetic_demo.json` is labelled `synthetic: true` and includes:

- a valid passing DT execution;
- a local execution excluded from KPI coverage;
- a valid failing DT execution (tested but not verified);
- generated but unexecuted evidence;
- an unclassified requirement;
- stale/superseded evidence.

The fixture is for automated verification only.

## Automated verification

The core test suite covers FR/NFR arithmetic, multiple and duplicate mappings, many-to-many relationships, zero denominators, unclassified requirements, superseded versions, stale mappings, non-DT exclusion, invalid/rejected/missing evidence, failing executions, inconclusive executions, contradictory verdicts and scope filters.

Initial implementation verification on 19 November 2026:

```text
49 core coverage/traceability tests passed
```

This includes the new coverage tests plus existing verdict, traceability-contract and ingestion regressions. Frontend build and broader regression outcomes should be recorded in the implementation handoff for the exact commit under review.

Additional verification in the same working tree:

```text
11 project-structure and knowledge-graph regression tests passed
Vite production build passed (655 modules transformed)
OpenAPI exposed the authenticated coverage route family
```

## Collections and operational guidance

Existing collections used:

- `requirement_sets`
- `traceability_submissions`
- `ifarlab_result_deliveries`
- `verification_verdicts`
- `traceability_events`

New collection:

- `requirement_coverage_snapshots` (explicit historical evaluations only)

For production scale, create indexes on requirement-set version/current flag, submission ID/revision/manifest requirement-set version, delivery hash/submission/run/link status, verdict submission/run/test case/evaluation time, and snapshot evaluation time/scope. Index creation and deployment migration are environment-specific and are not executed automatically by this repository change.

## Known limitations and future dependencies

- Historical native sessions that did not preserve requirement and scenario IDs cannot be retroactively counted without a reviewed migration/mapping process.
- Native MCP results are audit events but remain KPI-ineligible until linked deterministic DT evidence is supplied.
- A trusted DT registry is represented by registry reference/provenance fields; integration with the consortium's authoritative registry remains external.
- The existing repository has a globally current requirement-set convention. Multi-project deployments should always request an explicit requirement-set version until current-set selection is partitioned by project.
- The aggregation currently reads scoped traceability collections in application code. Large deployments should add the listed indexes and a MongoDB aggregation pipeline/materialized view after profiling.
- Authentication reuses the existing API-key mechanism; role-level authorization is not present in the repository.
- No real MATISSE KPI values are bundled or claimed.
