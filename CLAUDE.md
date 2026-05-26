---
description: Project configuration and memory bank system for Claude Code
alwaysApply: true
---

# Project Configuration

This file contains project-specific intelligence and configuration for Claude Code sessions.

## Memory Bank System

This project uses a Memory Bank system to maintain context across sessions. All memory files are stored in `.claude/memory-bank/` and should be read at the start of every conversation.

### Core Memory Files (Read these in order):
1. **memory-rules.md** - System documentation
2. **projectbrief.md** - Foundation document
3. **productContext.md** - Product vision
4. **systemPatterns.md** - Architecture patterns
5. **techContext.md** - Technical setup
6. **activeContext.md** - Current work focus
7. **progress.md** - Status tracking

## Instructions for Claude

### On Every Session Start:
1. **Read all core memory bank files** in the order listed above
2. Verify understanding of current context
3. Check activeContext.md for immediate priorities
4. Review progress.md to understand what's complete and what's pending
5. **Double-check `strings.json` and `translations/en.json` are in sync** when touching config flow UI strings

### When User Says "update memory bank":
1. **Review ALL memory bank files** (mandatory - don't skip any)
2. Update files that need changes based on recent work
3. Pay special attention to activeContext.md and progress.md
4. Document any new patterns discovered
5. Update project intelligence in this file if needed

### Planning Mode (via /plan command):
1. Read Memory Bank (automatic)
2. Verify context completeness
3. Ask 4-6 clarifying questions based on findings
4. Draft comprehensive plan
5. Get user approval
6. Implement systematically

## Repository Layout

```
emergency_alerts/
├── custom_components/emergency_alerts/   # the integration
│   ├── __init__.py, binary_sensor.py, select.py, sensor.py, switch.py
│   ├── config_flow.py, const.py, helpers.py, diagnostics.py
│   ├── manifest.json, strings.json, services.yaml, hacs.json
│   ├── translations/en.json              # must stay in sync with strings.json
│   ├── core/                             # trigger evaluator, action executor
│   ├── blueprints/script/                # blueprint templates
│   └── tests/
│       ├── conftest.py                   # hass fixtures, translation-error autocheck
│       ├── test_*.py                     # legacy flat suite (binary_sensor, config_flow, switch, sensor, init, dependencies)
│       ├── unit/                         # pure-logic tests (action parsing, state machine, trigger evaluation)
│       └── integration/                  # hass-fixture tests (api contracts, state sync, e2e scenarios, template rerender)
├── e2e-tests/                            # Playwright + TS suite — NOT run in CI
├── scripts/                              # all dev tooling (relocated in PR #15)
│   ├── run_tests.sh, lint.sh, fix-format.sh, docker-test.sh
│   ├── validate_integration.py, validate_translations.py
│   ├── update-card.sh, bypass-onboarding.sh, create-api-token.js, run-e2e.sh
├── dev_tools/                            # local-dev.sh + HA config for Docker dev
├── docs/                                 # TESTING.md, plans/, analysis docs
├── .github/workflows/test.yml            # CI: HACS + hassfest + backend-tests + lint
├── docker-compose.yml, Dockerfile.lint, Dockerfile.test
├── pytest.ini, pyproject.toml
└── CHANGELOG.md, README.md
```

## Local Verification

```bash
# Full backend suite (used by CI)
python -m pytest custom_components/emergency_alerts/tests/ -v

# Translation sync (also enforced by CI)
python scripts/validate_translations.py

# Integration structure
python scripts/validate_integration.py

# Convenience wrappers
./scripts/run_tests.sh                 # full suite
./scripts/run_tests.sh --backend-only  # pytest only
./scripts/lint.sh                      # black + isort + flake8 + mypy
./scripts/fix-format.sh                # auto-fix black + isort
```

## CI Gotchas

- `.github/workflows/test.yml` has 4 jobs: HACS Validation, Hassfest, Backend Tests (Python 3.13 only), Lint and Format Check.
- **Lint is non-blocking**: black/isort/flake8/mypy all run with `continue-on-error: true`. A green lint job does not mean the code is actually clean — run `./scripts/lint.sh` locally to see real status.
- **No E2E in CI**: `e2e-tests/` Playwright suite is not invoked by any workflow.
- **No branch protection on `main`**: no required status checks; green CI is not actually enforced before merge.
- **Codecov upload fails silently** (`fail_ci_if_error: false`); coverage data is not actually being collected upstream.
- Schedule: daily cron at 00:00 UTC catches HA version drift.

## Project Intelligence

This section grows as patterns and preferences are discovered during work on this project.

### Project-Specific Patterns
- **Translation sync is enforced.** `conftest.py` has an autouse fixture that fails any test if "Failed to format translation" appears in logs. Always edit `strings.json` and `translations/en.json` together.
- **Entity IDs are pinned in code.** `binary_sensor.py`, `select.py`, `sensor.py` each set `self.entity_id = ...` explicitly to avoid HA's slugify-combining device+entity names into doubled IDs (see PR #13). Don't remove these without understanding the bug they fix.
- **`on_triggered_script` is resolved**, not raw — `_resolve_on_triggered()` in `binary_sensor.py` synthesizes a `script.turn_on` call from the UI's script field. Goes into `data.entity_id` (not `target`) because `_execute_action` only forwards `data`.
- **Alert IDs are slugified** via `_slugify_alert_id()` in `config_flow.py` to handle names like `Smoke/CO Detector`.
- **Template triggers use `async_track_template_result`**, not `async_track_state_change_event([])` — the latter subscribes to nothing and never re-evaluates (PR #14).

### Known Gotchas
- **Lint job is theater** (see CI Gotchas above).
- **HA Service Worker caching** is aggressive — card resources must use `?v=X.X.X` cache-busters; incognito works best for testing.
- **EntitySelector defaults**: never provide a default value for an EntitySelector field; an empty default triggers "Entity not found" validation errors.
- **Device identifiers are immutable** in HA's device registry — changing them is a breaking change requiring re-add (see PR #6 history).

### Effective Approaches
- **Regression tests with bug references** — `tests/integration/test_template_trigger_rerender.py` is the model: dedicated file, docstring naming the bug, assertion message that says "Bug X regressed." Recent fix PRs that skip this step (#12, #13) leave gaps.
- **Single-page config flows** beat multi-step wizards for this domain (Adaptive Lighting pattern).
- **Memory bank first**: read `.claude/memory-bank/*.md` at session start; project state changes faster than code comments capture.

---

## Notes

- Memory Bank files are in `.claude/memory-bank/`
- Update frequently to maintain accuracy
- The Memory Bank is the primary context system for this project
