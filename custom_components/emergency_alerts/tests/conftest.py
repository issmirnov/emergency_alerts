"""Test configuration for Emergency Alerts integration."""

import pytest
pytest_plugins = "pytest_homeassistant_custom_component"

from unittest.mock import AsyncMock, Mock
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


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
