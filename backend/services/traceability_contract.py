"""Canonical hashing and manifest-to-code validation."""

import ast
import hashlib
import json
import re
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from models.traceability import SubmissionManifest


SUBMISSION_PREFIX = "S"
CONTRACT_PATH = Path(__file__).resolve().parents[2] / "config" / "ifarlab_contract_v1.json"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "dict"):
        return _jsonable(value.model_dump(exclude_none=False))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """RFC-8259 JSON encoded as UTF-8, sorted keys, compact separators.

    Numbers are emitted by the validated Pydantic model. Producers must hash the
    exact UTF-8 bytes returned here; no BOM, trailing newline, or whitespace is
    included.
    """
    return json.dumps(
        _jsonable(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=str, allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def contract_document() -> Dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def contract_sha256() -> str:
    return sha256_bytes(CONTRACT_PATH.read_bytes())


def python_test_functions(code: str) -> List[str]:
    tree = ast.parse(code)
    return [
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]


def validate_manifest_mapping(
    code: str,
    manifest: SubmissionManifest,
    requirement_ids: Iterable[str],
    test_case_ids: Iterable[str],
) -> None:
    discovered = python_test_functions(code)
    mapped = [item.function for item in manifest.tests]
    if len(mapped) != len(set(mapped)):
        raise ValueError("manifest contains duplicate function mappings")
    if sorted(discovered) != sorted(mapped):
        raise ValueError(f"manifest functions {sorted(mapped)} do not match code functions {sorted(discovered)}")
    known_requirements: Set[str] = set(requirement_ids)
    known_cases: Set[str] = set(test_case_ids)
    for item in manifest.tests:
        if item.test_case_id not in known_cases:
            raise ValueError(f"unknown test case identifier: {item.test_case_id}")
        unknown = sorted(set(item.requirements) - known_requirements)
        if unknown:
            raise ValueError(f"unknown requirement identifiers: {', '.join(unknown)}")
        required_prefix = f"test_{item.test_case_id.lower()}_"
        if not item.function.startswith(required_prefix):
            raise ValueError(f"test function {item.function!r} must start with {required_prefix!r}")
    actual_hash = sha256_bytes(code.encode("utf-8"))
    if manifest.code_sha256 != actual_hash:
        raise ValueError("code_sha256 does not match the exact UTF-8 test code bytes")
    if manifest.contract_sha256 != contract_sha256():
        raise ValueError("contract_sha256 does not match the active integration contract")


def format_submission_id(day: str, sequence: int) -> str:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", day):
        raise ValueError("submission day must use YYYY-MM-DD")
    if sequence < 1 or sequence > 9999:
        raise ValueError("daily submission sequence must be between 1 and 9999")
    return f"{SUBMISSION_PREFIX}-{day}-{sequence:04d}"
