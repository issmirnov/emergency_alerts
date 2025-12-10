"""Unit tests for action parsing logic."""

import json
import pytest
import yaml

from custom_components.emergency_alerts.binary_sensor import _parse_actions, _parse_logical_conditions


@pytest.mark.unit
class TestActionParsing:
    """Test action parsing functionality."""

    def test_parse_empty_action(self):
        """Test parsing empty action."""
        assert _parse_actions(None) == []
        assert _parse_actions("") == []
        assert _parse_actions([]) == []

    def test_parse_list_action(self):
        """Test parsing action that is already a list."""
        action_list = [{"service": "notify.test", "data": {"message": "test"}}]
        assert _parse_actions(action_list) == action_list

    def test_parse_json_action(self):
        """Test parsing JSON action string."""
        json_str = '[{"service": "notify.test", "data": {"message": "test"}}]'
        result = _parse_actions(json_str)
        assert len(result) == 1
        assert result[0]["service"] == "notify.test"
        assert result[0]["data"]["message"] == "test"

    def test_parse_yaml_action(self):
        """Test parsing YAML action string."""
        yaml_str = """
        - service: notify.test
          data:
            message: test
        """
        result = _parse_actions(yaml_str)
        assert len(result) == 1
        assert result[0]["service"] == "notify.test"
        assert result[0]["data"]["message"] == "test"

    def test_parse_invalid_json_falls_back_to_yaml(self):
        """Test that invalid JSON falls back to YAML."""
        yaml_str = """
        - service: notify.test
          data:
            message: test
        """
        result = _parse_actions(yaml_str)
        assert len(result) == 1

    def test_parse_invalid_action_returns_empty_list(self):
        """Test that invalid action string returns empty list."""
        invalid_str = "not valid json or yaml {"
        result = _parse_actions(invalid_str)
        assert result == []

    def test_parse_multiple_actions(self):
        """Test parsing multiple actions."""
        json_str = json.dumps([
            {"service": "notify.test1", "data": {}},
            {"service": "notify.test2", "data": {}}
        ])
        result = _parse_actions(json_str)
        assert len(result) == 2
        assert result[0]["service"] == "notify.test1"
        assert result[1]["service"] == "notify.test2"


@pytest.mark.unit
class TestLogicalConditionsParsing:
    """Test logical conditions parsing functionality."""

    def test_parse_empty_conditions(self):
        """Test parsing empty conditions."""
        assert _parse_logical_conditions(None) == []
        assert _parse_logical_conditions("") == []
        assert _parse_logical_conditions([]) == []

    def test_parse_list_conditions(self):
        """Test parsing conditions that are already a list."""
        conditions = [
            {"entity_id": "binary_sensor.test1", "state": "on"},
            {"entity_id": "binary_sensor.test2", "state": "off"}
        ]
        assert _parse_logical_conditions(conditions) == conditions

    def test_parse_json_conditions(self):
        """Test parsing JSON conditions string."""
        json_str = json.dumps([
            {"entity_id": "binary_sensor.test1", "state": "on"}
        ])
        result = _parse_logical_conditions(json_str)
        assert len(result) == 1
        assert result[0]["entity_id"] == "binary_sensor.test1"
        assert result[0]["state"] == "on"

    def test_parse_yaml_conditions(self):
        """Test parsing YAML conditions string."""
        yaml_str = """
        - entity_id: binary_sensor.test1
          state: "on"
        """
        result = _parse_logical_conditions(yaml_str)
        assert len(result) == 1
        assert result[0]["entity_id"] == "binary_sensor.test1"
        # YAML converts "on" to boolean True, so we check for either
        assert result[0]["state"] in ("on", True)

    def test_parse_invalid_conditions_returns_empty_list(self):
        """Test that invalid conditions string returns empty list."""
        invalid_str = "not valid json or yaml {"
        result = _parse_logical_conditions(invalid_str)
        assert result == []
