"""Unit tests for trigger evaluation logic."""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from custom_components.emergency_alerts.binary_sensor import EmergencyBinarySensor
from custom_components.emergency_alerts.const import DOMAIN


@pytest.mark.unit
class TestSimpleTriggerEvaluation:
    """Test simple trigger evaluation."""

    @patch('custom_components.emergency_alerts.binary_sensor.async_dispatcher_send')
    def test_simple_trigger_matches_state(self, mock_dispatcher):
        """Test that simple trigger matches entity state."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        # Mock entity state
        mock_state = Mock()
        mock_state.state = "on"
        hass.states.get = Mock(return_value=mock_state)
        
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
        
        # Mock async_write_ha_state to avoid entity_id requirement
        sensor.async_write_ha_state = Mock()
        
        sensor._evaluate_trigger()
        assert sensor._is_on is True

    @patch('custom_components.emergency_alerts.binary_sensor.async_dispatcher_send')
    def test_simple_trigger_does_not_match_state(self, mock_dispatcher):
        """Test that simple trigger does not match different state."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        # Mock entity state
        mock_state = Mock()
        mock_state.state = "off"
        hass.states.get = Mock(return_value=mock_state)
        
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
        
        # Mock async_write_ha_state to avoid entity_id requirement
        sensor.async_write_ha_state = Mock()
        
        sensor._evaluate_trigger()
        assert sensor._is_on is False

    @patch('custom_components.emergency_alerts.binary_sensor.async_dispatcher_send')
    def test_simple_trigger_missing_entity(self, mock_dispatcher):
        """Test that simple trigger handles missing entity."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        # Mock entity state as None (entity doesn't exist)
        hass.states.get = Mock(return_value=None)
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.missing",
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
        
        # Mock async_write_ha_state to avoid entity_id requirement
        sensor.async_write_ha_state = Mock()
        
        sensor._evaluate_trigger()
        assert sensor._is_on is False


@pytest.mark.unit
class TestLogicalTriggerEvaluation:
    """Test logical trigger evaluation."""

    @patch('custom_components.emergency_alerts.binary_sensor.async_dispatcher_send')
    def test_logical_trigger_and_operator_all_true(self, mock_dispatcher):
        """Test logical trigger with AND operator when all conditions are true."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        # Mock entity states
        def mock_get(entity_id):
            mock_state = Mock()
            mock_state.state = "on"
            return mock_state
        
        hass.states.get = Mock(side_effect=mock_get)
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "logical",
            "logical_conditions": [
                {"entity_id": "binary_sensor.door", "state": "on"},
                {"entity_id": "binary_sensor.alarm", "state": "on"},
            ],
            "logical_operator": "and",
            "severity": "critical",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        # Mock async_write_ha_state to avoid entity_id requirement
        sensor.async_write_ha_state = Mock()
        
        sensor._evaluate_trigger()
        assert sensor._is_on is True

    @patch('custom_components.emergency_alerts.binary_sensor.async_dispatcher_send')
    def test_logical_trigger_and_operator_one_false(self, mock_dispatcher):
        """Test logical trigger with AND operator when one condition is false."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        # Mock entity states - one on, one off
        def mock_get(entity_id):
            mock_state = Mock()
            if entity_id == "binary_sensor.door":
                mock_state.state = "on"
            else:
                mock_state.state = "off"
            return mock_state
        
        hass.states.get = Mock(side_effect=mock_get)
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "logical",
            "logical_conditions": [
                {"entity_id": "binary_sensor.door", "state": "on"},
                {"entity_id": "binary_sensor.alarm", "state": "on"},
            ],
            "logical_operator": "and",
            "severity": "critical",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        # Mock async_write_ha_state to avoid entity_id requirement
        sensor.async_write_ha_state = Mock()
        
        sensor._evaluate_trigger()
        assert sensor._is_on is False

    @patch('custom_components.emergency_alerts.binary_sensor.async_dispatcher_send')
    def test_logical_trigger_or_operator_one_true(self, mock_dispatcher):
        """Test logical trigger with OR operator when one condition is true."""
        hass = Mock()
        entry = Mock()
        entry.entry_id = "test_entry"
        
        # Mock entity states - one on, one off
        def mock_get(entity_id):
            mock_state = Mock()
            if entity_id == "binary_sensor.door":
                mock_state.state = "on"
            else:
                mock_state.state = "off"
            return mock_state
        
        hass.states.get = Mock(side_effect=mock_get)
        
        alert_data = {
            "name": "Test Alert",
            "trigger_type": "logical",
            "logical_conditions": [
                {"entity_id": "binary_sensor.door", "state": "on"},
                {"entity_id": "binary_sensor.alarm", "state": "on"},
            ],
            "logical_operator": "or",
            "severity": "critical",
        }
        
        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="test_alert",
            alert_data=alert_data,
            group="security",
            hub_name="test_hub",
        )
        
        # Mock async_write_ha_state to avoid entity_id requirement
        sensor.async_write_ha_state = Mock()
        
        sensor._evaluate_trigger()
        assert sensor._is_on is True
