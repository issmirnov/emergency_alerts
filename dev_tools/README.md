# Development Tools

Local development and testing tools for the Emergency Alerts integration.

## Quick Start

```bash
# Run tests without HA installation
python dev_tools/test_runner.py

# Run specific test
python dev_tools/test_runner.py --test config_flow

# Run with live reload
python dev_tools/test_runner.py --watch
```

## Components

- `mock_ha/` - Mock Home Assistant environment
- `test_fixtures/` - Sample data for testing
- `sample_alerts/` - Example alert configurations
- `test_runner.py` - Fast local test execution

## Testing Without Live HA Instance

The dev_tools setup provides a complete mock HA environment allowing you to:
- Test config flows interactively
- Validate trigger evaluations
- Test state machine transitions
- Run integration tests
- All without Docker or real HA installation

## Integration with Lovelace Card

The testing framework can also load and test the lovelace card located at:
`/home/vania/Projects/1.Personal/home_assistant/lovelace-emergency-alerts-card`