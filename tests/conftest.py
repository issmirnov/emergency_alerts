"""Test configuration for Emergency Alerts integration."""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, patch
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.setup import async_setup_component
from homeassistant.const import EVENT_HOMEASSISTANT_START

from custom_components.emergency_alerts.const import DOMAIN

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

@pytest_asyncio.fixture
async def hass():
    """Create a test Home Assistant instance."""
    from homeassistant.core import HomeAssistant
    from homeassistant.util.unit_system import METRIC_SYSTEM
    from homeassistant.config_entries import ConfigEntries
    
    hass = HomeAssistant("/tmp")
    hass.config.units = METRIC_SYSTEM
    hass.config.config_dir = "/tmp"
    hass.config.skip_pip = True
    
    # Initialize config entries
    hass.config_entries = ConfigEntries(hass, {})
    
    # Start the event loop
    await hass.async_start()
    
    # Fire the start event
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    
    yield hass
    
    # Clean up
    await hass.async_stop()

@pytest.fixture
def mock_config_entry():
    """Mock config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor",
            "trigger_state": "on",
            "severity": "warning",
            "group": "security"
        }
    )


@pytest.fixture
def mock_template_config_entry():
    """Return a mock config entry with template trigger for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Template Alert",
        data={
            "name": "Template Alert",
            "trigger_type": "template",
            "template": "{{ states('sensor.temperature') | float > 30 }}",
            "severity": "critical",
            "group": "environment",
            "on_triggered": [
                {"service": "notify.notify", "data": {"message": "High temp!"}}
            ],
            "on_cleared": [],
            "on_escalated": [],
        },
        unique_id="test_template_alert_unique_id",
    )


@pytest.fixture
def mock_logical_config_entry():
    """Return a mock config entry with logical trigger for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Logical Alert",
        data={
            "name": "Logical Alert",
            "trigger_type": "logical",
            "logical_conditions": [
                {
                    "type": "simple",
                    "entity_id": "binary_sensor.door",
                    "trigger_state": "on",
                },
                {
                    "type": "simple",
                    "entity_id": "binary_sensor.alarm",
                    "trigger_state": "on",
                },
            ],
            "severity": "critical",
            "group": "security",
            "on_triggered": [],
            "on_cleared": [],
            "on_escalated": [],
        },
        unique_id="test_logical_alert_unique_id",
    )
