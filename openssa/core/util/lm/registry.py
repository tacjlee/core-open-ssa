"""
========================
LLM PROVIDER REGISTRY
========================

`build_llm()` selects a language model by **configuration**, not by import — so switching the
model behind an agent is a config change, and adding a model is one `register_llm(...)` call.

Core registers only vendor-neutral providers:
  * ``"openai"``         — the stock `OpenAILM` (OpenAI defaults from `LMConfig`).
  * ``"openai_compat"``  — the generic `OpenAICompatLLM` (any OpenAI-compatible endpoint).

Application- or vendor-specific profiles (e.g. a Qwen/vLLM profile with thinking disabled and
TLS verification off) are NOT defined here — the app registers them so no model name leaks
into core::

    from openssa import register_llm, OpenAICompatLLM
    register_llm("qwen", lambda **kw: OpenAICompatLLM.from_defaults(
        api_base=os.environ["QWEN_API_BASE"], model=os.environ["QWEN_MODEL"],
        api_key=os.environ.get("QWEN_API_KEY", "EMPTY"),
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        verify_ssl=False, **kw))
    # then, anywhere:  llm = build_llm("qwen")   # or set LLM_PROVIDER=qwen and call build_llm()

(The inherited `OpenAILM`/`BaseLM`/`LMConfig` keep their upstream "LM" names; all new code
added by this fork uses "LLM".)
"""
from __future__ import annotations

import os
from collections.abc import Callable

from .base import BaseLM
from .config import LMConfig
from .openai_compat import OpenAICompatLLM

# A provider factory reads its own config/overrides and returns a ready LLM (a BaseLM).
LLMFactory = Callable[..., BaseLM]

_REGISTRY: dict[str, LLMFactory] = {}

# Used when neither an explicit provider nor the LLM_PROVIDER env var is given.
DEFAULT_PROVIDER: str = "openai"


def register_llm(name: str, factory: LLMFactory, *, overwrite: bool = False) -> None:
    """Register `factory` under provider `name` (case-insensitive)."""
    key = (name or "").strip().lower()
    if not key:
        raise ValueError("LLM provider name must be non-empty")
    if key in _REGISTRY and not overwrite:
        raise ValueError(f"LLM provider {key!r} already registered (pass overwrite=True to replace)")
    _REGISTRY[key] = factory


def available_llm_providers() -> list[str]:
    """Names of all registered providers."""
    return sorted(_REGISTRY)


def build_llm(provider: str | None = None, **overrides) -> BaseLM:
    """Build an LLM by provider name (falls back to `LLM_PROVIDER` env, then `DEFAULT_PROVIDER`).

    Extra keyword `overrides` are forwarded to the provider factory (e.g. `model=...`,
    `api_base=...`).
    """
    name = (provider or os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    try:
        factory = _REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"unknown LLM provider {name!r}; registered providers: {available_llm_providers()}"
        ) from None
    return factory(**overrides)


# --- built-in, vendor-neutral providers --------------------------------------------

def _openai_factory(**overrides) -> BaseLM:
    # Import here so merely importing the registry doesn't force the OpenAILM import chain.
    from .openai import OpenAILM
    cfg = dict(model=LMConfig.OPENAI_DEFAULT_MODEL,
               api_key=LMConfig.OPENAI_API_KEY,
               api_base=LMConfig.OPENAI_API_URL)
    cfg.update({k: v for k, v in overrides.items()
                if k in ("model", "api_key", "api_base") and v is not None})
    return OpenAILM(**cfg)


def _openai_compat_factory(**overrides) -> BaseLM:
    return OpenAICompatLLM.from_defaults(**overrides)


register_llm("openai", _openai_factory)
register_llm("openai_compat", _openai_compat_factory)
