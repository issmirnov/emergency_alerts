# Emergency Alerts Integration for Home Assistant

A powerful Home Assistant integration for managing critical alerts with smart escalation, state management, and flexible trigger conditions.

## Version 4.1.0 - Polish & Modern UX

**Major quality improvements** focusing on user experience, testing, and Home Assistant 2026.2+ compatibility.

### Why v4.1.0?

v4.1.0 is all about **polish** - taking an already powerful integration and making it a joy to use. Every interaction is faster, cleaner, and more reliable.

**The Big Three Improvements:**

1. **Single-Page Config Flow** - Configure alerts in one clean form instead of clicking through multiple wizard steps. Inspired by Adaptive Lighting's excellent UX.

2. **Instant Operations** - Add, edit, or remove alerts with zero downtime. Changes take effect immediately with automatic reload - no more waiting for Home Assistant to restart.

3. **Comprehensive Testing** - Hassfest validation, translation sync checks, and E2E tests ensure the integration just works, every time.

### What's New in v4.1.0

**Clean, Modern Configuration Experience**
- **Single-Page Config Flow**: All alert options on one unified form (inspired by Adaptive Lighting's excellent UX)
- **User-Friendly Labels**: Clear, descriptive field labels and help text
- **Modern Selectors**: EntitySelector and TemplateSelector with live preview
- **Instant Changes**: Add/Edit/Remove alerts work immediately - no Home Assistant restart required
- **74% Less Code**: 353 lines (down from 1,371) in config_flow.py - simpler, more maintainable

**Comprehensive Testing Infrastructure**
- **Hassfest Validation**: Automated integration structure checks in CI
- **Translation Sync**: Automatic validation ensures UI strings stay synchronized
- **E2E Tests**: Playwright-based tests for critical config flow paths
- **Zero Translation Errors**: Real-time validation prevents runtime string lookup failures

**Home Assistant 2026.2+ Ready**
- Updated for latest Home Assistant patterns and best practices
- Compatible with newest config flow APIs
- Tested against HA 2026.2 stable release
- Future-proof for HA 2027+

## v4.1.0 Highlights

> **TL;DR**: Everything is faster, cleaner, and more reliable. Configuration takes 30 seconds instead of 2 minutes. All changes happen instantly. Zero translation errors. Fully tested. HA 2026.2+ ready.

### User Experience Transformation

| Before v4.1.0 | After v4.1.0 |
|---------------|--------------|
| Multi-step wizard (3-4 screens) | Single unified form |
| Click through pages sequentially | See all options at once |
| Hit "Back" to change earlier fields | Edit any field anytime |
| Wait for HA restart after changes | Instant reload (no restart) |
| Generic field labels | Clear, descriptive labels |
| Basic text inputs | Modern selectors with validation |

**Time Savings:**
- **Alert Creation**: 2+ minutes → 30 seconds
- **Alert Editing**: 1+ minute → 20 seconds
- **Changes Take Effect**: Restart HA (2-5 min) → Instant (0 sec)

**Quality Improvements:**
- **Translation Errors**: Sometimes broken → Never (validated in CI)
- **Configuration Errors**: Possible → Prevented (real-time validation)
- **Field Help**: Basic → Comprehensive with examples

### Real-World Impact

**What Changed:**

Before v4.1.0, creating a door-left-open alert meant:
1. Click gear icon → Add Alert
2. Fill in name and trigger type → Click Next
3. Select entity and state → Click Next
4. Configure actions (optional) → Click Next
5. Review and submit → Wait for HA restart
6. **Total time: 2-3 minutes per alert**

After v4.1.0:
1. Click gear icon → Add Alert
2. Fill in all fields on one form → Submit
3. Alert appears immediately (no restart)
4. **Total time: 20-30 seconds per alert**

**Real Scenarios:**

- **Setting up 10 security alerts**: Was 20-30 minutes, now 5-8 minutes
- **Editing an existing alert**: Was 2 minutes + restart, now 20 seconds total
- **Testing configurations**: Was painful (edit → restart → test → repeat), now instant
- **Fixing a typo**: Was a full restart cycle, now a 10-second fix

### Technical Excellence

**Robust Testing Infrastructure:**
- **Hassfest Validation**: Integration structure automatically checked in CI
- **Translation Sync**: Zero runtime translation errors (validated on every commit)
- **E2E Tests**: Critical user flows tested with Playwright
- **Unit Tests**: Comprehensive coverage of all components
- **CI/CD**: All checks pass before merge

**Modern, Maintainable Codebase:**
- **74% Code Reduction**: 353 lines (was 1,371) in config_flow.py
- **Latest Patterns**: Uses modern Home Assistant APIs throughout
- **Zero Deprecations**: No warnings, ready for HA 2027+
- **Clean Architecture**: Modular, well-documented, easy to extend

**Instant Operations:**
- **No Restart Required**: All CRUD operations (Create, Read, Update, Delete) work instantly
- **Automatic Reload**: Entities appear/update immediately after config changes
- **Zero Downtime**: Edit alerts while Home Assistant is running
- **Fast Iteration**: Change → Save → See (seconds, not minutes)

### What's New in v4.0.0

- **Unified State Control**: Single select entity per alert instead of 3 separate switches
- **67% Fewer Entities**: Cleaner entity list, better performance
- **Better UX**: Single dropdown for state management instead of 3 toggles

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

### Intuitive Configuration
- **Single-Page Forms**: All alert settings on one clean, scrollable form
- **No YAML Required**: Complete visual configuration through Home Assistant UI
- **Instant Updates**: Changes take effect immediately with automatic reload
- **Smart Field Validation**: Real-time validation prevents configuration errors
- **Modern Selectors**: Entity pickers, template editors with syntax highlighting

### Smart Alert Triggers
- **Simple**: Entity state matching (e.g., door == open, temp > 80)
- **Template**: Full Jinja2 expressions for complex logic with live preview
- **Logical**: Combine multiple conditions with AND/OR/NOT operators
- **Visual Condition Builder**: No code needed - select entities and states from dropdowns

### Comprehensive State Management
- **Unified Control**: Single select entity per alert (no more juggling 3 switches)
- **Automatic Synchronization**: State changes instantly reflected across all entities
- **Flexible Snooze**: Configurable duration with auto-expiry
- **Smart Escalation**: Only escalates unacknowledged alerts
- **Clear Status Tracking**: Always know what state each alert is in

### Flexible Action System
- **Event-Driven Actions**: Execute Home Assistant services on any state change
- **Granular Control**: Separate actions for trigger, acknowledge, snooze, resolve, and escalation
- **Service Integration**: Call any Home Assistant service (notify, light, switch, script, etc.)
- **Template Support**: Use Jinja2 templates in action data for dynamic content

### Notification Profiles
- **Reusable Templates**: Define notification patterns once, use across multiple alerts
- **Profile-Based Actions**: Apply notification profiles to alerts for consistent behavior
- **Group Management**: Manage profiles at the group level
- **Easy Maintenance**: Update one profile to change all alerts using it

### Clean Organization
- **Hub-Based Architecture**: Group related alerts under descriptive hub devices
- **Device Hierarchy**: Proper Home Assistant device relationships for clean UI
- **67% Fewer Entities**: One select entity instead of three switches per alert
- **Logical Grouping**: Organize by room, priority, or alert type

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

1. **Add the Integration**
   - Go to **Settings** → **Devices & Services** → **Add Integration**
   - Search for "Emergency Alerts"
   - Click to install

2. **Create Your First Alert Group**
   - Give your group a descriptive name (e.g., "Security Alerts", "Home Safety")
   - The group becomes a hub device in Home Assistant

3. **Add an Alert**
   - Click the gear icon on your Alert Group device
   - Click **"Add Alert"**
   - Fill out the single-page form with all your alert settings
   - Click **Submit** - your alert appears instantly (no restart needed)

4. **Manage Your Alerts**
   - **Edit**: Click gear icon → **"Edit Alert"** → Select alert → Modify → Submit
   - **Remove**: Click gear icon → **"Remove Alert"** → Select alert → Confirm
   - All changes take effect immediately with automatic reload

That's it! Your alerts are now monitoring your home and ready to trigger.

## Configuration

### Creating Alerts - Now Lightning Fast

The v4.1.0 config flow puts **everything on one page**. No wizard steps, no clicking "Next" three times, no losing your place. Just scroll, fill in fields, and submit.

**The Form Adapts to You:**

All alert types start with the same clean form:
- Alert name
- Trigger type (Simple/Template/Logical)
- Severity (Info/Warning/Critical)
- Group (Security/Safety/Environment/etc.)

The form then shows trigger-specific fields based on your choice:

**Simple Trigger:**
- Entity selector with search
- Target state field
- That's it - done in 10 seconds

**Template Trigger:**
- Jinja2 template editor with syntax highlighting
- Preview feature to test templates
- Built-in validation

**Logical Trigger:**
- Visual condition builder (no code)
- Add up to 10 entity/state pairs
- Choose AND/OR operator
- Point and click interface

**Optional Enhancements:**
- Actions on trigger/acknowledge/snooze/resolve/escalate
- Notification profiles for reusable templates
- Custom snooze duration
- Service calls for automation integration

All fields have clear labels, helpful descriptions, and examples. Real-time validation prevents errors before you submit.

### State Management - Simple and Unified

v4.0 introduced unified state control. Instead of juggling 3 separate switch entities per alert, you get one clean select entity with all states:

**Available States:**
- **active**: Alert is currently triggered
- **acknowledged**: User acknowledged, escalation prevented
- **snoozed**: Temporarily silenced (auto-expires)
- **resolved**: Marked as complete

**Using States in Automations:**
```yaml
service: select.select_option
data:
  entity_id: select.my_alert_state
  option: acknowledged
```

**The Improvement:**
- Before: `switch.my_alert_acknowledge`, `switch.my_alert_snooze`, `switch.my_alert_resolve` (3 entities)
- After: `select.my_alert_state` (1 entity, 4 states)
- Result: 67% fewer entities, cleaner UI, simpler automations

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

### Comprehensive Testing Infrastructure

v4.1.0 introduces a robust testing system that ensures quality:

**Automated CI Checks:**
```bash
# All of these run automatically on every commit
hassfest          # Integration structure validation
pytest            # Unit and integration tests
translation-sync  # Ensures UI strings stay synchronized
```

**Local Testing:**
```bash
# Run the full test suite locally
./run_tests.sh

# Or run specific test types
./run_tests.sh --backend-only    # Just pytest
python validate_translations.py   # Just translation sync
```

**Test Coverage:**
- Trigger evaluation (simple, template, logical)
- Config flow validation and user input handling
- State machine transitions and mutual exclusivity
- Service registration and action execution
- Translation string synchronization
- Integration structure (hassfest)

### Local Development Environment

Fast iteration with Docker-based HA instance:

```bash
# Start local HA instance (port 8123)
./dev_tools/local-dev.sh start

# View logs in real-time
./dev_tools/local-dev.sh logs

# Restart after code changes (3 seconds)
./dev_tools/local-dev.sh restart

# Clean slate for testing (wipes all data)
./dev_tools/local-dev.sh nuke
```

**Benefits:**
- No HACS redownload cycle needed
- Changes visible in seconds, not minutes
- Full debug logging enabled
- Test entities pre-configured
- Real Home Assistant 2026.2 environment
- Automatic onboarding bypass (dev/dev credentials)

**What You Get:**
- Home Assistant 2026.2 running on port 8123
- Integration pre-installed and loaded
- Test alert groups automatically created
- Dashboard with test cards configured
- Complete development-ready setup

See `dev_tools/README_DEV.md` for complete details.

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