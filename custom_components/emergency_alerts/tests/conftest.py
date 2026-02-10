"""Test configuration for Emergency Alerts integration."""

import pytest
import os

# Set timezone environment before importing pytest-homeassistant-custom-component
# This helps with timezone validation in Docker environments
if "TZ" not in os.environ:
    os.environ["TZ"] = "America/Los_Angeles"

pytest_plugins = "pytest_homeassistant_custom_component"

# Patch Home Assistant's Config.set_time_zone method (if available)
# This is a workaround for pytest-homeassistant-custom-component hardcoding US/Pacific
# Note: Config is deprecated in newer HA versions, so we make this conditional
try:
    from homeassistant.core_config import Config as CoreConfig
    _config_class = CoreConfig
except ImportError:
    # Fallback to deprecated location for older HA versions
    try:
        import homeassistant.core as ha_core
        _config_class = ha_core.Config
    except (ImportError, AttributeError):
        _config_class = None

if _config_class is not None:
    try:
        from homeassistant.util import dt as dt_util
        
        # Only patch if the method exists
        if hasattr(_config_class, 'set_time_zone'):
            # Store original method
            _original_set_time_zone = _config_class.set_time_zone

            def _patched_set_time_zone(self, time_zone_str: str) -> None:
                """Patched version of set_time_zone that handles timezone aliases."""
                # Map common timezone aliases
                timezone_map = {
                    "US/Pacific": "America/Los_Angeles",
                    "US/Mountain": "America/Denver",
                    "US/Central": "America/Chicago",
                    "US/Eastern": "America/New_York",
                }
                
                # Use mapped timezone if available
                actual_timezone = timezone_map.get(time_zone_str, time_zone_str)
                
                # Try to get the timezone
                time_zone = dt_util.get_time_zone(actual_timezone)
                if time_zone is None:
                    # Fallback to UTC if timezone is still invalid
                    time_zone = dt_util.get_time_zone("UTC")
                
                if time_zone is None:
                    raise ValueError(f"Received invalid time zone {time_zone_str}")
                
                # Set the timezone using the original method's logic
                self._time_zone = time_zone
                # Also set the global default timezone (required for dt_util.now() etc.)
                dt_util.set_default_time_zone(time_zone)

            # Apply the patch on Config class
            _config_class.set_time_zone = _patched_set_time_zone
    except (AttributeError, ImportError):
        # Config class or set_time_zone method doesn't exist in this HA version
        # This is fine - newer HA versions handle timezone differently
        pass

from unittest.mock import AsyncMock, Mock, patch
from typing import Any
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN

# Try to import snapshot testing support (optional)
try:
    from syrupy.assertion import SnapshotAssertion
    SYRUPY_AVAILABLE = True
except ImportError:
    SYRUPY_AVAILABLE = False
    # Create a dummy type for type checking when syrupy is not available
    SnapshotAssertion = type('SnapshotAssertion', (), {})


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


@pytest.fixture
def snapshot(snapshot):  # type: ignore[type-arg]
    """Return snapshot assertion fixture with Home Assistant extension."""
    if SYRUPY_AVAILABLE:
        try:
            from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
            return snapshot.use_extension(HomeAssistantSnapshotExtension)
        except ImportError:
            # Fallback if extension not available
            return snapshot
    return snapshot


# Mock config entries with v2.0 hub-based structure
@pytest.fixture
def mock_config_entry():
    """Mock config entry for testing (v2.0 hub-based structure)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "hub_type": "group",
            "group": "security",
            "hub_name": "test_hub",
            "alerts": {
                "test_alert": {
                    "name": "Test Alert",
                    "trigger_type": "simple",
                    "entity_id": "binary_sensor.test_sensor",
                    "trigger_state": "on",
                    "severity": "warning",
                },
            },
        },
    )


@pytest.fixture
def mock_template_config_entry():
    """Return a mock config entry with template trigger for testing (v2.0)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Test Template Alert",
        data={
            "hub_type": "group",
            "group": "environment",
            "hub_name": "test_hub_env",
            "alerts": {
                "template_alert": {
                    "name": "Template Alert",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.temperature') | float > 30 }}",
                    "severity": "critical",
                    "on_triggered": [
                        {"service": "notify.notify", "data": {"message": "High temp!"}}
                    ],
                    "on_cleared": [],
                    "on_escalated": [],
                },
            },
        },
        unique_id="test_template_alert_unique_id",
    )


@pytest.fixture
def mock_logical_config_entry():
    """Return a mock config entry with logical trigger for testing (v2.0)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Test Logical Alert",
        data={
            "hub_type": "group",
            "group": "security",
            "hub_name": "test_hub_security",
            "alerts": {
                "logical_alert": {
                    "name": "Logical Alert",
                    "trigger_type": "logical",
                    "logical_conditions": [
                        {
                            "entity_id": "binary_sensor.door",
                            "state": "on",
                        },
                        {
                            "entity_id": "binary_sensor.alarm",
                            "state": "on",
                        },
                    ],
                    "logical_operator": "and",
                    "severity": "critical",
                    "on_triggered": [],
                    "on_cleared": [],
                    "on_escalated": [],
                },
            },
        },
        unique_id="test_logical_alert_unique_id",
    )


@pytest.fixture
async def create_binary_sensor(hass: HomeAssistant, mock_config_entry):
    """Factory fixture to create binary sensors for testing."""
    def _create_sensor(alert_id="test_alert", alert_data=None):
        """Create a binary sensor with the given config."""
        from custom_components.emergency_alerts.binary_sensor import EmergencyBinarySensor

        if alert_data is None:
            alert_data = mock_config_entry.data["alerts"]["test_alert"]

        group = mock_config_entry.data.get("group", "security")
        hub_name = mock_config_entry.data.get("hub_name", "test_hub")

        return EmergencyBinarySensor(
            hass=hass,
            entry=mock_config_entry,
            alert_id=alert_id,
            alert_data=alert_data,
            group=group,
            hub_name=hub_name,
        )

    return _create_sensor


# Mock entities fixture for sensor tests
@pytest.fixture
def mock_entities():
    """Create mock entities for sensor testing."""
    entity1 = Mock()
    entity1.entity_id = "binary_sensor.alert1"
    entity1.is_on = True
    entity1._severity = "critical"
    entity1._group = "security"

    entity2 = Mock()
    entity2.entity_id = "binary_sensor.alert2"
    entity2.is_on = True
    entity2._severity = "warning"
    entity2._group = "security"

    entity3 = Mock()
    entity3.entity_id = "binary_sensor.alert3"
    entity3.is_on = False
    entity3._severity = "info"
    entity3._group = "safety"

    return [entity1, entity2, entity3]


# Mock binary sensor for switch tests
@pytest.fixture
def mock_binary_sensor():
    """Create a mock binary sensor entity."""
    sensor = Mock()
    sensor.entity_id = "binary_sensor.emergency_test_alert"
    sensor._alert_id = "test_alert"
    sensor._config_entry = Mock()
    sensor._config_entry.entry_id = "test_entry_123"
    sensor._acknowledged = False
    sensor._snoozed = False
    sensor._resolved = False
    sensor._escalated = False
    sensor._escalation_task = Mock(cancel=Mock())  # Mock with cancel method
    sensor._snooze_task = Mock(cancel=Mock())  # Mock with cancel method
    sensor._snooze_until = None
    sensor.is_on = False
    sensor.async_update_ha_state = AsyncMock()
    sensor._execute_action = AsyncMock()
    sensor._start_escalation_timer = AsyncMock()
    return sensor


# init_integration fixtures following HA patterns
@pytest.fixture
async def init_global_hub(hass: HomeAssistant):
    """Initialize a global settings hub integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Global Settings",
        data={
            "hub_type": "global",
            "name": "Global Settings"
        },
        options={
            "default_escalation_time": 300,
            "enable_global_notifications": False,
            "notification_profiles": {}
        }
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def init_group_hub(hass: HomeAssistant):
    """Initialize a group hub integration with default test alert."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Test Group",
        data={
            "hub_type": "group",
            "group": "security",
            "hub_name": "test_hub",
            "alerts": {
                "test_alert": {
                    "name": "Test Alert",
                    "trigger_type": "simple",
                    "entity_id": "binary_sensor.test_sensor",
                    "trigger_state": "on",
                    "severity": "warning",
                },
            },
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def init_group_hub_with_template(hass: HomeAssistant):
    """Initialize a group hub with template trigger alert."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Template Group",
        data={
            "hub_type": "group",
            "group": "environment",
            "hub_name": "test_hub_env",
            "alerts": {
                "template_alert": {
                    "name": "Template Alert",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.temperature') | float > 30 }}",
                    "severity": "critical",
                    "on_triggered": [
                        {"service": "notify.notify", "data": {"message": "High temp!"}}
                    ],
                    "on_cleared": [],
                    "on_escalated": [],
                },
            },
        },
        unique_id="test_template_alert_unique_id",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def init_group_hub_with_logical(hass: HomeAssistant):
    """Initialize a group hub with logical trigger alert."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Logical Group",
        data={
            "hub_type": "group",
            "group": "security",
            "hub_name": "test_hub_security",
            "alerts": {
                "logical_alert": {
                    "name": "Logical Alert",
                    "trigger_type": "logical",
                    "logical_conditions": [
                        {
                            "entity_id": "binary_sensor.door",
                            "state": "on",
                        },
                        {
                            "entity_id": "binary_sensor.alarm",
                            "state": "on",
                        },
                    ],
                    "logical_operator": "and",
                    "severity": "critical",
                    "on_triggered": [],
                    "on_cleared": [],
                    "on_escalated": [],
                },
            },
        },
        unique_id="test_logical_alert_unique_id",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


# Factory fixtures for common alert configurations
@pytest.fixture
def alert_config_factory():
    """Factory fixture for creating alert configurations."""
    def _create_alert_config(
        name: str = "Test Alert",
        trigger_type: str = "simple",
        entity_id: str = "binary_sensor.test_sensor",
        trigger_state: str = "on",
        severity: str = "warning",
        **kwargs
    ) -> dict[str, Any]:
        """Create an alert configuration dictionary."""
        config = {
            "name": name,
            "trigger_type": trigger_type,
            "severity": severity,
        }
        
        if trigger_type == "simple":
            config["entity_id"] = entity_id
            config["trigger_state"] = trigger_state
        elif trigger_type == "template":
            config["template"] = kwargs.get("template", "{{ True }}")
        elif trigger_type == "logical":
            config["logical_conditions"] = kwargs.get("logical_conditions", [])
            config["logical_operator"] = kwargs.get("logical_operator", "and")
        
        # Add optional fields
        for key in ["on_triggered", "on_cleared", "on_escalated", "on_acknowledged", 
                   "on_snoozed", "on_resolved", "snooze_duration"]:
            if key in kwargs:
                config[key] = kwargs[key]
        
        return config
    
    return _create_alert_config


# Time manipulation fixtures (using freezegun if available)
@pytest.fixture
def freeze_time():
    """Fixture for freezing time in tests."""
    try:
        from freezegun import freeze_time as ft
        return ft
    except ImportError:
        try:
            from time_machine import travel
            # Return a context manager that works like freezegun
            def freeze_time_machine(*args, **kwargs):
                return travel(*args, **kwargs)
            return freeze_time_machine
        except ImportError:
            # Fallback: return a no-op context manager
            from contextlib import nullcontext
            return nullcontext


# Translation error detection fixture
@pytest.fixture(autouse=True)
def check_translation_errors(hass: HomeAssistant, caplog):
    """Auto-check for translation errors in all tests.

    This fixture automatically fails any test if translation formatting errors
    are detected in the logs. This catches missing keys in strings.json or
    translations/en.json files.
    """
    yield

    # Check for translation errors in logs after test completes
    translation_errors = [
        record for record in caplog.records
        if "Failed to format translation" in record.message
        or "translation key" in record.message.lower()
        or "missing translation" in record.message.lower()
    ]

    if translation_errors:
        error_messages = "\n".join([
            f"  - {record.levelname}: {record.message}"
            for record in translation_errors
        ])
        pytest.fail(
            f"Translation errors detected during test:\n{error_messages}\n\n"
            f"Fix: Ensure strings.json and translations/en.json are in sync.\n"
            f"Run: python validate_translations.py"
        )
