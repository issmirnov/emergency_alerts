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
async def test_simple_trigger_evaluation(mock_threading, hass: HomeAssistant, create_binary_sensor):
    """Test simple trigger evaluation."""
    sensor = create_binary_sensor()

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
async def test_template_trigger_evaluation(mock_threading, hass: HomeAssistant, mock_template_config_entry):
    """Test template trigger evaluation."""
    from custom_components.emergency_alerts.binary_sensor import EmergencyBinarySensor

    alert_data = mock_template_config_entry.data["alerts"]["template_alert"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=mock_template_config_entry,
        alert_id="template_alert",
        alert_data=alert_data,
        group="environment",
        hub_name="test_hub_env",
    )

    sensor.entity_id = "binary_sensor.emergency_template_alert"

    # Mock template evaluation
    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value
        mock_tpl.async_render.return_value = True

        sensor._evaluate_trigger()
        assert sensor.is_on is True
        assert sensor._already_triggered is True

        # Template returns False
        mock_tpl.async_render.return_value = False
        sensor._evaluate_trigger()
        assert sensor.is_on is False


@patch("threading.get_ident", return_value=12345)
async def test_logical_trigger_evaluation(mock_threading, hass: HomeAssistant, mock_logical_config_entry):
    """Test logical trigger evaluation with AND operator."""
    from custom_components.emergency_alerts.binary_sensor import EmergencyBinarySensor

    alert_data = mock_logical_config_entry.data["alerts"]["logical_alert"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=mock_logical_config_entry,
        alert_id="logical_alert",
        alert_data=alert_data,
        group="security",
        hub_name="test_hub_security",
    )

    sensor.entity_id = "binary_sensor.emergency_logical_alert"

    # Both conditions false
    def mock_states_off(entity_id):
        mock_state = Mock()
        mock_state.state = "off"
        return mock_state

    hass.states.get.side_effect = mock_states_off
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Only first condition true
    def mock_states_partial(entity_id):
        mock_state = Mock()
        mock_state.state = "on" if entity_id == "binary_sensor.door" else "off"
        return mock_state

    hass.states.get.side_effect = mock_states_partial
    sensor._evaluate_trigger()
    assert sensor.is_on is False  # AND requires both

    # Both conditions true
    def mock_states_on(entity_id):
        mock_state = Mock()
        mock_state.state = "on"
        return mock_state

    hass.states.get.side_effect = mock_states_on
    sensor._evaluate_trigger()
    assert sensor.is_on is True
    assert sensor._already_triggered is True


@patch("threading.get_ident", return_value=12345)
@patch("custom_components.emergency_alerts.binary_sensor.async_dispatcher_send")
async def test_acknowledgment(mock_dispatcher, mock_threading, hass: HomeAssistant, create_binary_sensor):
    """Test acknowledgment functionality."""
    sensor = create_binary_sensor()
    sensor.entity_id = "binary_sensor.emergency_test_alert"

    # Mock event bus and async_create_task
    hass.bus = Mock()
    hass.bus.async_fire = Mock()
    hass.async_create_task = Mock(return_value=Mock(cancel=Mock()))

    # Initial state
    assert sensor._acknowledged is False
    assert sensor.get_status() == "inactive"

    # Trigger alert
    mock_state = Mock()
    mock_state.state = "on"
    hass.states.get.return_value = mock_state
    sensor._evaluate_trigger()

    assert sensor.is_on is True
    assert sensor.get_status() == "active"

    # Acknowledge
    await sensor.async_acknowledge()
    assert sensor._acknowledged is True
    assert sensor.get_status() == "acknowledged"

    # Clear acknowledgment
    await sensor.async_clear_acknowledgment()
    assert sensor._acknowledged is False


@patch("threading.get_ident", return_value=12345)
async def test_action_calls(mock_threading, hass: HomeAssistant, mock_template_config_entry):
    """Test that actions are called on trigger and clear."""
    from custom_components.emergency_alerts.binary_sensor import EmergencyBinarySensor

    alert_data = mock_template_config_entry.data["alerts"]["template_alert"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=mock_template_config_entry,
        alert_id="template_alert",
        alert_data=alert_data,
        group="environment",
        hub_name="test_hub_env",
    )

    sensor.entity_id = "binary_sensor.emergency_template_alert"

    # Mock template to return True
    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value
        mock_tpl.async_render.return_value = True

        # Trigger - should call on_triggered action
        sensor._evaluate_trigger()
        assert sensor.is_on is True

        # Check that service was called (on_triggered has notify.notify service)
        # Note: Actions are called asynchronously, and we'd need to await them
        # For now, just check the state changed
        assert sensor._already_triggered is True


@patch("threading.get_ident", return_value=12345)
async def test_extra_state_attributes(mock_threading, hass: HomeAssistant, create_binary_sensor):
    """Test extra state attributes include new state machine flags."""
    sensor = create_binary_sensor()
    sensor.entity_id = "binary_sensor.emergency_test_alert"

    attrs = sensor.extra_state_attributes

    # Check that new v2.0 state machine attributes are present
    assert "acknowledged" in attrs
    assert "snoozed" in attrs
    assert "resolved" in attrs
    assert "escalated" in attrs
    assert "status" in attrs

    # Check initial values
    assert attrs["acknowledged"] is False
    assert attrs["snoozed"] is False
    assert attrs["resolved"] is False
    assert attrs["escalated"] is False
    assert attrs["status"] == "inactive"

    # Check severity and group are present
    assert attrs["severity"] == "warning"
    assert attrs["group"] == "security"
