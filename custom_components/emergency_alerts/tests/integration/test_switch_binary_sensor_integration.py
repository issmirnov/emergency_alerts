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


# ---------------------------------------------------------------------------
# v4.4.0: severity-aware select options + modern naming.
# ---------------------------------------------------------------------------


from custom_components.emergency_alerts.select import (
    ALERT_STATES,
    INFO_ALERT_STATES,
    EmergencyAlertStateSelect,
)


def _build_select(hass, severity: str = "warning"):
    """Build an EmergencyAlertStateSelect for naming/options tests."""
    from unittest.mock import MagicMock
    entry = MagicMock()
    entry.entry_id = "stub_entry"
    return EmergencyAlertStateSelect(
        hass=hass,
        entry=entry,
        alert_id="dishwasher_done",
        alert_data={"name": "Dishwasher Done", "severity": severity},
    )


def test_v4_4_select_uses_has_entity_name_with_status_suffix(hass):
    """Select friendly_name renders as `<Alert Name> State` via has_entity_name."""
    s = _build_select(hass)
    assert s._attr_has_entity_name is True
    assert s._attr_name == "State"
    # No leading prefix in the suffix.
    assert "Emergency:" not in s._attr_name


def test_v4_4_select_options_full_state_machine_for_warning(hass):
    """Warning alerts get the full option list (includes snoozed, escalated)."""
    s = _build_select(hass, severity="warning")
    assert s._attr_options == ALERT_STATES
    assert "snoozed" in s._attr_options
    assert "escalated" in s._attr_options


def test_v4_4_select_options_full_state_machine_for_critical(hass):
    """Critical severity behaves identically to warning."""
    s = _build_select(hass, severity="critical")
    assert s._attr_options == ALERT_STATES


def test_v4_4_select_options_ambient_for_info(hass):
    """Info alerts drop snoozed + escalated; keep ack + resolve."""
    s = _build_select(hass, severity="info")
    assert s._attr_options == INFO_ALERT_STATES
    assert "snoozed" not in s._attr_options, \
        "info alerts must not allow snooze (they auto-clear)"
    assert "escalated" not in s._attr_options, \
        "info alerts must not allow escalation (no on_escalated action target)"
    # But ack + resolve remain so users can dismiss a card they don't care about.
    assert "acknowledged" in s._attr_options
    assert "resolved" in s._attr_options


def test_v4_4_info_states_is_strict_subset_of_full_states():
    """INFO_ALERT_STATES must not introduce any state outside the full set."""
    assert set(INFO_ALERT_STATES).issubset(set(ALERT_STATES))
