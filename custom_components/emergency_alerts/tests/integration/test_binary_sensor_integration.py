"""Integration tests for binary sensor platform."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
    assert_entity_state,
    assert_binary_sensor_is_on,
    assert_binary_sensor_is_off,
)


@pytest.mark.integration
async def test_binary_sensor_entity_creation(hass: HomeAssistant, init_group_hub):
    """Test that binary sensor entities are created correctly."""
    await hass.async_block_till_done()
    
    # Check that binary sensor entity exists
    # Entity ID format: binary_sensor.emergency_{alert_id}
    entity_id = "binary_sensor.emergency_test_alert"
    state = hass.states.get(entity_id)
    
    assert state is not None, f"Binary sensor {entity_id} should exist. Available: {[e.entity_id for e in hass.states.async_all()]}"
    assert state.state == "off", "Binary sensor should start as off"
    assert state.attributes.get("severity") == "warning"
    assert state.attributes.get("group") == "security"


@pytest.mark.integration
async def test_binary_sensor_trigger_integration(hass: HomeAssistant, init_group_hub):
    """Test binary sensor triggering through entity state changes."""
    await hass.async_block_till_done()
    
    entity_id = "binary_sensor.emergency_test_alert"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Initially should be off
    assert_binary_sensor_is_off(hass, entity_id)
    
    # Set monitored entity to trigger state
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Binary sensor should now be on
    assert_binary_sensor_is_on(hass, entity_id)
    
    # Check status is active
    state = hass.states.get(entity_id)
    assert state.attributes.get("status") == "active"
    
    # Clear the trigger
    set_entity_state(hass, monitored_entity, "off")
    await hass.async_block_till_done()
    
    # Binary sensor should be off again
    assert_binary_sensor_is_off(hass, entity_id)


@pytest.mark.integration
async def test_binary_sensor_status_sensor_creation(hass: HomeAssistant, init_group_hub):
    """Test that status sensor is created for binary sensor."""
    await hass.async_block_till_done()
    
    status_entity_id = "sensor.emergency_test_alert_status"
    state = hass.states.get(status_entity_id)
    
    assert state is not None, f"Status sensor {status_entity_id} should exist"
    assert state.state == "inactive", "Status should start as inactive"


@pytest.mark.integration
async def test_binary_sensor_status_updates(hass: HomeAssistant, init_group_hub):
    """Test that status sensor updates when binary sensor changes."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    status_entity_id = "sensor.emergency_test_alert_status"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Check status sensor updated
    status_state = hass.states.get(status_entity_id)
    assert status_state is not None
    assert status_state.state == "active", "Status should be active when triggered"
    
    # Clear the alert
    set_entity_state(hass, monitored_entity, "off")
    await hass.async_block_till_done()
    
    # Status should be inactive
    status_state = hass.states.get(status_entity_id)
    assert status_state.state == "inactive", "Status should be inactive when cleared"
