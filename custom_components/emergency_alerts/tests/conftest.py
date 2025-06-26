"""Test configuration for Emergency Alerts integration."""

import pytest
from unittest.mock import Mock, AsyncMock
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.const import DOMAIN

# Simple Home Assistant fixture for testing
@pytest.fixture
async def hass():
    """Create a test Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.states = Mock()
    hass.states.async_set = Mock()
    hass.services = Mock()
    hass.services.async_call = AsyncMock()
    hass.services.has_service = Mock(return_value=True)
    hass.config_entries = Mock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.data = {}
    return hass

# Mock entities fixture for sensor tests
@pytest.fixture
def mock_entities():
    """Create mock entities for sensor testing."""
    entity1 = Mock()
    entity1.is_on = True
    entity1._severity = "critical"
    entity1._group = "security"
    
    entity2 = Mock()
    entity2.is_on = True
    entity2._severity = "warning"
    entity2._group = "security"
    
    entity3 = Mock()
    entity3.is_on = False
    entity3._severity = "info"
    entity3._group = "safety"
    
    return [entity1, entity2, entity3]

# Create a simple MockConfigEntry that doesn't require the HA plugin
class MockConfigEntry:
    """Mock config entry for testing."""
    
    def __init__(self, domain: str, data: dict, title: str = "Test Entry", unique_id: str = None):
        self.domain = domain
        self.data = data
        self.title = title
        self.unique_id = unique_id or "test_unique_id"
        self.entry_id = "test_entry_id"
        self.state = "loaded"

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
