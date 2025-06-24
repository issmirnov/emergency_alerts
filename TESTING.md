# Emergency Alerts Integration - Testing Guide

This document describes the comprehensive testing framework for the Emergency Alerts integration, covering both backend (Home Assistant integration) and frontend (Lovelace card) components.

## 📋 Overview

The testing suite includes:
- **Backend Unit Tests**: Python/pytest for integration logic
- **Frontend Unit Tests**: Jest/TypeScript for card functionality  
- **Integration Tests**: Cross-component sanity checks
- **CI/CD Pipeline**: Automated testing on GitHub Actions

## 🚀 Quick Start

### Run All Tests
```bash
./run_tests.sh
```

### Run Specific Test Suites
```bash
# Backend only
./run_tests.sh --backend-only

# Frontend only  
./run_tests.sh --frontend-only

# Skip linting
./run_tests.sh --skip-lint
```

## 🔧 Setup Requirements

### Backend Testing
- Python 3.9+ 
- pytest and Home Assistant test dependencies
- Install: `pip install -r custom_components/emergency_alerts/test_requirements.txt`

### Frontend Testing
- Node.js 16+
- Jest and testing utilities
- Install: `cd lovelace-emergency-alerts-card && npm install`

## 📦 Backend Tests

Located in: `custom_components/emergency_alerts/tests/`

### Test Structure
```
tests/
├── __init__.py
├── conftest.py          # Test fixtures and configuration
├── test_init.py         # Integration setup/teardown
├── test_binary_sensor.py # Alert entity logic
└── test_config_flow.py  # UI configuration flow
```

### What's Tested

#### Integration Setup (`test_init.py`)
- ✅ Config entry setup and teardown
- ✅ Service registration (`emergency_alerts.acknowledge`)
- ✅ Platform forwarding (binary_sensor, sensor)
- ✅ Multiple config entries handling

#### Binary Sensor Logic (`test_binary_sensor.py`)
- ✅ **Simple Triggers**: Entity state monitoring
- ✅ **Template Triggers**: Jinja template evaluation
- ✅ **Logical Triggers**: AND conditions across entities
- ✅ **Acknowledgment**: Alert acknowledgment workflow
- ✅ **Action Execution**: on_triggered/on_cleared/on_escalated
- ✅ **State Attributes**: Proper attribute exposure
- ✅ **Time Tracking**: first_triggered, last_cleared timestamps

#### Config Flow (`test_config_flow.py`)
- ✅ **UI Forms**: All trigger type configurations
- ✅ **Data Validation**: Input validation and defaults
- ✅ **Action Configuration**: Service call definitions
- ✅ **Error Handling**: Invalid configurations

### Test Fixtures
```python
# Simple trigger alert
@pytest.fixture
def mock_config_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor",
            "trigger_state": "on",
            "severity": "warning",
            "group": "security"
        }
    )
```

### Running Backend Tests
```bash
cd custom_components/emergency_alerts
python -m pytest tests/ -v --cov=. --cov-report=html
```

## 🎨 Frontend Tests

Located in: `lovelace-emergency-alerts-card/src/__tests__/`

### Test Structure
```
src/
├── __tests__/
│   └── emergency-alerts-card.test.ts
├── test-setup.ts        # Jest configuration
└── emergency-alerts-card.ts
```

### What's Tested

#### Card Functionality
- ✅ **Element Creation**: Custom element registration
- ✅ **Configuration**: setConfig validation and defaults
- ✅ **Rendering**: Shadow DOM and template rendering
- ✅ **Alert Grouping**: Severity-based alert organization
- ✅ **Time Formatting**: "X minutes ago" display logic
- ✅ **User Interactions**: Acknowledge button functionality
- ✅ **Service Calls**: Home Assistant service integration
- ✅ **Error Handling**: Missing hass, empty alerts

#### UI Components
- ✅ **Summary Header**: Active alert counts
- ✅ **Severity Icons**: Critical/warning/info icons
- ✅ **Color Coding**: Severity-based styling
- ✅ **Acknowledged State**: Visual acknowledgment feedback

### Mock Data
```typescript
const mockAlerts = {
  'binary_sensor.emergency_door_open': {
    entity_id: 'binary_sensor.emergency_door_open',
    state: 'on',
    attributes: {
      friendly_name: 'Emergency: Door Open',
      severity: 'critical',
      group: 'security',
      acknowledged: false,
      first_triggered: '2023-01-01T12:00:00Z',
    },
  },
  // ... more mock alerts
};
```

### Running Frontend Tests
```bash
cd lovelace-emergency-alerts-card
npm test                    # Run once
npm run test:watch          # Watch mode
npm test -- --coverage     # With coverage
```

## 🔗 Integration Tests

### File Structure Validation
Verifies all required files exist:
- Backend: `__init__.py`, `manifest.json`, `binary_sensor.py`, etc.
- Frontend: `emergency-alerts-card.ts`, `hacs.json`

### Python Import Validation
```python
# Verifies imports work correctly
from const import DOMAIN
from binary_sensor import EmergencyBinarySensor
from config_flow import EmergencyConfigFlow
```

### TypeScript Compilation
```bash
npx tsc --noEmit  # Check TypeScript without output
```

## 🎯 Test Coverage Goals

### Backend Coverage Targets
- **Overall**: >90%
- **Critical Paths**: 100% (trigger evaluation, acknowledgment)
- **Config Flow**: >85%
- **Error Handling**: >80%

### Frontend Coverage Targets
- **Component Logic**: >85%
- **User Interactions**: 100%
- **Rendering**: >80%
- **Service Integration**: 100%

## 🚦 CI/CD Pipeline

### GitHub Actions Workflow
Located in: `.github/workflows/test.yml`

The workflow automatically sets up virtual environments and runs comprehensive tests on every push and pull request.

#### Test Matrix
- **Python**: 3.9, 3.10, 3.11
- **Node.js**: 16, 18, 20

#### Pipeline Jobs

1. **Backend Tests**: Tests the Home Assistant integration
   - Sets up Python virtual environment automatically
   - Installs test dependencies via pip
   - Runs validation script (`validate_integration.py`)
   - Executes pytest with coverage reporting
   - Uploads coverage to Codecov

2. **Frontend Tests**: Tests the Lovelace card
   - Sets up Node.js environment with npm caching
   - Installs dependencies with `npm ci`
   - Checks TypeScript compilation
   - Runs Jest tests with coverage
   - Uploads coverage to Codecov

3. **Integration Tests**: Full end-to-end testing
   - Combines both Python and Node.js environments
   - Runs complete test suite via `run_tests.sh`
   - Builds frontend for distribution
   - Archives build artifacts for deployment

4. **Lint and Format**: Code quality checks
   - **Python**: Black formatting, isort imports, flake8 linting, mypy type checking
   - **TypeScript**: ESLint linting, Prettier formatting
   - Continues on non-critical errors to provide full feedback

#### Virtual Environment Handling
The workflow properly handles virtual environments:
```yaml
- name: Create virtual environment
  run: |
    python -m venv venv
    source venv/bin/activate
    echo "VIRTUAL_ENV=$VIRTUAL_ENV" >> $GITHUB_ENV
    echo "$VIRTUAL_ENV/bin" >> $GITHUB_PATH
```

#### Coverage Reporting
- Codecov integration for coverage tracking
- Separate coverage reports for backend and frontend
- HTML reports generated locally for development
- Coverage badges available for README

## 🐛 Debugging Tests

### Backend Debugging
```bash
# Run specific test
python -m pytest tests/test_binary_sensor.py::test_simple_trigger_evaluation -v

# Debug with pdb
python -m pytest tests/test_binary_sensor.py -v --pdb

# Show print statements
python -m pytest tests/test_binary_sensor.py -v -s
```

### Frontend Debugging
```bash
# Run specific test
npm test -- --testNamePattern="should handle acknowledge"

# Debug mode
npm test -- --debug

# Verbose output
npm test -- --verbose
```

### Common Issues

#### Backend
- **Import Errors**: Ensure `PYTHONPATH` includes current directory
- **Fixture Issues**: Check `conftest.py` fixture definitions
- **Mock Problems**: Verify Home Assistant mock objects

#### Frontend
- **Jest Configuration**: Check `jest.config.js` setup
- **TypeScript Errors**: Verify `tsconfig.json` types
- **DOM Issues**: Ensure `jsdom` environment configured

## 📊 Test Reports

### Coverage Reports
```bash
# Backend HTML report
open custom_components/emergency_alerts/htmlcov/index.html

# Frontend coverage
open lovelace-emergency-alerts-card/coverage/lcov-report/index.html
```

### Test Output
- **JUnit XML**: For CI integration
- **Terminal**: Colored output with progress
- **HTML**: Detailed coverage visualization

## 🔄 Continuous Testing

### Pre-commit Hooks (Recommended)
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Watch Mode Development
```bash
# Backend: Re-run tests on file changes
python -m pytest tests/ --watch

# Frontend: Jest watch mode
npm run test:watch
```

## 📈 Performance Testing

### Backend Performance
- Entity update frequency testing
- Memory usage monitoring  
- Service call latency measurement

### Frontend Performance
- Rendering performance with many alerts
- DOM update efficiency
- Memory leak detection

## 🎯 Test Strategy

### Test Pyramid
1. **Unit Tests (70%)**: Individual component testing
2. **Integration Tests (20%)**: Cross-component interaction
3. **E2E Tests (10%)**: Full user workflow (future)

### Testing Philosophy
- **Fast Feedback**: Quick test execution
- **Reliable**: Deterministic, no flaky tests
- **Maintainable**: Clear, readable test code
- **Comprehensive**: High coverage of critical paths

## 🚀 Future Enhancements

### Planned Additions
- **E2E Testing**: Playwright/Cypress for full workflows
- **Performance Testing**: Load testing for many alerts
- **Visual Regression**: Screenshot comparison testing
- **Accessibility Testing**: A11y compliance verification
- **Property-based Testing**: Hypothesis for edge cases

---

## 💡 Tips for Contributors

1. **Write Tests First**: TDD approach for new features
2. **Mock External Dependencies**: Isolate units under test
3. **Test Edge Cases**: Empty states, error conditions
4. **Keep Tests Simple**: One assertion per test when possible
5. **Use Descriptive Names**: Test names should explain intent
6. **Update Tests with Changes**: Keep tests synchronized with code

For questions about testing, check the [GitHub Issues](https://github.com/issmirnov/emergency_alerts/issues) or [Discussions](https://github.com/issmirnov/emergency_alerts/discussions). 