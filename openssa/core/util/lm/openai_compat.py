"""
==========================================
GENERIC OpenAI-COMPATIBLE LLM
==========================================

`OpenAICompatLLM` talks to ANY OpenAI-compatible chat-completions endpoint — OpenAI itself,
vLLM, TGI, Ollama, LM Studio, or a gateway in front of them. It is vendor- and model-neutral:
nothing here names a specific model. Endpoint-specific behavior is supplied through config /
constructor overrides, not through subclasses:

  * `extra_body`     — always-on request body params passed straight to the API (e.g. a
                       chat-template flag like `{"chat_template_kwargs": {"enable_thinking": false}}`).
  * `verify_ssl`     — TLS verification (default ON; turn OFF only for a self-signed LAN host).
  * timeouts/retries — bounded so a half-open socket fails fast instead of parking a worker.
  * `default_headers`— for gateways that need an auth/routing header.

A concrete deployment (say a Qwen/vLLM profile with thinking disabled and TLS off) is created
by passing those values — typically registered as a provider via `openssa.register_llm(...)`
in application code, so the model name stays out of core.

(Subclasses the upstream `OpenAILM`; the "LM" in that inherited name is upstream's — all
new code added by this fork uses "LLM".)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx
from openai import OpenAI

from .config import LMConfig
from .openai import OpenAILM

if TYPE_CHECKING:
    from .base import LMChatHist


def _env(*names: str, default: str | None = None) -> str | None:
    """First set environment variable among `names`, else `default`."""
    for n in names:
        v = os.environ.get(n)
        if v is not None:
            return v
    return default


def _as_bool(v: str | None, default: bool = False) -> bool:
    return default if v is None else v.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class OpenAICompatLLM(OpenAILM):
    """LLM for any OpenAI-compatible endpoint; model/vendor specifics come from config."""

    # All new fields are keyword-only so they don't disturb the inherited
    # (model, api_base, api_key) positional order from BaseLM/OpenAILM.
    extra_body: dict = field(default_factory=dict, kw_only=True)
    verify_ssl: bool = field(default=True, kw_only=True)
    connect_timeout: float = field(default=10.0, kw_only=True)
    read_timeout: float = field(default=300.0, kw_only=True)
    write_timeout: float = field(default=30.0, kw_only=True)
    pool_timeout: float = field(default=10.0, kw_only=True)
    max_retries: int = field(default=2, kw_only=True)
    default_headers: dict | None = field(default=None, kw_only=True)

    def __post_init__(self):
        # Build the OpenAI client ourselves (do NOT call OpenAILM.__post_init__, which makes a
        # plain client) so timeouts, retries, TLS and headers are all applied.
        timeout = httpx.Timeout(connect=self.connect_timeout, read=self.read_timeout,
                                write=self.write_timeout, pool=self.pool_timeout)
        self.client = OpenAI(
            api_key=self.api_key or "EMPTY",  # some gateways (vLLM) ignore it, but the SDK needs non-empty
            base_url=self.api_base,
            timeout=timeout,
            max_retries=self.max_retries,
            default_headers=self.default_headers,
            http_client=httpx.Client(verify=self.verify_ssl, timeout=timeout),
        )

    def call(self, messages: LMChatHist, **kwargs):
        # Merge (not clobber): a caller-supplied extra_body still wins on its own keys.
        merged = {**self.extra_body, **kwargs.pop("extra_body", {})}
        if merged:
            kwargs["extra_body"] = merged
        return super().call(messages, **kwargs)

    @classmethod
    def from_defaults(cls, **overrides) -> OpenAICompatLLM:
        """Build from environment, with any keyword `overrides` winning over env values.

        Env (all optional; falls back to OpenAI settings so an unconfigured instance still
        targets OpenAI):
            LLM_API_BASE / OPENAI_API_URL   endpoint base URL
            LLM_MODEL                        model name
            LLM_API_KEY / OPENAI_API_KEY     API key (default "EMPTY")
            LLM_EXTRA_BODY                   JSON object of always-on body params
            LLM_VERIFY_SSL                   "true"/"false" (default true)
            LLM_{CONNECT,READ,WRITE,POOL}_TIMEOUT, LLM_MAX_RETRIES
        """
        raw_extra = _env("LLM_EXTRA_BODY")
        try:
            extra_body = json.loads(raw_extra) if raw_extra else {}
        except json.JSONDecodeError:
            extra_body = {}

        cfg: dict = dict(
            model=_env("LLM_MODEL", default=LMConfig.OPENAI_DEFAULT_MODEL),
            api_base=_env("LLM_API_BASE", "OPENAI_API_URL", default=LMConfig.OPENAI_API_URL),
            api_key=_env("LLM_API_KEY", "OPENAI_API_KEY", default="EMPTY"),
            extra_body=extra_body,
            verify_ssl=_as_bool(_env("LLM_VERIFY_SSL"), default=True),
            connect_timeout=float(_env("LLM_CONNECT_TIMEOUT", default="10")),
            read_timeout=float(_env("LLM_READ_TIMEOUT", default="300")),
            write_timeout=float(_env("LLM_WRITE_TIMEOUT", default="30")),
            pool_timeout=float(_env("LLM_POOL_TIMEOUT", default="10")),
            max_retries=int(_env("LLM_MAX_RETRIES", default="2")),
        )
        cfg.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**cfg)
