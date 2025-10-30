# E2E Tests for Emergency Alerts

End-to-end tests for the Emergency Alerts integration and Lovelace card.

## Overview

These tests verify that the integration and card work together correctly:
- ✅ Card renders and displays alerts
- ✅ Clicking switches updates backend state
- ✅ Backend state changes update card UI
- ✅ Mutual exclusivity is enforced
- ✅ Status badges display correctly

## Quick Start

### Prerequisites

1. **Devcontainer setup** (automatic):
   - Open project in VS Code with Dev Containers extension
   - Container will auto-install Node.js, Playwright, and dependencies

2. **Or manual setup**:
   ```bash
   # Install Node.js 18+
   # Install dependencies
   cd e2e-tests
   npm install
   npx playwright install --with-deps chromium
   ```

### Running Tests

From project root:

```bash
# Run all tests
./scripts/run-e2e.sh

# Run in headed mode (see browser)
./scripts/run-e2e.sh --headed

# Run in debug mode (pause on failure)
./scripts/run-e2e.sh --debug

# Run in UI mode (interactive time-travel debugging)
./scripts/run-e2e.sh --ui

# Run specific test
./scripts/run-e2e.sh --grep "smoke"

# Generate test report
cd e2e-tests && npm run report
```

## Test Structure

```
e2e-tests/
├── tests/                       # Test suites
│   ├── 01-smoke.spec.ts        # Basic functionality tests
│   └── 02-integration.spec.ts  # Integration tests
├── helpers/                     # Test utilities
│   ├── ha-api.ts               # Home Assistant REST API client
│   ├── alert-helpers.ts        # Alert-specific helpers
│   ├── global-setup.ts         # Pre-test setup
│   └── global-teardown.ts      # Post-test cleanup
├── fixtures/                    # Test data (future)
├── reports/                     # Test reports (generated)
├── .screenshots/                # Named screenshots
└── test-results/                # Per-test artifacts
```

## Writing Tests

### Basic Test

```typescript
import { test, expect } from '@playwright/test';
import { createHAAPI } from '../helpers/ha-api';
import { createAlertHelpers } from '../helpers/alert-helpers';

test('My test', async ({ page, request }) => {
  // Set up helpers
  const haApi = createHAAPI(request);
  const alertHelpers = createAlertHelpers(page, haApi);

  // Navigate to dashboard
  await alertHelpers.navigateToEmergencyDashboard();

  // Interact with alert
  await alertHelpers.acknowledgeAlert('test_alert');

  // Verify backend state
  const state = await haApi.getState('switch.emergency_test_alert_acknowledged');
  expect(state.state).toBe('on');
});
```

### Available Helpers

**HA API (`ha-api.ts`)**:
- `getAllStates()` - Get all entity states
- `getState(entityId)` - Get specific entity
- `callService(domain, service, data)` - Call HA service
- `waitForState(entityId, state, timeout)` - Wait for state change
- `getEmergencyAlerts()` - Find all emergency alert entities

**Alert Helpers (`alert-helpers.ts`)**:
- `navigateToEmergencyDashboard()` - Go to alerts dashboard
- `acknowledgeAlert(alertId)` - Click acknowledge switch
- `snoozeAlert(alertId)` - Click snooze switch
- `resolveAlert(alertId)` - Click resolve switch
- `getAlertCard(alertId)` - Get alert card locator
- `screenshotAlert(alertId, name)` - Take alert screenshot

## Debugging

### View Test Report
```bash
cd e2e-tests
npm run report
# Opens HTML report with videos, screenshots, traces
```

### LLM Debugging
See [README-LLM-DEBUGGING.md](./README-LLM-DEBUGGING.md) for comprehensive guide on:
- Inspecting test artifacts
- Reading screenshots and traces
- Checking HA state via API
- Common debugging patterns

### Common Issues

**Tests fail with "HA not running"**:
```bash
# Check HA status
curl http://localhost:8123

# Start HA manually
hass --config ./config
```

**Card not found**:
```bash
# Build and deploy card
cd ../lovelace-emergency-alerts-card
npm run build
cp dist/emergency-alerts-card.js ../emergency-alerts-integration/config/www/
```

**Entity not found**:
- Ensure at least one test alert is configured in HA
- Check HA logs: `tail -f config/home-assistant.log`
- Verify integration is loaded: `curl http://localhost:8123/api/states | jq '.[] | select(.entity_id | contains("emergency"))'`

## CI Integration

Tests run automatically in GitHub Actions:
- On every push/PR
- Uses same devcontainer environment
- Uploads artifacts (screenshots, videos, traces) on failure
- Blocks merge if tests fail

See `.github/workflows/e2e-tests.yml` (to be added).

## Architecture

### Test Execution Flow

1. **Global Setup** (`helpers/global-setup.ts`):
   - Verify HA is running
   - Check integration is loaded
   - Verify card is available

2. **Before Each Test**:
   - Reset switch states to off
   - Navigate to clean dashboard

3. **Test Execution**:
   - Interact with page (clicks, form fills)
   - Verify UI changes
   - Check backend state via API

4. **After Each Test**:
   - Capture screenshot on failure
   - Record video on failure
   - Save trace for time-travel debugging

5. **Global Teardown** (`helpers/global-teardown.ts`):
   - Cleanup test data (future)

### Key Features

**LLM-Friendly**:
- All artifacts are files on disk
- Screenshots for visual inspection
- Traces with full execution data
- Chrome DevTools Protocol access on port 9222
- Comprehensive logging

**Fast Feedback**:
- Tests run in ~30 seconds
- Parallel execution (when stable)
- Smart waits (no arbitrary sleeps)

**Reliable**:
- Automatic retries in CI
- Real Home Assistant instance (not mocked)
- Same environment locally and in CI

## Contributing

When adding new tests:
1. Follow existing test patterns
2. Use helper functions (don't repeat selectors)
3. Add descriptive test names
4. Include debug screenshots for complex flows
5. Document new helper functions

## License

Same as main project (MIT).
