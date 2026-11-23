"""Fail-closed policy for prompts that contain IFARLAB SUT source code."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


POLICY_PATH = Path(__file__).resolve().parents[2] / "config" / "llm_sut_allowlist.json"
logger = logging.getLogger(__name__)


class SUTSourceDisclosureDenied(PermissionError):
    """Raised before an LLM request can disclose SUT source to an unapproved model."""


@dataclass(frozen=True)
class LLMDataUse:
    contains_sut_source: bool = False
    purpose: str = "unspecified"


def _policy() -> dict:
    try:
        value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SUTSourceDisclosureDenied("SUT LLM allowlist is unavailable or invalid") from exc
    if value.get("default") != "deny":
        raise SUTSourceDisclosureDenied("SUT LLM allowlist must be fail-closed")
    return value


def assert_llm_data_use_allowed(
    *, provider: str, model: Optional[str], data_use: LLMDataUse
) -> None:
    """Authorize an LLM call before network I/O.

    QCR-only calls are intentionally unaffected until IFARLAB decides whether
    they also require restrictions. Any call marked as containing SUT source is
    denied unless both provider and model match an active approval entry.
    """
    if not data_use.contains_sut_source:
        return
    normalized_provider = (provider or "").strip().lower()
    normalized_model = (model or "").strip()
    policy = _policy()
    for entry in policy.get("approvals", []):
        if not entry.get("active", False):
            continue
        if entry.get("provider", "").strip().lower() != normalized_provider:
            continue
        approved_model = entry.get("model")
        if approved_model == "*" or approved_model == normalized_model:
            logger.info(
                "Approved SUT source LLM use provider=%s model=%s purpose=%s approval=%s",
                normalized_provider, normalized_model, data_use.purpose, entry.get("approval_id"),
            )
            return
    logger.warning(
        "Denied SUT source LLM use provider=%s model=%s purpose=%s",
        normalized_provider, normalized_model, data_use.purpose,
    )
    raise SUTSourceDisclosureDenied(
        f"IFARLAB has not approved provider/model for SUT source: "
        f"{normalized_provider}/{normalized_model or '<unset>'}"
    )
