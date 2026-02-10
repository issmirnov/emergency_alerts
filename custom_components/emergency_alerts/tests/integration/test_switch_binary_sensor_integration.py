"""Integration tests for select ↔ binary sensor interactions (v4 architecture)."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
    assert_binary_sensor_is_on,
)


@pytest.mark.integration
async def test_acknowledge_select_updates_binary_sensor(hass: HomeAssistant, init_group_hub):
    """Test that acknowledge via select entity updates binary sensor state."""
    await hass.async_block_till_done()

    binary_sensor_id = "binary_sensor.emergency_test_alert"
    select_entity_id = "select.test_alert_state"
    monitored_entity = "binary_sensor.test_sensor"

    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()

    assert_binary_sensor_is_on(hass, binary_sensor_id)

    # Set to acknowledged
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "acknowledged"},
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
async def test_snooze_select_updates_binary_sensor(hass: HomeAssistant, init_group_hub):
    """Test that snooze via select entity updates binary sensor state."""
    await hass.async_block_till_done()

    binary_sensor_id = "binary_sensor.emergency_test_alert"
    select_entity_id = "select.test_alert_state"
    monitored_entity = "binary_sensor.test_sensor"

    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()

    # Set to snoozed
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "snoozed"},
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
async def test_resolve_select_updates_binary_sensor(hass: HomeAssistant, init_group_hub):
    """Test that resolve via select entity updates binary sensor state."""
    await hass.async_block_till_done()

    binary_sensor_id = "binary_sensor.emergency_test_alert"
    select_entity_id = "select.test_alert_state"
    monitored_entity = "binary_sensor.test_sensor"

    # Trigger the alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()

    # Set to resolved
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "resolved"},
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
async def test_select_mutual_exclusivity(hass: HomeAssistant, init_group_hub):
    """Test that select entity enforces mutual exclusivity between states."""
    await hass.async_block_till_done()

    binary_sensor_id = "binary_sensor.emergency_test_alert"
    select_entity_id = "select.test_alert_state"
    monitored_entity = "binary_sensor.test_sensor"

    # Trigger the alert
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

    binary_state = hass.states.get(binary_sensor_id)
    assert binary_state.attributes.get("acknowledged") is True

    # Set to snoozed - should clear acknowledge
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": select_entity_id, "option": "snoozed"},
        blocking=True,
    )
    await hass.async_block_till_done()

    binary_state = hass.states.get(binary_sensor_id)
    assert binary_state.attributes.get("acknowledged") is False
    assert binary_state.attributes.get("snoozed") is True
