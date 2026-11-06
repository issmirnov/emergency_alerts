"""Regression test: an acknowledgement must end with its incident.

Before the fix, ``_apply_cleared_state()`` reset ``_resolved`` and
``_escalated`` when the trigger condition cleared, but left ``_acknowledged``
set. While the alert was off, the State select still read "acknowledged".
When the condition came back, the new incident started out acknowledged: the
select and the status sensor said so before anyone had seen it, and warning
and critical alerts never armed their escalation timer.
"""

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    MockConfigEntry,
)

from custom_components.emergency_alerts.const import DOMAIN

SOURCE = "binary_sensor.door"
ALERT = "binary_sensor.emergency_door_alert"
STATE_SELECT = "select.door_alert_state"
STATUS_SENSOR = "sensor.emergency_door_alert_status"
REMIND_AFTER = 60


@pytest.fixture
async def door_alert_hub(hass: HomeAssistant) -> MockConfigEntry:
    """Hub with one warning alert that escalates after REMIND_AFTER seconds."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Acknowledgement Carry-over",
        data={
            "hub_type": "group",
            "group": "test",
            "hub_name": "test_ack_carryover",
            "alerts": {
                "door_alert": {
                    "name": "Door Alert",
                    "trigger_type": "simple",
                    "entity_id": SOURCE,
                    "trigger_state": "on",
                    "severity": "warning",
                    "remind_after_seconds": REMIND_AFTER,
                },
            },
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set(SOURCE, "off")
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _acknowledge_then_clear(hass: HomeAssistant) -> None:
    """Fire the alert, acknowledge it with the State select, then clear it."""
    hass.states.async_set(SOURCE, "on")
    await hass.async_block_till_done()
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": STATE_SELECT, "option": "acknowledged"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(STATE_SELECT).state == "acknowledged"

    hass.states.async_set(SOURCE, "off")
    await hass.async_block_till_done()


@pytest.mark.integration
async def test_cleared_alert_is_no_longer_acknowledged(
    hass: HomeAssistant, door_alert_hub
):
    """Once the condition clears, nothing reads "acknowledged" any more."""
    await _acknowledge_then_clear(hass)

    assert hass.states.get(ALERT).attributes["acknowledged"] is False, (
        "The acknowledgement survived the clear. Acknowledgement carry-over "
        "bug regressed."
    )
    assert hass.states.get(STATE_SELECT).state == "inactive", (
        "The State select still reads acknowledged after the clear. "
        "Acknowledgement carry-over bug regressed."
    )


@pytest.mark.integration
async def test_next_incident_starts_unacknowledged(hass: HomeAssistant, door_alert_hub):
    """A new incident reads "active" on every surface."""
    await _acknowledge_then_clear(hass)

    hass.states.async_set(SOURCE, "on")
    await hass.async_block_till_done()

    assert hass.states.get(ALERT).attributes["status"] == "active", (
        "The new incident inherited the old acknowledgement. Acknowledgement "
        "carry-over bug regressed."
    )
    assert hass.states.get(STATUS_SENSOR).state == "active"
    assert hass.states.get(STATE_SELECT).state == "active"


@pytest.mark.integration
async def test_next_incident_escalates(hass: HomeAssistant, door_alert_hub):
    """The new incident arms its escalation timer again."""
    await _acknowledge_then_clear(hass)

    hass.states.async_set(SOURCE, "on")
    await hass.async_block_till_done()
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=REMIND_AFTER + 1)
    )
    await hass.async_block_till_done()

    assert hass.states.get(ALERT).attributes["status"] == "escalated", (
        "The new incident never escalated: the stale acknowledgement skipped "
        "its escalation timer. Acknowledgement carry-over bug regressed."
    )
