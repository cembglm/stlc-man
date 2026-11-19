import io
import json
import tarfile
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import services.ifarlab_package_service as packages
from services.traceability_contract import contract_sha256


PACKAGE = "S-2026-11-18-0042__R-20261118-0197.result.tar"


def result_payload():
    return {
        "schema_version": "1.0",
        "submission_id": "S-2026-11-18-0042",
        "run_id": "R-20261118-0197",
        "requirements_set_version": "2026-11-18",
        "code_sha256": "a" * 64,
        "contract_sha256": contract_sha256(),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "test_results": [],
    }


def write_tar(path, members):
    with tarfile.open(path, "w") as archive:
        for name, content in members.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def configure(monkeypatch, root):
    monkeypatch.setattr(packages, "get_settings", lambda: SimpleNamespace(ifarlab_inbox_dir=root))


def test_reads_complete_safe_result_package(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path)
    write_tar(tmp_path / PACKAGE, {
        "result.json": json.dumps(result_payload()), "verdict.json": "{}",
        "metrics.json": "{}", "junit.xml": "<testsuite />",
    })
    result = packages.read_result_package(PACKAGE)
    assert result.submission_id == "S-2026-11-18-0042"
    assert result.run_id == "R-20261118-0197"


def test_rejects_archive_traversal(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path)
    write_tar(tmp_path / PACKAGE, {
        "../result.json": json.dumps(result_payload()), "verdict.json": "{}",
        "metrics.json": "{}", "junit.xml": "<testsuite />",
    })
    with pytest.raises(packages.ResultPackageError, match="traversal"):
        packages.read_result_package(PACKAGE)


def test_rejects_missing_contract_member(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path)
    write_tar(tmp_path / PACKAGE, {"result.json": json.dumps(result_payload())})
    with pytest.raises(packages.ResultPackageError, match="missing required"):
        packages.read_result_package(PACKAGE)
