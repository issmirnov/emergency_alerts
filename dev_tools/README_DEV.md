## Local Development Setup

Fast iteration loop for Emergency Alerts integration development.

## Quick Start

```bash
# Start local HA instance with integration auto-mounted
./dev_tools/local-dev.sh start

# Open http://localhost:8123
# Create user account on first run
# Add Emergency Alerts integration
```

## Architecture

The Docker Compose setup provides:

1. **Full Home Assistant Instance** (port 8123)
   - Custom integration auto-mounted from `./custom_components`
   - Persistent config in `./dev_tools/ha-config`
   - Test entities pre-configured

2. **VSCode Server** (port 8124, optional)
   - Edit files in browser
   - Password: `dev`

## Development Workflow

### Make Changes
```bash
# 1. Edit code in custom_components/emergency_alerts/
vim custom_components/emergency_alerts/config_flow.py

# 2. Restart HA to reload
./dev_tools/local-dev.sh restart

# 3. Test in web UI
# Changes appear immediately after restart
```

### Debug
```bash
# View live logs (see DEBUG messages)
./dev_tools/local-dev.sh logs

# Open shell in container
./dev_tools/local-dev.sh shell
```

### Clean Slate
```bash
# Delete ALL data (config entries, DB, etc.)
./dev_tools/local-dev.sh clean

# Then start fresh
./dev_tools/local-dev.sh start
```

## Test Entities

Pre-configured test entities for alert testing:

- `input_boolean.test_door` - Door sensor simulation
- `input_boolean.test_window` - Window sensor
- `input_boolean.test_motion` - Motion sensor
- `input_number.test_temperature` - Temperature sensor (0-100°C)
- `input_number.test_humidity` - Humidity sensor (0-100%)

## Example Test Scenarios

### Simple Alert
1. Create alert group
2. Add alert: `input_boolean.test_door` == `on`
3. Toggle door in UI
4. See alert trigger

### Template Alert
```jinja2
{{ states('input_number.test_temperature')|float > 25 }}
```

### Logical Alert
- Condition 1: `input_boolean.test_door` == `on`
- Condition 2: `input_number.test_temperature` > `30`
- Operator: `AND`

## Debugging Tips

### Enable Debug Logging
Already enabled in `dev_tools/ha-config/configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.emergency_alerts: debug
```

### Inspect Config Entries
```python
# In HA shell: ./dev_tools/local-dev.sh shell
# Then in Python:
>>> from homeassistant.config_entries import async_entries_for_domain
>>> entries = async_entries_for_domain(hass, "emergency_alerts")
>>> print(entries[0].data)
```

### Watch File Changes
The integration auto-reloads on HA restart. For instant feedback:
```bash
# Terminal 1: Edit files
vim custom_components/emergency_alerts/config_flow.py

# Terminal 2: Watch logs
./dev_tools/local-dev.sh logs

# Terminal 3: Quick restart when ready
./dev_tools/local-dev.sh restart
```

## Migration Testing

The integration includes auto-migration for old config entries:

```python
# In __init__.py:
if hub_type == "group" and "group" not in entry.data:
    # Auto-adds missing 'group' field
    # Logs: [MIGRATION] Adding group field
```

Watch logs for migration messages:
```bash
./dev_tools/local-dev.sh logs | grep MIGRATION
```

## Benefits vs Remote Testing

- ✅ Instant feedback (no HACS redownload)
- ✅ Full HA API available
- ✅ Real database persistence
- ✅ Test with real entities
- ✅ Debug logging visible
- ✅ Shell access for inspection
- ✅ Clean slate in seconds

## Alternative: Devcontainer

For core HA development (not needed for integrations):

```bash
# Use VSCode with Dev Containers extension
# Open project in container
# Full HA source code available
```

See `.devcontainer/` for configuration (if needed).