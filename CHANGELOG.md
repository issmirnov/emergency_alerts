# Changelog

All notable changes to the Emergency Alerts integration will be documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

No unreleased changes.

## [4.3.0] - 2026-05-26

Two user-facing features land together: a UI config-flow option for the
existing `logical` trigger type, and an `on_escalated_script` field that
parallels `on_triggered_script`.

### Added

- **`logical` trigger type is now selectable in the UI** ([#28](https://github.com/issmirnov/emergency_alerts/pull/28)). The evaluator has supported it for ages — combining N `{entity_id, state}` pairs with AND or OR — but the config flow only offered `simple` and `template`. Adds two new fields:
  - `logical_conditions` — `ObjectSelector` (YAML editor in the HA UI). A list where each item has an `entity_id` and a `state`. The existing JSON/YAML string parser still works for API-created alerts.
  - `logical_operator` — `and` (default) or `or`.

  Example:
  ```yaml
  - entity_id: binary_sensor.front_door
    state: 'on'
  - entity_id: binary_sensor.motion_living_room
    state: 'on'
  ```
  With `logical_operator: and` fires only when both are on. Validation
  rejects empty conditions or items missing `entity_id` / `state`.

- **`on_escalated_script` field** ([#27](https://github.com/issmirnov/emergency_alerts/pull/27)) — new optional config-flow field that mirrors `on_triggered_script`. Point it at a `script.<x>` entity and the integration will call `script.turn_on` against it when the escalation timer fires (alert active and unacknowledged past the escalation timeout). Lets users wire a louder/different notification on escalation without a separate HA automation listening for `select.<alert>_state → escalated`.

  Implementation note: factored out a shared `_resolve_script_field` helper in `binary_sensor.py` so both `_resolve_on_triggered` and `_resolve_on_escalated` follow the same explicit-action-wins-over-script-shortcut contract. The two resolvers stay independent — setting only `on_triggered_script` does NOT cause the escalation to fire it (and vice versa).

### Tests

- 7 new unit tests for the resolvers in `test_binary_sensor.py` covering: returns-None-when-neither-set, synthesizes-`script.turn_on`, explicit-actions-take-precedence, and a specific regression that the trigger and escalation resolvers stay independent.
- 4 new tests in `test_config_flow.py` covering: schema accepts logical-trigger submissions, `_build_alert_data` rejects logical with no conditions, rejects malformed conditions (missing state), and persists `logical_conditions` + `logical_operator` cleanly.

## [4.2.2] - 2026-05-26

Cleanup release: gets PRs #24 and #25 into a tagged version, corrects the
`hacs.json` HA-version claim, stops shipping dev artifacts in release
tarballs, and rounds out the README with an honest comparison to HA's
built-in `alert:` / `notify:`. No functional changes to alert behavior —
upgrade is risk-free.

### Fixed

- **`hacs.json` claimed HA 2023.1.0 minimum, which was a lie.** The
  integration uses `OptionsFlow.config_entry` as a sealed property — a
  feature that landed in HA 2026.2. On anything older, every options-flow
  step raises `AttributeError: 'EmergencyOptionsFlow' object has no
  attribute 'config_entry'`. Bumped `hacs.json` and `test_requirements.txt`
  to `homeassistant>=2026.2.0` so HACS users see the correct compatibility
  warning and the test image matches the true floor.
- **Test image was running HA 2024.3.3** because `test_requirements.txt`
  said `>=2024.1.0`, so three integration tests (`test_concurrent_updates`,
  `test_snooze_select_updates_binary_sensor`, `test_select_mutual_exclusivity`)
  appeared "flaky" — they were actually hitting the `config_entry`
  attribute-error on the older HA. Pinning the test floor to 2026.2
  resolves them; all 99 tests now pass on the matched-floor image.

### Changed

- **Stop shipping dev artifacts in release tarballs.** Added
  `.gitattributes` with `export-ignore` for `tests/`, `test_requirements.txt`,
  `htmlcov/`, `dev_tools/`, `e2e-tests/`, `.devcontainer/`, `Dockerfile.*`,
  `docker-compose.yml`, `scripts/`, `docs/`, the `lovelace-emergency-alerts-card`
  vendored copy, and other dev-only paths. The next release tarball drops
  from ~bloat to ~180KB and no longer creates spurious `tests/` and
  `test_requirements.txt` files under `custom_components/emergency_alerts/`
  on user installs. ([#24](https://github.com/issmirnov/emergency_alerts/pull/24) covered the symlink; this finishes the cleanup.)
- **Bumped `Dockerfile.test` base to `python:3.13-slim`** to match HA
  2026's Python-3.13 requirement (CI was already on 3.13; the Dockerfile
  drifted).
- **Bumped `pyproject.toml` mypy target to `3.13`** (was `3.9`).

### Documentation

- **README: added "How it compares to HA's built-in `alert:` and `notify:`"
  section** — a side-by-side table covering config style, state model,
  trigger types, ack/snooze/escalate semantics, severity rollups, and
  when to pick each. Helps anyone evaluating against the in-tree options.

### Workflow

- **Architect-Gate now actually reviews diffs.** The Claude review action
  was running with no tools and couldn't read the diff file or run git;
  every SAR landed as "you haven't provided a PR diff". Added
  `--allowed-tools Read,Grep,Glob,Bash(git*)` and appended a PR Changes
  Summary block with explicit git commands. Mirrors the working config
  in `chronicle` and `claude-k8s`. ([#25](https://github.com/issmirnov/emergency_alerts/pull/25))
- **Dropped dangling dev-mode symlink** `custom_components/emergency_alerts/emergency_alerts`
  that shipped in every release tarball as a broken symlink and made
  HACS's post-extract backup step error out. ([#24](https://github.com/issmirnov/emergency_alerts/pull/24))

## [4.2.1] - 2026-05-26

Single-bug patch release. Cuts a separate version because the fix unblocks
programmatic alert updates via the options-flow API, which is how external
tooling (provisioning scripts, migrations) interacts with the integration.

### Fixed

- **Edit-alert form misfired as "already_configured".** Submitting the edit form for an existing alert always rejected with `{name: already_configured}` because `async_step_edit_alert_form` shared `step_id="add_alert"` with the create flow, so HA routed POSTs to `async_step_add_alert`, which then ran the duplicate-name guard against the very alert being edited. The guard now respects `self._editing_alert_id` and allows the slug match when it points at the alert under edit. Renaming an alert during edit removes the old slug. Removes the dead, unreachable user-input branch from `async_step_edit_alert_form`. ([#22](https://github.com/issmirnov/emergency_alerts/pull/22))

## [4.2.0] - 2026-05-26

Mostly a bug-fix release that papers over six rough edges in v4.1.0, plus one
genuinely new feature: a top-level `for_seconds` field that gives every alert a
HA-native sustain-duration debounce.

### Added

- **`for_seconds` debounce field.** New top-level alert config that delays
  triggering until the underlying condition has been continuously true for the
  given number of seconds (HA `for:` semantics). Applies uniformly to simple,
  template, and logical triggers. Cleanly cancels the dwell when the condition
  flaps. Default `0` keeps old behavior. ([#18](https://github.com/issmirnov/emergency_alerts/pull/18))

### Fixed

- **Template-trigger alerts never re-evaluated.** `async_track_state_change_event(hass, [], …)` was subscribing to an empty entity list, so template-triggered alerts latched on/off until the next integration reload. Switched to `async_track_template_result`, which subscribes to the entities referenced inside the Jinja template. ([#14](https://github.com/issmirnov/emergency_alerts/pull/14))
- **`on_triggered_script` UI field was silently ignored.** The script entity selected in the config flow was stored on the alert but never wired into action execution. Added `_resolve_on_triggered()` in `binary_sensor.py` to synthesize a `script.turn_on` call from the field. ([#13](https://github.com/issmirnov/emergency_alerts/pull/13))
- **Duplicate / mangled entity IDs.** HA was slugify-combining device name + entity name into IDs like `binary_sensor.emergency_alert_<name>_emergency_<name>`. `binary_sensor`, `select`, and `sensor` platforms now pin `self.entity_id` explicitly so new alerts get clean IDs. Existing alerts in the entity registry are unaffected. ([#13](https://github.com/issmirnov/emergency_alerts/pull/13))
- **Select entity showed "unknown" for inactive alerts.** `STATE_INACTIVE` (and `STATE_ESCALATED`) were not in the select's `ALERT_STATES` option list, so the widget rendered `unknown` whenever the alert was off. Added both to the options list. ([#12](https://github.com/issmirnov/emergency_alerts/pull/12))
- **Alert IDs broke on names with special characters.** Names like `Smoke/CO Detector (Triggered)` produced alert IDs with slashes and parens, which broke remove-alert lookups and entity-ID derivation. Added `_slugify_alert_id()` in `config_flow.py` to collapse non-alphanumeric runs into single underscores. ([#12](https://github.com/issmirnov/emergency_alerts/pull/12))
- **Hub summary sensor reported configured count instead of active count.** `sensor.emergency_alerts_<hub>_summary` was emitting the total number of alerts ever configured on the hub, which made it useless for visibility gating on the dashboard ("show this section when any alert in this hub is firing"). The state is now the count of currently-triggered alerts on the hub, computed via the existing `SUMMARY_UPDATE_SIGNAL` dispatcher. ([#16](https://github.com/issmirnov/emergency_alerts/pull/16))
- **EntitySelector fields rejected empty submissions.** Leaving an EntitySelector blank on the add/edit alert form raised "Entity not found" because `vol.Optional(key, default="")` was injecting an empty string that EntitySelector then validated against the entity registry. Switched to `description={"suggested_value": ...}` pre-fill via a new `_optional()` helper so unset fields go through cleanly. Removes the long-standing "EntitySelector fields must not have default values" caveat. ([#20](https://github.com/issmirnov/emergency_alerts/pull/20))

### Changed

- Relocated all dev scripts into `scripts/` (`run_tests.sh`, `lint.sh`, `fix-format.sh`, `docker-test.sh`, `update-card.sh`, `validate_integration.py`, `validate_translations.py`). CI workflow updated to match. Dropped obsolete LLM-era docs from repo root. ([#15](https://github.com/issmirnov/emergency_alerts/pull/15))
- Added MIT `LICENSE` file (was referenced by README but missing on disk).
- Added an automated "architect-gate" PR review workflow that posts a System Architecture Review on every PR. ([#19](https://github.com/issmirnov/emergency_alerts/pull/19))

### Documentation

- README rewritten to focus on what the integration does, with concrete configuration examples and a link to the companion Lovelace card. ([#17](https://github.com/issmirnov/emergency_alerts/pull/17))
- `CLAUDE.md` gained Repository Layout, Local Verification, and CI Gotchas sections, plus the conventions surfaced by recent fix PRs (entity-ID pinning, `on_triggered_script` resolution, alert-ID slugification, `async_track_template_result` for templates).
- Added `CONTRIBUTING.md` and badges across the README. ([#17](https://github.com/issmirnov/emergency_alerts/pull/17))

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
