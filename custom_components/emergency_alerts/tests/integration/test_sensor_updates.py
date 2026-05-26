"""Integration tests for sensor platform updates."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
    assert_sensor_value,
)


@pytest.mark.integration
async def test_global_summary_sensor_updates(hass: HomeAssistant, init_group_hub):
    """Test that global summary sensor updates when alerts change."""
    await hass.async_block_till_done()
    
    summary_entity_id = "sensor.emergency_alerts_summary"
    monitored_entity = "binary_sensor.test_sensor"
    
    # Initially no active alerts
    summary_state = hass.states.get(summary_entity_id)
    assert summary_state is not None
    assert_sensor_value(hass, summary_entity_id, 0)
    
    # Trigger an alert
    set_entity_state(hass, monitored_entity, "on")
    await hass.async_block_till_done()
    
    # Summary should show 1 active alert
    assert_sensor_value(hass, summary_entity_id, 1)
    
    # Check active_alerts attribute
    summary_state = hass.states.get(summary_entity_id)
    active_alerts = summary_state.attributes.get("active_alerts", [])
    assert len(active_alerts) == 1
    assert "binary_sensor.emergency_test_alert" in active_alerts


@pytest.mark.integration
async def test_hub_summary_state_is_active_count_attrs_carry_configured(
    hass: HomeAssistant, init_group_hub
):
    """Hub summary state = firing-alert count (for visibility gating); configured count is in attrs."""
    await hass.async_block_till_done()

    hub_summary_id = "sensor.emergency_alerts_security_summary"
    hub_state = hass.states.get(hub_summary_id)
    assert hub_state is not None

    # Nothing is firing yet → state is 0 (so `numeric_state > 0` gates work)
    assert_sensor_value(hass, hub_summary_id, 0)

    # Configured-count + alert list still available via attributes
    assert hub_state.attributes.get("group") == "security"
    assert hub_state.attributes.get("configured_count") == 1
    assert hub_state.attributes.get("alert_count") == 1  # legacy alias
    assert "test_alert" in hub_state.attributes.get("alerts", [])
    assert hub_state.attributes.get("active_alerts") == []


@pytest.mark.integration
async def test_hub_summary_state_flips_with_firing_alert(
    hass: HomeAssistant, init_group_hub
):
    """Hub summary state moves 0 → 1 → 0 as the underlying alert fires/clears."""
    await hass.async_block_till_done()
    hub_summary_id = "sensor.emergency_alerts_security_summary"
    monitored = "binary_sensor.test_sensor"

    # Baseline: nothing firing
    assert_sensor_value(hass, hub_summary_id, 0)

    # Trigger the alert
    set_entity_state(hass, monitored, "on")
    await hass.async_block_till_done()
    assert_sensor_value(hass, hub_summary_id, 1)
    hub_state = hass.states.get(hub_summary_id)
    assert hub_state.attributes.get("active_alerts") == [
        "binary_sensor.emergency_test_alert"
    ]

    # Clear the alert
    set_entity_state(hass, monitored, "off")
    await hass.async_block_till_done()
    assert_sensor_value(hass, hub_summary_id, 0)


@pytest.mark.integration
async def test_summary_sensor_configured_count_updates_on_add(
    hass: HomeAssistant, init_group_hub
):
    """Adding an alert bumps configured_count attribute while state stays 0 (nothing firing)."""
    await hass.async_block_till_done()

    entry = init_group_hub
    alerts = dict(entry.data.get("alerts", {}))
    alerts["test_alert_2"] = {
        "name": "Test Alert 2",
        "trigger_type": "simple",
        "entity_id": "binary_sensor.test_sensor_2",
        "trigger_state": "on",
        "severity": "critical",
    }

    new_data = dict(entry.data)
    new_data["alerts"] = alerts
    hass.config_entries.async_update_entry(entry, data=new_data)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    hub_summary_id = "sensor.emergency_alerts_security_summary"
    assert_sensor_value(hass, hub_summary_id, 0)
    hub_state = hass.states.get(hub_summary_id)
    assert hub_state.attributes.get("configured_count") == 2
