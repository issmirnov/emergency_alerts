# Testing Guide

This document describes the simplified testing approach for the Emergency Alerts integration.

## Testing Philosophy

We use a **hybrid testing approach** that balances comprehensive coverage with maintainability:

1. **Hassfest** - Validates manifest and integration structure
2. **Pytest** - Unit and integration tests for business logic
3. **Minimal E2E** - Critical user flows and translation validation
4. **Docker Compose** - Manual testing with local Home Assistant

## Quick Start

```bash
# Run all tests locally
pytest custom_components/emergency_alerts/tests/ -v

# Validate translations are in sync
python validate_translations.py

# Start local HA for manual testing
./dev_tools/local-dev.sh start

# Run E2E tests (requires local HA running)
cd e2e-tests && npm test
```

## Test Layers

### 1. Hassfest Validation (CI)

Hassfest validates the integration structure and manifest:

- ✅ Manifest.json structure and required fields
- ✅ Integration metadata
- ✅ Code quality standards
- ✅ Home Assistant compatibility

**Runs:** Automatically in CI on every push/PR

**Local testing:** Install HA and run:
```bash
pip install homeassistant
python -m script.hassfest --integration-path custom_components/emergency_alerts
```

### 2. Translation Sync Validation

Ensures `strings.json` and `translations/en.json` stay in sync:

```bash
python validate_translations.py
```

**Why:** Translation mismatches cause runtime errors in the config flow UI that are hard to debug. This validation catches them early.

**Runs:** Automatically in CI and as a pytest fixture

**Fix:** If validation fails:
1. Check differences in the validation output
2. Update `translations/en.json` to match `strings.json`
3. Or update `strings.json` if translation was incorrect
4. Keep both files in sync for all future changes

### 3. Pytest - Unit & Integration Tests

Fast, reliable tests for business logic:

```bash
# Run all tests
pytest custom_components/emergency_alerts/tests/ -v

# Run specific test file
pytest custom_components/emergency_alerts/tests/test_config_flow.py -v

# Run with coverage
pytest custom_components/emergency_alerts/tests/ --cov=custom_components/emergency_alerts

# Run unit tests only
pytest custom_components/emergency_alerts/tests/unit/ -v

# Run integration tests only
pytest custom_components/emergency_alerts/tests/integration/ -v
```

**Test Structure:**
- `tests/unit/` - Pure Python logic, minimal HA dependencies
- `tests/integration/` - Component interactions, requires HA fixtures
- `tests/conftest.py` - Shared fixtures and translation error detection

**Translation Error Detection:**
The `conftest.py` includes an autouse fixture that automatically fails tests if translation errors are detected in logs. This catches missing keys at test time.

### 4. E2E Tests (Playwright)

Minimal end-to-end tests for critical user flows:

```bash
cd e2e-tests

# Install dependencies (first time)
npm install

# Run E2E tests (requires local HA on port 8123)
npm test

# Run specific test
npm test -- 03-config-flow-add-alert

# Run in headed mode (see browser)
npm test -- --headed

# Debug mode
npm test -- --debug
```

**What we test:**
- ✅ Add alert config flow (catches translation errors)
- ✅ Card functionality (state changes, button clicks)
- ✅ Console error detection (translation failures)

**Prerequisites:**
1. Local HA instance running: `./dev_tools/local-dev.sh start`
2. Integration installed and configured
3. At least one test alert for integration tests

**Translation Detection:**
E2E tests monitor browser console for translation errors and fail if any are detected. This catches runtime translation issues that pytest might miss.

### 5. Manual Testing (Docker Compose)

Local Home Assistant instance for manual testing and debugging:

```bash
# Start HA with dev/dev auth
./dev_tools/local-dev.sh start

# View logs (check for translation errors)
./dev_tools/local-dev.sh logs

# Restart HA after code changes
./dev_tools/local-dev.sh restart

# Wipe all data and start fresh
./dev_tools/local-dev.sh clean

# Stop HA
./dev_tools/local-dev.sh stop
```

**Access:**
- Web UI: http://localhost:8123
- Login: `dev` / `dev`
- VSCode: http://localhost:8124 (password: `dev`)

**Integration auto-mounted from:**
- `./custom_components/` → `/config/custom_components/`

**Config persisted in:**
- `./dev_tools/ha-config/`

**Manual Testing Workflow:**
1. Start HA: `./dev_tools/local-dev.sh start`
2. Login and add integration
3. Create test alerts
4. Test config flows, state changes, actions
5. Check logs for translation errors: `./dev_tools/local-dev.sh logs | grep -i translation`

## Common Issues

### Translation Errors

**Symptom:** Form fields show as "translation_key.path" instead of human text

**Cause:** Mismatch between `strings.json` and `translations/en.json`

**Fix:**
```bash
# Check for differences
python validate_translations.py

# Sync files (copy strings.json to translations/en.json)
cp custom_components/emergency_alerts/strings.json \
   custom_components/emergency_alerts/translations/en.json
```

### Pytest Import Errors

**Symptom:** `ModuleNotFoundError` when running pytest

**Fix:** Install test requirements:
```bash
pip install -r custom_components/emergency_alerts/test_requirements.txt
```

### E2E Tests Fail

**Symptom:** E2E tests can't connect to HA or find elements

**Fix:**
1. Ensure HA is running: `./dev_tools/local-dev.sh logs`
2. Check HA is on port 8123: `curl http://localhost:8123`
3. Verify integration is installed in HA
4. Check test selectors match current HA version

### Hassfest Errors

**Symptom:** CI fails on hassfest validation

**Fix:** Check manifest.json for:
- Required fields (domain, name, version, etc.)
- Valid version format
- Correct dependencies
- Valid IoT class if specified

## CI/CD Pipeline

Our GitHub Actions workflow runs:

1. **Hassfest Validation** - Integration structure
2. **Translation Validation** - Sync check
3. **HACS Validation** - Community store standards
4. **Backend Tests** - Pytest with coverage
5. **Lint & Format** - Code quality checks

All checks must pass before merging.

## Adding New Tests

### Pytest Test

```python
# custom_components/emergency_alerts/tests/test_new_feature.py
from homeassistant.core import HomeAssistant
import pytest

async def test_new_feature(hass: HomeAssistant):
    """Test description."""
    # Setup
    # ...

    # Act
    # ...

    # Assert
    assert expected == actual
```

### E2E Test

```typescript
// e2e-tests/tests/04-new-flow.spec.ts
import { test, expect } from '@playwright/test';

test('should test new user flow', async ({ page }) => {
  await page.goto('/your-page');

  // Interact with UI
  await page.locator('button').click();

  // Assert
  await expect(page.locator('.result')).toBeVisible();
});
```

## Best Practices

1. **Keep strings.json and translations/en.json in sync**
   - Update both files together
   - Run `python validate_translations.py` before committing

2. **Run tests before committing**
   ```bash
   pytest custom_components/emergency_alerts/tests/ -v
   python validate_translations.py
   ```

3. **Test manually before releasing**
   - Start local HA
   - Test all config flows
   - Check logs for errors

4. **Use type hints in Python tests**
   - Makes tests self-documenting
   - Catches type errors early

5. **E2E tests should be resilient**
   - Use flexible selectors (text matching)
   - Handle timing with proper waits
   - Don't over-test UI details

## Resources

- [Home Assistant Testing Docs](https://developers.home-assistant.io/docs/development_testing)
- [Hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [Playwright Docs](https://playwright.dev)
