# Contributing

Thanks for taking a look. This is a single-maintainer hobby project — issues, PRs, and questions are all welcome, just expect responses on a hobbyist timeline.

## Reporting issues

File issues at [github.com/issmirnov/emergency_alerts/issues](https://github.com/issmirnov/emergency_alerts/issues). Helpful detail:

- Home Assistant version (Settings → About).
- Integration version (visible on the integration card).
- The alert config that triggers the bug (sanitized).
- Relevant Home Assistant log lines (`homeassistant.log` or Settings → System → Logs).

## Development environment

The fastest loop is the included Docker setup. It launches a clean Home Assistant on port 8123 with the integration symlinked, dev-user auto-created, and trusted-network auth bypassed so you can iterate without re-logging in.

```bash
./dev_tools/local-dev.sh start     # boot HA on http://localhost:8123 (user: dev / dev)
./dev_tools/local-dev.sh logs      # tail HA logs
./dev_tools/local-dev.sh restart   # pick up code changes
./dev_tools/local-dev.sh nuke      # wipe HA state and start fresh
./dev_tools/local-dev.sh stop
```

The Home Assistant version is pinned in `docker-compose.yml` — don't change it to `:latest`; pin to a specific release so test results are reproducible.

For testing the companion Lovelace card alongside the integration:

```bash
./scripts/update-card.sh   # rebuilds + copies the card from a sibling checkout
```

## Running tests

The same commands CI runs:

```bash
# Full backend pytest suite (86 tests at time of writing)
python -m pytest custom_components/emergency_alerts/tests/ -v

# Translation sync (strings.json ↔ translations/en.json)
python scripts/validate_translations.py

# Integration structure (hassfest-equivalent local check)
python scripts/validate_integration.py
```

Convenience wrappers:

```bash
./scripts/run_tests.sh                  # full suite
./scripts/run_tests.sh --backend-only   # pytest only
```

The test suite lives in `custom_components/emergency_alerts/tests/`:

- `tests/test_*.py` — legacy flat suite (binary_sensor, config_flow, switch, sensor, init, dependencies).
- `tests/unit/` — pure-logic tests (action parsing, state machine, trigger evaluation).
- `tests/integration/` — hass-fixture tests using `pytest-homeassistant-custom-component` (state sync, e2e scenarios, template-trigger rerender regression, etc.).

`conftest.py` installs an autouse fixture that fails any test if `Failed to format translation` appears in the log output — this is how the translation-sync requirement is enforced at the test level.

### Playwright E2E (local-only)

`e2e-tests/` contains a Playwright + TypeScript suite for end-to-end UI verification (config flow, card rendering, console-error monitoring). It is **not** run in CI — invoke it against the Docker HA instance locally:

```bash
./scripts/run-e2e.sh
```

## Code style

Python is formatted with Black + isort and linted with flake8 + mypy. Run before pushing:

```bash
./scripts/lint.sh         # check: black + isort + flake8 + mypy
./scripts/fix-format.sh   # auto-fix: black + isort
```

Note: at present the CI lint job runs all four tools with `continue-on-error: true`, so a green CI does not mean the code is clean. Use `./scripts/lint.sh` locally for the real signal until that's tightened up.

## Translation sync (critical)

Any change to `strings.json` requires a matching change to `translations/en.json`. Mismatches cause runtime errors that surface as `Failed to format translation: <key>` in HA logs.

- `scripts/validate_translations.py` is run in CI and locally.
- `conftest.py` has an autouse fixture that fails any test if a translation error appears in the captured logs.

When in doubt: edit both files together in the same commit.

## Pull request guidelines

- **One concern per PR.** Easier to review, easier to revert.
- **Conventional Commits** — match the existing style:
  - `fix:` for bugfixes
  - `feat:` for new functionality
  - `docs:` for docs-only changes
  - `chore:` for tooling / housekeeping
  - `refactor:` for non-behavior-changing code restructure
- **Update `CHANGELOG.md`** under `## [Unreleased]` for anything user-visible (fix, feat, breaking change). Skip for chores / docs / refactors with no user-visible effect.
- **Bump `manifest.json` version** only when cutting a release (separate PR from feature work).
- CI must pass: HACS Validation, Hassfest, Backend Tests.

### Fix PRs must include a regression test

This is a hard rule. If your PR fixes a bug, add a test that **fails on `main` and passes with your fix**. The pattern to copy is [`tests/integration/test_template_trigger_rerender.py`](custom_components/emergency_alerts/tests/integration/test_template_trigger_rerender.py):

- Dedicated test file named after the bug.
- Docstring at the top naming the bug and what the failure mode was.
- Assertion message that says e.g. `"Bug X regressed"`, so a future failure is self-explanatory.

This convention exists because four out of the last five fix PRs shipped without a regression test — and the bugs were the kind of silent UI / wiring failures unit tests don't catch on their own.

If the bug genuinely can't be tested (HA limitation, browser-only behavior, etc.), say so in the PR description and explain why.

## Repository layout

```
emergency_alerts/
├── custom_components/emergency_alerts/   # the integration
│   ├── __init__.py, binary_sensor.py, select.py, sensor.py, switch.py
│   ├── config_flow.py, const.py, helpers.py, diagnostics.py
│   ├── manifest.json, strings.json, services.yaml, hacs.json
│   ├── translations/en.json              # keep in sync with strings.json
│   ├── core/                             # trigger evaluator, action executor
│   ├── blueprints/script/                # script blueprints
│   └── tests/
│       ├── conftest.py                   # hass fixtures, translation-error autocheck
│       ├── test_*.py                     # legacy flat suite
│       ├── unit/                         # pure-logic tests
│       └── integration/                  # hass-fixture tests
├── e2e-tests/                            # Playwright + TS suite — NOT run in CI
├── scripts/                              # all dev tooling
│   ├── run_tests.sh, lint.sh, fix-format.sh, docker-test.sh
│   ├── validate_integration.py, validate_translations.py
│   ├── update-card.sh, bypass-onboarding.sh, create-api-token.js, run-e2e.sh
├── dev_tools/                            # local-dev.sh + HA config for Docker dev
├── docs/                                 # TESTING.md, plans/, analysis docs
├── .github/workflows/test.yml            # CI: HACS + hassfest + backend-tests + lint
├── docker-compose.yml, Dockerfile.lint, Dockerfile.test
├── pytest.ini, pyproject.toml
└── CHANGELOG.md, README.md, LICENSE
```

## Common pitfalls

- **Don't set defaults on EntitySelector fields.** A `default=""` triggers `Entity not found` validation errors in the config flow. Leave EntitySelectors unset by default.
- **Device identifiers are immutable** in HA's device registry. Changing one is a breaking change — existing installations end up with orphaned devices in the registry and have to re-add the integration.
- **HA's service worker caching is aggressive** for frontend resources. The companion card uses `?v=X.X.X` cache-busting; bump the version when shipping card changes.
- **Don't unpin entity_id assignments** in `binary_sensor.py`, `select.py`, or `sensor.py`. Each platform explicitly sets `self.entity_id = ...` to work around HA's slugify-doubling behavior (device name + entity name combined into IDs like `binary_sensor.emergency_alert_<n>_emergency_<n>`). Removing those lines reintroduces the doubled-ID bug fixed in #13.
- **Template triggers must use `async_track_template_result`**, not `async_track_state_change_event([])`. The latter subscribes to nothing and silently never re-evaluates the template. Fixed in #14.
