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

### Docker Testing
```bash
# Build and run Docker tests
./docker-test.sh

# Debug Docker container
docker run -it --rm emergency-alerts-test bash

# Check container environment
docker run --rm emergency-alerts-test env | grep PYTHON
```

## 🚨 Troubleshooting Guide

This section documents common issues encountered during testing and their solutions, based on real debugging sessions.

### Docker Test Environment Issues

#### Problem 1: Missing Build Dependencies
**Error**: `command 'g++' failed: No such file or directory`

**Symptoms**:
- Python packages like `ciso8601`, `lru-dict`, `pymicro-vad`, `pyspeex-noise` fail to compile
- Docker build succeeds but test execution fails during dependency installation

**Root Cause**: Home Assistant test dependencies require C++ compilation for certain packages

**Solution**: Updated `Dockerfile.test` to include build tools:
```dockerfile
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
```

#### Problem 2: pytest-homeassistant-custom-component Plugin Not Found
**Error**: `ImportError: Error importing plugin "pytest_homeassistant_custom_component.plugin": No module named 'pytest_homeassistant_custom_component.plugin'`

**Symptoms**:
- Package is installed but pytest can't find the plugin
- Tests fail to start with plugin import error
- Issue persists even after package installation

**Root Cause**: Multiple potential causes in Docker environments:
1. Incorrect import paths in test configuration
2. Missing pytest plugin registration
3. PYTHONPATH issues in containerized environment
4. Missing `custom_components/__init__.py` file

**Solutions Applied**:

1. **Fixed Import Paths** in `conftest.py`:
   ```python
   # Before (incorrect)
   from emergency_alerts.const import DOMAIN
   
   # After (correct)
   from custom_components.emergency_alerts.const import DOMAIN
   ```

2. **Added Plugin Registration** in `conftest.py`:
   ```python
   # Explicitly register the Home Assistant pytest plugin
   pytest_plugins = ['pytest_homeassistant_custom_component.plugin']
   ```

3. **Enhanced PYTHONPATH** in Docker:
   ```dockerfile
   ENV PYTHONPATH="/app:/usr/local/lib/python3.11/site-packages"
   ```

4. **Created Missing `__init__.py`** files:
   ```bash
   # Ensure all required __init__.py files exist
   touch custom_components/__init__.py
   touch custom_components/emergency_alerts/__init__.py
   touch custom_components/emergency_alerts/tests/__init__.py
   ```

#### Problem 3: Docker Container Detection Issues
**Research Finding**: The `pytest-homeassistant-custom-component` package has known issues in Docker environments.

**Additional Solutions** (if above don't work):
1. **Container Detection**: Some versions require `/.dockerenv` file
2. **Alternative Plugin Loading**: Use direct imports instead of plugin discovery
3. **Virtual Environment**: Ensure proper venv activation in container

### Import and Path Issues

#### Backend Import Errors
**Common Patterns**:
```python
# ❌ Wrong - relative imports from test directory
from emergency_alerts.const import DOMAIN

# ✅ Correct - absolute imports from package
from custom_components.emergency_alerts.const import DOMAIN
```

**Debugging Steps**:
1. Check current working directory: `pwd`
2. Verify PYTHONPATH: `echo $PYTHONPATH`
3. Test imports manually: `python -c "from custom_components.emergency_alerts.const import DOMAIN; print(DOMAIN)"`

#### Test Discovery Issues
**Problem**: Tests not discovered by pytest

**Solutions**:
- Ensure all directories have `__init__.py` files
- Use proper test file naming (`test_*.py` or `*_test.py`)
- Check pytest configuration in `pytest.ini`

### Configuration Flow Debugging

#### 500 Internal Server Error in HACS
**Problem**: Integration setup fails with internal server error

**Debugging Approach**:
1. **Add Comprehensive Logging** to `config_flow.py`:
   ```python
   import logging
   _LOGGER = logging.getLogger(__name__)
   
   async def async_step_user(self, user_input=None):
       _LOGGER.debug("Config flow started with input: %s", user_input)
       try:
           # ... existing code ...
           _LOGGER.info("Config flow completed successfully")
       except Exception as e:
           _LOGGER.exception("Config flow failed: %s", e)
           raise
   ```

2. **Monitor Home Assistant Logs**:
   ```bash
   # In Home Assistant container/logs
   tail -f home-assistant.log | grep emergency_alerts
   ```

3. **Test Configuration Manually**:
   ```python
   # In Home Assistant developer tools
   service: emergency_alerts.acknowledge
   data:
     entity_id: binary_sensor.test_alert
   ```

### Common Issues

#### Backend
- **Import Errors**: Ensure `PYTHONPATH` includes current directory
- **Fixture Issues**: Check `conftest.py` fixture definitions
- **Mock Problems**: Verify Home Assistant mock objects
- **Plugin Loading**: Ensure pytest-homeassistant-custom-component is properly registered
- **Docker Paths**: Verify all paths are absolute in containerized environments

#### Frontend
- **Jest Configuration**: Check `jest.config.js` setup
- **TypeScript Errors**: Verify `tsconfig.json` types
- **DOM Issues**: Ensure `jsdom` environment configured

#### Docker-Specific
- **Build Dependencies**: Ensure C++ compiler tools are installed
- **Python Paths**: Set PYTHONPATH to include both app and site-packages
- **Plugin Discovery**: Use explicit plugin registration in conftest.py
- **File Permissions**: Ensure test files are readable in container

### Debugging Workflow

#### Systematic Approach
1. **Identify Error Type**: Import, runtime, configuration, or dependency
2. **Check Environment**: Local vs Docker vs CI
3. **Verify Dependencies**: All packages installed and compatible
4. **Test Isolation**: Run single test to isolate issue
5. **Add Logging**: Insert debug statements to trace execution
6. **Compare Working**: Check against known working configurations

#### Useful Commands
```bash
# Test environment verification
python -c "import sys; print('\n'.join(sys.path))"
python -c "import pytest_homeassistant_custom_component; print('Plugin found')"
python -m pytest --collect-only  # Show test discovery

# Docker debugging
docker run -it --rm emergency-alerts-test python -c "import sys; print(sys.path)"
docker run --rm emergency-alerts-test find /app -name "*.py" | head -10

# Home Assistant integration testing
python -c "from custom_components.emergency_alerts import DOMAIN; print(f'Domain: {DOMAIN}')"
```

### Known Limitations

#### Docker Environment
- Some Home Assistant test utilities may not work identically in containers
- Plugin discovery can be unreliable in certain Docker configurations
- File watching and hot-reload features are limited

#### CI/CD Environment
- GitHub Actions containers may have different Python path handling
- Caching can sometimes cause stale dependency issues
- Matrix builds may expose environment-specific problems

### Best Practices

#### Test Environment Setup
1. **Consistent Paths**: Use absolute imports throughout
2. **Explicit Dependencies**: Pin versions in test_requirements.txt
3. **Environment Variables**: Set PYTHONPATH explicitly
4. **Plugin Registration**: Always use explicit pytest_plugins declaration

#### Docker Testing
1. **Multi-stage Builds**: Separate dependency installation from test execution
2. **Layer Caching**: Order Dockerfile commands for optimal caching
3. **Minimal Images**: Use slim base images but include necessary build tools
4. **Volume Mounts**: For development, mount source code as volumes

#### Debugging Strategy
1. **Start Simple**: Test basic imports before complex functionality
2. **Incremental**: Add one test at a time when debugging
3. **Logging**: Use structured logging with clear context
4. **Documentation**: Record solutions for future reference

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

## 📋 Current Status & Next Steps

### ✅ Completed Fixes
Based on recent troubleshooting sessions, the following issues have been resolved:

1. **Config Flow Logging**: Added comprehensive logging to `config_flow.py` for debugging 500 errors
2. **Docker Build Dependencies**: Fixed missing C++ compiler tools in `Dockerfile.test`
3. **Import Path Corrections**: Fixed relative imports in `conftest.py` to use absolute paths
4. **Plugin Registration**: Added explicit `pytest_plugins` declaration in test configuration
5. **PYTHONPATH Configuration**: Enhanced Docker environment variables for proper module discovery

### 🔄 Pending Issues
Some issues may still need attention depending on your environment:

1. **Docker Plugin Discovery**: The `pytest-homeassistant-custom-component` plugin may still have issues in some Docker configurations
2. **Container Detection**: Some plugin versions require additional Docker environment markers
3. **Test Dependencies Validation**: Need to implement `test_dependencies.py` script following Home Assistant best practices

### 🎯 Recommended Next Steps

#### Immediate Actions
1. **Test Current Fixes**: Run `./docker-test.sh` to verify all fixes are working
2. **Validate Plugin Loading**: Ensure pytest can discover and load the Home Assistant plugin
3. **Check CI Pipeline**: Verify GitHub Actions workflow is passing with current changes

#### Future Improvements
1. **Implement hassfest Validation**: Add Home Assistant's official validation workflow
2. **Add Dependency Testing**: Create comprehensive dependency validation script
3. **Enhance Error Handling**: Add more specific error messages for common failure modes

### 🔧 Environment-Specific Notes

#### Local Development
- Use virtual environments to avoid dependency conflicts
- Set PYTHONPATH explicitly if encountering import issues
- Use `python -m pytest` instead of bare `pytest` for better module discovery

#### Docker Testing
- Ensure all `__init__.py` files exist in the package hierarchy
- Use absolute imports throughout test files
- Consider using volume mounts for faster development cycles

#### CI/CD Pipeline
- Monitor for environment-specific failures in matrix builds
- Use dependency caching to speed up builds
- Set up proper artifact collection for debugging failed builds

## 🚀 Future Enhancements

### Planned Additions
- **E2E Testing**: Playwright/Cypress for full workflows
- **Performance Testing**: Load testing for many alerts
- **Visual Regression**: Screenshot comparison testing
- **Accessibility Testing**: A11y compliance verification
- **Property-based Testing**: Hypothesis for edge cases
- **hassfest Integration**: Official Home Assistant validation workflow
- **Dependency Validation**: Automated dependency compatibility checking

### Integration Improvements
- **Test Data Management**: Centralized test fixture management
- **Mock Improvements**: More realistic Home Assistant environment mocking
- **Coverage Enhancement**: Increase coverage for edge cases and error conditions
- **Documentation Testing**: Automated validation of code examples in documentation

---

## 💡 Tips for Contributors

1. **Write Tests First**: TDD approach for new features
2. **Mock External Dependencies**: Isolate units under test
3. **Test Edge Cases**: Empty states, error conditions
4. **Keep Tests Simple**: One assertion per test when possible
5. **Use Descriptive Names**: Test names should explain intent
6. **Update Tests with Changes**: Keep tests synchronized with code
7. **Document Issues**: Add troubleshooting notes when encountering new problems
8. **Test in Multiple Environments**: Verify changes work in local, Docker, and CI environments

## 📞 Getting Help

### Common Resources
- **Home Assistant Developer Docs**: https://developers.home-assistant.io/
- **pytest-homeassistant-custom-component**: https://github.com/MatthewFlamm/pytest-homeassistant-custom-component
- **HACS Integration Guidelines**: https://hacs.xyz/docs/publish/integration

### Reporting Issues
For questions about testing, check the [GitHub Issues](https://github.com/issmirnov/emergency_alerts/issues) or [Discussions](https://github.com/issmirnov/emergency_alerts/discussions).

When reporting test issues, please include:
- Environment details (local/Docker/CI)
- Full error messages and stack traces
- Python and dependency versions
- Steps to reproduce the issue 