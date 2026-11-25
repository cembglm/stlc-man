import hashlib

from services.robot_capability_service import capability_descriptor


def test_descriptor_preserves_exact_byte_identity_when_raw_contract_is_available():
    contract = {"schema_version": "1", "meta": {"approval": {"approved": True}}}
    raw = b'{"schema_version":"1","meta":{"approval":{"approved":true}}}'
    descriptor = capability_descriptor(contract, raw)
    assert descriptor["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert descriptor["hash_mode"] == "canonical_json"
    assert descriptor["semantic_sha256"]
