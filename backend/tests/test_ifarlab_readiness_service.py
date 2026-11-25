import hashlib
import io
import json
import tarfile
from types import SimpleNamespace

import services.ifarlab_readiness_service as readiness


def test_readiness_separates_local_failures_from_external_blockers(monkeypatch, tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    monkeypatch.setattr(readiness, "get_settings", lambda: SimpleNamespace(
        allow_http_result_ingest=False, ifarlab_contract_bundle_path=tmp_path / "missing.tar",
        ifarlab_inbox_dir=inbox, ssh_execution_host=None, ssh_execution_identity_file=None,
    ))
    report = readiness.readiness_report()
    assert report["asrlab_ready"] is True
    assert report["ready"] is False
    assert {item["id"] for item in report["external_blockers"]} >= {
        "canonical_contract_bundle", "robot_capability_approval", "ssh_peer_configuration",
    }


def test_contract_bundle_verifies_pinned_hash_and_internal_sums(monkeypatch, tmp_path):
    files = {
        "verdict_engine.py": b"ENGINE_VERSION='2.6.0'\n",
        "rule_sets.json": b"{}",
        "README.md": b"readme",
        "CHANGELOG.md": b"changes",
        "package.json": b"{}",
    }
    for index in range(20):
        files[f"schemas/{index:02d}.schema.json"] = b"{}"
    for index in range(53):
        files[f"vectors/vector_{index:02d}.json"] = b"{}"
    sums = "\n".join(f"{hashlib.sha256(data).hexdigest()}  {name}" for name, data in files.items()).encode()
    files["SHA256SUMS"] = sums
    bundle = tmp_path / "bundle.tar"
    with tarfile.open(bundle, "w") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    expected = tmp_path / "expected.json"
    expected.write_text(json.dumps({
        "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "expected_schema_count": 20, "expected_vector_count": 53,
    }), encoding="utf-8")
    monkeypatch.setattr(readiness, "EXPECTED_PATH", expected)
    result = readiness.validate_contract_bundle(bundle)
    assert result["valid"] is True
    assert result["schema_count"] == 20
    assert result["vector_file_count"] == 53
