# Emergency Alerts Integration for Home Assistant

[![Tests](https://img.shields.io/github/actions/workflow/status/issmirnov/emergency_alerts/test.yml?branch=main&label=tests&logo=github)](https://github.com/issmirnov/emergency_alerts/actions/workflows/test.yml)
[![HACS Validated](https://img.shields.io/badge/HACS-Validated-41BDF5.svg?logo=home-assistant&logoColor=white)](https://hacs.xyz)
[![Latest Release](https://img.shields.io/github/v/release/issmirnov/emergency_alerts?include_prereleases&sort=semver&logo=github)](https://github.com/issmirnov/emergency_alerts/releases)
[![Release Date](https://img.shields.io/github/release-date/issmirnov/emergency_alerts?logo=github)](https://github.com/issmirnov/emergency_alerts/releases)
[![HA Version](https://img.shields.io/badge/HA-2026.2%2B-41BDF5.svg?logo=home-assistant&logoColor=white)](https://www.home-assistant.io)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg?logo=python&logoColor=white)](https://www.python.org)
[![Stars](https://img.shields.io/github/stars/issmirnov/emergency_alerts?style=flat&logo=github)](https://github.com/issmirnov/emergency_alerts/stargazers)
[![Issues](https://img.shields.io/github/issues/issmirnov/emergency_alerts?logo=github)](https://github.com/issmirnov/emergency_alerts/issues)
[![License](https://img.shields.io/github/license/issmirnov/emergency_alerts)](LICENSE)
[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=issmirnov&repository=emergency_alerts&category=integration)

A Home Assistant custom integration for defining emergency alerts with a real state-machine lifecycle (active → acknowledged / snoozed / escalated / resolved), per-event action hooks, and a single-page UI config flow. Pairs with the companion [Lovelace card](https://github.com/issmirnov/lovelace-emergency-alerts-card) for one-tap acknowledge / snooze / resolve on your dashboard.

## What it does

You define an **alert** — a condition over your Home Assistant entities (simple state match, Jinja template, or AND/OR of up to 10 conditions). The integration watches it and, when it fires:

1. Flips a `binary_sensor.emergency_<your_alert>` to `on`.
2. Drives a `select.<your_alert>_state` entity through a real lifecycle (`inactive → active → acknowledged → resolved`, with `snoozed` and `escalated` branches).
3. Runs whatever HA service calls you wired to each transition (`on_triggered`, `on_acknowledged`, `on_snoozed`, `on_resolved`, `on_escalated`, `on_cleared`).
4. Optionally re-fires the trigger actions on a reminder timer until someone acknowledges.

Everything is exposed as plain HA entities you can chart, automate against, or wrap in the [companion card](https://github.com/issmirnov/lovelace-emergency-alerts-card).

## Features

- **Three trigger types** — simple entity-state match, Jinja2 templates (re-evaluated on referenced-entity change), or logical AND/OR over up to 10 entity/state pairs.
- **State lifecycle** — `inactive`, `active`, `acknowledged`, `snoozed`, `escalated`, `resolved`. Snooze auto-expires; escalation only fires for unacknowledged alerts.
- **Severity levels** — `info`, `warning`, `critical`, each rolled up into a group summary sensor.
- **Six action hooks** — `on_triggered`, `on_acknowledged`, `on_snoozed`, `on_resolved`, `on_escalated`, `on_cleared`. Plus an `on_triggered_script` shortcut that wires a `script.<x>` entity directly.
- **Reminders** — per-alert `remind_after_seconds` re-runs trigger actions until the alert is acknowledged or resolved.
- **Hub organization** — group related alerts under named hub devices for clean device hierarchy.
- **UI-first** — full visual config flow, zero YAML required to set up alerts.
- **Zero external runtime dependencies** — pure HA integration.

## Companion card

[**lovelace-emergency-alerts-card**](https://github.com/issmirnov/lovelace-emergency-alerts-card) — a dashboard card that renders each alert with one-tap acknowledge / snooze / resolve buttons driving the `select.<alert>_state` entity this integration exposes. Install separately via HACS.

## Installation

### HACS (recommended)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/issmirnov/emergency_alerts` (category: **Integration**)
3. Install **Emergency Alerts** and restart Home Assistant.

### Manual

Copy `custom_components/emergency_alerts/` into your HA `config/custom_components/`, then restart.

## Quick start

1. **Settings → Devices & Services → Add Integration → "Emergency Alerts"**
2. Pick a group name (e.g., `Security`, `Environment`, `Safety`). This creates a hub device.
3. Click the gear on the new hub → **Add Alert**.
4. Fill the single-page form, submit. The alert is live immediately — no HA restart needed.

Repeat step 3 for each alert. Edit and remove flows live in the same gear menu.

## Configuration examples

All configuration is UI-driven; the snippets below describe what to enter on the **Add Alert** form. Once submitted, each example yields a `binary_sensor.emergency_<alert_id>` plus a `select.<alert_id>_state` you can use anywhere in HA.

### Door left open (simple trigger)

| Field | Value |
|---|---|
| Name | `Front Door Left Open` |
| Trigger Type | `simple` |
| Entity | `binary_sensor.front_door` |
| Trigger State | `on` |
| Severity | `warning` |
| On Triggered Script | `script.notify_phone` |

Result:
- `binary_sensor.emergency_front_door_left_open` flips `on` whenever the door is open.
- `script.notify_phone` runs each time it transitions to active.

### Server room overheating (template trigger + reminder)

| Field | Value |
|---|---|
| Name | `Server Room Overheating` |
| Trigger Type | `template` |
| Template | `{{ states('sensor.server_room_temp') \| float(0) > 30 }}` |
| Severity | `critical` |
| Remind After (sec) | `300` |
| On Triggered Script | `script.page_oncall` |

The template is re-evaluated whenever any entity it references changes (`sensor.server_room_temp` here). `remind_after_seconds: 300` re-runs the trigger actions every 5 minutes until someone acknowledges.

### Night-time motion (logical trigger)

| Field | Value |
|---|---|
| Name | `Unexpected Motion at Night` |
| Trigger Type | `logical` |
| Condition 1 | `binary_sensor.living_room_motion` == `on` |
| Condition 2 | `sun.sun` == `below_horizon` |
| Operator | `AND` |
| Severity | `warning` |

Fires only when both conditions are simultaneously true. Use `OR` for either-or semantics, and add up to 10 conditions per alert.

## Using alerts in automations

### Acknowledge / snooze / resolve from anywhere

```yaml
service: select.select_option
data:
  entity_id: select.front_door_left_open_state
  option: acknowledged   # or: snoozed, resolved, active
```

### Or use the registered services

```yaml
# Available services: emergency_alerts.acknowledge, .clear, .escalate
service: emergency_alerts.acknowledge
data:
  entity_id: binary_sensor.emergency_front_door_left_open
```

### React to lifecycle transitions in automations

```yaml
trigger:
  - platform: state
    entity_id: select.server_room_overheating_state
    to: escalated
action:
  - service: notify.alerts_channel
    data:
      message: "Server room overheating has escalated — no acknowledgement yet."
```

### Lifecycle states

| State | Meaning |
|---|---|
| `inactive` | Trigger condition is false. |
| `active` | Trigger fired; waiting for user action. |
| `acknowledged` | Someone saw it; escalation suppressed. |
| `snoozed` | Temporarily silenced; auto-expires after `snooze_duration`. |
| `escalated` | Past the ack window without acknowledgement; `on_escalated` actions ran. |
| `resolved` | Marked complete. |

## Screenshots

<!-- TODO: capture screenshots of:
     - Add Alert single-page form
     - Alert device with its binary_sensor + select + summary sensor
     - Sister card on a dashboard showing one-tap acknowledge
-->

_Screenshots coming soon. See the [companion card repo](https://github.com/issmirnov/lovelace-emergency-alerts-card) for dashboard examples._

## Architecture

Brief tour of the moving parts:

- `binary_sensor.py` — the alert itself: trigger evaluation, lifecycle state, action execution, reminder timer.
- `select.py` — unified state-machine control surface; one `select.<alert>_state` per alert.
- `sensor.py` — per-group summary sensors counting active alerts by severity.
- `config_flow.py` — single-page add/edit/remove UI; persists alert config into the config entry's data.
- `core/` — modular trigger evaluator and action executor.

Full repository layout, local-verification commands, and CI gotchas live in [CLAUDE.md](CLAUDE.md). Testing details in [docs/TESTING.md](docs/TESTING.md).

## Development

```bash
# Backend tests (matches CI exactly)
python -m pytest custom_components/emergency_alerts/tests/ -v

# Translation sync (also enforced in CI)
python scripts/validate_translations.py

# Convenience wrappers
./scripts/run_tests.sh                  # full suite
./scripts/run_tests.sh --backend-only   # pytest only
./scripts/lint.sh                       # black + isort + flake8 + mypy
./scripts/fix-format.sh                 # auto-fix formatting

# Docker-based local HA (port 8123, user: dev/dev)
./dev_tools/local-dev.sh start
./dev_tools/local-dev.sh logs           # tail logs
./dev_tools/local-dev.sh restart        # pick up code changes
./dev_tools/local-dev.sh nuke           # wipe & start fresh
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Support

- **Issues**: [github.com/issmirnov/emergency_alerts/issues](https://github.com/issmirnov/emergency_alerts/issues)
- **Companion card**: [github.com/issmirnov/lovelace-emergency-alerts-card](https://github.com/issmirnov/lovelace-emergency-alerts-card)

## License

MIT — see [LICENSE](LICENSE).
