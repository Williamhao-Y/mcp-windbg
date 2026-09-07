# mcp-windbg

A [Model Context Protocol](https://modelcontextprotocol.io/) server that lets AI models
analyze Windows crash dumps and drive live or remote debugging through WinDbg/CDB. It is a
Python wrapper around `cdb.exe`: the model calls MCP tools, the server runs the matching
debugger commands and returns the text output. Windows-only (needs CDB). The single entry
point is `mcp-windbg`, which speaks MCP over stdio or streamable-http.

## Build / test / run

Python 3.10+ with the `uv` package manager. CDB must be installed for the live tests (WinDbg
from the Microsoft Store, or the Windows SDK).

```powershell
uv sync --dev                                                       # install incl. dev deps
uv run pytest src/mcp_windbg/tests/ -v                             # full test suite
uv run pytest src/mcp_windbg/tests/ -v -m "not live"              # hermetic subset (no CDB)
uv run python -m mcp_windbg --verbose                              # run the server (stdio)
uv run python -m mcp_windbg --transport streamable-http --port 8000   # HTTP transport
```

### Coverage

The code under test runs in **two** processes, and both must be measured or the number lies:

- the hosted server subprocess, where tool dispatch executes. Set `MCP_WINDBG_COVERAGE` so the
  harness launches it under `coverage run --parallel-mode`.
- the pytest process itself, where the hermetic unit tests (`tests/test_*.py`) run. This needs
  `coverage run -m pytest`, not plain `pytest`. Miss this and every unit test reads as dead
  code: that is how `kd_session.py` once reported 34% while fully tested.

Both write parallel-mode data files that `coverage combine` merges:

```powershell
uv run coverage erase
$env:MCP_WINDBG_COVERAGE = "1"
uv run coverage run -m pytest src/mcp_windbg/tests/     # measures pytest AND the server
$env:MCP_WINDBG_COVERAGE = $null
uv run coverage combine                 # merge the per-process .coverage.* files
uv run coverage report                  # or: uv run coverage html  ->  htmlcov/
```

CI runs exactly this and gates on `--fail-under=88`. To reproduce CI's number, leave
`MCP_WINDBG_KERNEL_CONNECTION` unset so the kernel scenarios skip as they do there. Run it with
the variable set for the honest local number, which covers `kd_session.py` against a real
target rather than a fake process.

### Test suite

The suite is a declarative end-to-end harness: each `tests/scenarios/*.yaml` file is run
against a real `python -m mcp_windbg` server hosted over stdio and driven by a real MCP client
(only the LLM is faked, by the scripted tool calls). Scenarios that need a debugger carry the
`live` (and `remote` / `kernel`) marker and `pytest.skip` cleanly when `cdb.exe` or the Git LFS
dump is absent, so `-m "not live"` always runs and stays green off-Windows. See
`src/mcp_windbg/tests/e2e/README.md` for the scenario format. Test dumps live in
`src/mcp_windbg/tests/dumps/` via Git LFS (`git lfs pull`).

**Kernel scenarios.** `kernel_session.yaml` drives a real kernel target through `kd.exe`. CI has
no target machine, so it skips there; locally, point it at a debuggable VM or box and it runs:

```powershell
$env:MCP_WINDBG_KERNEL_CONNECTION = "net:port=50005,key=1.2.3.4"   # the -k connection string
uv run pytest src/mcp_windbg/tests/ -m kernel -v
```

Kernel code paths that CI cannot reach are held up by the hermetic fake-`kd.exe` tests in
`tests/test_kd_session.py`. Treat those as the CI floor, not as proof the feature works: before
shipping a kernel change, run the `kernel` marker against a real target.

## Layout

```
src/mcp_windbg/
  __init__.py        main(): CLI argument parsing, picks the transport
  __main__.py        module entry point
  server.py          MCP server: tool param models + list_tools + call_tool dispatch
  cdb_session.py     CDBSession: spawns cdb.exe, sends commands, reads output
  filter_script.py   --filter-script loader and tool content hooks
  prompts/           prompt templates (dump-triage.prompt.md)
  tests/             e2e harness: e2e/ (runner + harness), scenarios/*.yaml, dumps/ (Git LFS)
scripts/             check-version-consistency.ps1, validate-server-schema.py, Format-Docs.ps1
examples/            small C++ programs that crash, for generating test dumps
docs/                MkDocs user guide (Material), built locally when needed
.github/workflows/   ci.yml -> build-and-test.yml (tests), dependency-canary.yml (scheduled)
pyproject.toml       project + dependency config         server.json   MCP registry manifest
```

## Conventions

Topic-scoped conventions live in `.claude/rules/` and load automatically when you read a
matching file:

- `markdown.md` - Markdown typography for every `*.md`: plain hyphens (no em/en dashes), no
  emojis. Run `pwsh scripts/Format-Docs.ps1`. (`**/*.md`)
- `documentation.md` - authoring style for the `docs/` user guide (scenario-first, link to
  the reference, sentence-case). (`docs/**`)

Tool and CLI facts come from `src/mcp_windbg/server.py` (tool schemas) and
`src/mcp_windbg/__init__.py` (command-line options). Keep `docs/reference/` in sync with them.

**The plugin has two names, and they do different jobs.** The marketplace entry in
`.claude-plugin/marketplace.json` is named `mcp-windbg-uvx` - that is the install identity, so
the command is `/plugin install mcp-windbg-uvx@mcp-windbg`, and it is what the plugin cache
directory is named after. The `name` in `plugins/mcp-windbg/.claude-plugin/plugin.json` stays
`mcp-windbg`, and that is what skills and MCP tools are scoped by: `/mcp-windbg:analyze-dump` and
`mcp__plugin_mcp-windbg_mcp-windbg__<tool>`, whatever the entry is called.

That split is deliberate. It lets a second entry ship the same plugin a different way -
`mcp-windbg-native` for a bundled binary, `mcp-windbg-pipx` for `pipx run` - while every variant
keeps identical skill names, identical tool names, and one set of documentation. Change
`plugin.json`'s name and you rename every skill and every tool with it.

## Fork workflow

This fork uses `main` as its working branch. Pull requests and pushes to `main` run the reusable
test workflow through `.github/workflows/ci.yml`; the dependency canary remains available on its
schedule and through manual dispatch.

There is no automated release, package publication, MCP Registry publication, or GitHub Pages
deployment in this fork. Upstream releases are synchronized manually. When version-bearing files
are changed by hand, run `scripts/check-version-consistency.ps1` to compare `pyproject.toml`,
`server.json`, the Claude plugin manifests, the plugin's `uvx` pin, and the top CHANGELOG entry.

## Docs

```powershell
pip install -r requirements-docs.txt
python -m mkdocs serve                  # live preview at http://127.0.0.1:8000
python -m mkdocs build --strict         # what Pages builds; links must resolve
pwsh scripts/Format-Docs.ps1            # markdown typography
```
