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

    # Acknowledge via service
    await hass.services.async_call(
        "emergency_alerts",
        "acknowledge",
        {"entity_id": binary_sensor_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Check sync again
    binary_state = hass.states.get(binary_sensor_id)
    status_state = hass.states.get(status_entity_id)

    assert binary_state.attributes.get("status") == status_state.state
    assert status_state.state == "acknowledged"


@pytest.mark.integration
async def test_select_binary_sensor_sync(hass: HomeAssistant, init_group_hub):
    """Test that select entity and binary sensor stay in sync."""
    await hass.async_block_till_done()

    binary_sensor_id = "binary_sensor.emergency_test_alert"
    select_entity_id = "select.test_alert_state"
    monitored_entity = "binary_sensor.test_sensor"

    # Trigger alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()

    # Set to acknowledged via select
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "acknowledged"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Check sync
    binary_state = hass.states.get(binary_sensor_id)
    select_state = hass.states.get(select_entity_id)

    # Check that acknowledged attribute matches select state
    assert binary_state.attributes.get("acknowledged") is True
    assert select_state.state == "acknowledged"

    # Set to active (clears acknowledgment)
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "active"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Check sync again
    binary_state = hass.states.get(binary_sensor_id)
    select_state = hass.states.get(select_entity_id)

    # After setting to active, acknowledged should be False
    assert binary_state.attributes.get("acknowledged") is False
    assert select_state.state == "active"


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
    select_entity_id = "select.test_alert_state"
    monitored_entity = "binary_sensor.test_sensor"

    # Trigger alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()

    # Set to acknowledged
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "acknowledged"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Set to snoozed (should clear acknowledge due to mutual exclusivity)
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "snoozed"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Check consistency
    binary_state = hass.states.get(binary_sensor_id)
    select_state = hass.states.get(select_entity_id)

    # Acknowledge should be off, snooze should be on
    assert binary_state.attributes.get("acknowledged") is False
    assert binary_state.attributes.get("snoozed") is True
    assert select_state.state == "snoozed"

    # Status should reflect snoozed
    assert binary_state.attributes.get("status") == "snoozed"
