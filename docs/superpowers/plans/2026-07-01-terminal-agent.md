# Terminal Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight terminal agent that starts with `JW` or `jw`, connects to an OpenAI-compatible model, and runs approved tools with confirmation boundaries.

**Architecture:** The implementation adds a small REPL and tool registry beside the existing cinema CLI. Model access, configuration, shell execution, Quark login, and cinema tool wrappers are split into focused modules.

**Tech Stack:** Python standard library plus the existing `httpx` dependency.

---

### Task 1: Tests First

**Files:**
- Create: `tests/test_agent_config.py`
- Create: `tests/test_tools.py`
- Create: `tests/test_install_agent_command.py`

- [x] **Step 1: Write failing tests**

Cover environment overrides, safe config summaries, Quark cookie storage, registry confirmation policy, shell command blocking, and launcher generation.

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`

Expected: FAIL because the agent modules do not exist yet.

### Task 2: Core Modules

**Files:**
- Create: `scripts/agent_config.py`
- Create: `scripts/tools/registry.py`
- Create: `scripts/tools/shell_tools.py`
- Create: `scripts/tools/quark_tools.py`
- Create: `scripts/tools/cinema_tools.py`

- [ ] **Step 1: Implement minimal code for tests**
- [ ] **Step 2: Run unit tests**
- [ ] **Step 3: Refactor while tests stay green**

### Task 3: Model and REPL

**Files:**
- Create: `scripts/llm.py`
- Create: `scripts/agent_core.py`
- Create: `scripts/agent.py`

- [ ] **Step 1: Add OpenAI-compatible chat completions client**
- [ ] **Step 2: Add slash commands and model-required fallback**
- [ ] **Step 3: Add tool-call execution with confirmation hooks**

### Task 4: Launcher Installation

**Files:**
- Create: `scripts/install_agent_command.py`
- Modify: `scripts/setup.py`
- Modify: `config.example.json`
- Modify: `README.md`
- Modify: `README_CN.md`

- [ ] **Step 1: Install `JW` and `jw` launchers into a bin directory**
- [ ] **Step 2: Add `setup.py --install-agent-command`**
- [ ] **Step 3: Document startup and model environment variables**

### Task 5: Verification

**Files:**
- All modified files

- [ ] **Step 1: Run unit tests**

Run: `python3 -m unittest discover -s tests -v`

- [ ] **Step 2: Smoke test local help**

Run: `python3 scripts/agent.py --help`

- [ ] **Step 3: Smoke test installer help or dry run where possible**

Run: `python3 scripts/install_agent_command.py --bin-dir /tmp/cinema-agent-bin-test`
