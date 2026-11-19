"""Safe importer for IFARLAB result packages delivered into the SSH inbox."""

import json
import re
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict

from core.settings import get_settings
from models.traceability import IFARLABResult


PACKAGE_PATTERN = re.compile(
    r"^(?P<submission>S-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})__"
    r"(?P<run>R-[0-9]{8}-[0-9]{4})\.result\.tar$"
)
ALLOWED_MEMBERS = {"result.json", "verdict.json", "metrics.json", "junit.xml"}
REQUIRED_MEMBERS = set(ALLOWED_MEMBERS)
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
        stream = archive.extractfile(result_member)
        if stream is None:
            raise ResultPackageError("result.json could not be read")
        try:
            payload: Dict[str, Any] = json.loads(stream.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResultPackageError("result.json must be valid UTF-8 JSON") from exc

    match = PACKAGE_PATTERN.fullmatch(package_name)
    if payload.get("submission_id") != match.group("submission") or payload.get("run_id") != match.group("run"):
        raise ResultPackageError("package name identifiers do not match result.json")
    return IFARLABResult(**payload)
