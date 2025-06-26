"""Test the Emergency Alerts integration setup."""

from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts import async_setup_entry, async_unload_entry
from custom_components.emergency_alerts.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Test setting up a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Test setup
    result = await async_setup_entry(hass, mock_config_entry)
    assert result is True

    # Check that the service is registered
    assert hass.services.has_service(DOMAIN, "acknowledge")

    # Check that platforms are forwarded (2 calls: binary_sensor and sensor)
    assert hass.async_create_task.call_count == 2
    # The async_forward_entry_setup should be called for both binary_sensor and sensor
    assert hass.config_entries.async_forward_entry_setup.call_count == 2


async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Setup first
    await async_setup_entry(hass, mock_config_entry)

    # Test unload
    result = await async_unload_entry(hass, mock_config_entry)
    assert result is True


async def test_multiple_config_entries(hass: HomeAssistant, mock_config_entry):
    """Test setting up multiple config entries."""
    # Create multiple config entries
    entry1 = mock_config_entry
    from custom_components.emergency_alerts.tests.conftest import MockConfigEntry

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
