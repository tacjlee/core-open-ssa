# Provenance — core-open-ssa

`core-open-ssa` is a **vendored, locally-buildable repackaging of OpenSSA**. It exists to
replace a fragile, mutable dependency:

```
# before (mutable branch zip — silently changes when the branch is pushed to)
OpenSSA[contrib] @ https://GitHub.com/Aitomatic/OpenSSA/archive/examples/FinanceBench.zip
```

with a pinned, controllable wheel we build ourselves — exactly the way `dxo-client` is built.

## Upstream snapshot

| | |
|---|---|
| Upstream repo | https://github.com/Aitomatic/OpenSSA |
| Branch | `main` |
| Commit | `3652ac85c6e66cb8d03b59222101588e4d0c4217` |
| Upstream version | `0.24.12.12` |
| Vendored on | 2026-10-19 |

At this commit, `main`, the latest release tag `0.24.12.12`, and the `examples/FinanceBench`
branch (the old zip URL) all resolve to **the same source** — verified by a full tree diff
against the previously-installed `openssa 0.24.12.12` build (zero content differences,
line-endings aside).

## What changed vs. upstream

The import namespace is **unchanged** (`import openssa` still works). Only two things differ:

1. **Distribution renamed** `openssa` → `core-open-ssa` (the *package name* on PyPI/wheel;
   the *import name* stays `openssa`, like `dxo-client` imports as `dxo_client`).
2. **Build backend** poetry-core → setuptools, so it builds the same way as `dxo-client`
   (`build.sh` → `python -m build` → `dist/*.whl`). Dependencies and extras (`contrib`,
   `langchain`) are carried over verbatim from the upstream `0.24.12.12` metadata.
3. **`openssa/__init__.py` version lookup** made robust: the original fell back to reading a
   poetry `pyproject.toml` relative to the install dir, which crashes once the distribution is
   renamed. It now resolves the version from whichever distribution name provides the package
   and otherwise uses a baked-in string, so `import openssa` never fails on version lookup.

4. **Dropped the upstream `openssa/deprecated/` package** (old SSM/SSA/OODA-RAG demos) as
   unused — `core` has zero references to it; only the `contrib` streamlit demo imported it.
   `contrib/` is kept (its `[contrib]` extra supplies the Streamlit deps), but its
   `streamlit_ssa_prob_solver` demo is non-importable without `deprecated` — harmless here,
   since this project never imports `openssa.contrib`.

No other edits to the `openssa/` source — the agent (DANA / HTPlanner / OODA / resources /
LM adapters) is byte-for-byte upstream.

## Refreshing to a newer upstream

1. `git clone --depth 1 https://github.com/Aitomatic/OpenSSA.git` (or checkout a tag).
2. Replace the `openssa/` directory here with the upstream one.
3. Re-apply the `openssa/__init__.py` version-lookup patch (above).
4. Sync `dependencies` / optional-dependencies in `pyproject.toml` from the upstream metadata.
5. Bump `version` in `pyproject.toml`, update this file's snapshot table, rebuild.
