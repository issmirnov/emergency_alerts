"""Test the Emergency Alerts binary sensor."""
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.binary_sensor import (
    async_setup_entry,
    EmergencyBinarySensor,
)


async def test_simple_trigger_setup(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test setting up a simple trigger binary sensor."""
    mock_config_entry.add_to_hass(hass)

    # Mock the add_entities callback
    add_entities_mock = AsyncMock()

    # Setup the binary sensor platform
    await async_setup_entry(hass, mock_config_entry, add_entities_mock)

    # Check that a sensor was added
    add_entities_mock.assert_called_once()
    sensors = add_entities_mock.call_args[0][0]
    assert len(sensors) == 1

    sensor = sensors[0]
    assert isinstance(sensor, EmergencyBinarySensor)
    assert sensor._attr_name == "Emergency: Test Alert"
    assert sensor._trigger_type == "simple"
    assert sensor._entity_id == "binary_sensor.test_sensor"
    assert sensor._trigger_state == "on"
    assert sensor._severity == "warning"
    assert sensor._group == "security"


async def test_simple_trigger_evaluation(hass: HomeAssistant):
    """Test simple trigger evaluation."""
    sensor = EmergencyBinarySensor(
        hass=hass,
        name="Test Alert",
        trigger_type="simple",
        entity_id="binary_sensor.test_sensor",
        trigger_state="on",
        severity="warning",
        group="security",
    )

    # Mock the monitored entity state
    hass.states.async_set("binary_sensor.test_sensor", "off")

    # Initial evaluation should be False
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Change to trigger state
    hass.states.async_set("binary_sensor.test_sensor", "on")
    sensor._evaluate_trigger()
    assert sensor.is_on is True
    assert sensor._already_triggered is True
    assert sensor._first_triggered is not None

    # Change back to off
    hass.states.async_set("binary_sensor.test_sensor", "off")
    sensor._evaluate_trigger()
    assert sensor.is_on is False
    assert sensor._already_triggered is False


async def test_template_trigger_evaluation(hass: HomeAssistant):
    """Test template trigger evaluation."""
    sensor = EmergencyBinarySensor(
        hass=hass,
        name="Template Alert",
        trigger_type="template",
        template="{{ states('sensor.temperature') | float > 30 }}",
        severity="critical",
        group="environment",
    )

    # Mock temperature sensor
    hass.states.async_set("sensor.temperature", "25")

    # Should not trigger
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Set high temperature
    hass.states.async_set("sensor.temperature", "35")
    sensor._evaluate_trigger()
    assert sensor.is_on is True


async def test_logical_trigger_evaluation(hass: HomeAssistant):
    """Test logical (AND) trigger evaluation."""
    sensor = EmergencyBinarySensor(
        hass=hass,
        name="Logical Alert",
        trigger_type="logical",
        logical_conditions=[
            {
                "type": "simple",
                "entity_id": "binary_sensor.door",
                "trigger_state": "on",
            },
            {
                "type": "simple",
                "entity_id": "binary_sensor.alarm",
                "trigger_state": "on",
            },
        ],
        severity="critical",
        group="security",
    )

    # Set initial states
    hass.states.async_set("binary_sensor.door", "off")
    hass.states.async_set("binary_sensor.alarm", "off")

    # Should not trigger with both off
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Should not trigger with only one on
    hass.states.async_set("binary_sensor.door", "on")
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Should trigger with both on
    hass.states.async_set("binary_sensor.alarm", "on")
    sensor._evaluate_trigger()
    assert sensor.is_on is True


async def test_acknowledgment(hass: HomeAssistant):
    """Test alert acknowledgment."""
    sensor = EmergencyBinarySensor(
        hass=hass,
        name="Test Alert",
        trigger_type="simple",
        entity_id="binary_sensor.test_sensor",
        trigger_state="on",
        severity="warning",
        group="security",
    )

    # Trigger the alert
    hass.states.async_set("binary_sensor.test_sensor", "on")
    sensor._evaluate_trigger()
    assert sensor.is_on is True
    assert sensor._acknowledged is False

    # Acknowledge the alert
    await sensor.async_acknowledge()
    assert sensor._acknowledged is True
    assert sensor.is_on is False  # is_on should be False when acknowledged


async def test_action_calls(hass: HomeAssistant):
    """Test that actions are called at appropriate times."""
    on_triggered = [
        {"service": "notify.notify", "data": {"message": "Alert triggered!"}}
    ]
    on_cleared = [{"service": "notify.notify", "data": {"message": "Alert cleared!"}}]

    sensor = EmergencyBinarySensor(
        hass=hass,
        name="Test Alert",
        trigger_type="simple",
        entity_id="binary_sensor.test_sensor",
        trigger_state="on",
        severity="warning",
        group="security",
        on_triggered=on_triggered,
        on_cleared=on_cleared,
    )

    # Mock the service call
    with patch.object(hass.services, "async_call", new_callable=AsyncMock) as mock_call:
        # Trigger the alert
        hass.states.async_set("binary_sensor.test_sensor", "on")
        sensor._evaluate_trigger()

        # Check that on_triggered action was called
        mock_call.assert_called_with(
            "notify", "notify", {"message": "Alert triggered!"}, blocking=False
        )

        # Clear the alert
        hass.states.async_set("binary_sensor.test_sensor", "off")
        sensor._evaluate_trigger()

        # Check that on_cleared action was called
        assert mock_call.call_count == 2
        mock_call.assert_called_with(
            "notify", "notify", {"message": "Alert cleared!"}, blocking=False
        )


async def test_extra_state_attributes(hass: HomeAssistant):
    """Test that extra state attributes are properly exposed."""
    sensor = EmergencyBinarySensor(
        hass=hass,
        name="Test Alert",
        trigger_type="simple",
        entity_id="binary_sensor.test_sensor",
        trigger_state="on",
        severity="warning",
        group="security",
    )

    attributes = sensor.extra_state_attributes

    assert attributes["severity"] == "warning"
    assert attributes["group"] == "security"
    assert attributes["trigger_type"] == "simple"
    assert attributes["monitored_entity"] == "binary_sensor.test_sensor"
    assert attributes["trigger_state"] == "on"
    assert attributes["acknowledged"] is False
    assert attributes["escalated"] is False
