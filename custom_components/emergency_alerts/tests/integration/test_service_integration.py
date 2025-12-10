"""Integration tests for service calls."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
    assert_binary_sensor_is_on,
)


@pytest.mark.integration
async def test_acknowledge_service(hass: HomeAssistant, init_group_hub):
    """Test emergency_alerts.acknowledge service."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    assert_binary_sensor_is_on(hass, binary_sensor_id)
    
    # Call acknowledge service
    await hass.services.async_call(
        DOMAIN,
        "acknowledge",
        {"entity_id": binary_sensor_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check that alert is acknowledged
    state = hass.states.get(binary_sensor_id)
    assert state.attributes.get("acknowledged") is True
    assert state.attributes.get("status") == "acknowledged"


@pytest.mark.integration
async def test_clear_service(hass: HomeAssistant, init_group_hub):
    """Test emergency_alerts.clear service."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    assert_binary_sensor_is_on(hass, binary_sensor_id)
    
    # Call clear service
    await hass.services.async_call(
        DOMAIN,
        "clear",
        {"entity_id": binary_sensor_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Alert should be cleared (off)
    state = hass.states.get(binary_sensor_id)
    assert state.state == "off"


@pytest.mark.integration
async def test_escalate_service(hass: HomeAssistant, init_group_hub):
    """Test emergency_alerts.escalate service."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    assert_binary_sensor_is_on(hass, binary_sensor_id)
    
    # Call escalate service
    await hass.services.async_call(
        DOMAIN,
        "escalate",
        {"entity_id": binary_sensor_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check that alert is escalated
    state = hass.states.get(binary_sensor_id)
    assert state.attributes.get("escalated") is True
    assert state.attributes.get("status") == "escalated"
