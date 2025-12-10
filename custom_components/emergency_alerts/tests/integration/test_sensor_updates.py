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
async def test_hub_summary_sensor_counts_alerts(hass: HomeAssistant, init_group_hub):
    """Test that hub summary sensor counts alerts correctly."""
    await hass.async_block_till_done()
    
    hub_summary_id = "sensor.emergency_alerts_security_summary"
    
    # Should have 1 alert configured
    hub_state = hass.states.get(hub_summary_id)
    assert hub_state is not None
    assert_sensor_value(hass, hub_summary_id, 1)
    
    # Check attributes
    assert hub_state.attributes.get("group") == "security"
    assert hub_state.attributes.get("alert_count") == 1
    alerts = hub_state.attributes.get("alerts", [])
    assert "test_alert" in alerts


@pytest.mark.integration
async def test_summary_sensor_multiple_alerts(hass: HomeAssistant, init_group_hub):
    """Test summary sensor with multiple alerts."""
    await hass.async_block_till_done()
    
    # Add another alert to the hub
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
    
    # Hub summary should show 2 alerts
    hub_summary_id = "sensor.emergency_alerts_security_summary"
    assert_sensor_value(hass, hub_summary_id, 2)
