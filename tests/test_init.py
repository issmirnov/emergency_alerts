"""Test the Emergency Alerts integration setup."""

import pytest
from typing import Any, Dict
from homeassistant.core import HomeAssistant

class MockConfigEntry:
    """Mock config entry for testing."""
    
    def __init__(self, domain: str, data: Dict[str, Any], entry_id: str = "test_entry_id"):
        self.domain = domain
        self.data = data
        self.entry_id = entry_id
        self.title = "Test Entry"
        self.state = "loaded"
        
    def add_to_hass(self, hass: HomeAssistant):
        """Add this entry to hass."""
        if not hasattr(hass, 'config_entries'):
            from homeassistant.config_entries import ConfigEntries
            hass.config_entries = ConfigEntries(hass, {})
        hass.config_entries._entries[self.entry_id] = self

from custom_components.emergency_alerts import async_setup_entry, async_unload_entry
from custom_components.emergency_alerts.const import DOMAIN

@pytest.mark.asyncio
async def test_setup_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test setting up a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Test setup
    result = await async_setup_entry(hass, mock_config_entry)
    assert result is True

    # Check that the service is registered
    assert hass.services.has_service(DOMAIN, "acknowledge")

    # Check that platforms are forwarded
    assert len(hass.config_entries.async_forward_entry_setups.call_args_list) >= 2

    assert DOMAIN in hass.data
    assert hass.data[DOMAIN]["entities"] == []

@pytest.mark.asyncio
async def test_unload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Setup first
    await async_setup_entry(hass, mock_config_entry)

    assert DOMAIN in hass.data

    # Test unload
    result = await async_unload_entry(hass, mock_config_entry)
    assert result is True

    assert DOMAIN not in hass.data

async def test_multiple_config_entries(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test setting up multiple config entries."""
    # Create multiple config entries
    entry1 = mock_config_entry
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        title="Test Alert 2",
        data={
            "name": "Test Alert 2",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor_2",
            "trigger_state": "on",
            "severity": "critical",
            "group": "safety",
        },
        unique_id="test_alert_2_unique_id",
    )

    entry1.add_to_hass(hass)
    entry2.add_to_hass(hass)

    # Setup both
    result1 = await async_setup_entry(hass, entry1)
    result2 = await async_setup_entry(hass, entry2)

    assert result1 is True
    assert result2 is True

    # Service should still be registered (only once)
    assert hass.services.has_service(DOMAIN, "acknowledge")
