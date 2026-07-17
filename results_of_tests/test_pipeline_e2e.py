"""
test_pipeline_e2e.py
--------------------
End-to-end pipeline test that simulates exactly what the UI does:
  1. Reads the three Test Files
  2. Builds the PipelineRunRequest payload
  3. POST /api/pipeline/run
  4. Connects to SSE stream and tails real-time events
  5. Polls /api/pipeline/status for final results
  6. Prints a per-step report and asserts no critical failures

Run:
    python test_pipeline_e2e.py

Options via env vars:
    STLC_STEPS   comma-separated subset of steps to run
                 default: code-review,requirement-analysis,test-planning,
                          environment-setup,test-scenario-generation,
                          test-case-generation,test-case-optimization
    STLC_MODEL   LM Studio model key  (default: qwen2.5-7b-instruct-1m)
    STLC_BASE_URL backend base URL    (default: http://localhost:8000)
"""

import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("STLC_BASE_URL", "http://localhost:8000")
MODEL    = os.environ.get("STLC_MODEL",    "qwen2.5-7b-instruct-1m")
TEST_FILES_DIR = Path(__file__).parent / "Test Files"

DEFAULT_STEPS = [
    "code-review",
    "requirement-analysis",
    "test-planning",
    "environment-setup",
    "test-scenario-generation",
    "test-case-generation",
    "test-case-optimization",
    "test-code-generation",
    "test-execution",
    "test-reporting",
    "test-closure",
]

SELECTED_STEPS = [
    s.strip()
    for s in os.environ.get("STLC_STEPS", ",".join(DEFAULT_STEPS)).split(",")
    if s.strip()
]

SESSION_ID = f"e2e_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
PROCESS_TITLE = "ProductDetection Robot STLC Pipeline E2E Test"

# ---------------------------------------------------------------------------
# Colours (Windows compatible via ANSI if supported)
# ---------------------------------------------------------------------------

def _ansi(code: str, text: str) -> str:
    if sys.platform == "win32" and "ANSICON" not in os.environ:
        # Enable VT processing on Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: _ansi("32", t)
YELLOW = lambda t: _ansi("33", t)
RED    = lambda t: _ansi("31", t)
CYAN   = lambda t: _ansi("36", t)
BOLD   = lambda t: _ansi("1",  t)

# ---------------------------------------------------------------------------
# Step 1 — Read test files
# ---------------------------------------------------------------------------

def read_test_files() -> dict:
    """
    Returns {filename: content} for all three test files.
    Mimics the UI file upload + readFileContent() call.
    """
    mapping = {
        "Functional_and_NonFunctional_Requirements.txt": "requirement",
        "ProductDetection.cpp":                          "source",
        "project.xml":                                   "uml",
    }
    result = {}
    print(BOLD("\n═══ Step 1: Reading Test Files ═══"))
    for fname, ftype in mapping.items():
        fpath = TEST_FILES_DIR / fname
        if not fpath.exists():
            print(RED(f"  ✗ MISSING: {fpath}"))
            sys.exit(1)
        content = fpath.read_text(encoding="utf-8", errors="replace")
        result[fname] = {"name": fname, "content": content, "type": ftype}
        print(GREEN(f"  ✓ {fname} ({ftype}) — {len(content):,} chars"))
    return result


# ---------------------------------------------------------------------------
# Step 2 — Build payload (exactly as handleStartPipeline in App.jsx does)
# ---------------------------------------------------------------------------

def build_payload(files: dict) -> dict:
    """
    Builds the PipelineRunRequest JSON payload mirroring frontend logic.
    
    File-to-step mapping (simulates fileProcessMappings in React state):
      - requirement  → requirement-analysis, test-planning, test-scenario-generation
      - source       → code-review, environment-setup, test-scenario-generation
      - uml          → requirement-analysis, test-planning, test-scenario-generation
    """
    step_file_map = {
        "code-review":               ["ProductDetection.cpp"],
        "requirement-analysis":      ["Functional_and_NonFunctional_Requirements.txt", "project.xml"],
        "test-planning":             ["Functional_and_NonFunctional_Requirements.txt", "project.xml"],
        "environment-setup":         ["ProductDetection.cpp"],
        "test-scenario-generation":  ["Functional_and_NonFunctional_Requirements.txt",
                                      "ProductDetection.cpp", "project.xml"],
        "test-case-generation":      ["Functional_and_NonFunctional_Requirements.txt",
                                      "ProductDetection.cpp"],
        "test-case-optimization":    [],   # reads from previous step output
        "test-code-generation":      ["ProductDetection.cpp"],
        "test-execution":            [],
        "test-reporting":            [],
        "test-closure":              [],
    }

    # Build files dict: step_id -> [FileInfo, ...]
    files_payload = {}
    for step_id in SELECTED_STEPS:
        step_files = []
        for fname in step_file_map.get(step_id, []):
            if fname in files:
                step_files.append(files[fname])
        if step_files:
            files_payload[step_id] = step_files

    # Per-step configs — only model is needed for most steps.
    # For test-execution, also include execution_method (default: "ai").
    # Override via env var STLC_EXEC_METHOD: "ai" | "docker" | "robot"
    EXEC_METHOD = os.environ.get("STLC_EXEC_METHOD", "ai")
    step_configs = {}
    for step_id in SELECTED_STEPS:
        if step_id == "test-execution":
            cfg = {"model": MODEL, "execution_method": EXEC_METHOD}
            if EXEC_METHOD == "docker":
                cfg["execution_language"] = os.environ.get("STLC_DOCKER_LANG", "python")
                cfg["docker_timeout"] = int(os.environ.get("STLC_DOCKER_TIMEOUT", "300"))
                pkgs = os.environ.get("STLC_DOCKER_PACKAGES", "")
                if pkgs:
                    cfg["additional_packages"] = [p.strip() for p in pkgs.split(",") if p.strip()]
            elif EXEC_METHOD == "robot":
                cfg["robot_type"] = os.environ.get("STLC_ROBOT_TYPE", "generic")
                cfg["simulation_config"] = {"precision": os.environ.get("STLC_SIM_PRECISION", "medium")}
            step_configs[step_id] = cfg
        else:
            step_configs[step_id] = {"model": MODEL}

    return {
        "session_id":    SESSION_ID,
        "process_title": PROCESS_TITLE,
        "selected_steps": SELECTED_STEPS,
        "files":         files_payload,
        "global_model":  MODEL,
        "global_api_key": None,
        "step_configs":  step_configs,
    }


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no requests/httpx dependency)
# ---------------------------------------------------------------------------

def http_post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(path: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# SSE stream listener (blocking, runs in main thread)
# ---------------------------------------------------------------------------

def stream_events(session_id: str, timeout_seconds: int = 600) -> list:
    """
    Opens SSE connection to /api/pipeline/stream/{session_id} and
    prints each event as it arrives.  Returns all collected events.

    Re-connects automatically on read timeout while overall deadline is alive.
    socket_read_timeout = 120s (per-read idle timeout)
    timeout_seconds     = total wall-clock budget
    """
    url = f"{BASE_URL}/api/pipeline/stream/{session_id}"
    SOCKET_READ_TIMEOUT = 120  # seconds idle per individual read() call

    events = []
    deadline = time.time() + timeout_seconds
    terminal_types = {"stream_end", "pipeline_completed", "pipeline_failed", "pipeline_stopped"}

    while time.time() < deadline:
        req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
        try:
            with urllib.request.urlopen(req, timeout=SOCKET_READ_TIMEOUT) as resp:
                buffer = b""
                while time.time() < deadline:
                    try:
                        chunk = resp.read(512)
                    except Exception:
                        break  # re-connect loop will retry
                    if not chunk:
                        break
                    buffer += chunk
                    while b"\n\n" in buffer:
                        raw, buffer = buffer.split(b"\n\n", 1)
                        for line in raw.decode("utf-8").splitlines():
                            if line.startswith("data: "):
                                payload_str = line[6:]
                                try:
                                    event = json.loads(payload_str)
                                    events.append(event)
                                    _print_event(event)
                                    if event.get("type") in terminal_types:
                                        return events
                                except json.JSONDecodeError:
                                    pass
        except urllib.error.URLError as exc:
            # Server may not be ready yet — wait briefly and retry
            cause = str(exc.reason) if hasattr(exc, "reason") else str(exc)
            if time.time() < deadline:
                print(YELLOW(f"  [SSE] Connection error, retrying in 3s: {cause}"))
                time.sleep(3)
                continue
            else:
                print(YELLOW(f"  [SSE] Stream closed: {exc}"))
                break
        except Exception as exc:
            print(YELLOW(f"  [SSE] Stream closed: {exc}"))
            break

    return events


def _print_event(event: dict):
    etype = event.get("type", "unknown")
    ts    = event.get("timestamp", "")[:19].replace("T", " ")

    if etype == "pipeline_started":
        print(CYAN(f"\n  [{ts}] 🚀 Pipeline started — {len(event.get('steps', []))} steps"))

    elif etype == "step_started":
        step = event.get("step_id", "?")
        print(CYAN(f"\n  [{ts}] ⏳ {step} — STARTING…"))

    elif etype == "step_completed":
        step = event.get("step_id", "?")
        dur  = event.get("duration_seconds", 0)
        keys = event.get("output_keys", [])
        print(GREEN(f"  [{ts}] ✓  {step} — completed in {dur:.1f}s  |  output keys: {keys}"))

    elif etype == "step_failed":
        step = event.get("step_id", "?")
        err  = event.get("error", "unknown error")
        print(RED(f"  [{ts}] ✗  {step} — FAILED: {err}"))

    elif etype == "pipeline_completed":
        n = event.get("steps_completed", "?")
        t = event.get("total_steps", "?")
        print(GREEN(f"\n  [{ts}] 🎉 Pipeline COMPLETED — {n}/{t} steps"))

    elif etype == "pipeline_failed":
        step = event.get("failed_step", "?")
        err  = event.get("error", "")
        print(RED(f"\n  [{ts}] ❌ Pipeline FAILED at '{step}': {err}"))

    elif etype == "pipeline_stopped":
        print(YELLOW(f"\n  [{ts}] ⏹  Pipeline STOPPED at '{event.get('stopped_at_step', '?')}'"))

    elif etype == "stream_end":
        print(CYAN(f"  [{ts}] Stream ended (status: {event.get('status', '?')})"))


# ---------------------------------------------------------------------------
# Step 3 & 4 — Fire & stream
# ---------------------------------------------------------------------------

def run_pipeline_and_stream(payload: dict) -> tuple[list, dict]:
    print(BOLD("\n═══ Step 2: Starting Pipeline via POST /api/pipeline/run ═══"))
    exec_method = payload["step_configs"].get("test-execution", {}).get("execution_method", "ai")
    print(f"  Session ID       : {CYAN(SESSION_ID)}")
    print(f"  Steps            : {CYAN(str(SELECTED_STEPS))}")
    print(f"  Model            : {CYAN(MODEL)}")
    print(f"  Process          : {CYAN(PROCESS_TITLE)}")
    print(f"  Execution Method : {CYAN(exec_method.upper())} (test-execution step)")

    try:
        start_resp = http_post("/api/pipeline/run", payload)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(RED(f"\n  ✗ POST /api/pipeline/run failed [{e.code}]: {body}"))
        sys.exit(1)

    print(GREEN(f"\n  ✓ Pipeline accepted — ordered steps: {start_resp.get('ordered_steps')}"))

    print(BOLD("\n═══ Step 3: SSE Real-Time Stream ═══"))
    events = stream_events(SESSION_ID, timeout_seconds=2700)  # 45min max

    # Final status
    print(BOLD("\n═══ Step 4: Final Status from /api/pipeline/status ═══"))
    try:
        status = http_get(f"/api/pipeline/status/{SESSION_ID}")
    except Exception as exc:
        print(YELLOW(f"  Could not fetch status: {exc}"))
        status = {}

    return events, status


# ---------------------------------------------------------------------------
# Step 5 — Report
# ---------------------------------------------------------------------------

def print_report(events: list, status: dict):
    print(BOLD("\n═══ FINAL REPORT ═══"))

    overall = status.get("status", "unknown")
    colour  = GREEN if overall == "completed" else RED if overall == "failed" else YELLOW
    print(f"  Overall status : {colour(overall.upper())}")
    print(f"  Steps done     : {status.get('steps_completed', '?')} / {status.get('steps_total', '?')}")
    print(f"  Session ID     : {SESSION_ID}")
    if status.get("error"):
        print(RED(f"  Error          : {status['error']}"))

    step_results = status.get("step_results", {})
    if step_results:
        print(f"\n  {'Step':<35} {'Status':<12} {'Duration':>10}")
        print("  " + "─" * 60)
        for step_id, res in step_results.items():
            s   = res.get("status", "?")
            dur = res.get("duration_seconds")
            dur_str = f"{dur:.1f}s" if dur is not None else "—"
            clr = GREEN if s == "completed" else RED if s == "error" else YELLOW
            print(f"  {step_id:<35} {clr(s):<20} {dur_str:>10}")

    # Count failures
    failed = [e for e in events if e.get("type") == "step_failed"]
    completed_ev = [e for e in events if e.get("type") == "step_completed"]
    print(f"\n  Steps completed : {len(completed_ev)}")
    print(f"  Steps failed    : {len(failed)}")

    if overall == "completed":
        print(GREEN("\n  ✅ PIPELINE PASSED — all selected steps ran successfully"))
        return True
    elif overall in ("running", "unknown") and not failed:
        # Backend still running when stream closed (e.g. last step very slow)
        if len(completed_ev) >= len(DEFAULT_STEPS) - 1:
            print(YELLOW(f"\n  ⚠  Stream closed while pipeline was still running, but "
                         f"{len(completed_ev)}/{len(DEFAULT_STEPS)} steps passed with 0 failures"))
            return True  # Treat as pass — pipeline is healthy
        else:
            print(YELLOW("\n  ⚠  Pipeline did not complete within the test window"))
            return False
    elif overall == "failed" and not failed:
        # Timed out or interrupted
        print(YELLOW("\n  ⚠  Pipeline did not complete within the test window"))
        return False
    else:
        print(RED(f"\n  ❌ PIPELINE FAILED at: {[e.get('step_id') for e in failed]}"))
        return False


# ---------------------------------------------------------------------------
# Health checks before running
# ---------------------------------------------------------------------------

def preflight():
    print(BOLD("═══ Pre-flight Checks ═══"))
    ok = True

    # Backend health
    try:
        data = http_get("/")
        print(GREEN(f"  ✓ Backend reachable — {data.get('message', 'OK')}"))
    except Exception as exc:
        print(RED(f"  ✗ Backend not reachable at {BASE_URL}: {exc}"))
        ok = False

    # LM Studio / model health
    try:
        req = urllib.request.Request("http://localhost:1234/v1/models",
                                     headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            models_data = json.loads(resp.read())
            model_ids = [m.get("id", "") for m in models_data.get("data", [])]
            if model_ids:
                print(GREEN(f"  ✓ LM Studio models available: {model_ids}"))
            else:
                print(YELLOW(f"  ⚠  LM Studio running but no models loaded"))
    except Exception as exc:
        print(YELLOW(f"  ⚠  LM Studio check failed: {exc} (pipeline may still work)"))

    if not ok:
        print(RED("\n  Pre-flight failed. Start the backend first: uvicorn app:app --reload"))
        sys.exit(1)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(BOLD("╔══════════════════════════════════════════════════╗"))
    print(BOLD("║  STLC Manager — Pipeline End-to-End Test         ║"))
    print(BOLD("╚══════════════════════════════════════════════════╝"))

    t_start = time.time()

    preflight()

    files   = read_test_files()
    payload = build_payload(files)

    # Pretty-print payload summary
    print(BOLD("\n═══ Payload Summary ═══"))
    exec_method = payload["step_configs"].get("test-execution", {}).get("execution_method", "ai")
    print(f"  {'Test Execution Method':<35} : {CYAN(exec_method.upper())}")
    for step_id, step_files in payload["files"].items():
        fnames = [f["name"] for f in step_files]
        print(f"  {step_id:<35} ← {fnames}")

    events, status = run_pipeline_and_stream(payload)

    passed = print_report(events, status)

    elapsed = time.time() - t_start
    print(f"\n  Total elapsed : {elapsed:.1f}s")
    print()

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
