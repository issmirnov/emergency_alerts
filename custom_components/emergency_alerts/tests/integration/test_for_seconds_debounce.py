"""Integration tests for the ``for_seconds`` debounce field.

The alert fires only after the trigger has been continuously true for the
configured number of seconds. If the trigger clears before the dwell time
elapses, no alert fires.

Common use cases:
  - "Window open for >5 minutes"
  - "Garage open too long"
  - "Water leak sensor on for >10 seconds (debounce false positives)"
"""
from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.emergency_alerts.const import DOMAIN
from custom_components.emergency_alerts.tests.helpers.state_helpers import (
    set_entity_state,
)


async def _setup_hub(hass: HomeAssistant, alert_config: dict) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - For Seconds Test",
        data={
            "hub_type": "group",
            "group": "test",
            "hub_name": "test_for_seconds",
            "alerts": {"sustain_alert": alert_config},
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.integration
async def test_for_seconds_zero_fires_immediately(hass: HomeAssistant):
    """for_seconds=0 (or absent) preserves the old immediate-fire behavior."""
    await _setup_hub(hass, {
        "name": "Sustain Alert",
        "trigger_type": "simple",
        "entity_id": "binary_sensor.zero_sustain_source",
        "trigger_state": "on",
        "severity": "warning",
        # No for_seconds key set
    })
    alert = "binary_sensor.emergency_sustain_alert"

    # Trigger on — alert fires same tick.
    set_entity_state(hass, "binary_sensor.zero_sustain_source", "on")
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "on"

    # Trigger off — alert clears same tick.
    set_entity_state(hass, "binary_sensor.zero_sustain_source", "off")
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "off"


@pytest.mark.integration
async def test_for_seconds_holds_then_fires(hass: HomeAssistant):
    """With for_seconds=60, alert stays off for the dwell time then fires."""
    await _setup_hub(hass, {
        "name": "Sustain Alert",
        "trigger_type": "simple",
        "entity_id": "binary_sensor.hold_source",
        "trigger_state": "on",
        "severity": "warning",
        "for_seconds": 60,
    })
    alert = "binary_sensor.emergency_sustain_alert"

    # Trigger on — alert does NOT fire immediately.
    set_entity_state(hass, "binary_sensor.hold_source", "on")
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "off", "Alert should hold for dwell time"

    # Still under 60s — still off.
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "off"

    # Past 60s — alert fires.
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "on", "Alert should fire after dwell time"


@pytest.mark.integration
async def test_for_seconds_cancels_if_trigger_clears_during_dwell(hass: HomeAssistant):
    """If the trigger clears before the dwell elapses, the alert never fires."""
    await _setup_hub(hass, {
        "name": "Sustain Alert",
        "trigger_type": "simple",
        "entity_id": "binary_sensor.flap_source",
        "trigger_state": "on",
        "severity": "warning",
        "for_seconds": 60,
    })
    alert = "binary_sensor.emergency_sustain_alert"

    # Trigger on — dwell timer armed
    set_entity_state(hass, "binary_sensor.flap_source", "on")
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "off"

    # Trigger clears before 60s
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=20))
    await hass.async_block_till_done()
    set_entity_state(hass, "binary_sensor.flap_source", "off")
    await hass.async_block_till_done()

    # Even past 60s, alert should NOT fire — the dwell was cancelled.
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=120))
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "off", "Cancelled dwell should not fire"


@pytest.mark.integration
async def test_for_seconds_works_with_template_triggers(hass: HomeAssistant):
    """Debounce applies uniformly to template-trigger alerts as well."""
    await _setup_hub(hass, {
        "name": "Sustain Alert",
        "trigger_type": "template",
        "template": "{{ states('sensor.tpl_source') | int(0) > 50 }}",
        "severity": "warning",
        "for_seconds": 30,
    })
    alert = "binary_sensor.emergency_sustain_alert"

    # Push value above threshold — alert should NOT fire immediately
    hass.states.async_set("sensor.tpl_source", "75")
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "off"

    # After dwell — alert fires
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "on"
