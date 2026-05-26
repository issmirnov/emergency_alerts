# Project-Specific Architecture Rules — Emergency Alerts Integration

This prompt extends the general architecture review with rules specific to the **Emergency Alerts** Home Assistant custom integration. Apply both prompts together when reviewing PRs.

---

## Project Context

**Project Name**: Emergency Alerts Integration for Home Assistant
**Tech Stack**: Python 3.9+ (HA targets 3.13), Home Assistant Core 2023.x+ (test against latest stable, currently 2026.2+), Jinja2 (HA template engine), pytest + `pytest-homeassistant-custom-component`
**Architecture Style**: HA custom integration with **hub-based device hierarchy** (Global Settings Hub → Alert Group Hubs → Alert Devices)
**Distribution**: HACS (Home Assistant Community Store)
**Deployment**: Runs inside the user's Home Assistant instance — no external hosting, no telemetry
**Maintainer**: Single maintainer (@issmirnov); developed with heavy AI-assistant collaboration
**Source Root**: `custom_components/emergency_alerts/`
**Project-specific memory bank**: `.claude/memory-bank/` (this project's variant — read the files there for architecture context; the canonical files are `projectbrief.md`, `techContext.md`, `systemPatterns.md`, `productContext.md`, `activeContext.md`, `progress.md`)

### Key Repository Layout

```
custom_components/emergency_alerts/
├── __init__.py              # Entry point: service registration, platform forwarding
├── binary_sensor.py         # CORE: alert entities, trigger evaluation, lifecycle (~820 lines)
├── config_flow.py           # Multi-step UI flows for hub + alert CRUD (~366 lines)
├── sensor.py                # Summary sensors + hub devices
├── button.py / select.py    # Action buttons / selectors (per-alert)
├── switch.py                # Action toggles (e.g. enable/disable)
├── const.py                 # Constants, signals, config keys
├── helpers.py / diagnostics.py
├── manifest.json            # MUST stay HACS-compliant, requirements MUST stay []
├── strings.json             # UI strings (source of truth)
├── translations/en.json     # MUST stay byte-for-byte in sync with strings.json
├── services.yaml            # Service definitions
└── tests/                   # pytest suite
scripts/
├── validate_integration.py
└── validate_translations.py # strings.json ↔ translations/en.json sync check
```

---

## Critical Architectural Invariants

These rules are **non-negotiable**. Violations are blockers (severity ≥ 3).

### 1. strings.json ↔ translations/en.json MUST stay in sync

**Rule**: Every key added/changed/removed in `custom_components/emergency_alerts/strings.json` MUST have a matching change in `custom_components/emergency_alerts/translations/en.json`. The two files must have the same structure.

**Why This Matters**:
- HA's UI loads translations from `translations/en.json`, not `strings.json`
- Drift causes UI to show raw translation keys (e.g. `component.emergency_alerts.config.step.user.title`) instead of human-readable text
- CI runs `scripts/validate_translations.py` and will fail the build
- This rule is explicitly called out in the project `CLAUDE.md`

**How to Check**:
```
- Diff strings.json and translations/en.json
- Any key added to one MUST appear in the other
- The line count and structure should match
- Run: python scripts/validate_translations.py
```

**Example — Bad Pattern**:
```diff
# strings.json
+ "step": { "new_step": { "title": "New Step" } }

# translations/en.json (UNCHANGED)
# ← Build fails. UI shows the raw key.
```

**Example — Good Pattern**:
```diff
# strings.json
+ "step": { "new_step": { "title": "New Step" } }

# translations/en.json
+ "step": { "new_step": { "title": "New Step" } }
```

---

### 2. Zero external runtime dependencies

**Rule**: `custom_components/emergency_alerts/manifest.json` MUST keep `"requirements": []` and `"dependencies": []` (HA core dependencies). No `pip install` libraries may be added at runtime.

**Why This Matters**:
- "Pure HA integration" is a core project value — keeps installation reliable, avoids HACS distribution friction
- External deps add attack surface, version conflicts, and update burden
- HA already provides Jinja2, voluptuous, aiohttp, async helpers — use them

**How to Check**:
```
- Look at manifest.json: requirements must be []
- Look for new `import` statements pulling in non-stdlib, non-homeassistant packages
- Test requirements (test_requirements.txt) are fine — they don't ship
```

**Example — Bad Pattern**:
```json
// manifest.json
{
  "requirements": ["requests>=2.0", "pyyaml>=6.0"]
}
```

**Example — Good Pattern**:
```python
# Use HA-provided modules instead:
from homeassistant.helpers.template import Template       # not jinja2 directly
from homeassistant.helpers.aiohttp_client import async_get_clientsession  # not requests
import yaml  # stdlib (or just use HA's YAML helpers)
```

---

### 3. Async-first: never block the HA event loop

**Rule**: All HA-facing functions must be `async def`. Sync I/O (file reads, network calls, `time.sleep`, blocking subprocess) inside an async context MUST be wrapped via `hass.async_add_executor_job(...)`.

**Why This Matters**:
- HA runs a single event loop. A blocking call freezes the UI and every other integration
- HA logs warnings like `Detected blocking call to ... inside the event loop`
- Hub-based integrations have many entities; blocking in one breaks all

**How to Check**:
```
- Any `open()`, `requests.`, `subprocess.run`, `time.sleep` inside async function = BLOCKER
- Missing `await` on coroutines (linter usually catches but verify)
- New imports of synchronous I/O libraries
```

**Example — Bad Pattern**:
```python
async def async_update(self):
    with open("/some/path") as f:        # ❌ blocks event loop
        data = f.read()
    response = requests.get(url)          # ❌ blocks event loop
```

**Example — Good Pattern**:
```python
async def async_update(self):
    data = await self.hass.async_add_executor_job(self._read_file)
    session = async_get_clientsession(self.hass)
    response = await session.get(url)
```

---

### 4. Entities are created by platforms — never in `__init__.py`

**Rule**: Entity instances (`BinarySensorEntity`, `SensorEntity`, `ButtonEntity`, etc.) MUST be created inside their platform module's `async_setup_entry(hass, entry, async_add_entities)`. `__init__.py` only forwards setup via `hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`.

**Why This Matters**:
- Violates HA platform pattern; breaks device organization
- Entities created outside platforms miss the entity registry/device registry hooks
- HA may not reload them cleanly on config entry update

**How to Check**:
```
- `__init__.py` should NOT instantiate `*Entity` subclasses
- Look for `async_add_entities([...])` calls — these belong in platform files only
```

**Example — Good Pattern**: see `custom_components/emergency_alerts/__init__.py` — it only calls `async_forward_entry_setups()` and registers services.

---

### 5. Hub-based device hierarchy via `via_device`

**Rule**: Every alert entity's `DeviceInfo` MUST include `via_device=(DOMAIN, f"hub_{config_entry.entry_id}")` so it appears nested under its hub in the HA device UI.

**Why This Matters**:
- Without `via_device`, alerts appear as orphan devices instead of children of their hub
- Breaks the "Group → Alert" mental model the entire integration is built around
- Confuses users browsing the device list

**How to Check**:
```
- New entity classes: does `_attr_device_info` or `device_info` include `via_device`?
- Hub identifier format: `(DOMAIN, f"hub_{entry.entry_id}")`
- Alert identifier format: `(DOMAIN, f"alert_{entry.entry_id}_{alert_id}")`
```

**Example — Good Pattern**: see `binary_sensor.py` and `sensor.py` for the canonical `DeviceInfo` shape.

---

### 6. Alert configs live in `entry.data`, not `entry.options`

**Rule**: Alert definitions are stored on the config entry via `entry.data`, mutated through `hass.config_entries.async_update_entry(entry, data=...)`, and reloaded with `hass.config_entries.async_reload(entry.entry_id)`. Do not move them to `entry.options`.

**Why This Matters**:
- `entry.data` is available immediately during platform setup; `entry.options` requires the options flow
- Entities need alert configs at setup time, not after options-flow completion
- Past production fix (#13) depended on this pattern working correctly

**How to Check**:
```
- Look for `entry.options` reads in platform files (binary_sensor.py, sensor.py, etc.) — should be entry.data
- Look for new options-flow handlers adding alert state — likely wrong
- Config flow should call async_update_entry(data=...) + async_reload()
```

---

### 7. Constants come from `const.py` — no hardcoded strings

**Rule**: Use the symbols defined in `const.py` for config keys, signals, event types, and the `DOMAIN`. Do not hardcode strings like `"emergency_alerts"`, `"alert_update"`, or `"trigger_type"` in platform code.

**Why This Matters**:
- Renaming or refactoring becomes a multi-file grep; constants make it one diff
- Typos in hardcoded strings silently break dispatcher signals and config reads
- Past fix (#12) involved special-character handling in IDs — centralizing helps

**How to Check**:
```
- grep for string literals matching DOMAIN, signal names, or CONF_* keys outside const.py
- New CONF_*, SIGNAL_*, EVENT_* additions should be in const.py
```

---

### 8. Template triggers must subscribe to referenced entities

**Rule**: Template-based alert triggers MUST re-evaluate when entities referenced inside the template change state — not only on a fixed polling interval. Use HA's `async_track_template_result` or `async_track_state_change_event` keyed on the template's referenced entities.

**Why This Matters**:
- Past production fix (#14) was exactly this: template-trigger alerts didn't re-evaluate on referenced-entity changes
- Without this, alerts can be stale until next forced poll
- Jinja2 templates must always be wrapped in `try/except TemplateError` — never let template failures crash the entity

**How to Check**:
```
- New template-trigger code: is there a subscription to referenced entities?
- Template renders wrapped in try/except TemplateError?
- Log + return safe default on error, never re-raise into HA's core loop
```

**Example — Bad Pattern**:
```python
# ❌ Polls only, no subscription, no error handling
async def async_update(self):
    rendered = Template(self._template, self.hass).async_render()
    self._attr_is_on = rendered == "True"
```

**Example — Good Pattern**:
```python
# ✅ Tracks template results, handles errors
from homeassistant.helpers.event import async_track_template_result
from homeassistant.exceptions import TemplateError

async def async_added_to_hass(self):
    try:
        tracker = async_track_template_result(
            self.hass,
            [TrackTemplate(Template(self._template, self.hass), None)],
            self._handle_template_result,
        )
        self.async_on_remove(tracker.async_remove)
    except TemplateError as err:
        _LOGGER.warning("Template error in alert %s: %s", self._name, err)
```

---

### 9. Stable, sanitized `unique_id` and `suggested_object_id`

**Rule**: Every entity MUST set `_attr_unique_id` derived from `config_entry.entry_id + alert_id`. Entity IDs derived from user-provided alert names MUST be sanitized for special characters (no `/`, spaces collapsed to `_`, lowercase). Use `suggested_object_id` to disambiguate when names collide.

**Why This Matters**:
- Past fixes (#12, #13) addressed exactly these: `alert_id` broke on special chars, and duplicate names produced colliding entity_ids
- Without stable `unique_id`, HA generates random IDs on re-add — automations break
- Without sanitization, HA rejects the entity or generates malformed entity_ids

**How to Check**:
```
- New entity classes: `_attr_unique_id` set deterministically?
- User-string-derived IDs: sanitized via slugify or similar?
- Collision-prone names: `suggested_object_id` used?
```

---

### 10. Dispatcher signals for cross-component updates — never direct entity references

**Rule**: When a binary_sensor changes state and a summary `sensor` needs to refresh, send via `async_dispatcher_send(hass, SIGNAL_ALERT_UPDATE, entry.entry_id)`. The sensor listens via `async_dispatcher_connect`. Do NOT walk the entity registry or import entity classes directly.

**Why This Matters**:
- Direct cross-platform references create import cycles and reload bugs
- The dispatcher pattern is HA-idiomatic and survives entity reload
- Keeps `binary_sensor.py` and `sensor.py` decoupled

**How to Check**:
```
- New cross-platform state propagation: is it using dispatcher signals?
- Imports between platform files (e.g. sensor.py importing from binary_sensor.py)
- Walking `hass.states` or entity registry from platform code to find peers
```

---

## Home Assistant-Specific Patterns

### Service Registration

- Services registered in `__init__.py` via `hass.services.async_register(DOMAIN, "service_name", handler, schema=vol.Schema({...}))`
- All services declared in `services.yaml` with descriptions and field definitions
- Service handlers must validate inputs via voluptuous schemas

### Config Flow

- Multi-step with progressive disclosure: basic → trigger-type-specific → actions
- Errors returned as `{"field_name": "error_key"}`, error_key must exist in `strings.json` AND `translations/en.json`
- Use `selector.EntitySelector`, `selector.SelectSelector`, `selector.TemplateSelector` — not raw text fields
- Final step calls `async_create_entry()` or `async_update_entry()` + `async_reload()`

### Diagnostics

- `diagnostics.py` exposes a `async_get_config_entry_diagnostics(hass, entry)` for debug support
- Must NOT leak secrets (none expected in this integration, but a guard for the future)
- Output should include alert configs, current states, and recent state-change history

### Logging

- Use `_LOGGER = logging.getLogger(__name__)` at module top
- `_LOGGER.warning` for recoverable issues; `_LOGGER.error` for true errors
- Never log raw user input at INFO+ levels (template strings can contain sensitive entity names)

---

## Testing Requirements

### Required Patterns
- [ ] **pytest-homeassistant-custom-component**: fixtures via `conftest.py`, not real HA boot
- [ ] **Coverage**: target >90% overall, 100% for `_evaluate_trigger` paths in `binary_sensor.py`
- [ ] **All trigger types tested**: simple, template, logical (AND/OR) — each with state-change scenarios
- [ ] **Config flow tests**: full happy-path and at least one validation-error path per step
- [ ] **No real network in tests**: mock all external service calls

### Anti-Patterns to Block
- ❌ Tests that boot a full Home Assistant instance (use the integration test fixtures)
- ❌ Tests that depend on real wall-clock time (use `freezegun` or async-timer mocks)
- ❌ Tests that mutate shared global state without teardown
- ❌ New core logic in `binary_sensor.py` without a corresponding test

---

## Common Production Issues (Learned Lessons)

### Issue: Template-trigger alerts didn't re-evaluate on referenced-entity changes (PR #14)

**What Broke**: Alerts using a Jinja2 template trigger only updated on forced polls, so state changes in referenced entities didn't fire the alert.

**Root Cause**: Template was rendered on update but no subscription was registered for the template's referenced entities.

**How to Prevent** — check for:
- Template trigger code missing `async_track_template_result` or equivalent
- No teardown via `async_on_remove`

See **Invariant #8** above for the enforced pattern.

---

### Issue: Duplicate entity_ids and missing `on_triggered_script` wiring (PR #13)

**What Broke**: Two alerts with similar names produced colliding `entity_id`s; `on_triggered_script` action was configured in the UI but never invoked.

**Root Cause**:
1. Entity factory didn't pass `suggested_object_id` derived from a sanitized alert_id
2. The `on_triggered_script` field was read from config but not wired into `_handle_state_change`

**How to Prevent** — check for:
- New action types added to config flow → confirm they are read AND invoked in `binary_sensor.py`
- Entity-naming code → confirm sanitization + `suggested_object_id`

---

### Issue: Select dropdown showed "unknown"; alert_id broke on special chars (PR #12)

**What Broke**: A `SelectEntity` with no valid options defaulted to "unknown"; alert IDs containing `.` or `/` produced malformed entity_ids.

**Root Cause**: Missing input sanitization on the user-provided alert name, no default option for SelectEntity.

**How to Prevent** — check for:
- New `SelectEntity` subclasses with no `_attr_current_option` default
- User-string-derived IDs not sanitized through `slugify` or equivalent

---

## Project-Specific Anti-Patterns

### Anti-Pattern: Adding switch.py logic when button.py is the right home

**Description**: One-time user actions (acknowledge / clear / escalate) belong in **ButtonEntity**, not SwitchEntity. Switches are stateful toggles, buttons are one-shot events.

**Why It's Bad**: Confuses users (button shows misleading "on" state), couples UI semantics to internal state machine.

**Detection**: New `SwitchEntity` subclasses representing one-time actions. Check if `ButtonEntity` would be the better fit.

---

### Anti-Pattern: Storing alert state in module-level globals or `hass.data` instead of the entity

**Description**: Alert flags (`_acknowledged`, `_cleared`, `_escalated`) belong on the entity instance. `hass.data[DOMAIN]` is for cross-platform shared references (entry-id maps), not per-alert state.

**Why It's Bad**: Module globals don't survive integration reload; `hass.data` shape becomes a hidden API.

**Detection**: New module-level mutable state, or new keys being written to `hass.data[DOMAIN]` from platform code.

---

### Anti-Pattern: Direct `hass.states.get(entity_id).state` without None check

**Description**: `hass.states.get()` returns `None` for unknown entities. Accessing `.state` on `None` raises `AttributeError` and crashes the alert evaluation.

**Detection**:
```python
# ❌ BAD
state = hass.states.get(entity_id).state

# ✅ GOOD
state_obj = hass.states.get(entity_id)
if state_obj is None:
    return False
state = state_obj.state
```

---

## Deployment & Distribution Patterns

### Required Practices

- [ ] **manifest.json version bumped** for user-visible changes (semver-ish; HACS expects this)
- [ ] **HACS-compliant structure**: `custom_components/emergency_alerts/` flat layout
- [ ] **hassfest passes**: validated via `home-assistant/actions/hassfest@master` in `.github/workflows/test.yml`
- [ ] **HACS validation passes**: validated via `hacs/action@main`
- [ ] **No `:latest` Docker tags** in `dev_tools/` — pin to a specific HA version (e.g. `homeassistant/home-assistant:2026.2`)

### Anti-Patterns to Block

- ❌ Adding entries to `manifest.json` `requirements` (zero-deps invariant)
- ❌ Removing `codeowners` or `documentation` from manifest.json
- ❌ Breaking changes to service signatures in `services.yaml` without a deprecation note
- ❌ Renaming `DOMAIN` (would break every user's existing config entries)

---

## Code Review Checklist for This Project

When reviewing a PR, verify:

**HA Integration Hygiene**:
- [ ] `manifest.json` `requirements` still `[]`
- [ ] `strings.json` and `translations/en.json` in sync (line count + structure)
- [ ] All new entities have `unique_id`, `device_info` with `via_device`, `name`
- [ ] No blocking I/O inside async functions
- [ ] All new strings have entries in BOTH `strings.json` and `translations/en.json`

**Alert Logic**:
- [ ] New trigger types in `binary_sensor.py` have try/except around evaluation
- [ ] Template triggers subscribe to referenced entities (Invariant #8)
- [ ] State-change handlers fire `SIGNAL_ALERT_UPDATE`
- [ ] Config keys come from `const.py`

**Config Flow**:
- [ ] New steps have entries in `strings.json` AND `translations/en.json`
- [ ] User inputs validated (voluptuous schema or selector type)
- [ ] User-string-derived entity_ids sanitized
- [ ] `async_update_entry(data=...)` + `async_reload()` pattern for edits

**Testing**:
- [ ] New trigger/action paths have pytest coverage
- [ ] Tests use `pytest-homeassistant-custom-component` fixtures
- [ ] `scripts/validate_translations.py` passes
- [ ] `scripts/validate_integration.py` passes
- [ ] hassfest passes (CI will enforce)

**Backwards Compatibility**:
- [ ] No breaking changes to `services.yaml` signatures
- [ ] No removal/rename of existing config-entry data keys without migration
- [ ] No removal of `entity_id` patterns users may have referenced in automations

**Documentation**:
- [ ] `README.md` updated for user-facing feature changes
- [ ] `manifest.json` version bumped
- [ ] `.claude/memory-bank/activeContext.md` and `progress.md` updated when patterns change

---

## Severity Guidelines for This Project

**Severity 0**: Documentation, comments, README, memory-bank updates only
**Severity 1**: Style nits, minor refactors, non-user-visible cleanup
**Severity 2**: Should fix — quality concerns, missing tests on non-critical paths, HACS warnings
**Severity 3**: Must fix before merge — invariant violation (any of #1–#10), broken integration setup, missing platform pattern
**Severity 4**: Critical — security issue, data loss, event-loop blocker, manifest breaks HACS/hassfest

**Blockers = true** when:
- Any of the 10 critical invariants above is violated
- `strings.json` / `translations/en.json` out of sync (CI will fail anyway)
- External dependencies added to `manifest.json`
- Blocking I/O introduced into the event loop
- Breaking change to a public surface (service signature, DOMAIN, entry data shape) without migration

---

## Integration with General Prompt

This prompt **extends** the general architecture review (`01-general-architecture-review.prompt.md`). The general prompt covers universal concerns (SOLID, DRY, security, anti-patterns). This prompt adds Home Assistant integration discipline and the specific patterns earned through past production fixes (#12, #13, #14).

Claude will apply **both** sets of rules when reviewing PRs.
