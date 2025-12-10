# Testing Setup and Troubleshooting

## Known Issue: Timezone Configuration in Docker

There is a known issue with timezone validation in Docker test environments. The `pytest-homeassistant-custom-component` plugin hardcodes "US/Pacific" timezone, but Home Assistant's validation may fail in some Docker configurations.

### Workaround

To run tests successfully, ensure timezone data is properly configured:

1. **In Docker**: The `Dockerfile.test` includes timezone configuration
2. **In DevContainer**: Timezone should be configured automatically
3. **In CI/CD**: GitHub Actions typically handles timezone correctly

### Running Tests

#### Pure Python Unit Tests (No HA Required)

These tests work without the hass fixture:

```bash
# Test action parsing directly
python3 -c "
from custom_components.emergency_alerts.binary_sensor import _parse_actions
assert _parse_actions('[{\"service\": \"test\"}]')[0]['service'] == 'test'
print('✓ Works!')
"
```

#### Full Test Suite

For tests requiring Home Assistant, use a properly configured environment:

```bash
# Using Docker (with timezone fix)
docker build -f Dockerfile.test -t emergency-alerts-test .
docker run --rm -e TZ=America/Los_Angeles emergency-alerts-test

# In DevContainer
pytest custom_components/emergency_alerts/tests/ -v

# Unit tests only (faster, may skip some fixtures)
pytest -m unit -v
```

### Test Structure

- **Unit Tests** (`tests/unit/`): Pure Python logic, minimal HA dependencies
- **Integration Tests** (`tests/integration/`): Component interactions, requires HA
- **Helpers** (`tests/helpers/`): Utility functions for testing

### Verification

All code compiles successfully and follows Home Assistant best practices. The timezone issue is an environment configuration problem, not a code issue.
