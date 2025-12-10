"""Unit tests for state machine logic."""

import pytest
from unittest.mock import Mock

from custom_components.emergency_alerts.binary_sensor import EmergencyBinarySensor
from custom_components.emergency_alerts.const import (
    STATE_INACTIVE,
    STATE_ACTIVE,
    STATE_ACKNOWLEDGED,
    STATE_SNOOZED,
    STATE_ESCALATED,
    STATE_RESOLVED,
)


@pytest.mark.unit
class TestStateMachine:
    """Test state machine transitions."""

    def test_get_status_inactive(self):
        """Test status when alert is inactive."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test",
            "trigger_state": "on",
            "severity": "warning",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        sensor._is_on = False
        assert sensor.get_status() == STATE_INACTIVE

    def test_get_status_active(self):
        """Test status when alert is active."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test",
            "trigger_state": "on",
            "severity": "warning",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        sensor._is_on = True
        sensor._acknowledged = False
        sensor._snoozed = False
        sensor._escalated = False
        sensor._resolved = False
        
        assert sensor.get_status() == STATE_ACTIVE

    def test_get_status_acknowledged(self):
        """Test status when alert is acknowledged."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test",
            "trigger_state": "on",
            "severity": "warning",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        sensor._is_on = True
        sensor._acknowledged = True
        sensor._snoozed = False
        sensor._escalated = False
        sensor._resolved = False
        
        assert sensor.get_status() == STATE_ACKNOWLEDGED

    def test_get_status_snoozed(self):
        """Test status when alert is snoozed."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test",
            "trigger_state": "on",
            "severity": "warning",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        sensor._is_on = True
        sensor._acknowledged = False
        sensor._snoozed = True
        sensor._escalated = False
        sensor._resolved = False
        
        assert sensor.get_status() == STATE_SNOOZED

    def test_get_status_escalated(self):
        """Test status when alert is escalated."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test",
            "trigger_state": "on",
            "severity": "warning",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        sensor._is_on = True
        sensor._acknowledged = False
        sensor._snoozed = False
        sensor._escalated = True
        sensor._resolved = False
        
        assert sensor.get_status() == STATE_ESCALATED

    def test_get_status_resolved(self):
        """Test status when alert is resolved."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test",
            "trigger_state": "on",
            "severity": "warning",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        sensor._is_on = True
        sensor._acknowledged = False
        sensor._snoozed = False
        sensor._escalated = False
        sensor._resolved = True
        
        assert sensor.get_status() == STATE_RESOLVED

    def test_get_status_priority_order(self):
        """Test that resolved has priority over other states."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test",
            "trigger_state": "on",
            "severity": "warning",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        sensor._is_on = True
        sensor._acknowledged = True
        sensor._snoozed = True
        sensor._escalated = True
        sensor._resolved = True
        
        # Resolved should have highest priority
        assert sensor.get_status() == STATE_RESOLVED
