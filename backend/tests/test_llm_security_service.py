import json

import pytest

import services.llm_security_service as security


def write_policy(tmp_path, approvals):
    path = tmp_path / "allowlist.json"
    path.write_text(json.dumps({"default": "deny", "approvals": approvals}), encoding="utf-8")
    return path


def test_qcr_only_call_is_not_restricted(monkeypatch, tmp_path):
    monkeypatch.setattr(security, "POLICY_PATH", tmp_path / "missing.json")
    security.assert_llm_data_use_allowed(
        provider="remote", model="anything",
        data_use=security.LLMDataUse(contains_sut_source=False, purpose="qcr_generation"),
    )


def test_sut_source_is_denied_for_unapproved_provider(monkeypatch, tmp_path):
    monkeypatch.setattr(security, "POLICY_PATH", write_policy(tmp_path, []))
    with pytest.raises(security.SUTSourceDisclosureDenied, match="not approved"):
        security.assert_llm_data_use_allowed(
            provider="gemini", model="gemini-pro",
            data_use=security.LLMDataUse(contains_sut_source=True, purpose="test_generation"),
        )


def test_sut_source_requires_provider_and_model_match(monkeypatch, tmp_path):
    monkeypatch.setattr(security, "POLICY_PATH", write_policy(tmp_path, [{
        "approval_id": "A-1", "provider": "local", "model": "approved-model", "active": True,
        "status": "approved", "approved_by": "IFARLAB security", "approved_at": "2026-11-25T10:00:00Z",
    }]))
    security.assert_llm_data_use_allowed(
        provider="local", model="approved-model",
        data_use=security.LLMDataUse(contains_sut_source=True, purpose="patch_generation"),
    )
    with pytest.raises(security.SUTSourceDisclosureDenied):
        security.assert_llm_data_use_allowed(
            provider="local", model="other-model",
            data_use=security.LLMDataUse(contains_sut_source=True),
        )


@pytest.mark.parametrize("entry", [
    {"approval_id": "A-1", "provider": "local", "model": "*", "active": True},
    {"approval_id": "A-1", "provider": "local", "model": "*", "active": True,
     "status": "pending_external_approval", "approved_by": "IFARLAB-pending-confirmation"},
    {"approval_id": "A-1", "provider": "local", "model": "*", "active": True,
     "status": "approved", "approved_by": "IFARLAB security"},
])
def test_pending_or_incomplete_approval_is_fail_closed(monkeypatch, tmp_path, entry):
    monkeypatch.setattr(security, "POLICY_PATH", write_policy(tmp_path, [entry]))
    with pytest.raises(security.SUTSourceDisclosureDenied):
        security.assert_llm_data_use_allowed(
            provider="local", model="any-model",
            data_use=security.LLMDataUse(contains_sut_source=True),
        )
