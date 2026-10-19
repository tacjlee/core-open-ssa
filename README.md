# core-open-ssa

A **vendored, locally-buildable** build of [OpenSSA](https://github.com/Aitomatic/OpenSSA)
(*Small Specialist Agents for Industrial AI*) — the neurosymbolic agent framework (DANA +
hierarchical task planning + OODA reasoning) behind the `quality-gate-agent` / FinanceBench
work.

It replaces the mutable `…/archive/examples/FinanceBench.zip` branch dependency with a pinned
wheel we build ourselves, packaged the same way as `dxo-client`. The **import namespace stays
`openssa`**, so existing code (`from openssa import DANA`) works unchanged — only the
distribution name is `core-open-ssa`.

See [`ORIGIN.md`](./ORIGIN.md) for the exact upstream commit/version and the (minimal) changes.

## Build

```bash
bash build.sh
# → dist/core_open_ssa-0.24.12.12-py3-none-any.whl
```

## Install

```bash
# Local wheel
pip install dist/core_open_ssa-*.whl

# From another project's requirements.txt (local path)
core-open-ssa @ file:///D:/PROJECTS/core-open-ssa/dist/core_open_ssa-0.24.12.12-py3-none-any.whl

# With extras (same as upstream)
pip install "dist/core_open_ssa-*.whl[contrib]"      # Streamlit contrib app deps
pip install "dist/core_open_ssa-*.whl[langchain]"    # langchainhub + faiss-cpu
```

## Usage

Identical to upstream OpenSSA:

```python
from openssa import DANA, ProgramStore, HTP, HTPlanner, FileResource, LMConfig, OpenAILM

print(__import__("openssa").__version__)   # 0.24.12.12
```

## Layout

```
core-open-ssa/
├── openssa/          # the vendored framework (core + contrib; upstream deprecated/ removed)
├── pyproject.toml    # setuptools build; distribution name = core-open-ssa
├── build.sh          # venv → python -m build → dist/*.whl   (dxo-client style)
├── ORIGIN.md         # upstream provenance + how to refresh
├── LICENSE.md        # Apache-2.0 (OpenSSA)
└── README.md
```

## License

Apache-2.0 — see [`LICENSE.md`](./LICENSE.md). OpenSSA is © Aitomatic, Inc.
