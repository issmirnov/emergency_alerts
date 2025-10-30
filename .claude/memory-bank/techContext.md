# Technical Context

> **Derived from**: projectbrief.md
> **Purpose**: Documents technologies, tools, and technical setup

## Technology Stack

### Core Technologies
- **Language**: Python 3.9+
- **Runtime**: Home Assistant Core 2023.x+
- **Framework**: Home Assistant Integration Platform
- **Database**: Home Assistant's internal state machine (no external DB)

### Major Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| homeassistant | 2023.x+ | Core platform, all integration APIs |
| pytest | ^7.0 | Testing framework |
| pytest-homeassistant-custom-component | latest | HA-specific test fixtures |
| pytest-cov | latest | Test coverage reporting |

**Note**: Integration has ZERO external runtime dependencies - pure Home Assistant integration.

### Development Tools
- **Testing**: pytest with Home Assistant test fixtures
- **Linter**: Ruff (Home Assistant standard)
- **CI/CD**: GitHub Actions
- **Validation**: `validate_integration.py` (custom validation script)
- **HACS**: Validation via HACS GitHub Action

## Development Setup

### Prerequisites
```bash
# Required installations
- Python 3.9 or higher
- Home Assistant (for testing)
- Git
- Optional: Docker (for devcontainer)
```

### Installation
```bash
# Clone repository
git clone https://github.com/issmirnov/emergency-alerts-integration.git
cd emergency-alerts-integration

# Install test dependencies
pip install -r custom_components/emergency_alerts/test_requirements.txt

# Run validation
python validate_integration.py

# Run tests
./run_tests.sh
```

### Configuration
- **No Environment Variables**: Configuration handled entirely through Home Assistant UI
- **Config Files**:
  - `manifest.json`: Integration metadata (version, domain, platforms)
  - `strings.json`: UI strings and form descriptions
  - `services.yaml`: Service definitions for automations
  - `translations/en.json`: Internationalization (currently English only)

### Running Locally

#### Option 1: Dev Container (Recommended)
```bash
# Open in VS Code with Dev Containers extension
# Container configuration in .devcontainer.json
# Provides full Home Assistant dev environment
```

#### Option 2: Manual Setup
```bash
# Copy to Home Assistant custom_components
cp -r custom_components/emergency_alerts /path/to/homeassistant/custom_components/

# Restart Home Assistant
# Integration appears in Settings → Devices & Services

# Run tests
cd custom_components/emergency_alerts
python -m pytest tests/ -v --cov=. --cov-report=html
```

#### Running Validation
```bash
# Validate integration structure
python validate_integration.py

# Run full test suite
./run_tests.sh

# Run backend tests only
./run_tests.sh --backend-only
```

## Technical Constraints

### Performance Requirements
- **State Evaluation**: Alert conditions evaluated on every relevant state change (HA event-driven)
- **UI Responsiveness**: Config flow forms must respond within 200ms
- **Entity Updates**: Status sensors must update within 100ms of state changes
- **Memory**: Minimal footprint - all state stored in HA's state machine

### Platform Support
- **Home Assistant**: Core 2023.x or higher
- **Python**: 3.9+ (Home Assistant requirement)
- **Architecture**: Any platform supporting Home Assistant (Linux, Windows, macOS, containers)
- **HACS**: Must remain HACS-compliant for distribution

### Security Requirements
- **No External Network**: Integration operates entirely within Home Assistant
- **User Input Validation**: All config flow inputs validated and sanitized
- **Template Safety**: Jinja2 templates executed in HA's sandboxed template engine
- **Permissions**: Inherits Home Assistant's user permission system

## Infrastructure

### Deployment
- **Distribution**: HACS (Home Assistant Community Store)
- **Installation**: User downloads via HACS or manual copy
- **Updates**: HACS auto-update mechanism
- **Environments**: Runs in user's Home Assistant instance (no external hosting)

### CI/CD
- **GitHub Actions**:
  - `test.yml`: Runs pytest on every commit/PR
  - HACS validation on schedule
  - Code coverage reporting to codecov.io
- **Validation**: Pre-commit validation via `validate_integration.py`

### Monitoring
- **Home Assistant Logs**: All errors/warnings logged to HA's logging system
- **Diagnostics**: Built-in diagnostics data available via HA's diagnostics interface (diagnostics.py:1)
- **No External Monitoring**: Runs locally, no telemetry or external error tracking

## External Integrations

### Home Assistant Core Services
- **Purpose**: Trigger actions on alert events
- **Authentication**: Inherits HA's service authentication
- **Services Used**: Any HA service (notify, light, switch, script, etc.)
- **Documentation**: https://www.home-assistant.io/docs/scripts/service-calls/

### HACS (Home Assistant Community Store)
- **Purpose**: Distribution and updates
- **Requirements**: manifest.json compliance, GitHub repository structure
- **Validation**: Automated via GitHub Actions
- **Documentation**: https://hacs.xyz/

## Technical Debt

### Known Limitations
1. **Legacy Support Code**: Still contains backward compatibility code for pre-hub installations (can be cleaned up post-migration period)
2. **Switch Platform**: switch.py:1 created but not fully utilized - consider removal or proper implementation
3. **Global Settings Underused**: Global settings hub exists but not all features leverage it yet
4. **Limited Internationalization**: Infrastructure exists (translations/) but only English implemented
5. **Blueprint Integration**: Basic blueprint included (blueprints/script/) but not comprehensive

### Future Refactoring Needs
- Remove legacy non-hub code paths after sufficient migration period
- Consolidate dispatcher signal usage (some redundancy in SIGNAL_ALERT_UPDATE)
- Consider abstracting alert evaluation logic into separate evaluator classes
- Improve test coverage for edge cases in logical condition evaluation

## Version History

### v1.0.0 (Current)
- Hub-based architecture
- Multi-step configuration UI
- Visual condition builder
- Status sensors with full lifecycle
- Edit alert functionality
- HACS compliant

### Pre-1.0 (Development Phases)
- Initial simple alert implementation
- Global settings introduction
- Major hub architecture refactor
- UI modernization
- Testing infrastructure establishment

## Development Notes

### File Structure
```
custom_components/emergency_alerts/
├── __init__.py              # Entry point, service registration
├── binary_sensor.py         # Alert entities with trigger evaluation
├── button.py               # Action buttons (acknowledge/clear/escalate)
├── sensor.py               # Summary sensors and hub devices
├── switch.py               # Currently minimal/unused
├── config_flow.py          # UI configuration flows
├── const.py                # Constants and configuration keys
├── helpers.py              # Utility functions
├── diagnostics.py          # Diagnostics data collection
├── services.yaml           # Service definitions
├── strings.json            # UI strings
├── manifest.json           # Integration metadata
├── translations/
│   └── en.json            # English translations
├── blueprints/
│   └── script/            # Blueprint templates
└── tests/                 # Pytest test suite
    ├── conftest.py        # Test fixtures
    ├── test_init.py       # Setup/teardown tests
    ├── test_binary_sensor.py
    ├── test_config_flow.py
    ├── test_button.py
    └── test_dependencies.py
```

### Key Technical Decisions
- **Pure Python Integration**: No external dependencies keeps it simple and reliable
- **Hub Architecture**: Unique approach for organization, more complex but better UX
- **Dispatcher Pattern**: Used for real-time entity updates across components
- **Config Entry Data**: Alert definitions stored in config entry data (not options) for immediate entity availability
- **Device Relationships**: via_device properly implemented for clean UI hierarchy
