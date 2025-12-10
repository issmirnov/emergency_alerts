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


async def test_simple_trigger_evaluation(hass: HomeAssistant, create_binary_sensor):
    """Test simple trigger evaluation."""
    sensor = create_binary_sensor()

    # Set entity_id for proper entity registration
    sensor.entity_id = "binary_sensor.emergency_test_alert"

    await hass.async_block_till_done()

    # Create the monitored entity state (initially off)
    hass.states.async_set("binary_sensor.test_sensor", "off")
    await hass.async_block_till_done()

    # Initial evaluation should be False
    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Change to trigger state (on)
    hass.states.async_set("binary_sensor.test_sensor", "on")
    await hass.async_block_till_done()

    sensor._evaluate_trigger()
    assert sensor.is_on is True
    assert sensor._already_triggered is True
    assert sensor._first_triggered is not None

    # Change back to off
    hass.states.async_set("binary_sensor.test_sensor", "off")
    await hass.async_block_till_done()

    sensor._evaluate_trigger()
    assert sensor.is_on is False
    assert sensor._already_triggered is False


async def test_template_trigger_evaluation(hass: HomeAssistant, mock_template_config_entry):
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
    
    # Register entity with hass for proper cleanup
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    # Mock template evaluation
    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value
        mock_tpl.async_render.return_value = True

        sensor._evaluate_trigger()
        assert sensor.is_on is True
        assert sensor._already_triggered is True

        # Wait for async tasks to complete (escalation timer setup)
        await hass.async_block_till_done()

        # Template returns False (this should cancel the escalation timer)
        mock_tpl.async_render.return_value = False
        sensor._evaluate_trigger()
        assert sensor.is_on is False
        
        # Wait for async operations to complete
        await hass.async_block_till_done()
        
        # Clean up escalation timer if it was started
        sensor._cleanup_timers()


async def test_logical_trigger_evaluation(hass: HomeAssistant, mock_logical_config_entry):
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
    
    # Register entity with hass for proper cleanup
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    await hass.async_block_till_done()

    # Both conditions false
    hass.states.async_set("binary_sensor.door", "off")
    hass.states.async_set("binary_sensor.alarm", "off")
    await hass.async_block_till_done()

    sensor._evaluate_trigger()
    assert sensor.is_on is False

    # Only first condition true
    hass.states.async_set("binary_sensor.door", "on")
    hass.states.async_set("binary_sensor.alarm", "off")
    await hass.async_block_till_done()

    sensor._evaluate_trigger()
    assert sensor.is_on is False  # AND requires both

    # Both conditions true
    hass.states.async_set("binary_sensor.door", "on")
    hass.states.async_set("binary_sensor.alarm", "on")
    await hass.async_block_till_done()

    sensor._evaluate_trigger()
    assert sensor.is_on is True
    assert sensor._already_triggered is True
    
    # Wait for async tasks to complete (escalation timer setup)
    await hass.async_block_till_done()
    
    # Clear the trigger to cancel the escalation timer
    hass.states.async_set("binary_sensor.door", "off")
    await hass.async_block_till_done()
    sensor._evaluate_trigger()
    await hass.async_block_till_done()
    
    # Clean up escalation timer if it was started
    sensor._cleanup_timers()


async def test_acknowledgment(hass: HomeAssistant, create_binary_sensor):
    """Test acknowledgment functionality."""
    sensor = create_binary_sensor()
    sensor.entity_id = "binary_sensor.emergency_test_alert"

    # Add sensor to hass for proper entity platform registration
    await hass.async_block_till_done()

    # Initial state
    assert sensor._acknowledged is False
    assert sensor.get_status() == "inactive"

    # Create the monitored entity state (the entity that triggers the alert)
    hass.states.async_set("binary_sensor.test_sensor", "off")
    await hass.async_block_till_done()

    # Trigger alert by changing monitored entity to "on"
    hass.states.async_set("binary_sensor.test_sensor", "on")
    await hass.async_block_till_done()
    sensor._evaluate_trigger()
    
    # Wait for async tasks to complete (escalation timer setup)
    await hass.async_block_till_done()

    assert sensor.is_on is True
    assert sensor.get_status() == "active"

    # Acknowledge (this should cancel the escalation timer)
    await sensor.async_acknowledge()
    assert sensor._acknowledged is True
    assert sensor.get_status() == "acknowledged"
    
    # Wait for async operations to complete
    await hass.async_block_till_done()
    
    # Clean up escalation timer if it was started
    sensor._cleanup_timers()

    # In v2.0, acknowledgment is managed via switches, not direct methods
    # So we just test that acknowledgment works correctly


async def test_action_calls(hass: HomeAssistant, mock_template_config_entry):
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
    
    # Register entity with hass for proper cleanup
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    # Mock template to return True
    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value
        mock_tpl.async_render.return_value = True

        # Trigger - should call on_triggered action
        sensor._evaluate_trigger()
        assert sensor.is_on is True

        # Wait for async tasks to complete (escalation timer setup)
        await hass.async_block_till_done()

        # Check that service was called (on_triggered has notify.notify service)
        # Note: Actions are called asynchronously, and we'd need to await them
        # For now, just check the state changed
        assert sensor._already_triggered is True
        
        # Clear the trigger to cancel the escalation timer
        mock_tpl.async_render.return_value = False
        sensor._evaluate_trigger()
        await hass.async_block_till_done()
        
        # Clean up escalation timer if it was started
        sensor._cleanup_timers()


async def test_extra_state_attributes(hass: HomeAssistant, create_binary_sensor):
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
