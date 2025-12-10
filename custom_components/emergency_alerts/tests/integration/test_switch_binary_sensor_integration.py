"""Integration tests for switch ↔ binary sensor interactions."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
    assert_binary_sensor_is_on,
)


@pytest.mark.integration
async def test_acknowledge_switch_updates_binary_sensor(hass: HomeAssistant, init_group_hub):
    """Test that acknowledge switch updates binary sensor state."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    acknowledge_switch_id = "switch.test_alert_acknowledged"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    assert_binary_sensor_is_on(hass, binary_sensor_id)
    
    # Turn on acknowledge switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": acknowledge_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check binary sensor attributes
    binary_state = hass.states.get(binary_sensor_id)
    assert binary_state.attributes.get("acknowledged") is True
    assert binary_state.attributes.get("status") == "acknowledged"
    
    # Check status sensor
    status_state = hass.states.get("sensor.emergency_test_alert_status")
    assert status_state.state == "acknowledged"


@pytest.mark.integration
async def test_snooze_switch_updates_binary_sensor(hass: HomeAssistant, init_group_hub):
    """Test that snooze switch updates binary sensor state."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    snooze_switch_id = "switch.test_alert_snoozed"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Turn on snooze switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": snooze_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check binary sensor attributes
    binary_state = hass.states.get(binary_sensor_id)
    assert binary_state.attributes.get("snoozed") is True
    assert binary_state.attributes.get("status") == "snoozed"
    
    # Check status sensor
    status_state = hass.states.get("sensor.emergency_test_alert_status")
    assert status_state.state == "snoozed"


@pytest.mark.integration
async def test_resolve_switch_updates_binary_sensor(hass: HomeAssistant, init_group_hub):
    """Test that resolve switch updates binary sensor state."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    resolve_switch_id = "switch.test_alert_resolved"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Turn on resolve switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": resolve_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check binary sensor attributes
    binary_state = hass.states.get(binary_sensor_id)
    assert binary_state.attributes.get("resolved") is True
    assert binary_state.attributes.get("status") == "resolved"
    
    # Check status sensor
    status_state = hass.states.get("sensor.emergency_test_alert_status")
    assert status_state.state == "resolved"


@pytest.mark.integration
async def test_switch_mutual_exclusivity(hass: HomeAssistant, init_group_hub):
    """Test that switches enforce mutual exclusivity."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    acknowledge_switch_id = "switch.test_alert_acknowledged"
    snooze_switch_id = "switch.test_alert_snoozed"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Turn on acknowledge
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": acknowledge_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    binary_state = hass.states.get(binary_sensor_id)
    assert binary_state.attributes.get("acknowledged") is True
    
    # Turn on snooze - should turn off acknowledge
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": snooze_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    binary_state = hass.states.get(binary_sensor_id)
    assert binary_state.attributes.get("acknowledged") is False
    assert binary_state.attributes.get("snoozed") is True
