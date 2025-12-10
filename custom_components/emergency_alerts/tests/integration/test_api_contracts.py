"""API contract tests to ensure entity state structure matches UI expectations."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
)


@pytest.mark.integration
async def test_binary_sensor_entity_structure(hass: HomeAssistant, init_group_hub):
    """Test that binary sensor entity has all required attributes for UI."""
    await hass.async_block_till_done()
    
    # Entity ID format: binary_sensor.emergency_{alert_id}
    # Based on unique_id: emergency_{hub_name}_{alert_id}
    entity_id = "binary_sensor.emergency_test_alert"
    state = hass.states.get(entity_id)
    
    assert state is not None, f"Entity {entity_id} not found. Available entities: {[e.entity_id for e in hass.states.async_all()]}"
    
    # Required attributes for UI
    required_attrs = [
        "severity",
        "group",
        "status",
        "acknowledged",
        "snoozed",
        "resolved",
        "escalated",
        "first_triggered",
        "monitored_entity",
        "trigger_type",
    ]
    
    for attr in required_attrs:
        assert attr in state.attributes, f"Missing required attribute: {attr}"
    
    # Verify attribute types
    assert isinstance(state.attributes.get("severity"), str)
    assert isinstance(state.attributes.get("group"), str)
    assert isinstance(state.attributes.get("status"), str)
    assert isinstance(state.attributes.get("acknowledged"), bool)
    assert isinstance(state.attributes.get("snoozed"), bool)
    assert isinstance(state.attributes.get("resolved"), bool)
    assert isinstance(state.attributes.get("escalated"), bool)


@pytest.mark.integration
async def test_status_sensor_structure(hass: HomeAssistant, init_group_hub):
    """Test that status sensor has required structure for UI."""
    await hass.async_block_till_done()
    
    status_entity_id = "sensor.emergency_test_alert_status"
    state = hass.states.get(status_entity_id)
    
    assert state is not None
    
    # Required attributes
    required_attrs = [
        "friendly_name",
        "icon",
        "device_class",
        "alert_id",
        "alert_name",
    ]
    
    for attr in required_attrs:
        assert attr in state.attributes, f"Missing required attribute: {attr}"
    
    # Verify state is a valid status value
    valid_statuses = ["inactive", "active", "acknowledged", "snoozed", "escalated", "resolved"]
    assert state.state in valid_statuses, f"Invalid status value: {state.state}"


@pytest.mark.integration
async def test_summary_sensor_structure(hass: HomeAssistant, init_group_hub):
    """Test that summary sensor has required structure for UI."""
    await hass.async_block_till_done()
    
    summary_entity_id = "sensor.emergency_alerts_summary"
    state = hass.states.get(summary_entity_id)
    
    assert state is not None
    
    # Required attributes
    assert "active_alerts" in state.attributes
    assert "alert_count" in state.attributes
    
    # Verify types
    assert isinstance(state.attributes.get("active_alerts"), list)
    assert isinstance(state.attributes.get("alert_count"), int)
    
    # State should be a number (count)
    assert state.state.isdigit() or state.state == "0"


@pytest.mark.integration
async def test_service_call_formats(hass: HomeAssistant, init_group_hub):
    """Test that service calls accept correct data formats."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Test acknowledge service with entity_id
    await hass.services.async_call(
        DOMAIN,
        "acknowledge",
        {"entity_id": binary_sensor_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    state = hass.states.get(binary_sensor_id)
    assert state.attributes.get("acknowledged") is True
    
    # Test clear service
    await hass.services.async_call(
        DOMAIN,
        "clear",
        {"entity_id": binary_sensor_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    state = hass.states.get(binary_sensor_id)
    assert state.state == "off"
