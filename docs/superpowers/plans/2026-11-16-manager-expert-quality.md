# Manager, Expert and Quality Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give manager product cards source-backed sales scripts, expose the day-two sales materials as manager cards, make trainee reporting use registered names, and record questions the knowledge base cannot answer.

**Architecture:** Keep content source-driven. `manager-library.js` selects and renders only existing materials; `server.py` records operational data in the existing persistent state stores. The leader governance screen reads the unanswered-question events alongside revisions without changing trainee learning content.

**Tech Stack:** Vanilla JavaScript, Python standard-library HTTP server, Supabase/Cloudflare persistent state abstraction, Python `unittest`.

## Global Constraints

- Do not change the trainee curriculum or its tiles.
- Manager scripts are shown only on non-technical product cards and only from `03 SALES` sources.
- Preserve source wording; render it more clearly rather than inventing facts.
- Store unanswered questions without blocking the assistant response.
- Registered trainee names are authoritative in reporting and duplicate records are merged case-insensitively.

---

### Task 1: Source-backed manager scripts and day-two cards

**Files:**
- Modify: `academy-app/manager-library.js`
- Test: `academy-app/tests/test_library_catalog.py`

- [x] Add failing source-contract assertions for a manager-only `Скрипт` section and the day-two cards.
- [x] Add a source selection helper limited to `03 SALES` and render `Скрипт` after `Ход работы` for non-technical manager product cards.
- [x] Add manager-only cards for the general sales script, price, first-KP case and call review, using existing source paths.
- [x] Run `python3 -m unittest academy-app/tests/test_library_catalog.py`.

### Task 2: Trainee registry reconciliation

**Files:**
- Modify: `academy-app/server.py`
- Test: `academy-app/tests/test_library_catalog.py`

- [x] Add a failing test where a registered trainee name overrides a generated/legacy reporting alias.
- [x] Normalize and merge primary, registry and fallback records by canonical name; exclude blank/generated labels from the visible registry.
- [x] Run the focused registry tests and then the full suite.

### Task 3: Unanswered-question improvement journal

**Files:**
- Modify: `academy-app/server.py`
- Modify: `academy-app/manager-library.js`
- Test: `academy-app/tests/test_library_catalog.py`

- [x] Add a failing test for a deduplicated `knowledge_gap` event when internal retrieval finds no source.
- [x] Record the question, role, name and time through the existing persistent event store without failing the chat request.
- [x] Load and show the resulting entries in the leader governance screen as `Вопросы без ответа в базе`.
- [x] Run focused and full tests.

### Task 4: Display copy audit

**Files:**
- Modify: `academy-app/manager-library.js`
- Test: `academy-app/tests/test_library_catalog.py`

- [x] Scan cards and source rendering for visible `br` artifacts and lowercase display headings.
- [x] Preserve source wording and existing capitalized display headings; source rendering already removes literal `br` artifacts.
- [x] Run the full suite after the display-source audit.

### Task 5: Verification and deployment

**Files:**
- Modify: `docs/superpowers/plans/2026-11-16-manager-expert-quality.md`

- [x] Run `node --check academy-app/manager-library.js`, the Python test suite and `git diff --check`.
- [ ] Inspect the live manager and leader flows after the Render auto-deploy is green.
- [ ] Commit only the intended source, test and plan files and push `main` under the existing user-approved auto-deploy workflow.
