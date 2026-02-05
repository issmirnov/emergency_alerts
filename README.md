# Emergency Alerts Integration for Home Assistant

A powerful Home Assistant integration for managing critical alerts with smart escalation, state management, and flexible trigger conditions.

## Version 4.0.0 - Major Modernization Release

**BREAKING CHANGE**: This version replaces 3 switches per alert with 1 unified select entity for simpler state management.

### What's New in v4.0.0

- **Unified State Control**: Single select entity per alert instead of 3 separate switches
- **67% Fewer Entities**: Cleaner entity list, better performance
- **Modern HA 2026.2 Patterns**: Follows latest Home Assistant best practices
- **Simplified Config Flow**: Removed Global Settings Hub requirement
- **Better UX**: Single dropdown for state management instead of 3 toggles
- **Full Local Development**: Docker-based HA environment for fast iteration

### Migration from v3.x

If you're upgrading from v3.x, you'll need to update automations:

**Old (v3.x):**
```yaml
service: switch.turn_on
target:
  entity_id: switch.door_alert_acknowledged
```

**New (v4.0.0):**
```yaml
service: select.select_option
data:
  entity_id: select.door_alert_state
  option: acknowledged
```

**Available States:**
- `active` - Alert is actively triggered
- `acknowledged` - Alert acknowledged (prevents escalation)
- `snoozed` - Alert temporarily silenced
- `resolved` - Alert marked as resolved

## Features

### Smart Alert Triggers
- **Simple**: Entity state matching (door == open)
- **Template**: Jinja2 expressions for complex logic
- **Logical**: Combine multiple conditions with AND/OR/NOT

### Alert State Management
- Unified state control via select entity
- Automatic state synchronization
- Snooze with configurable duration
- Escalation prevention when acknowledged

### Flexible Actions
- Execute Home Assistant actions on trigger
- Separate actions for acknowledge, snooze, resolve
- Escalation actions for unacknowledged alerts

### Notification Profiles
- Reusable notification templates
- Profile-based action execution
- Group-level profile management

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the 3 dots menu → Custom repositories
4. Add: `https://github.com/issmirnov/emergency_alerts`
5. Category: Integration
6. Install "Emergency Alerts"
7. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/emergency_alerts` to your HA config directory
2. Restart Home Assistant

## Quick Start

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Emergency Alerts"
3. Follow the setup wizard to create an Alert Group
4. Add alerts using the unified form
5. Configure actions and notification profiles

## Configuration

### Creating Alerts

The integration uses a smart single-page form that adapts based on your trigger type:

**Simple Trigger:**
- Select an entity
- Choose the target state
- Done!

**Template Trigger:**
- Write a Jinja2 template
- Returns true when alert should trigger

**Logical Trigger:**
- Combine multiple conditions
- Use AND/OR/NOT operators
- Build complex alert logic

### State Management

Each alert provides a select entity with these states:

- **active**: Alert is currently triggered
- **acknowledged**: User acknowledged, escalation prevented
- **snoozed**: Temporarily silenced (auto-expires)
- **resolved**: Marked as complete

Change state using:
```yaml
service: select.select_option
data:
  entity_id: select.my_alert_state
  option: acknowledged
```

### Actions

Configure actions for different events:

- **on_trigger**: When alert activates
- **on_acknowledged**: When alert is acknowledged
- **on_snoozed**: When alert is snoozed
- **on_resolved**: When alert is resolved
- **on_escalation**: When alert escalates (unacknowledged)

Example:
```yaml
on_trigger:
  - service: notify.mobile_app
    data:
      message: "Alert triggered!"
```

## Development

### Local Testing Environment

Fast iteration with Docker-based HA instance:

```bash
# Start local HA instance (port 8123)
./dev_tools/local-dev.sh start

# View logs in real-time
./dev_tools/local-dev.sh logs

# Restart after code changes (3 seconds)
./dev_tools/local-dev.sh restart

# Run unit tests
./dev_tools/local-dev.sh test

# Clean slate (delete all data)
./dev_tools/local-dev.sh clean
```

Benefits:
- No HACS redownload cycle
- Changes visible in seconds
- Full debug logging
- Test entities pre-configured
- Real HA environment

See `dev_tools/README_DEV.md` for details.

### Running Tests

```bash
python dev_tools/test_runner.py
```

Tests cover:
- Trigger evaluation (simple, template, logical)
- Config flow validation
- State machine transitions
- Import validation
- Translation placeholder validation

## Architecture

### Core Components

- **binary_sensor.py**: Alert trigger evaluation and state tracking
- **select.py**: Unified state control entity
- **sensor.py**: Status and metrics reporting
- **config_flow.py**: Setup wizard and configuration UI
- **core/**: Modular trigger evaluator and action executor

### State Machine

The select entity manages alert states:

```
active → acknowledged → active
  ↓          ↓
snoozed → resolved
```

State changes are mutually exclusive and synchronized with the binary sensor.

## Support

- **Issues**: https://github.com/issmirnov/emergency_alerts/issues
- **Documentation**: See CHANGELOG.md for version history

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## License

MIT License - See LICENSE file for details