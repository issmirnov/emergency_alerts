"""State manipulation utilities using hass.states."""

from typing import Any, Dict, Optional
from homeassistant.core import HomeAssistant


def set_entity_state(
    hass: HomeAssistant,
    entity_id: str,
    state: str,
    attributes: Dict[str, Any] | None = None
) -> None:
    """Set an entity state in Home Assistant."""
    if attributes is None:
        attributes = {}
    hass.states.async_set(entity_id, state, attributes)


def get_entity_state(hass: HomeAssistant, entity_id: str) -> Optional[Any]:
    """Get an entity state from Home Assistant."""
    return hass.states.get(entity_id)


def assert_entity_state(
    hass: HomeAssistant,
    entity_id: str,
    expected_state: str,
    expected_attributes: Dict[str, Any] | None = None
) -> None:
    """Assert an entity has the expected state and attributes."""
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"
    assert state.state == expected_state, \
        f"Expected state '{expected_state}' but got '{state.state}' for {entity_id}"
    
    if expected_attributes:
        for key, value in expected_attributes.items():
            assert key in state.attributes, \
                f"Attribute '{key}' not found in {entity_id}"
            assert state.attributes[key] == value, \
                f"Expected {key}={value} but got {key}={state.attributes[key]} for {entity_id}"


def assert_entity_exists(hass: HomeAssistant, entity_id: str) -> None:
    """Assert an entity exists."""
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} does not exist"


def assert_entity_not_exists(hass: HomeAssistant, entity_id: str) -> None:
    """Assert an entity does not exist."""
    state = hass.states.get(entity_id)
    assert state is None, f"Entity {entity_id} exists but should not"


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
