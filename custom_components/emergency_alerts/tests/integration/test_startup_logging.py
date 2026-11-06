"""Regression test: setting up a hub must not dump its config at warning level.

Before the fix, ``async_setup_entry`` logged four ``[DEBUG]`` lines at WARNING
level for every config entry on every startup, one of them the entry's full
data. They were left over from diagnosing a translation bug, and they filled
the Home Assistant log with each hub's complete alert configuration.
"""

import logging

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN


@pytest.mark.integration
async def test_setup_logs_nothing_at_warning_level(hass: HomeAssistant, caplog):
    """A normal hub setup logs no warnings from the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Quiet Startup",
        data={
            "hub_type": "group",
            "group": "test",
            "hub_name": "test_quiet_startup",
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

    caplog.set_level(logging.DEBUG, logger="custom_components.emergency_alerts")
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    warnings = [
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("custom_components.emergency_alerts")
        and record.levelno >= logging.WARNING
    ]
    assert not warnings, (
        f"Hub setup logged at warning level: {warnings}. Startup log noise "
        "bug regressed."
    )
