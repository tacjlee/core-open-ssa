"""
======================================================
`OpenSSA`: SMALL SPECIALIST AGENTS FOR PROBLEM-SOLVING
======================================================

`OpenSSA` is an agentic AI framework for solving complex problems in real-world industry applications.
"""


from importlib.metadata import version, PackageNotFoundError

from .core.agent.dana import DANA

from .core.program_store.program_store import ProgramStore
from .core.programming.hierarchical.plan import HTP
from .core.programming.hierarchical.planner import HTPlanner

from .core.reasoning.ooda.ooda_reasoner import OodaReasoner
from .core.reasoning.simple.simple_reasoner import SimpleReasoner

from .core.resource.file import FileResource

from .core.task.task import Task

from .core.util.lm.config import LMConfig
from .core.util.lm.huggingface import HuggingFaceLM
from .core.util.lm.llama import LlamaLM
from .core.util.lm.openai import OpenAILM

# --- core-open-ssa additions (keep in this marked block for clean upstream merges) ---
# Model-agnostic LLM selection: a generic OpenAI-compatible LLM + a provider registry, so the
# model behind an agent is chosen by config (build_llm) rather than hardcoded imports.
# (Upstream's BaseLM/OpenAILM/LMConfig keep their "LM" names; new code uses "LLM".)
from .core.util.lm.openai_compat import OpenAICompatLLM
from .core.util.lm.registry import build_llm, register_llm, available_llm_providers
# --- end core-open-ssa additions ---


# Vendored as the `core-open-ssa` distribution (import namespace kept as `openssa`).
# Resolve the version from whichever distribution name provides this package, falling
# back to a baked-in string so `import openssa` never fails on version lookup.
__version__: str = '0.24.12.12'
for _dist_name in ('core-open-ssa', 'openssa', 'OpenSSA'):
    try:
        __version__ = version(distribution_name=_dist_name)
        break
    except PackageNotFoundError:
        continue
