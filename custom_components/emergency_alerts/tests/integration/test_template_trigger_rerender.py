"""Regression test for bug 7: template-trigger alerts must re-evaluate on state changes.

Before the fix, ``async_track_state_change_event(hass, [], state_change)`` was
called with an empty entity list for template triggers, which subscribes to
nothing. Template alerts then never re-evaluated and would latch on/off until
the next integration reload.

The fix replaces that with ``async_track_template_result`` which subscribes to
the entities referenced inside the Jinja template.
"""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN


@pytest.fixture
async def template_alert_hub(hass: HomeAssistant):
    """Hub with one template-trigger alert that watches an external sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Template Group",
        data={
            "hub_type": "group",
            "group": "test",
            "hub_name": "test_template_hub",
            "alerts": {
                "rerender_alert": {
                    "name": "Rerender Alert",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.watched_value') | float(0) > 50 }}",
                    "severity": "warning",
                },
            },
        },
    )
    entry.add_to_hass(hass)

    # Seed the watched entity below threshold before setup so the alert
    # starts in the off state.
    hass.states.async_set("sensor.watched_value", "10")

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.integration
async def test_template_trigger_reevaluates_on_referenced_entity_change(
    hass: HomeAssistant, template_alert_hub
):
    """Bug 7: template alerts should flip on/off when the watched entity changes.

    Before the fix, this test would fail because async_track_state_change_event
    was passed an empty entity list, so the binary_sensor never re-evaluated.
    """
    # Find the alert entity (entity_id format varies across branches — clean
    # form lands in PR #13). Match by name fragment to be robust.
    candidates = [
        s.entity_id
        for s in hass.states.async_all()
        if s.entity_id.startswith("binary_sensor.") and "rerender_alert" in s.entity_id
    ]
    assert candidates, (
        f"No rerender_alert binary_sensor found. All entities: "
        f"{[s.entity_id for s in hass.states.async_all()]}"
    )
    alert = candidates[0]

    # Initial state: watched=10 (below 50) so alert is off.
    assert hass.states.get(alert).state == "off"

    # Move watched value above threshold — alert should flip ON.
    hass.states.async_set("sensor.watched_value", "75")
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "on", (
        "Template alert did not re-evaluate when its referenced entity changed. "
        "Bug 7 regressed."
    )

    # Move back below threshold — alert should flip OFF again.
    hass.states.async_set("sensor.watched_value", "25")
    await hass.async_block_till_done()
    assert hass.states.get(alert).state == "off", (
        "Template alert did not re-evaluate on second change. Bug 7 regressed."
    )
