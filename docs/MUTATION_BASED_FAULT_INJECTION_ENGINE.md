# Mutation-Based Fault Injection Engine

## Purpose and boundary

The mutation subsystem measures whether tests detect deliberately introduced first-order faults. Its outcomes are **test-strength evidence**. They never update requirement verification verdicts, KPI 3.4 coverage, or any KPI 2.2 commitment. In particular, this implementation makes no claim that a 50% mutation score or any other threshold has been achieved.

## Architecture

- `backend/mutation/adapters.py`: language adapter registry and deterministic Python AST generator.
- `backend/mutation/evaluator.py`: baseline validation, outcome classification, and score aggregation.
- `backend/mutation/execution.py`: pluggable execution boundary. The shipped adapter is intentionally unavailable and cannot execute code.
- `backend/mutation/service.py`: campaign, artifact, result, and evidence persistence.
- `backend/routers/mutation_router.py`: authenticated API under `/api/mutations/v1`.
- `MutationTestingPanel.jsx`: configuration, preview, results, and evidence report UI inside Test Code Generation.

Mutation artifacts are stored separately in `mutation_campaigns`, `mutation_mutants`, and `mutation_results`. Lifecycle references are appended to `traceability_events` with `mutation_verdict_is_requirement_verdict=false`; the subsystem never writes verification verdicts.

## Data model and lifecycle

A campaign records project/session references, source artifact/version and hash, test-suite hash, selected adapter/operators, scope, seed, execution limits, baseline evidence, state, and timestamps. A mutant is an immutable content-addressed artifact with source and mutant hashes, AST replacement metadata, location, function, source text, and diff. A result records one deterministic outcome, reason, individual-test observations, and an evidence hash. Retries upsert by campaign and mutant identity.

The lifecycle is `draft → generated → ready → running → completed`; the shipped configuration normally follows `draft → generated → baseline_unavailable`. Cancellation is persisted as `cancelled`. Configuration becomes immutable after generation.

## Python operators

The Python adapter parses input without importing or executing it. Each output contains exactly one mutation and includes a stable mutant ID, original source hash, mutant hash, location, containing function, operator family, and unified diff.

| Family | Transformations |
|---|---|
| AOR | `+ ↔ -`, `* ↔ /`, `// ↔ %` |
| ROR | `> ↔ >=`, `< ↔ <=`, `== ↔ !=` |
| LOR | `and ↔ or` |
| CON | Boolean literal replacement and `if`/`while`/conditional-expression negation |

Generation order is stable by source location and operator identity. A maximum count selects the leading deterministic set unless a seed is provided, in which case repeatable sampling is used. Identical mutant source hashes are deduplicated. The C++/ROS2 adapter is registered as a visible but unsupported future contract.

## Execution safety

Untrusted source is never run by the backend or on the host. The repository's existing executors have not been accepted as a mutation adapter because the required profile—no network, no secrets, restricted read-only mounts, explicit CPU/memory/time limits, and disposable isolation—has not been demonstrated as an enforceable contract. Baseline and campaign execution therefore return `execution_unavailable`; generated mutants remain previewable and persistable, and results are `not_executed`.

A future execution adapter must implement that security profile before it can report `available=true`. Trusted external systems may submit structured per-test evidence through the result-ingestion API; arbitrary commands are not accepted.

An execution adapter must also create a disposable workspace, validate source, apply one approved artifact, enforce timeout/CPU/memory/network/filesystem policy, collect per-test evidence, clean up, and expose cancellation. None of those capabilities are advertised by the unavailable adapter.

## Classification and score

A baseline is valid only when it completes, contains tests, and every recorded test passes. Outcomes are deterministic:

- `killed`: a baseline-passing test fails for the mutant.
- `survived`: all baseline tests retain the same passing result.
- `invalid`, `timeout`, `execution_error`: explicit runner states.
- `equivalent`: only accepted when explicitly human-confirmed.
- `undetermined`: incomplete/conflicting evidence or invalid baseline.
- `not_executed`: no execution evidence.

The score is `killed / (killed + survived)`. All other outcomes are excluded. When the denominator is zero, the score is `null` and `assessable=false`. Reports include overall and family/file/function breakdowns plus detecting-test relationships.

## API workflow

All endpoints use the existing API-key dependency (when authentication is enabled):

1. Inspect `GET /api/mutations/v1/adapters` and `/operators`.
2. Create `POST /campaigns`, then `POST /campaigns/{id}/generate`.
3. Preview `GET /campaigns/{id}/mutants`.
4. Request baseline or execution; the default adapter records the explicit unavailable state.
5. Optionally ingest trusted structured evidence with `POST /campaigns/{id}/results`.
6. Read `/results`, `/score`, `/evidence`, or download `/report`.

Campaign cancellation is idempotent. Mutant generation and result ingestion upsert by campaign/mutant identity so retries do not duplicate evidence.

## Frontend workflow

The existing Test Code Generation page now contains `Test Code Generation` and `Mutation Testing` sub-tabs. The mutation view supports language/operator/scope/sampling and execution-limit configuration, explicit source upload, preview and diff inspection, baseline/campaign controls, status/cancellation, result counters and filtering, per-test drill-down, and JSON report download. Execution buttons are disabled when the adapter capability response says no safe executor is available.

## Known limitations and C++/ROS 2 extension

- No real isolated baseline or mutant execution has been verified; runtime outcomes require trusted structured evidence from an external executor.
- Automatic equivalence analysis is intentionally absent; equivalence requires an explicit independent confirmation.
- Python formatting and comments can change because `ast.unparse` regenerates source, although program structure outside the selected AST mutation is preserved semantically and the original artifact is untouched.
- The current persistence layer relies on MongoDB availability and does not add tenant ownership beyond the repository's existing API-key access model.

The future C++/ROS 2 adapter must use a compiler-aware parser such as Clang tooling, stable source ranges, compilation database/build metadata, syntax and compile validation, and isolated `colcon test`/CTest result collection. ROS graph and middleware isolation, resource limits, deterministic workspace overlays, and cleanup must be proven before the adapter can be marked available.

## Relationship to MATISSE KPI 2.2

This engine supplies technical evidence for later research. Mutation score is not fault-detection improvement, is not a conventional-baseline comparison, and does not demonstrate the KPI 2.2 50% improvement target. Measuring that KPI remains separate work requiring a defined conventional baseline, comparable datasets and environments, statistical method, and approved interpretation.

## Verification

Run:

```bash
cd backend
pytest tests/test_mutation_engine.py tests/test_mutation_evaluator.py tests/test_mutation_execution_boundary.py
```

The tests cover required operators, syntax validity, stable IDs and seeded selection, filtering, all outcome classes, invalid baselines, deduplication, score exclusions, and the zero-denominator case. No test executes generated source.
