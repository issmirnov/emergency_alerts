"""State synchronization tests to verify UI-visible state stays in sync."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
)


@pytest.mark.integration
async def test_binary_sensor_status_sensor_sync(hass: HomeAssistant, init_group_hub):
    """Test that binary sensor and status sensor stay in sync."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    status_entity_id = "sensor.emergency_test_alert_status"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Check sync
    binary_state = hass.states.get(binary_sensor_id)
    status_state = hass.states.get(status_entity_id)
    
    assert binary_state.attributes.get("status") == status_state.state
    
    # Acknowledge via switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.test_alert_acknowledged"},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check sync again
    binary_state = hass.states.get(binary_sensor_id)
    status_state = hass.states.get(status_entity_id)
    
    assert binary_state.attributes.get("status") == status_state.state
    assert status_state.state == "acknowledged"


@pytest.mark.integration
async def test_switch_binary_sensor_sync(hass: HomeAssistant, init_group_hub):
    """Test that switches and binary sensor stay in sync."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    acknowledge_switch_id = "switch.test_alert_acknowledged"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Turn on acknowledge switch
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": acknowledge_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check sync
    binary_state = hass.states.get(binary_sensor_id)
    switch_state = hass.states.get(acknowledge_switch_id)
    
    # Check that acknowledged attribute matches switch state
    assert binary_state.attributes.get("acknowledged") is True
    assert switch_state.state == "on"
    
    # Turn off switch
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": acknowledge_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check sync again
    binary_state = hass.states.get(binary_sensor_id)
    switch_state = hass.states.get(acknowledge_switch_id)
    
    # After turning off, acknowledged should be False and switch should be off
    assert binary_state.attributes.get("acknowledged") is False
    assert switch_state.state == "off"


@pytest.mark.integration
async def test_summary_sensor_sync(hass: HomeAssistant, init_group_hub):
    """Test that summary sensor stays in sync with binary sensors."""
    await hass.async_block_till_done()
    
    summary_entity_id = "sensor.emergency_alerts_summary"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Initially no active alerts
    summary_state = hass.states.get(summary_entity_id)
    assert summary_state.state == "0"
    
    # Trigger alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Summary should update
    summary_state = hass.states.get(summary_entity_id)
    assert summary_state.state == "1"
    
    # Clear alert
    set_entity_state(hass, monitored_entity, "off")
    await hass.async_block_till_done()
    
    # Summary should update
    summary_state = hass.states.get(summary_entity_id)
    assert summary_state.state == "0"


@pytest.mark.integration
async def test_concurrent_updates(hass: HomeAssistant, init_group_hub):
    """Test that concurrent updates from multiple sources maintain consistency."""
    await hass.async_block_till_done()
    
    binary_sensor_id = "binary_sensor.emergency_test_alert"
    acknowledge_switch_id = "switch.test_alert_acknowledged"
    snooze_switch_id = "switch.test_alert_snoozed"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Trigger alert
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
    
    # Turn on snooze (should turn off acknowledge)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": snooze_switch_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    
    # Check consistency
    binary_state = hass.states.get(binary_sensor_id)
    ack_switch_state = hass.states.get(acknowledge_switch_id)
    snooze_switch_state = hass.states.get(snooze_switch_id)
    
    # Acknowledge should be off, snooze should be on
    assert binary_state.attributes.get("acknowledged") is False
    assert binary_state.attributes.get("snoozed") is True
    assert ack_switch_state.state == "off"
    assert snooze_switch_state.state == "on"
    
    # Status should reflect snoozed
    assert binary_state.attributes.get("status") == "snoozed"
