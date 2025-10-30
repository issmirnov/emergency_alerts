"""Test switch platform for Emergency Alerts integration."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.emergency_alerts.switch import (
    async_setup_entry,
    EmergencyAlertAcknowledgeSwitch,
    EmergencyAlertSnoozeSwitch,
    EmergencyAlertResolveSwitch,
)
from custom_components.emergency_alerts.const import (
    DOMAIN,
    STATE_ACKNOWLEDGED,
    STATE_SNOOZED,
    STATE_RESOLVED,
    SWITCH_TYPE_ACKNOWLEDGE,
    SWITCH_TYPE_SNOOZE,
    SWITCH_TYPE_RESOLVE,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry_123"
    entry.data = {
        "hub_type": "group",
        "hub_name": "test_hub",
        "alerts": {
            "test_alert": {
                "name": "Test Alert",
                "trigger_type": "simple",
                "entity_id": "binary_sensor.test",
                "trigger_state": "on",
                "severity": "warning",
                "snooze_duration": 300,
            }
        }
    }
    return entry


@pytest.fixture
def mock_binary_sensor():
    """Create a mock binary sensor entity."""
    sensor = Mock()
    sensor.entity_id = "binary_sensor.emergency_test_alert"
    sensor._alert_id = "test_alert"
    sensor._config_entry = Mock()
    sensor._config_entry.entry_id = "test_entry_123"
    sensor._acknowledged = False
    sensor._snoozed = False
    sensor._resolved = False
    sensor._escalated = False
    sensor._escalation_task = None
    sensor._snooze_task = None
    sensor._snooze_until = None
    sensor.is_on = False
    sensor.async_update_ha_state = AsyncMock()
    sensor._execute_action = AsyncMock()
    return sensor


@pytest.mark.asyncio
async def test_async_setup_entry_creates_switches(hass: HomeAssistant, mock_config_entry):
    """Test that async_setup_entry creates 3 switches per alert."""
    async_add_entities = Mock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    # Should create 3 switches (acknowledge, snooze, resolve)
    assert async_add_entities.called
    switches = async_add_entities.call_args[0][0]
    assert len(switches) == 3

    # Verify switch types
    switch_types = [type(s).__name__ for s in switches]
    assert "EmergencyAlertAcknowledgeSwitch" in switch_types
    assert "EmergencyAlertSnoozeSwitch" in switch_types
    assert "EmergencyAlertResolveSwitch" in switch_types


@pytest.mark.asyncio
async def test_async_setup_entry_skips_global_hub(hass: HomeAssistant):
    """Test that global hub doesn't create switches."""
    entry = Mock()
    entry.data = {"hub_type": "global"}
    async_add_entities = Mock()

    await async_setup_entry(hass, entry, async_add_entities)

    # Should not create any entities
    assert not async_add_entities.called


@pytest.mark.asyncio
async def test_acknowledge_switch_initialization(hass: HomeAssistant, mock_config_entry):
    """Test acknowledge switch initialization."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]

    switch = EmergencyAlertAcknowledgeSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )

    assert switch._switch_type == SWITCH_TYPE_ACKNOWLEDGE
    assert switch._attr_name == "Test Alert Acknowledged"
    assert switch._attr_unique_id == "test_entry_123_test_alert_acknowledged"
    assert switch._attr_icon == "mdi:check-circle-outline"
    assert switch._attr_is_on is False


@pytest.mark.asyncio
async def test_acknowledge_switch_turn_on(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test turning on acknowledge switch."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertAcknowledgeSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_acknowledged"

    # Mock the binary sensor lookup (preserve existing keys)
    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}

    await switch.async_turn_on()

    # Verify state changes
    assert mock_binary_sensor._acknowledged is True
    assert switch._attr_is_on is True

    # Verify escalation task cancelled
    if mock_binary_sensor._escalation_task:
        mock_binary_sensor._escalation_task.cancel.assert_called_once()


@pytest.mark.asyncio
async def test_acknowledge_switch_turn_off(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test turning off acknowledge switch."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertAcknowledgeSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_acknowledged"

    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}
    mock_binary_sensor._acknowledged = True
    mock_binary_sensor.is_on = True
    mock_binary_sensor._start_escalation_timer = AsyncMock()

    await switch.async_turn_off()

    # Verify state changes
    assert mock_binary_sensor._acknowledged is False
    assert switch._attr_is_on is False

    # Verify escalation timer restarted for active alert
    mock_binary_sensor._start_escalation_timer.assert_called_once()


@pytest.mark.asyncio
async def test_snooze_switch_initialization(hass: HomeAssistant, mock_config_entry):
    """Test snooze switch initialization."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]

    switch = EmergencyAlertSnoozeSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_snoozed"

    assert switch._switch_type == SWITCH_TYPE_SNOOZE
    assert switch._attr_name == "Test Alert Snoozed"
    assert switch._attr_unique_id == "test_entry_123_test_alert_snoozed"
    assert switch._attr_icon == "mdi:bell-sleep"
    assert switch._attr_is_on is False


@pytest.mark.asyncio
async def test_snooze_switch_turn_on(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test turning on snooze switch."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertSnoozeSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_snoozed"

    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}

    with patch("asyncio.create_task") as mock_create_task:
        await switch.async_turn_on()

    # Verify state changes
    assert mock_binary_sensor._snoozed is True
    assert switch._attr_is_on is True
    assert mock_binary_sensor._snooze_until is not None

    # Verify snooze task created
    mock_create_task.assert_called_once()

    # Verify snooze duration (should be 5 minutes from now)
    time_diff = (mock_binary_sensor._snooze_until - datetime.now()).total_seconds()
    assert 295 < time_diff < 305  # Allow 5 second margin


@pytest.mark.asyncio
async def test_snooze_switch_turn_off(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test turning off snooze switch (cancel snooze)."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertSnoozeSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_snoozed"

    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}

    # Set up snoozed state
    mock_binary_sensor._snoozed = True
    mock_binary_sensor._snooze_until = datetime.now() + timedelta(seconds=300)
    mock_cancel = Mock()
    mock_binary_sensor._snooze_task = Mock()
    mock_binary_sensor._snooze_task.cancel = mock_cancel

    await switch.async_turn_off()

    # Verify state changes
    assert mock_binary_sensor._snoozed is False
    assert mock_binary_sensor._snooze_until is None
    assert switch._attr_is_on is False

    # Verify snooze task cancelled (check the saved mock since _snooze_task is now None)
    mock_cancel.assert_called_once()


@pytest.mark.asyncio
async def test_snooze_timer_auto_expires(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test snooze timer automatically expires."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertSnoozeSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_snoozed"

    # Manually call the timer function with short duration
    await switch._snooze_timer(0.1, mock_binary_sensor)

    # After timer expires
    assert mock_binary_sensor._snoozed is False
    assert mock_binary_sensor._snooze_until is None
    assert switch._attr_is_on is False


@pytest.mark.asyncio
async def test_resolve_switch_initialization(hass: HomeAssistant, mock_config_entry):
    """Test resolve switch initialization."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]

    switch = EmergencyAlertResolveSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_resolved"

    assert switch._switch_type == SWITCH_TYPE_RESOLVE
    assert switch._attr_name == "Test Alert Resolved"
    assert switch._attr_unique_id == "test_entry_123_test_alert_resolved"
    assert switch._attr_icon == "mdi:check-circle"
    assert switch._attr_is_on is False


@pytest.mark.asyncio
async def test_resolve_switch_turn_on(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test turning on resolve switch."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertResolveSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_resolved"

    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}

    await switch.async_turn_on()

    # Verify state changes
    assert mock_binary_sensor._resolved is True
    assert switch._attr_is_on is True


@pytest.mark.asyncio
async def test_resolve_switch_turn_off(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test turning off resolve switch."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertResolveSwitch(
        hass, mock_config_entry, "test_alert", alert_data
    )
    switch.entity_id = "switch.emergency_test_alert_resolved"

    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}
    mock_binary_sensor._resolved = True

    await switch.async_turn_off()

    # Verify state changes
    assert mock_binary_sensor._resolved is False
    assert switch._attr_is_on is False


@pytest.mark.asyncio
async def test_switch_mutual_exclusivity(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test that switches enforce mutual exclusivity."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]

    ack_switch = EmergencyAlertAcknowledgeSwitch(hass, mock_config_entry, "test_alert", alert_data)
    ack_switch.entity_id = "switch.emergency_test_alert_acknowledged"
    snooze_switch = EmergencyAlertSnoozeSwitch(hass, mock_config_entry, "test_alert", alert_data)
    snooze_switch.entity_id = "switch.emergency_test_alert_snoozed"
    resolve_switch = EmergencyAlertResolveSwitch(hass, mock_config_entry, "test_alert", alert_data)
    resolve_switch.entity_id = "switch.emergency_test_alert_resolved"

    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}

    # Turn on acknowledge
    await ack_switch.async_turn_on()
    assert mock_binary_sensor._acknowledged is True

    # Turn on snooze - should turn off acknowledge
    with patch("asyncio.create_task"):
        await snooze_switch.async_turn_on()

    # After enforcement, acknowledged should be False
    assert mock_binary_sensor._acknowledged is False
    assert mock_binary_sensor._snoozed is True

    # Turn on resolve - should turn off snooze
    await resolve_switch.async_turn_on()

    # After enforcement, snoozed should be False
    assert mock_binary_sensor._snoozed is False
    assert mock_binary_sensor._resolved is True


@pytest.mark.asyncio
async def test_switch_handles_missing_binary_sensor(hass: HomeAssistant, mock_config_entry):
    """Test switches handle missing binary sensor gracefully."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    switch = EmergencyAlertAcknowledgeSwitch(hass, mock_config_entry, "test_alert", alert_data)
    switch.entity_id = "switch.emergency_test_alert_acknowledged"

    hass.data[DOMAIN] = {"entities": []}  # No binary sensor

    # Should not raise exception
    await switch.async_turn_on()
    await switch.async_turn_off()


@pytest.mark.asyncio
async def test_switch_executes_configured_actions(hass: HomeAssistant, mock_config_entry, mock_binary_sensor):
    """Test that switches execute configured actions."""
    alert_data = mock_config_entry.data["alerts"]["test_alert"]
    alert_data["on_acknowledged"] = [{"service": "notify.test", "data": {}}]

    switch = EmergencyAlertAcknowledgeSwitch(hass, mock_config_entry, "test_alert", alert_data)
    switch.entity_id = "switch.emergency_test_alert_acknowledged"

    hass.data[DOMAIN] = {"entities": [mock_binary_sensor]}

    await switch.async_turn_on()

    # Verify action executed
    mock_binary_sensor._execute_action.assert_called_once_with(alert_data["on_acknowledged"])
