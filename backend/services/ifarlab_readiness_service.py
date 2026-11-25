"""Fail-closed readiness and canonical IFARLAB contract-bundle checks."""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List

from core.settings import get_settings


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PATH = ROOT / "config" / "ifarlab_bundle_expected.json"
LLM_POLICY_PATH = ROOT / "config" / "llm_sut_allowlist.json"
CAPABILITY_PATH = ROOT / "config" / "robot_capabilities.json"
DECISIONS_PATH = ROOT / "config" / "ifarlab_decisions.json"
VECTOR_RESULT_PATH = ROOT / "config" / "ifarlab_contracts" / "validation_result.json"
MAX_BUNDLE_BYTES = 100 * 1024 * 1024


class ContractBundleError(ValueError):
    pass


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_contract_bundle(path: Path) -> Dict[str, Any]:
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    path = Path(path)
    if not path.is_file():
        raise ContractBundleError("canonical IFARLAB contract bundle is not installed")
    if path.stat().st_size > MAX_BUNDLE_BYTES:
        raise ContractBundleError("contract bundle exceeds 100 MB")
    package_sha = _sha256(path.read_bytes())
    if package_sha != expected["sha256"]:
        raise ContractBundleError("contract bundle SHA-256 does not match the IFARLAB-pinned value")

    files: Dict[str, bytes] = {}
    with tarfile.open(path, "r:") as archive:
        for member in archive.getmembers():
            normalized = PurePosixPath(member.name)
            if normalized.is_absolute() or ".." in normalized.parts:
                raise ContractBundleError("contract bundle contains an unsafe path")
            if member.issym() or member.islnk():
                raise ContractBundleError("contract bundle links are not allowed")
            if not member.isfile():
                continue
            stream = archive.extractfile(member)
            if stream is None:
                raise ContractBundleError(f"could not read {member.name}")
            files[member.name] = stream.read()

    basenames = {PurePosixPath(name).name for name in files}
    required = {"verdict_engine.py", "rule_sets.json", "README.md", "CHANGELOG.md", "package.json", "SHA256SUMS"}
    missing = sorted(required - basenames)
    if missing:
        raise ContractBundleError("contract bundle is missing: " + ", ".join(missing))

    sums_name = next(name for name in files if PurePosixPath(name).name == "SHA256SUMS")
    sums_dir = PurePosixPath(sums_name).parent
    for line in files[sums_name].decode("utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-f0-9]{64})\s+\*?(.+)", line.strip())
        if not match:
            raise ContractBundleError("SHA256SUMS contains an invalid line")
        digest, relative = match.groups()
        candidate = str(sums_dir / PurePosixPath(relative)) if str(sums_dir) != "." else relative
        if candidate not in files or _sha256(files[candidate]) != digest:
            raise ContractBundleError(f"SHA256SUMS verification failed for {relative}")

    schemas = [name for name in files if name.endswith(".schema.json")]
    vector_files = [name for name in files if "vector" in name.lower() and name.endswith(".json")]
    return {
        "valid": True,
        "package_sha256": package_sha,
        "file_count": len(files),
        "schema_count": len(schemas),
        "vector_file_count": len(vector_files),
        "expected": expected,
        "content_minimums_met": len(schemas) >= expected["expected_schema_count"],
    }


def readiness_report() -> Dict[str, Any]:
    settings = get_settings()
    checks: List[Dict[str, Any]] = []

    def add(check_id: str, status: str, detail: str, owner: str = "ASRLab") -> None:
        checks.append({"id": check_id, "status": status, "owner": owner, "detail": detail})

    add("http_result_ingest", "pass" if not settings.allow_http_result_ingest else "fail",
        "HTTP result ingestion is disabled." if not settings.allow_http_result_ingest else "Disable ALLOW_HTTP_RESULT_INGEST.")

    policy = json.loads(LLM_POLICY_PATH.read_text(encoding="utf-8"))
    invalid_active = [entry.get("approval_id") for entry in policy.get("approvals", []) if entry.get("active") and (
        entry.get("status") != "approved" or not entry.get("approved_by") or not entry.get("approved_at")
    )]
    add("llm_fail_closed", "pass" if not invalid_active else "fail",
        "No incomplete LLM approval is active." if not invalid_active else "Incomplete active approvals: " + ", ".join(invalid_active))

    decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    for decision in decisions.get("decisions", []):
        decided = decision.get("status") == "approved"
        add("decision:" + decision["id"], "pass" if decided else "blocked",
            decision.get("note", decision.get("status", "pending")), decision.get("required_from", "IFARLAB+ASRLab"))

    capability_raw = CAPABILITY_PATH.read_bytes()
    capability = json.loads(capability_raw.decode("utf-8-sig"))
    expected_capability_sha = "580d1637d385c8602fd3ff1f4f12e913030b156eb0f0c146cdaf311db98001d9"
    actual_capability_sha = _sha256(capability_raw)
    add("robot_capability_bytes", "pass" if actual_capability_sha == expected_capability_sha else "blocked",
        f"actual={actual_capability_sha}; expected={expected_capability_sha}", "IFARLAB+ASRLab")
    approval = capability.get("meta", {}).get("approval", {})
    approved = approval.get("approved") is True and approval.get("approved_by") and approval.get("approved_at")
    add("robot_capability_approval", "pass" if approved else "blocked",
        "Capability contract is approved." if approved else "Human engineering approval and Q1-Q5 closure are required.", "IFARLAB+ASRLab")

    try:
        bundle = validate_contract_bundle(settings.ifarlab_contract_bundle_path)
        add("canonical_contract_bundle", "pass" if bundle["content_minimums_met"] else "fail", json.dumps(bundle, sort_keys=True))
        validation = json.loads(VECTOR_RESULT_PATH.read_text(encoding="utf-8")) if VECTOR_RESULT_PATH.is_file() else {}
        compatible = (
            validation.get("package_sha256") == bundle["package_sha256"]
            and validation.get("passed") == bundle["expected"]["expected_vector_count"]
            and validation.get("failed") == 0
        )
        add("canonical_vector_compatibility", "pass" if compatible else "blocked",
            "Canonical vectors passed." if compatible else "Run and record the canonical 53-vector compatibility suite.",
            "IFARLAB+ASRLab")
    except ContractBundleError as exc:
        add("canonical_contract_bundle", "blocked", str(exc), "IFARLAB")
        add("canonical_vector_compatibility", "blocked", "Canonical bundle is required before vectors can run.", "IFARLAB+ASRLab")

    inbox = settings.ifarlab_inbox_dir.resolve()
    add("ssh_inbox_directory", "pass" if inbox.is_dir() else "fail", str(inbox))
    ssh_ready = bool(settings.ssh_execution_host and settings.ssh_execution_identity_file)
    add("ssh_peer_configuration", "pass" if ssh_ready else "blocked",
        "SSH peer and identity configured." if ssh_ready else "IFARLAB host/inbox and an authorized SSH identity are not configured.", "IFARLAB+ASRLab")

    local_failures = [item for item in checks if item["owner"] == "ASRLab" and item["status"] != "pass"]
    external_blockers = [item for item in checks if item["owner"] != "ASRLab" and item["status"] != "pass"]
    return {
        "ready": not local_failures and not external_blockers,
        "asrlab_ready": not local_failures,
        "checks": checks,
        "local_failures": local_failures,
        "external_blockers": external_blockers,
        "pending_decisions": [item for item in decisions.get("decisions", []) if item.get("status") != "approved"],
    }
