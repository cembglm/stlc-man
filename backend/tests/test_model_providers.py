import asyncio
import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.settings import get_settings, reset_settings_cache  # noqa: E402
from pipeline.pipeline_models import PipelineRunRequest, StepConfig  # noqa: E402
from pipeline.step_adapters import _get_step_config  # noqa: E402
from services.model_provider_service import (  # noqa: E402
    get_current_provider,
    get_provider_config,
    model_provider_context,
    provider_slot,
)
from utils.model_client import LLMClient  # noqa: E402


def _reset(monkeypatch, **values):
    for key, value in values.items():
        monkeypatch.setenv(key, str(value))
    reset_settings_cache()


def test_provider_settings_keep_legacy_lm_studio_fallback(monkeypatch):
    monkeypatch.delenv("LM_STUDIO_BASE_URL", raising=False)
    monkeypatch.delenv("LM_STUDIO_API_KEY", raising=False)
    _reset(
        monkeypatch,
        MODEL_API_BASE_URL="http://legacy-lm:1234",
        MODEL_API_KEY="legacy-key",
        COLIBRI_BASE_URL="http://colibri:8011",
        COLIBRI_API_KEY="colibri-key",
        COLIBRI_MODEL_IDENTIFIER="qwen3-coder-30b",
    )
    lm_studio = get_provider_config("lm_studio")
    colibri = get_provider_config("colibri")

    assert lm_studio.api_url == "http://legacy-lm:1234/v1"
    assert lm_studio.api_key == "legacy-key"
    assert colibri.api_url == "http://colibri:8011/v1"
    assert colibri.api_key == "colibri-key"
    assert colibri.default_model == "qwen3-coder-30b"


def test_pipeline_step_provider_and_model_override(monkeypatch):
    _reset(
        monkeypatch,
        DEFAULT_MODEL_PROVIDER="lm_studio",
        COLIBRI_MODEL_IDENTIFIER="colibri-default",
    )
    request = PipelineRunRequest(
        session_id="provider-test",
        process_title="Provider test",
        selected_steps=["code-review", "test-planning"],
        global_provider="lm_studio",
        global_model="lm-model",
        step_configs={
            "test-planning": StepConfig(provider="colibri", model="colibri-model")
        },
    )

    assert _get_step_config(request, "code-review")["model"] == "lm-model"
    planning = _get_step_config(request, "test-planning")
    assert planning["provider"] == "colibri"
    assert planning["model"] == "colibri-model"


def test_colibri_client_preserves_server_model_id_and_auth(monkeypatch):
    _reset(
        monkeypatch,
        COLIBRI_BASE_URL="http://colibri:8011",
        COLIBRI_API_KEY="secret",
    )
    with model_provider_context("colibri"):
        client = LLMClient(model_name="org/qwen3-coder-30b")

    assert client.provider == "colibri"
    assert client.model_name == "org/qwen3-coder-30b"
    assert client.get_model_identifier("org/qwen3-coder-30b") == "org/qwen3-coder-30b"
    assert client.api_url == "http://colibri:8011/v1"
    assert client.timeout_seconds == 3600
    assert client._request_headers() == {"Authorization": "Bearer secret"}


def test_provider_context_is_scoped_and_concurrency_slot_works(monkeypatch):
    _reset(monkeypatch, DEFAULT_MODEL_PROVIDER="lm_studio", COLIBRI_MAX_CONCURRENCY="1")
    assert get_current_provider() == "lm_studio"
    with model_provider_context("colibri"):
        assert get_current_provider() == "colibri"
    assert get_current_provider() == "lm_studio"

    async def acquire_once():
        async with provider_slot("colibri") as config:
            return config.max_concurrency

    assert asyncio.run(acquire_once()) == 1


def teardown_module():
    for name in (
        "MODEL_API_BASE_URL", "MODEL_API_KEY", "DEFAULT_MODEL_PROVIDER",
        "COLIBRI_BASE_URL", "COLIBRI_API_KEY", "COLIBRI_MODEL_IDENTIFIER",
        "COLIBRI_MAX_CONCURRENCY",
    ):
        os.environ.pop(name, None)
    reset_settings_cache()
