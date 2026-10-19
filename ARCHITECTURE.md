# Architecture — core-open-ssa

How this fork is meant to be shaped, and why. `core-open-ssa` is an **enhanced, generic
fork of OpenSSA** — one `openssa` package, improved in place, that stays independent of any
specific LLM, any specific retrieval backend, and any specific application domain.

See [`ORIGIN.md`](./ORIGIN.md) for provenance (upstream commit/version) and the exact edits
to the vendored tree.

---

## 1. Charter

- **One package, `openssa`.** Improvements are folded into the framework directly, not bolted
  on as a second package. The *import namespace* stays `openssa`; the *distribution* is
  `core-open-ssa`.
- **A hard fork, with its own version.** Upstream is effectively dormant, so we own the
  version scheme (e.g. a PEP 440 local version such as `0.24.12.12+dxo.N`) rather than
  mirroring upstream's number on diverged code.
- **Generic first.** The framework must be reusable by any consumer, not just the QG2 / DXO
  work it grew from.

## 2. The governing rule — what may live in core

> Core contains the **framework and backend-free pieces only**. Anything that names a
> specific **model** (Qwen), a specific **service** (dxo-knowledge), or a specific **domain**
> (QG2, estimation workbooks, Excel) does **not** belong in core — not even as an "optional"
> subclass, because the import alone re-couples core to that backend.

Everything model-, service-, or domain-specific is **application code**. It already lives in
the consuming app today (`quality-gate-agent`), and it stays there (or in a separate DXO
package), subclassing core's abstractions.

### The boundary at a glance

```
APP / DXO tier  (quality-gate-agent, or a dxo lib)      CORE  (openssa, generic)
──────────────────────────────────────────────────      ────────────────────────────
Qwen gateway config / profile                            BaseLM  (the LM contract)
dxo-knowledge client + RAG resources                     build_llm()  (provider registry)
QG2 checklist, estimation domain, eval rules             OpenAI-compatible LLM  (generic)
Excel reading (pandas / openpyxl)                        BaseResource  (the resource contract)
   flatten_workbook → text                               TextResource  (text + LM → answer)
EstimationResource / DxoKnowledgeResource / ProjectResource    DANA · HTPlanner · OODA · ProgramStore · Task
```

Core only ever receives **a finished string and an LM**. It never opens a file, never calls
a service, never names a model.

## 3. Model independence

Today the stack runs on Qwen; tomorrow it may not. Core must owe nothing to that choice.

- **The abstraction is already in core.** `openssa/core/util/lm/base.py` defines `BaseLM`;
  `DANA` / `HTPlanner` / the OODA reasoner only ever take an injected `BaseLM`. The framework
  has no model dependency — only the *app wiring* does (today via a hardcoded
  `get_qwen_lm()` in `dana.py` / `qc_agent.py`).
- **Selection by config, not by import.** Add a provider registry + `build_llm()` beside the
  existing `openssa/core/util/lm/` providers. The app calls `build_llm()`, which reads a
  `LLM_PROVIDER` setting and returns the right `BaseLM`. Swapping models becomes a config
  change, not a code change; adding a model is one new adapter + one registration.
- **Generalize the Qwen adapter out of existence.** Today's `qwen_lm.py` (in the app) is just
  `OpenAILM` + "disable thinking tokens" + "don't verify TLS" — both are client/`extra_body`
  knobs, not Qwen logic. Core carries a generic **OpenAI-compatible LLM** (`OpenAICompatLLM`,
  works against vLLM, TGI, Ollama, OpenAI). "Qwen" then reduces to a **config profile** (base
  URL, model name, `extra_body`) registered via `register_llm(...)`, and the word "Qwen"
  disappears from code.
- **Naming:** new code added by this fork uses **`LLM`** (`build_llm`, `register_llm`,
  `OpenAICompatLLM`); inherited upstream symbols keep their names (`BaseLM`, `OpenAILM`,
  `LMConfig`, the `openssa/core/util/lm/` package) so upstream merges stay clean.
- **Expose capabilities, don't hardcode them.** Model-specific facts — context-window size,
  whether `response_format=json_schema` is supported, whether thinking tokens exist — are
  declared on the LM (e.g. `lm.context_window`, `lm.supports_json_schema`) and read by
  callers, never written as literals in planner / resource / app code.

## 4. Backend (retrieval) independence

Grounding/retrieval is as backend-specific as the model is, and is handled the same way.

- **The abstraction is in core.** `openssa/core/resource/base.py` defines `BaseResource`: a
  source the agent can `.answer(question)` against. Its only required members are
  `unique_name`, `name`, and `answer()`. The reasoner calls `present_full_answer()` and never
  knows whether a PDF, a database, a RAG service, or a spreadsheet is behind it.
- **A generic grounding resource belongs in core.** The backend-free half of today's
  `EstimationResource` — *"hold some text, answer questions grounded on it via an injected
  LM"* — becomes `TextResource(BaseResource)` in core. No file I/O, no domain, no service.
- **Domain / service resources stay app-side.** The estimation flavor is a thin subclass
  `EstimationResource(TextResource)` that only supplies *how to produce the text*
  (`qg2/workbook.flatten_workbook`, which uses pandas/openpyxl). `DxoKnowledgeResource` and
  `ProjectResource` stay in the app as direct `BaseResource` implementations, because they
  bind to the dxo-knowledge service (`ingestion.client`) and retrieve dynamically.
- **File reading is not core's job.** Core receives text, not paths. Upstream's own
  `FileResource` (PDF/DOCX via LlamaIndex) is the heavy exception and should sit behind an
  optional extra, not in the mandatory core.

## 5. Dependency policy

- **Lean core.** Only the framework's true needs — `openai`, `httpx`, `pydantic`, `loguru`,
  `tqdm`, `python-dotenv`. Everything else is optional or app-owned.
- **Heavy / backend deps behind extras.** `llama-index` (FileResource), cloud filesystems
  (`adlfs`, `gcsfs`, `s3fs`), `google-api-python-client`, `googlesearch-python` — move to
  extras (`[llama]`, `[aws]`, `[gcs]`, …). Each is supply-chain surface a vendored fork now
  owns patching; keep it out of the default install.
- **Domain deps are the app's.** `pandas` / `openpyxl` (Excel), the dxo-knowledge client, and
  QG2 logic belong to `quality-gate-agent`, never to core.

## 6. Known leaks to fix (current → target)

| Where (file) | Leak | Target |
|---|---|---|
| `qg2/workbook.py` `MAX_TOTAL_CHARS = 55_000` | context budget hardcoded to Qwen's window | derive from `lm.context_window` |
| app `qwen_lm.py` `QWEN_VERIFY_SSL=false` default | TLS verification off by default, silently | warn loudly; secure-by-default once the gateway has a trusted cert |
| `dana.py` / `qc_agent.py` `get_qwen_lm()` | model hardcoded at the wiring point | `build_llm()` + `LLM_PROVIDER` config |
| `eval.py` GPT-4o judge | judge model hardcoded | same `build_llm()` registry (judge is just another provider choice) |
| Qwen `enable_thinking` / `json_schema` | model quirks must not leak past the adapter | keep inside the OpenAI-compatible adapter; surface via capabilities |

## 7. Fork maintenance

- **Track pristine upstream in git.** Keep the untouched upstream import on a
  `vendor/upstream` branch (or a tag per import, e.g. `upstream/0.24.12.12`); do work on
  `main`. Refresh = drop the new upstream onto `vendor/upstream`, then merge into `main` —
  git shows exactly where your changes collide.
- **Minimize edits to vendored files.** New files never conflict on merge; only edits to
  upstream files do. Keep such edits to a clearly-marked block (today: the version lookup and
  the symbol exports in `openssa/__init__.py`).
- **`ORIGIN.md` is the fork changelog** — every file added and every upstream file touched.

## 8. Improvement roadmap (ranked)

1. **Distribute properly.** Push to internal GitLab, tag, and depend via `git+https://…@tag`
   (like `dxo-client`) instead of a machine-specific local wheel path in `requirements.txt`.
2. **Model-agnostic LLM seam.** Add the `build_llm()` registry + a generic OpenAI-compatible
   LM in core; reduce Qwen to a config profile; route the app and the `eval.py` judge through
   it.
3. **Generic resource seam.** Add `TextResource` to core; refactor `EstimationResource` to
   subclass it; leave dxo-knowledge resources app-side.
4. **Lean the deps into extras + add an audit** (`pip-audit`, a lockfile with hashes).
5. **Tests + CI.** Smoke test (`import openssa`; build a `DANA` with a fake LM + fake
   resource; trivial solve) and adapter tests; build + test + audit on push.
6. **Later:** async LM path and response caching, if service load justifies it.

Items 1–3 carry most of the architectural value; they turn "a renamed zip" into "a generic,
reusable SSA core that happens to run on Qwen today."
