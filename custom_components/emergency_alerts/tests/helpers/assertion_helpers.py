"""Custom assertions for HA entities."""

from typing import Any, Dict, Optional
from homeassistant.core import HomeAssistant, State


def assert_entity_has_attribute(
    state: State | None,
    attribute_name: str,
    expected_value: Any | None = None
) -> None:
    """Assert an entity has a specific attribute, optionally with a value."""
    assert state is not None, "Entity state is None"
    assert attribute_name in state.attributes, \
        f"Entity {state.entity_id} missing attribute '{attribute_name}'"
    
    if expected_value is not None:
        actual_value = state.attributes[attribute_name]
        assert actual_value == expected_value, \
            f"Entity {state.entity_id} attribute '{attribute_name}' expected {expected_value}, got {actual_value}"


def assert_entity_state_matches(
    state: State | None,
    expected_state: str,
    expected_attributes: Dict[str, Any] | None = None
) -> None:
    """Assert entity state and attributes match expected values."""
    assert state is not None, "Entity state is None"
    assert state.state == expected_state, \
        f"Entity {state.entity_id} state expected '{expected_state}', got '{state.state}'"
    
    if expected_attributes:
        for key, value in expected_attributes.items():
            assert_entity_has_attribute(state, key, value)


def assert_binary_sensor_is_on(hass: HomeAssistant, entity_id: str) -> None:
    """Assert a binary sensor is on."""
    state = hass.states.get(entity_id)
    assert state is not None, f"Binary sensor {entity_id} not found"
    assert state.state == "on", \
        f"Binary sensor {entity_id} expected to be 'on', got '{state.state}'"


def assert_binary_sensor_is_off(hass: HomeAssistant, entity_id: str) -> None:
    """Assert a binary sensor is off."""
    state = hass.states.get(entity_id)
    assert state is not None, f"Binary sensor {entity_id} not found"
    assert state.state == "off", \
        f"Binary sensor {entity_id} expected to be 'off', got '{state.state}'"


def assert_sensor_value(
    hass: HomeAssistant,
    entity_id: str,
    expected_value: Any
) -> None:
    """Assert a sensor has the expected value."""
    state = hass.states.get(entity_id)
    assert state is not None, f"Sensor {entity_id} not found"
    assert state.state == str(expected_value), \
        f"Sensor {entity_id} expected value '{expected_value}', got '{state.state}'"
