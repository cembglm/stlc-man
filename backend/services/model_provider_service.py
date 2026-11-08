"""Provider-aware configuration for OpenAI-compatible local model servers."""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Dict, Iterator, Optional
from weakref import WeakKeyDictionary

from core.settings import get_settings


SUPPORTED_MODEL_PROVIDERS = ("lm_studio", "colibri")
_provider_context: ContextVar[Optional[str]] = ContextVar(
    "stlc_model_provider", default=None
)
_loop_semaphores: "WeakKeyDictionary[asyncio.AbstractEventLoop, Dict[str, asyncio.Semaphore]]" = WeakKeyDictionary()


@dataclass(frozen=True)
class ModelProviderConfig:
    name: str
    label: str
    base_url: str
    api_key: Optional[str]
    default_model: Optional[str]
    timeout_seconds: int
    max_concurrency: int

    @property
    def api_url(self) -> str:
        base = self.base_url.rstrip("/")
        return base if base.endswith("/v1") else f"{base}/v1"


def normalize_provider(provider: Optional[str]) -> str:
    value = (provider or get_settings().default_model_provider).strip().lower()
    aliases = {"lmstudio": "lm_studio", "lm-studio": "lm_studio"}
    value = aliases.get(value, value)
    if value not in SUPPORTED_MODEL_PROVIDERS:
        raise ValueError(
            f"Unsupported model provider '{value}'. Expected one of: "
            f"{', '.join(SUPPORTED_MODEL_PROVIDERS)}"
        )
    return value


def get_provider_config(provider: Optional[str] = None) -> ModelProviderConfig:
    settings = get_settings()
    name = normalize_provider(provider)
    if name == "colibri":
        return ModelProviderConfig(
            name=name,
            label="Colibri",
            base_url=settings.colibri_base_url,
            api_key=settings.colibri_api_key,
            default_model=settings.colibri_model_identifier,
            timeout_seconds=settings.colibri_timeout_seconds,
            max_concurrency=settings.colibri_max_concurrency,
        )
    return ModelProviderConfig(
        name=name,
        label="LM Studio",
        base_url=settings.lm_studio_base_url,
        api_key=settings.lm_studio_api_key,
        default_model=settings.model_identifier,
        timeout_seconds=settings.lm_studio_timeout_seconds,
        max_concurrency=settings.lm_studio_max_concurrency,
    )


def get_current_provider() -> str:
    return normalize_provider(_provider_context.get())


@contextmanager
def model_provider_context(provider: Optional[str]) -> Iterator[str]:
    normalized = normalize_provider(provider)
    token = _provider_context.set(normalized)
    try:
        yield normalized
    finally:
        _provider_context.reset(token)


def _get_semaphore(config: ModelProviderConfig) -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    semaphores = _loop_semaphores.setdefault(loop, {})
    semaphore = semaphores.get(config.name)
    if semaphore is None:
        semaphore = asyncio.Semaphore(config.max_concurrency)
        semaphores[config.name] = semaphore
    return semaphore


@asynccontextmanager
async def provider_slot(provider: Optional[str] = None):
    config = get_provider_config(provider)
    semaphore = _get_semaphore(config)
    async with semaphore:
        yield config
