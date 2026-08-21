# STLC Manager

STLC Manager is an AI-assisted web application designed to manage the Software Testing Life Cycle (STLC) from source code, requirements, and the outputs of earlier testing phases.

The application provides an 11-step workflow that covers code review and requirement analysis, test planning, scenario and test case generation, test code generation, Docker and ROS 2-based execution, reporting, and test closure.

> **Project status:** This project is under active development. Some features require local services, a running Docker daemon, a ROS 2 container, or an external model provider. Additional safety and operator-approval layers are required before running generated tests on physical robots.

## Table of contents

- [Key features](#key-features)
- [STLC pipeline](#stlc-pipeline)
- [Test Case Optimization](#test-case-optimization)
- [Test execution methods](#test-execution-methods)
- [Execution on a remote robot computer](#execution-on-a-remote-robot-computer)
- [Architecture and directory structure](#architecture-and-directory-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the services](#running-the-services)
- [Configuration](#configuration)
- [Tests and utility scripts](#tests-and-utility-scripts)
- [API and health checks](#api-and-health-checks)
- [Known limitations](#known-limitations)
- [Security considerations](#security-considerations)

## Key features

- An 11-phase STLC pipeline
- Source code and document-based code review and requirement analysis
- AI-assisted generation of test plans, scenarios, test cases, and executable test code
- Individual, bulk, and parallel test case optimization
- Local models through LM Studio and Google Gemini API models
- MongoDB persistence for sessions, process outputs, and execution results
- Isolated test execution in Docker containers
- Parallel test execution in multiple Docker containers
- Robot arm simulation and ROS 2/Gazebo-oriented execution paths
- Test deployment to a local or network-shared directory and result collection
- Test reporting, quality evaluation, and test closure reports
- Live pipeline progress through Server-Sent Events (SSE) and pipeline cancellation

The quality evaluation layer calculates data-driven dimensions such as completeness, clarity, coverage, and depth. The relevant implementations are located in `backend/services/quality_metrics_calculator.py` and `backend/services/report_quality_evaluator.py`.

## STLC pipeline

Pipeline steps run in the following canonical order:

| Order | Step | Primary output | Dependencies |
|---:|---|---|---|
| 1 | Code Review | Code review report | — |
| 2 | Requirement Analysis | Requirement analysis report | — |
| 3 | Test Planning | Test plan | Code Review, Requirement Analysis |
| 4 | Environment Setup | Environment setup report | — |
| 5 | Test Scenario Generation | Test scenarios | Test Planning |
| 6 | Test Case Generation | Detailed test cases | Test Scenario Generation |
| 7 | Test Case Optimization | Deduplicated and optimized test cases | Test Case Generation |
| 8 | Test Code Generation | Executable test code | Test Case Optimization, Environment Setup |
| 9 | Test Execution | Test output and execution status | Test Code Generation |
| 10 | Test Reporting | Test report and metrics | Test Execution |
| 11 | Test Closure | Test closure report | Test Reporting |

The authoritative dependency graph is defined in `backend/pipeline/pipeline_controller.py`. The current primary frontend pipeline keeps all 11 steps enabled, while the backend still validates dependencies for the submitted step set.

The pipeline supports:

- Per-step model and prompt configuration
- File-to-step mapping
- Passing outputs between dependent steps
- Current status and step-result queries
- Live progress over SSE
- Stopping a running pipeline

## Test Case Optimization

Test Case Optimization is the seventh pipeline step and sits between Test Case Generation and Test Code Generation. Its purpose is to identify semantically overlapping test cases, retain representative cases, and reduce unnecessary downstream test-code generation and execution work.

This module does not simply compare titles or perform exact-text deduplication. It uses the selected language model to evaluate whether test cases exercise the same behavior, conditions, and expected outcome.

### Inputs and selection

The optimization interface supports:

- Loading generated test cases by process title
- Combining test cases from multiple process titles
- Selecting all cases or an explicit subset
- Assigning a name to the optimization run
- Selecting a configured local or API model
- Supplying a custom optimization prompt
- Choosing an optimization strategy

The selected process titles, process name, model, prompt state, and optimization type are retained with the session output.

### Optimization strategies

#### Individual optimization

Individual optimization processes test cases serially. Each candidate is compared with the representative cases already retained in the unique set. When the model determines that a candidate is semantically equivalent to a retained case, the candidate is recorded as a duplicate; otherwise, it becomes a new representative case.

This mode is straightforward and produces pair-level comparison information, but the number of model calls can grow significantly with larger test sets.

#### Bulk optimization

Bulk optimization submits the selected test-case set to the model in a consolidated request. The model is asked to return representative indices and duplicate groups. The service accepts several supported JSON response shapes and converts them into the common optimization result structure.

Bulk mode generally requires fewer model requests than serial pairwise processing, but its effectiveness depends on the selected model's context capacity and its ability to return valid structured output.

#### Parallel optimization

Parallel optimization prepares pairwise comparisons for parallel batch processing, aggregates the comparison results, and derives the final unique and duplicate sets. The service includes batch splitting, cross-batch duplicate handling, rate-limit retry behavior, and validation that a test case is not simultaneously classified as unique and duplicate.

The current router enables parallel optimization only for Gemini models. The frontend reflects this constraint and recommends Bulk Optimization when a selected model cannot use the parallel path.

### Results and persistence

An optimization result can contain:

- The original number of selected test cases
- Representative or unique test cases
- Duplicate/similar test cases and their matched representative
- Unique and duplicate counts
- Reduction statistics
- Comparison logs or batch metadata, depending on the strategy
- The model, prompt, process name, process titles, session ID, and optimization type

Results are stored per process title in the `test_case_optimizations` MongoDB collection. A session-level copy is also written under `session_history.processes.test_case_optimization` for traceability across the STLC pipeline.

Stored results can be queried by process title or process name. The API also supports deleting saved results for a process title.

### Process control and monitoring

The module exposes operations for:

- Starting smart selection with `individual`, `bulk`, or `parallel` mode
- Checking a running process by process ID
- Listing active optimization processes
- Requesting cancellation of an active process
- Exporting a session monitoring report
- Reading aggregated error statistics
- Configuring retry behavior
- Reading or resetting optimization monitoring statistics

The primary API prefix is `/api/test-case-optimization`.

### Interpretation and limitations

- Similarity decisions are model-dependent and may differ between models or prompts.
- Optimization identifies semantic redundancy; it does not prove requirement coverage or test effectiveness.
- A representative test should be reviewed before discarding a test that contains distinct data, preconditions, risk, or traceability information.
- Individual pairwise comparison can approach quadratic growth as the number of test cases increases.
- Bulk mode is constrained by model context size and structured-output reliability.
- Parallel mode requires a supported Gemini model and may still be affected by provider quotas and rate limits.
- Optimization results should remain traceable to their source test cases and requirements, especially in regulated or safety-critical systems.

## Test execution methods

The project contains several execution paths with different semantics and trust levels.

### 1. Standard Execution (MCP and AI provider)

- Generated test code stored in MongoDB can be selected by process or test identifier.
- The backend sends the test content to the local MCP server through JSON-RPC.
- The MCP server uses either LM Studio or Gemini as the provider.
- Terminal-like output and basic pass/fail statistics can be persisted in MongoDB.

The default MCP endpoint is `http://localhost:8001`, and the default LM Studio endpoint is `http://localhost:1234`.

> Standard Execution is an AI/MCP-based execution path. By itself, it is not an operating-system-level remote agent that runs commands on a physical robot computer.

### 2. Docker Process

- Writes test code into a temporary working directory.
- Starts an isolated container using the configured language image.
- Collects `stdout`, `stderr`, the exit code, and container metadata.
- Supports timeouts, additional packages, and environment variables.
- Removes temporary containers, custom images, and working directories after execution.

Current language mappings:

| Language | Default image |
|---|---|
| Python | `python:3.9-slim` |
| JavaScript | `node:18-alpine` |
| Java | `openjdk:11-jre-slim` |
| C# | `mcr.microsoft.com/dotnet/sdk:6.0` |
| Go | `golang:1.19-alpine` |
| Rust | `rust:1.70-slim` |

Docker may need to download the selected image during its first execution.

### 3. Parallel Docker Execution

- Splits selected tests into separate Docker jobs.
- Allows the maximum number of concurrent containers to be configured.
- Exposes session-based progress and result queries.
- Supports cancellation of an active parallel execution.

Parallel execution can consume significant CPU and memory. Configure `max_parallel`, timeout, and additional packages according to the capacity of the execution host.

### 4. Docker Sandbox

The sandbox runs test code entered directly in the user interface inside Docker. It does not require selecting a generated test process from the database.

### 5. Robot Simulation

- Provides a container-based simulation path for `generic`, `industrial`, and `collaborative` robot types.
- Can build a Python environment with NumPy, SciPy, Matplotlib, Robotics Toolbox, and SpatialMath.
- Does not establish a direct connection to a physical robot controller.

### 6. ROS 2 Docker Execution

- Checks whether the expected ROS 2 Docker container is running.
- Copies a test script into the container as `/tmp/stlc_<test-id>.py`.
- Sources the ROS 2 environment and executes the script inside the container.
- Supports single and batch execution.
- Can use X11/GUI configuration for visual tests.
- Collects the exit code, output, errors, and duration.

The ROS 2 image definition and helper scripts are under `docker/`. The compose file in that directory assumes a specific external ROS 2 workspace layout. Review and adjust its build context and volume paths for your own workspace.

### 7. Robot Test Execution (ROS 2 and Gazebo)

The robot test panel can:

- Retrieve generated tests by process name.
- Run selected tests as a batch.
- Query session progress and results.
- Check Gazebo availability through a dedicated endpoint.
- Store execution records in MongoDB.

This execution path requires a Docker, ROS 2, and Gazebo environment that is accessible to the backend host.

## Execution on a remote robot computer

The project contains a **Remote Robot Execution** user interface and backend service. This feature is a shared-directory deployment protocol, not direct SSH/SFTP-based remote command execution.

### Current workflow

1. STLC Manager creates an execution directory under the supplied local or UNC network path.
2. It prepares the following directory and metadata structure:

```text
test_exec_<session>_<timestamp>/
├── source_files/
├── results/
├── logs/
├── deployment_info.json
└── execution_status.json
```

3. Generated test code is written to `source_files/`.
4. An external runner or service on the robot computer reads and executes the tests.
5. The runner writes JSON results to `results/`, writes logs to `logs/`, and updates the status file.
6. STLC Manager reads the results and aggregates total, passed, failed, and skipped tests together with the pass rate.

### Requirements for a computer in another city

- A VPN or corporate network connection between the two computers
- A directory on the remote computer exposed through SMB/UNC, for example `\\robot-pc\stlc-tests`
- Read and write permissions for the operating-system account running the FastAPI backend
- A separate runner or agent on the remote computer that monitors the directory and executes tests
- A runner implementation that writes the expected JSON result format and updates `execution_status.json`

### Operations that are not currently automated

- SSH connection and authentication
- SFTP/SCP file transfer
- Starting or stopping a process on the remote computer
- Remote runner installation or updates
- Durable job queues and retry policies for offline machines
- Operator approval and safety PLC integration for physical robots

The accurate description of the current feature is therefore:

> Shared-directory-based remote test deployment and result collection are implemented. End-to-end remote execution orchestration still requires a runner on the target computer.

## Architecture and directory structure

```text
STLC-Manager/
├── backend/
│   ├── app.py                    # Main FastAPI application (port 8000)
│   ├── mcp_server.py             # MCP test execution service (port 8001)
│   ├── config/                   # Model and optimization configuration
│   ├── core/                     # MongoDB, file, and prompt infrastructure
│   ├── models/                   # Robot and test-criteria data models
│   ├── pipeline/                 # Pipeline order, models, and executor
│   ├── routers/                  # REST API endpoints
│   ├── services/                 # Business logic and execution services
│   ├── stlc/                     # STLC process implementations
│   ├── templates/                # Docker and output templates
│   ├── utils/                    # Model client, text, and validation utilities
│   └── scripts/
│       ├── diagnostics/          # Read-only inspection tools
│       ├── experiments/          # Manual debugging and experiments
│       ├── maintenance/          # Data maintenance and repair tools
│       └── migrations/           # Database migration tools
├── frontend/
│   ├── src/components/           # React components
│   ├── src/store/                # Redux store and slices
│   ├── src/services/             # Backend API calls
│   └── src/hooks/                # Model, API-key, and pipeline hooks
├── docker/                       # ROS 2 Dockerfile, compose file, and helpers
├── test_inputs/                  # Sample test inputs
├── test_results/                 # Experiment and test results
└── tests/
    ├── unit/
    ├── integration/
    ├── performance/
    ├── utils/
    └── results/
```

Some legacy `test_*.py` files remain in the backend root. Several of them are manual or integration tests that depend on live MongoDB, API, Docker, or model services and have not yet been fully classified under `tests/`.

## Prerequisites

Recommended development environment:

- Python 3.10 or later
- Node.js 18 or later
- MongoDB, either local or otherwise made accessible to the application
- An npm-compatible package manager

Optional integrations:

- LM Studio for local LLM execution
- A Google Gemini API key for Gemini models
- Docker Desktop or Docker Engine for container execution
- ROS 2 Humble, a Gazebo/MoveIt workspace, and a suitable Docker image for robot execution
- VcXsrv or an equivalent X server for Windows GUI scenarios

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/cembglm/stlc-man.git
cd STLC-Manager
```

Alternative ESOGU organization remote: <https://github.com/ESOGU-SRLAB/STLC-Manager>

### 2. Install backend dependencies

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux or macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start MongoDB

Ensure that a local MongoDB server is running on `localhost:27017`. The current primary database name is `stlc_database`.

Example Docker command:

```bash
docker run -d --name stlc-mongodb -p 27017:27017 mongo:latest
```

> The current `backend/core/database.py` defines the MongoDB URI directly as `mongodb://localhost:27017`. Changing only `MONGO_URI` in `.env` does not affect that database helper. Centralize the database configuration before using a remote MongoDB deployment.

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

## Running the services

MongoDB, the FastAPI backend, and the frontend must run during normal development. Start the MCP service as well when using Standard Execution.

### Terminal 1 — Backend API

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python app.py
```

Backend: <http://localhost:8000>

Swagger UI: <http://localhost:8000/docs>

### Terminal 2 — MCP server

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python mcp_server.py
```

MCP health endpoint: <http://localhost:8001/health>

When using a local model with Standard Execution, start the LM Studio OpenAI-compatible server on `http://localhost:1234` and load the selected model.

### Terminal 3 — Frontend

```bash
cd frontend
npm run dev
```

The default Vite URL is <http://localhost:5173>.

### Quick checks

```text
GET http://localhost:8000/
GET http://localhost:8000/api/health/prompts
GET http://localhost:8000/api/docker-execution/status
GET http://localhost:8000/api/ros2-execution/status
GET http://localhost:8000/api/remote-execution/health
GET http://localhost:8001/health
GET http://localhost:8001/providers/status
```

## Configuration

Primary backend configuration values:

| Variable | Default | Purpose |
|---|---|---|
| `MODEL_API_BASE_URL` | `http://localhost:1234` | General local model API endpoint |
| `MODEL_IDENTIFIER` | `llama-3.2-3b-instruct` | General default model |
| `MCP_SERVER_URL` | `http://localhost:8001` | MCP endpoint used by the pipeline |
| `MCP_SERVER_PORT` | `8001` | MCP service port |
| `LM_STUDIO_BASE_URL` | `http://localhost:1234` | LM Studio endpoint used by MCP |
| `DEFAULT_LM_STUDIO_MODEL` | `llama-3.2-3b-instruct` | Default local model used by MCP |

Example `backend/.env`:

```dotenv
MODEL_API_BASE_URL=http://localhost:1234
MODEL_IDENTIFIER=llama-3.2-3b-instruct
MCP_SERVER_URL=http://localhost:8001
MCP_SERVER_PORT=8001
LM_STUDIO_BASE_URL=http://localhost:1234
DEFAULT_LM_STUDIO_MODEL=llama-3.2-3b-instruct
```

API keys can be entered through the API Key settings in the user interface and are sent to the backend with the relevant requests. Never commit API keys to the repository.

The frontend has partial support for `VITE_API_BASE_URL`, but several components still use `http://localhost:8000` directly. If the frontend and backend are hosted on different machines, route all frontend API calls through a centralized base URL first.

## Tests and utility scripts

The primary test structure is under `tests/`:

```bash
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest tests/performance
```

`pytest` is not currently listed in `backend/requirements.txt`. Install the test dependencies separately in your development environment:

```bash
pip install pytest pytest-asyncio
```

Some tests use live MongoDB, LM Studio/Gemini, Docker, or running backend endpoints. Review the requirements of each test file before running the entire suite; not every file is a self-contained unit test.

Backend utility scripts are organized under `backend/scripts/`. Run them as modules from the `backend` directory so imports continue to resolve correctly:

```powershell
cd backend
python -m scripts.diagnostics.check_routes
python -m scripts.diagnostics.check_mongo_connection
```

Utilities under `maintenance/` and `migrations/` can modify or delete data. Review their source code and target database before running them.

## API and health checks

When FastAPI is running, the current endpoint list is available through Swagger:

- Swagger UI: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

Primary API groups:

| Prefix | Purpose |
|---|---|
| `/api/processes/*` | Run individual STLC steps |
| `/api/prompts/*` | Read or update module prompts |
| `/api/models/*` | List and filter configured models |
| `/api/pipeline/*` | Start, monitor, inspect, or stop a pipeline |
| `/api/test-execution/*` | MCP and AI-based test execution |
| `/api/docker-execution/*` | Docker, simulation, and parallel execution |
| `/api/ros2-execution/*` | ROS 2 container execution |
| `/api/robot-execution/*` | ROS 2/Gazebo robot test sessions |
| `/api/remote-execution/*` | Shared-directory deployment and result collection |
| `/api/test-reporting/*` | Test reporting |
| `/api/test-closure/*` | Test closure reports |

## Known limitations

- Remote execution does not use SSH, SFTP, or WinRM; it requires an accessible filesystem or UNC share.
- The repository does not yet provide a complete target-side runner service for the robot computer.
- The MongoDB connection in `backend/core/database.py` is fixed to the local address.
- Frontend API endpoints are not fully centralized, so multi-host deployment requires additional configuration work.
- `docker/docker-compose.yml` assumes a specific external ROS 2 workspace layout.
- Some tests require live external services and are not suitable for unattended CI execution as currently written.
- Legacy backend test scripts have not been completely moved under `tests/`.
- Python dependency versions are not pinned, so a lock or version-pinning strategy is still needed for reproducible deployments.
- Standard Execution output and tests actually executed in Docker or ROS 2 should not be treated as having the same evidence level.

## Security considerations

- Treat generated test code as untrusted code.
- Docker socket access is highly privileged; do not expose the backend directly to untrusted users.
- Only trusted users should be allowed to request additional package installation.
- Apply least-privilege permissions to Remote Execution network shares.
- Never write API keys to source files, test results, or logs.
- CORS is intentionally broad for development; restrict allowed origins before production deployment.
- Physical robot testing requires simulation validation, speed, torque, and workspace limits, an emergency stop, safety PLC integration, and explicit operator approval.

## Contribution and development workflow

When adding a feature:

1. Keep business logic under `backend/services/`.
2. Define the HTTP layer under `backend/routers/`.
3. If the feature joins the pipeline, update `pipeline_controller.py` and `step_adapters.py` together.
4. Route frontend calls through the centralized API helper whenever possible.
5. Add tests to the appropriate `unit`, `integration`, or `performance` category.
6. Document MongoDB schema and session-output changes.
7. Update this README and the relevant Docker or ROS 2 guide.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
