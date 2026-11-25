"""Safe importer for IFARLAB result packages delivered into the SSH inbox."""

import json
import hashlib
import re
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any, Dict

from core.settings import get_settings
from models.traceability import IFARLABResult


PACKAGE_PATTERN = re.compile(
    r"^(?P<submission>S-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})__"
    r"(?P<run>R-[0-9]{8}-[0-9]{4})\.result\.tar$"
)
ALLOWED_MEMBERS = {"result.json", "verdict.json", "metrics.json", "junit.xml", "coverage.xml"}
REQUIRED_MEMBERS = {"result.json", "verdict.json", "metrics.json", "junit.xml"}
MAX_PACKAGE_BYTES = 50 * 1024 * 1024
MAX_RESULT_BYTES = 10 * 1024 * 1024


class ResultPackageError(ValueError):
    pass


def package_path(package_name: str) -> Path:
    if not PACKAGE_PATTERN.fullmatch(package_name):
        raise ResultPackageError("result package name does not follow the integration contract")
    root = get_settings().ifarlab_inbox_dir.resolve()
    candidate = (root / package_name).resolve()
    if candidate.parent != root:
        raise ResultPackageError("result package must remain inside the configured inbox")
    return candidate


def read_result_package(package_name: str) -> IFARLABResult:
    path = package_path(package_name)
    if not path.is_file():
        raise FileNotFoundError(package_name)
    if path.stat().st_size > MAX_PACKAGE_BYTES:
        raise ResultPackageError("result package exceeds the configured size limit")

    with tarfile.open(path, mode="r:") as archive:
        members = archive.getmembers()
        total_size = 0
        by_name: Dict[str, tarfile.TarInfo] = {}
        for member in members:
            normalized = PurePosixPath(member.name)
            if normalized.is_absolute() or ".." in normalized.parts or len(normalized.parts) != 1:
                raise ResultPackageError("nested or traversal archive paths are not allowed")
            if member.issym() or member.islnk() or not member.isfile():
                raise ResultPackageError("links and non-file archive entries are not allowed")
            if member.name not in ALLOWED_MEMBERS:
                raise ResultPackageError(f"unexpected result package member: {member.name}")
            total_size += member.size
            if total_size > MAX_PACKAGE_BYTES:
                raise ResultPackageError("expanded result package exceeds the size limit")
            if member.name in by_name:
                raise ResultPackageError(f"duplicate result package member: {member.name}")
            by_name[member.name] = member
        missing = sorted(REQUIRED_MEMBERS - set(by_name))
        if missing:
            raise ResultPackageError("missing required package members: " + ", ".join(missing))
        result_member = by_name["result.json"]
        if result_member.size > MAX_RESULT_BYTES:
            raise ResultPackageError("result.json exceeds the size limit")
        json_payloads = {}
        member_hashes: Dict[str, str] = {}
        for name in ("result.json", "verdict.json", "metrics.json"):
            stream = archive.extractfile(by_name[name])
            if stream is None:
                raise ResultPackageError(f"{name} could not be read")
            try:
                raw_member = stream.read()
                member_hashes[name] = hashlib.sha256(raw_member).hexdigest()
                json_payloads[name] = json.loads(raw_member.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ResultPackageError(f"{name} must be valid UTF-8 JSON") from exc
        for name in ("junit.xml", "coverage.xml"):
            if name not in by_name:
                continue
            stream = archive.extractfile(by_name[name])
            if stream is None:
                raise ResultPackageError(f"{name} could not be read")
            try:
                raw_member = stream.read()
                member_hashes[name] = hashlib.sha256(raw_member).hexdigest()
                ET.fromstring(raw_member)
            except ET.ParseError as exc:
                raise ResultPackageError(f"{name} must be well-formed XML") from exc
        payload: Dict[str, Any] = json_payloads["result.json"]

    match = PACKAGE_PATTERN.fullmatch(package_name)
    if payload.get("submission_id") != match.group("submission") or payload.get("run_id") != match.group("run"):
        raise ResultPackageError("package name identifiers do not match result.json")
    for document_name in ("verdict.json", "metrics.json"):
        document = json_payloads[document_name]
        if not isinstance(document, dict):
            raise ResultPackageError(f"{document_name} root must be a JSON object")
        for field in ("submission_id", "run_id", "requirements_set_version", "code_sha256", "contract_sha256"):
            if field in document and document[field] != payload.get(field):
                raise ResultPackageError(f"{document_name}.{field} does not match result.json")
    inputs = json_payloads["verdict.json"].get("inputs", {})
    if inputs is not None and not isinstance(inputs, dict):
        raise ResultPackageError("verdict.json.inputs must be an object")
    for member_name, declared in (inputs or {}).items():
        if member_name not in member_hashes:
            continue
        declared_hash = declared.get("sha256") if isinstance(declared, dict) else declared
        if declared_hash != member_hashes[member_name]:
            raise ResultPackageError(f"verdict.json.inputs hash mismatch for {member_name}")
    payload["package_manifest"] = {
        "package_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "members": member_hashes,
    }
    payload["package_verdict"] = json_payloads["verdict.json"]
    payload["package_metrics"] = json_payloads["metrics.json"]
    return IFARLABResult(**payload)
