# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

pico is a local terminal coding agent written in Python (3.10+). It connects to a model provider (OpenAI-compatible or Anthropic-compatible API), reads code, runs shell commands, edits files, and persists memory — all inside a local repo. It has a Textual TUI, a plain REPL, and a one-shot mode, all backed by the same synchronous runtime.

## Commands

```bash
# Install editable with dev deps
pip install -e ".[dev]"

# Run the agent (Textual TUI if terminal, else REPL)
uv run pico
pico                           # if installed

# Plain REPL
pico --repl

# One-shot task
pico "找出测试失败的根因"

# Run tests
pytest tests/ -q

# Run a single test file
pytest tests/test_pico.py -q

# Run a specific test
pytest tests/test_pico.py::test_agent_runs_tool_then_final -q

# Lint
ruff check pico/

# Live smoke tests (requires a real provider key)
PICO_LIVE_SMOKE=1 pytest tests/test_release_smoke.py -q
```

No build step — it's a pure Python package with setuptools. Entry point is `pico.cli:main`.

## Architecture

### Startup flow

`main()` → `build_arg_parser()` → `build_agent()` assembles a `Pico` instance → `interaction_mode()` decides TUI/REPL/one-shot → enters the chosen mode.

`build_agent()` is the assembly point: it resolves provider config, creates the model client, builds a `WorkspaceContext` snapshot, and wires everything into `Pico`.

### Core object graph

**`Pico` (core/runtime.py)** is the god object — it owns ALL state through composition:
- `model_client` — OpenAICompatibleModelClient or AnthropicCompatibleModelClient
- `workspace` — WorkspaceContext (git snapshot, project docs)
- `session` — dict with history, memory, runtime_mode, checkpoints
- `engine` — Engine (the turn control loop)
- `memory` — LayeredMemory (working memory: files, notes, file summaries)
- `tools` — dict of RegisteredTool instances from registry.py
- `plan_mode` — PlanModeController
- `worker_manager` — WorkerManager (subagents)
- `todo_ledger` — TodoLedger
- `compact_manager` — CompactManager
- `context_manager` — ContextManager (prompt assembly)
- `session_event_bus` — SessionEventBus (JSONL event log)
- `run_store` — RunStore (trace + report persistence under `.pico/runs/`)
- `permission_checker` — PermissionChecker
- `sandbox_runner` — SandboxRunner

**`Engine` (core/engine.py)** is the turn control loop:
1. `_build_prompt_and_metadata()` — assemble the full prompt via ContextManager
2. `complete_model()` — call the provider
3. `parse()` — extract `<tool>`, `<final>`, or retry from model output
4. If tool: `execute_tool_payload()` → validate → approve → run → record → loop
5. If final: record, promote durable memory, maintain memory, emit traces, yield final

### Provider protocol

`providers/clients.py` uses **only stdlib `urllib`** — no requests/httpx dependency. Two clients:
- `OpenAICompatibleModelClient` → POST to `/v1/responses`, handles both JSON and SSE responses, supports prompt cache
- `AnthropicCompatibleModelClient` → POST to `/v1/messages`, uses `x-api-key` header

Provider config is resolved with this priority: CLI args > env vars > `.pico.toml` (project) > `~/.config/pico/config.toml` (global) > code defaults. The key insight: `provider` name (e.g. "deepseek") selects which TOML section/env vars to use; `protocol` ("openai" or "anthropic") selects which HTTP client class.

### Prompt structure

ContextManager assembles the prompt from fixed sections in order:
1. **prefix** — system rules, tool definitions, workspace snapshot
2. **memory** — working memory (task summary, recent files, notes, file summaries)
3. **skills** — discovered skill prompts
4. **relevant_memory** — top-3 retrieval candidates from durable memory
5. **history** — recent turn transcript (formatted by TurnHistoryBuilder)
6. **current_request** — the user's message (never truncated)

Each section has a budget. When total exceeds ~60k chars, sections are reduced in order: relevant_memory → skills → history → memory → prefix. The current request is never cut.

### Tool system

Tools are explicitly registered in `tools/registry.py` (`BASE_TOOL_SPECS` → `build_tool_registry()`). Each tool has: name, schema dict, risky flag, description, and a `runner` partial. Tool profiles (default/plan/readonly) control which tools are available in which mode. PermissionChecker enforces `prior_read_required` for write/patch tools.

### Memory system (features/memory.py)

Three layers:
- **Working memory** — per-session: task summary, recent files (max 8), episodic notes (max 12), file summaries (max 6). Lives in `session["memory"]["working"]`.
- **Daily log** — `/remember` writes to `.pico/memory/logs/YYYY/MM/YYYY-MM-DD.md`
- **Durable topics** — `/dream` consolidates daily logs into `.pico/memory/topics/*.md`, indexed by `.pico/memory/MEMORY.md`

Auto-dream runs in a background thread after N sessions (default 5) with a minimum interval (default 24h).

### Slash commands

Defined in `commands/slash.py`. Handled in `cli.py:handle_repl_command()` — a flat if/elif chain (not a dispatch table). Skills use `/skill <name>` and trigger `skills_runtime.invoke_skill()`.

### Key design choices

- **Synchronous throughout** — no asyncio. Model calls are blocking `urllib` requests.
- **No external HTTP deps** — stdlib only for provider communication.
- **XML tool calling** — model outputs `<tool>{"name":"...","args":{...}}</tool>` or `<tool name="write_file" path="..."><content>...</content></tool>` for multi-line. Final answers use `<final>...</final>`.
- **Pico's `path()` method** anchors all file access to workspace root — this is the single security boundary for file operations.
- **`ScriptedModelClient`** in `pico/testing.py` is the test harness: feed it a list of output strings, it replays them. Most tests use this instead of mocking HTTP.

## Tests

Tests live in `tests/` and use pytest. The test pattern:
- `build_agent(tmp_path, [outputs])` creates a Pico with ScriptedModelClient
- Each string in the list is one model response (tool or final)
- Assert on `agent.session["history"]`, `agent.session["memory"]`, or the returned answer

Key test categories:
- `test_pico.py` — core agent end-to-end behavior
- `test_engine_acceptance.py` — engine loop correctness
- `test_memory.py` — working/durable memory, dream consolidation
- `test_context_manager.py` — prompt budget and reduction
- `test_v3_runtime.py` — runtime coordination behavior
- `test_runtime_evidence_acceptance.py` — trace/report evidence
- `test_release_smoke.py` — live provider smoke (requires key)
- `test_business_scenario_dogfood.py` — real-world scenario tests
- Acceptance tests (`test_*_acceptance.py`) — behavioral contracts
