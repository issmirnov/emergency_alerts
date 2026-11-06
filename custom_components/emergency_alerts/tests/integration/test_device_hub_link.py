"""Regression test: alert devices must link to their hub without `via_device`.

Before the fix, each alert's device info carried
``"via_device": (DOMAIN, f"hub_{entry_id}")``. Home Assistant passes device
info straight to ``DeviceRegistry.async_get_or_create``, where ``via_device`` is
deprecated: HA 2026.10 logs a warning for it on every startup, and HA 2027.8
stops accepting it. Its replacement, ``via_device_id``, is not a device info
key in HA 2026.2, the oldest version this integration supports.

The fix leaves ``via_device`` out of the device info and links each alert
device to its hub through the device registry once the platforms are set up.
"""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN


@pytest.mark.integration
async def test_alert_device_links_to_hub_without_via_device(hass: HomeAssistant):
    """The alert device hangs off its hub, and no call passes `via_device`."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Hub Link",
        data={
            "hub_type": "group",
            "group": "test",
            "hub_name": "test_hub_link",
            "alerts": {
                "door_alert": {
                    "name": "Door Alert",
                    "trigger_type": "simple",
                    "entity_id": "binary_sensor.door",
                    "trigger_state": "on",
                    "severity": "warning",
                },
            },
        },
    )
    entry.add_to_hass(hass)

    calls = []
    original = dr.DeviceRegistry.async_get_or_create

    def spy(self, *args, **kwargs):
        calls.append(kwargs)
        return original(self, *args, **kwargs)

    with patch.object(dr.DeviceRegistry, "async_get_or_create", spy):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert not [call for call in calls if "via_device" in call], (
        "A device was registered with the deprecated via_device parameter. "
        "via_device deprecation bug regressed."
    )

    dev_reg = dr.async_get(hass)
    hub = dev_reg.async_get_device(identifiers={(DOMAIN, f"hub_{entry.entry_id}")})
    alert = dev_reg.async_get_device(
        identifiers={(DOMAIN, f"alert_{entry.entry_id}_door_alert")}
    )
    assert hub is not None and alert is not None
    assert alert.via_device_id == hub.id, "The alert device lost its hub link."
