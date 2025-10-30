"""Test the Emergency Alerts integration setup."""

from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts import async_setup_entry, async_unload_entry
from custom_components.emergency_alerts.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Test setting up a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Use the proper HA config entry setup flow
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that the service is registered
    assert hass.services.has_service(DOMAIN, "acknowledge")

    # Check that entry is loaded
    assert mock_config_entry.state.name == "LOADED"


async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Setup first using proper HA flow
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Test unload
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state.name == "NOT_LOADED"


async def test_multiple_config_entries(hass: HomeAssistant, mock_config_entry):
    """Test setting up multiple config entries."""
    # Create multiple config entries
    entry1 = mock_config_entry
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry2 = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Test Alert 2",
        data={
            "hub_type": "group",
            "group": "safety",
            "hub_name": "test_hub_2",
            "alerts": {
                "test_alert_2": {
                    "name": "Test Alert 2",
                    "trigger_type": "simple",
                    "entity_id": "binary_sensor.test_sensor_2",
                    "trigger_state": "on",
                    "severity": "critical",
                },
            },
        },
        unique_id="test_alert_2_unique_id",
    )

    entry1.add_to_hass(hass)
    entry2.add_to_hass(hass)

    # Setup both using proper HA flow - setup each independently
    result1 = await hass.config_entries.async_setup(entry1.entry_id)
    await hass.async_block_till_done()
    result2 = await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    assert result1 is True
    assert result2 is True

    # Service should still be registered (only once)
    assert hass.services.has_service(DOMAIN, "acknowledge")

    # Both entries should be loaded
    assert entry1.state.name == "LOADED"
    assert entry2.state.name == "LOADED"
