"""Test the Emergency Alerts binary sensor."""

from unittest.mock import AsyncMock, Mock, patch

from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.binary_sensor import (
    async_setup_entry,
    EmergencyBinarySensor,
)


async def test_simple_trigger_setup(hass: HomeAssistant, mock_config_entry):
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


@patch("threading.get_ident", return_value=12345)  # Match hass.loop_thread_id
async def test_simple_trigger_evaluation(mock_threading, hass: HomeAssistant):
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

    # Set entity_id for proper entity registration
    sensor.entity_id = "binary_sensor.emergency_test_alert"

    # Mock the monitored entity state to return "off" initially
    mock_state_off = Mock()
    mock_state_off.state = "off"

    mock_state_on = Mock()
    mock_state_on.state = "on"

    # Configure the mock to return different states
    def mock_get_state(entity_id):
        if entity_id == "binary_sensor.test_sensor":
            return mock_state_off  # Initially off
        return None

    hass.states.get.side_effect = mock_get_state

    # Initial evaluation should be False
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Change to trigger state
    def mock_get_state_on(entity_id):
        if entity_id == "binary_sensor.test_sensor":
            return mock_state_on  # Now on
        return None

    hass.states.get.side_effect = mock_get_state_on
    sensor._evaluate_trigger()
    assert sensor.is_on is True
    assert sensor._already_triggered is True
    assert sensor._first_triggered is not None

    # Change back to off
    hass.states.get.side_effect = mock_get_state
    sensor._evaluate_trigger()
    assert sensor.is_on is False
    assert sensor._already_triggered is False


@patch("threading.get_ident", return_value=12345)  # Match hass.loop_thread_id
async def test_template_trigger_evaluation(mock_threading, hass: HomeAssistant):
    """Test template trigger evaluation."""
    sensor = EmergencyBinarySensor(
        hass=hass,
        name="Template Alert",
        trigger_type="template",
        template="{{ states('sensor.temperature') | float > 30 }}",
        severity="critical",
        group="environment",
    )

    # Set entity_id for proper entity registration
    sensor.entity_id = "binary_sensor.emergency_template_alert"

    # Mock temperature sensor states
    mock_state_25 = Mock()
    mock_state_25.state = "25"

    mock_state_35 = Mock()
    mock_state_35.state = "35"

    def mock_get_state_25(entity_id):
        if entity_id == "sensor.temperature":
            return mock_state_25
        return None

    def mock_get_state_35(entity_id):
        if entity_id == "sensor.temperature":
            return mock_state_35
        return None

    # Mock template rendering
    with patch("homeassistant.helpers.template.Template.async_render") as mock_render:
        # Should not trigger with low temperature
        hass.states.get.side_effect = mock_get_state_25
        mock_render.return_value = False
        sensor._evaluate_trigger()
        assert sensor.is_on is False

        # Should trigger with high temperature
        hass.states.get.side_effect = mock_get_state_35
        mock_render.return_value = True
        sensor._evaluate_trigger()
        assert sensor.is_on is True


@patch("threading.get_ident", return_value=12345)  # Match hass.loop_thread_id
async def test_logical_trigger_evaluation(mock_threading, hass: HomeAssistant):
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

    # Set entity_id for proper entity registration
    sensor.entity_id = "binary_sensor.emergency_logical_alert"

    # Mock states
    mock_door_off = Mock()
    mock_door_off.state = "off"
    mock_door_on = Mock()
    mock_door_on.state = "on"

    mock_alarm_off = Mock()
    mock_alarm_off.state = "off"
    mock_alarm_on = Mock()
    mock_alarm_on.state = "on"

    # Both sensors off
    def mock_get_state_both_off(entity_id):
        if entity_id == "binary_sensor.door":
            return mock_door_off
        elif entity_id == "binary_sensor.alarm":
            return mock_alarm_off
        return None

    hass.states.get.side_effect = mock_get_state_both_off
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Only door on
    def mock_get_state_door_on(entity_id):
        if entity_id == "binary_sensor.door":
            return mock_door_on
        elif entity_id == "binary_sensor.alarm":
            return mock_alarm_off
        return None

    hass.states.get.side_effect = mock_get_state_door_on
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Both on
    def mock_get_state_both_on(entity_id):
        if entity_id == "binary_sensor.door":
            return mock_door_on
        elif entity_id == "binary_sensor.alarm":
            return mock_alarm_on
        return None

    hass.states.get.side_effect = mock_get_state_both_on
    sensor._evaluate_trigger()
    assert sensor.is_on is True


@patch("threading.get_ident", return_value=12345)  # Match hass.loop_thread_id
async def test_acknowledgment(mock_threading, hass: HomeAssistant):
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

    # Set entity_id for proper entity registration
    sensor.entity_id = "binary_sensor.emergency_test_alert"

    # Mock trigger state
    mock_state_on = Mock()
    mock_state_on.state = "on"

    def mock_get_state_on(entity_id):
        if entity_id == "binary_sensor.test_sensor":
            return mock_state_on
        return None

    hass.states.get.side_effect = mock_get_state_on

    # Trigger the alert
    sensor._evaluate_trigger()
    assert sensor.is_on is True
    assert sensor._acknowledged is False

    # Acknowledge the alert
    await sensor.async_acknowledge()
    assert sensor._acknowledged is True
    assert sensor.is_on is False  # is_on should be False when acknowledged


@patch("threading.get_ident", return_value=12345)  # Match hass.loop_thread_id
async def test_action_calls(mock_threading, hass: HomeAssistant):
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

    # Set entity_id for proper entity registration
    sensor.entity_id = "binary_sensor.emergency_test_alert"

    # Mock states
    mock_state_on = Mock()
    mock_state_on.state = "on"
    mock_state_off = Mock()
    mock_state_off.state = "off"

    # Mock the service call
    with patch.object(hass.services, "async_call", new_callable=AsyncMock) as mock_call:
        # Trigger the alert
        def mock_get_state_on(entity_id):
            if entity_id == "binary_sensor.test_sensor":
                return mock_state_on
            return None

        hass.states.get.side_effect = mock_get_state_on
        sensor._evaluate_trigger()

        # Check that on_triggered action was called
        mock_call.assert_called_with(
            "notify", "notify", {"message": "Alert triggered!"}, blocking=False
        )

        # Clear the alert
        def mock_get_state_off(entity_id):
            if entity_id == "binary_sensor.test_sensor":
                return mock_state_off
            return None

        hass.states.get.side_effect = mock_get_state_off
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
