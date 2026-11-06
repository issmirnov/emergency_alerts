"""Regression test: alert service calls must reach the alerts they name.

Before the fix, the acknowledge, clear and escalate handlers compared each
alert's entity_id with ``call.data["entity_id"]`` using ``==``. Home Assistant
turns ``target: entity_id:`` into a list, and so does any caller that names
several alerts. The comparison never matched, so the call did nothing and
raised no error. Only a bare string under ``data:`` worked.

Even then, the State select never heard about the change and kept showing
its old option.
"""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN

FRONT_SOURCE = "binary_sensor.front_door"
BACK_SOURCE = "binary_sensor.back_door"
FRONT = "binary_sensor.emergency_front_door"
BACK = "binary_sensor.emergency_back_door"


def _door_alert(name: str, source: str) -> dict:
    return {
        "name": name,
        "trigger_type": "simple",
        "entity_id": source,
        "trigger_state": "on",
        "severity": "warning",
    }


@pytest.fixture
async def two_door_alerts(hass: HomeAssistant) -> MockConfigEntry:
    """Hub with two alerts, both firing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Service Targets",
        data={
            "hub_type": "group",
            "group": "test",
            "hub_name": "test_service_targets",
            "alerts": {
                "front_door": _door_alert("Front Door", FRONT_SOURCE),
                "back_door": _door_alert("Back Door", BACK_SOURCE),
            },
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(FRONT_SOURCE, "on")
    hass.states.async_set(BACK_SOURCE, "on")
    await hass.async_block_till_done()
    assert hass.states.get(FRONT).state == "on"
    assert hass.states.get(BACK).state == "on"
    return entry


@pytest.mark.integration
async def test_acknowledge_from_a_script_with_target(
    hass: HomeAssistant, two_door_alerts
):
    """The usual YAML form, ``target: entity_id:``, acknowledges the alert."""
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "acknowledge_front_door": {
                    "sequence": [
                        {
                            "action": f"{DOMAIN}.acknowledge",
                            "target": {"entity_id": FRONT},
                        }
                    ]
                }
            }
        },
    )
    await hass.services.async_call("script", "acknowledge_front_door", blocking=True)
    await hass.async_block_till_done()

    assert (
        hass.states.get(FRONT).attributes["status"] == "acknowledged"
    ), "acknowledge with target: did nothing. Service entity_id list bug regressed."
    status_sensor = hass.states.get("sensor.emergency_front_door_status")
    assert status_sensor.state == "acknowledged"
    assert (
        hass.states.get("select.front_door_state").state == "acknowledged"
    ), "The State select did not follow the acknowledge service."
    assert hass.states.get(BACK).attributes["status"] == "active"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("service", "expected_status"),
    [
        ("acknowledge", "acknowledged"),
        ("clear", "inactive"),
        ("escalate", "escalated"),
    ],
)
async def test_service_handles_every_alert_in_a_list(
    hass: HomeAssistant, two_door_alerts, service: str, expected_status: str
):
    """A list of entity IDs reaches every alert in it."""
    await hass.services.async_call(
        DOMAIN, service, {"entity_id": [FRONT, BACK]}, blocking=True
    )
    await hass.async_block_till_done()

    for alert in (FRONT, BACK):
        assert hass.states.get(alert).attributes["status"] == expected_status, (
            f"{service} with a list of entity IDs skipped {alert}. Service "
            "entity_id list bug regressed."
        )


@pytest.mark.integration
async def test_clear_service_updates_the_state_select(
    hass: HomeAssistant, two_door_alerts
):
    """The State select follows a service call, here a plain-string clear."""
    await hass.services.async_call(DOMAIN, "clear", {"entity_id": FRONT}, blocking=True)
    await hass.async_block_till_done()

    assert (
        hass.states.get("select.front_door_state").state == "inactive"
    ), "The State select did not follow the clear service."
