"""Test the Emergency Alerts summary sensors (global and hub)."""

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.sensor import (
    EmergencyGlobalSummarySensor,
    EmergencyHubSensor,
)


@pytest.fixture
def mock_entities():
    class MockEntity:
        def __init__(self, entity_id, is_on, group):
            self.entity_id = entity_id
            self.is_on = is_on
            self._group = group

    return [
        MockEntity("binary_sensor.alert1", True, "security"),
        MockEntity("binary_sensor.alert2", False, "security"),
        MockEntity("binary_sensor.alert3", True, "environment"),
        MockEntity("binary_sensor.alert4", True, "security"),
    ]


def test_global_summary_sensor_counts_active_alerts(hass: HomeAssistant, mock_entities):
    hass.data[DOMAIN] = {"entities": mock_entities}
    sensor = EmergencyGlobalSummarySensor(hass)
    sensor._update_active_alerts()
    assert sensor.native_value == 3
    assert set(sensor.extra_state_attributes["active_alerts"]) == {
        "binary_sensor.alert1",
        "binary_sensor.alert3",
        "binary_sensor.alert4",
    }
    assert sensor.extra_state_attributes["alert_count"] == 3


def test_hub_sensor_counts_alerts_in_entry(hass: HomeAssistant):
    """Test that hub sensor counts alerts in its config entry."""
    # Create a mock config entry
    mock_entry = MagicMock()
    mock_entry.data = {
        "hub_type": "group",
        "group": "security",
        "hub_name": "Security Alerts",
        "alerts": {
            "alert1": {"name": "Alert 1"},
            "alert2": {"name": "Alert 2"},
            "alert3": {"name": "Alert 3"},
        }
    }

    sensor = EmergencyHubSensor(hass, mock_entry, "security", "Security Alerts")

    assert sensor.native_value == 3
    assert sensor.extra_state_attributes["group"] == "security"
    assert sensor.extra_state_attributes["alert_count"] == 3
    assert set(sensor.extra_state_attributes["alerts"]) == {"alert1", "alert2", "alert3"}


def test_hub_sensor_empty_hub(hass: HomeAssistant):
    """Test that hub sensor handles empty alert list."""
    mock_entry = MagicMock()
    mock_entry.data = {
        "hub_type": "group",
        "group": "power",
        "hub_name": "Power Alerts",
        "alerts": {}
    }

    sensor = EmergencyHubSensor(hass, mock_entry, "power", "Power Alerts")

    assert sensor.native_value == 0
    assert sensor.extra_state_attributes["group"] == "power"
    assert sensor.extra_state_attributes["alert_count"] == 0
    assert sensor.extra_state_attributes["alerts"] == []


@pytest.mark.asyncio
async def test_summary_sensor_signal_update(hass: HomeAssistant, mock_entities):
    hass.data[DOMAIN] = {"entities": mock_entities}
    sensor = EmergencyGlobalSummarySensor(hass)
    sensor.async_write_ha_state = MagicMock()
    await sensor.async_added_to_hass()
    # Simulate a signal
    async_dispatcher_send(hass, "emergency_alerts_summary_update")
    # The callback should update and write state
    sensor.async_write_ha_state.assert_called()
