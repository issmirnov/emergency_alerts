# Emergency Alerts Integration

[![Test Emergency Alerts Integration](https://github.com/issmirnov/emergency-alerts-integration/actions/workflows/test.yml/badge.svg)](https://github.com/issmirnov/emergency-alerts-integration/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/issmirnov/emergency-alerts-integration/branch/main/graph/badge.svg)](https://codecov.io/gh/issmirnov/emergency-alerts-integration)

A comprehensive Home Assistant custom integration for managing emergency alerts and critical notifications.

## Features

- **Multiple Trigger Types**: Simple, template-based, and logical triggers
- **Severity Levels**: Critical, warning, and info classifications
- **Alert Grouping**: Organize alerts by custom groups
- **Acknowledgment System**: Track and manage alert responses
- **Action Automation**: Execute actions on trigger, clear, or escalation
- **Persistent State**: Maintains alert history and timing information
- **HACS Compatible**: Easy installation through Home Assistant Community Store

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the "+" button and search for "Emergency Alerts"
4. Install the integration
5. Restart Home Assistant
6. Add the integration via Settings → Devices & Services

### Manual Installation

1. Copy the `custom_components/emergency_alerts` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services

## Configuration

The integration supports three types of triggers:

### Simple Triggers
Monitor a single entity state:
```yaml
# Example: Door left open
entity_id: binary_sensor.front_door
state: "on"
severity: warning
group: security
```

### Template Triggers
Use Jinja2 templates for complex conditions:
```yaml
# Example: High temperature with low humidity
template: "{{ states('sensor.temperature')|float > 30 and states('sensor.humidity')|float < 20 }}"
severity: critical
group: climate
```

### Logical Triggers
Combine multiple conditions:
```yaml
# Example: Multiple sensors triggered
conditions:
  - entity_id: binary_sensor.motion_kitchen
    state: "on"
  - entity_id: binary_sensor.motion_living_room
    state: "on"
operator: and
severity: info
group: security
```

## Entities Created

For each configured alert, the integration creates:

- **Binary Sensor**: `binary_sensor.emergency_{name}` - Alert state (on/off)
- **Sensor**: `sensor.emergency_{name}_summary` - Alert summary and timing

## Services

- `emergency_alerts.acknowledge` - Acknowledge an active alert
- `emergency_alerts.clear` - Manually clear an alert
- `emergency_alerts.test` - Test an alert configuration

## Frontend Card

For the Lovelace dashboard card, see the separate repository:
[Emergency Alerts Card](https://github.com/issmirnov/lovelace-emergency-alerts-card)

## Development

### Testing

```bash
# Run all tests
./run_tests.sh

# Run validation only
python validate_integration.py

# Run specific test
cd custom_components/emergency_alerts
python -m pytest tests/test_binary_sensor.py -v
```

### Test Coverage

The integration maintains high test coverage:
- Overall: >90%
- Critical paths: 100%
- Config flow: >85%

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## Testing

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- [GitHub Issues](https://github.com/issmirnov/emergency-alerts-integration/issues)
- [Home Assistant Community Forum](https://community.home-assistant.io/)
- [GitHub Discussions](https://github.com/issmirnov/emergency-alerts-integration/discussions) 