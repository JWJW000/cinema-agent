# Quark QR Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add QR-first Quark login to the JW terminal agent.

**Architecture:** Add `scripts/quark_auth/` as the only auth orchestration boundary. Keep old browser/Cookie login as fallback and keep downstream Quark code reading `config.json`.

**Tech Stack:** Python stdlib, optional `quarkpan`, existing unittest suite.

---

### Task 1: Auth Module Tests

**Files:**
- Create: `tests/test_quark_auth.py`
- Create: `scripts/quark_auth/__init__.py`
- Create: `scripts/quark_auth/providers.py`
- Create: `scripts/quark_auth/storage.py`
- Create: `scripts/quark_auth/manager.py`

- [ ] Write tests for QR provider success, unavailable provider, manager fallback, and redacted status.
- [ ] Run `python3 -m unittest tests.test_quark_auth -v` and confirm failures are due to missing module/code.
- [ ] Implement minimal auth module code.
- [ ] Re-run `python3 -m unittest tests.test_quark_auth -v`.

### Task 2: CLI Integration

**Files:**
- Modify: `scripts/agent.py`
- Modify: `scripts/tools/quark_tools.py`
- Modify: `tests/test_agent_entry.py`

- [ ] Write/update tests for `/login quark` summary behavior.
- [ ] Run targeted tests and confirm the new expectation fails.
- [ ] Replace direct `login_quark_with_browser()` usage with `QuarkAuthManager`.
- [ ] Re-run targeted tests.

### Task 3: Docs and Dependency

**Files:**
- Modify: `requirements.txt`
- Modify: `README.md`
- Modify: `README_CN.md`
- Modify: `config.example.json`

- [ ] Add `quarkpan` and `qrcode` as dependencies for QR terminal display.
- [ ] Update login docs to describe QR-first and fallback behavior.
- [ ] Run full unit tests and Python compile check.
