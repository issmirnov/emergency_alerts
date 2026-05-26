# Changelog

All notable changes to the Emergency Alerts integration will be documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

These changes are merged to `main` but `manifest.json` is still at `4.1.0`. Bump to `4.1.1` to cut a release.

### Fixed

- **Template-trigger alerts never re-evaluated.** `async_track_state_change_event(hass, [], …)` was subscribing to an empty entity list, so template-triggered alerts latched on/off until the next integration reload. Switched to `async_track_template_result`, which subscribes to the entities referenced inside the Jinja template. ([#14](https://github.com/issmirnov/emergency_alerts/pull/14))
- **`on_triggered_script` UI field was silently ignored.** The script entity selected in the config flow was stored on the alert but never wired into action execution. Added `_resolve_on_triggered()` in `binary_sensor.py` to synthesize a `script.turn_on` call from the field. ([#13](https://github.com/issmirnov/emergency_alerts/pull/13))
- **Duplicate / mangled entity IDs.** HA was slugify-combining device name + entity name into IDs like `binary_sensor.emergency_alert_<name>_emergency_<name>`. `binary_sensor`, `select`, and `sensor` platforms now pin `self.entity_id` explicitly so new alerts get clean IDs. Existing alerts in the entity registry are unaffected. ([#13](https://github.com/issmirnov/emergency_alerts/pull/13))
- **Select entity showed "unknown" for inactive alerts.** `STATE_INACTIVE` (and `STATE_ESCALATED`) were not in the select's `ALERT_STATES` option list, so the widget rendered `unknown` whenever the alert was off. Added both to the options list. ([#12](https://github.com/issmirnov/emergency_alerts/pull/12))
- **Alert IDs broke on names with special characters.** Names like `Smoke/CO Detector (Triggered)` produced alert IDs with slashes and parens, which broke remove-alert lookups and entity-ID derivation. Added `_slugify_alert_id()` in `config_flow.py` to collapse non-alphanumeric runs into single underscores. ([#12](https://github.com/issmirnov/emergency_alerts/pull/12))

### Changed

- Relocated all dev scripts into `scripts/` (`run_tests.sh`, `lint.sh`, `fix-format.sh`, `docker-test.sh`, `update-card.sh`, `validate_integration.py`, `validate_translations.py`). CI workflow updated to match. Dropped obsolete LLM-era docs from repo root. ([#15](https://github.com/issmirnov/emergency_alerts/pull/15))
- Added MIT `LICENSE` file (was referenced by README but missing on disk).

### Documentation

- README rewritten to focus on what the integration does, with concrete configuration examples and a link to the companion Lovelace card.
- `CLAUDE.md` gained Repository Layout, Local Verification, and CI Gotchas sections, plus the conventions surfaced by recent fix PRs (entity-ID pinning, `on_triggered_script` resolution, alert-ID slugification, `async_track_template_result` for templates).

## [4.1.0] - 2026-02-10

Major polish release. Focused on UX, testing infrastructure, and Home Assistant 2026.2 compatibility.

### Added

- **Single-page config flow** (Adaptive Lighting pattern) — all alert options on one scrollable form instead of a multi-step wizard.
- **Full edit & remove flows** with pre-filled forms and field-default preservation.
- **Instant entity updates** after add / edit / remove via `config_entries.async_reload()` — no HA restart needed.
- **User-friendly field labels** and template-testing guidance on every config-flow field.
- **Hassfest validation** in CI.
- **Translation sync validation** via `scripts/validate_translations.py` (run in CI) plus an autouse pytest fixture in `conftest.py` that fails any test with a "Failed to format translation" log line.
- **Playwright E2E test** for config flow with console-error monitoring (`e2e-tests/tests/03-config-flow-add-alert.spec.ts`).
- **Comprehensive testing docs** (`docs/TESTING.md`).
- **Automated dev environment** via `dev_tools/local-dev.sh` — trusted-network auth bypass, auto-creates sun integration + 2 test alerts, registers dashboard + card resources on startup.

### Changed

- **Config flow code**: 1,371 → 366 lines (~73% reduction) in `config_flow.py`.
- **Script storage**: actions stored as entity-ID string (`{"script": "script.notify_phone"}`) instead of nested action array. Migration logic handles the legacy array format.
- **Card V4** (separate repo): switched from `switch.toggle` to `select.select_option`; cache-busting via `?v=4.0.0` resource parameter.
- **Modern selectors** (`EntitySelector`, `TemplateSelector`) replace bare text inputs across the config flow.
- **Docker dev environment** pinned to Home Assistant `2026.2` (never `:latest`).

### Fixed

- 40+ translation-string mismatches between `strings.json` and `translations/en.json`.
- HA 2026.2 `OptionsFlow.config_entry` is read-only — removed custom `__init__` from `OptionsFlow` subclasses.
- `async_show_menu` doesn't support `description_placeholders` — switched to `async_show_form` where placeholders were needed.

### Known incompatibilities

- `EntitySelector` fields must not have default values. A `default=""` triggers "Entity not found" validation. Leave EntitySelectors unset by default.

## [4.0.0] - 2026-02-04

### Changed (BREAKING)

Replaced 3 switches per alert with 1 select entity for unified state control.

**Migration:**
- Old: `switch.{alert_name}_acknowledged`, `switch.{alert_name}_snoozed`, `switch.{alert_name}_resolved`
- New: `select.{alert_name}_state` with options: `active`, `acknowledged`, `snoozed`, `resolved`
- Update automations from `switch.turn_on` to `select.select_option`:
  ```yaml
  service: select.select_option
  data:
    entity_id: select.door_alert_state
    option: acknowledged
  ```

**Benefits:** 67% fewer entities, single dropdown instead of 3 toggles, simpler state management, better alignment with HA 2026.2 patterns.

### Added

- New `select` platform for unified alert state control.
- Automatic state syncing with the alert binary sensor.

### Deprecated

- `switch.py` is deprecated and will be removed in v5.0.0.

## [3.0.3] - 2026-02-04

### Fixed
- Auto-migration for old config entries missing the `group` field.
- Translation error: `group_name was not provided`.

### Added
- Debug logging for config-entry diagnostics.
- Local Docker-based development environment.
- Mock-HA development testing framework.
- Translation audit tool.
- Import validation tests.

## [3.0.2] - 2026-02-04

### Fixed
- Translation placeholder errors in config flow.
- Missing `group_name` in `description_placeholders`.

## [3.0.1] - 2026-02-04

### Fixed
- `ImportError` for the removed `TRIGGER_TYPE_COMBINED` constant.

## [3.0.0] - 2026-02-04

### Changed
- Removed the separate Global Settings Hub — no longer required.
- Config flow goes directly to alert-group creation.
- Simple / template triggers use a single unified form; logical triggers use a multi-step wizard.
- Removed "combined" trigger type (superseded by logical).

### Added
- Unified single-page alert creation form.
- Smart form that adapts based on trigger type.
- Entity autocomplete in the config flow.
- Notification profiles at group level.
- Modular trigger evaluator and action executor under `core/`.
- Comprehensive local testing framework.

## [2.x.x] and earlier

See git history.
