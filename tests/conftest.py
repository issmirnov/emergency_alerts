"""Test configuration for Emergency Alerts integration."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Emergency Alert",
        data={
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor",
            "trigger_state": "on",
            "severity": "warning",
            "group": "security",
            "on_triggered": [],
            "on_cleared": [],
            "on_escalated": [],
        },
        unique_id="test_alert_unique_id",
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
