from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import async_get_platforms

DOMAIN = "emergency_alerts"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    async def handle_acknowledge(call):
        entity_id = call.data.get("entity_id")
        for entity in hass.data.get(DOMAIN, {}).get("entities", []):
            if entity.entity_id == entity_id:
                await entity.async_acknowledge()
                break

    hass.services.async_register(DOMAIN, "acknowledge", handle_acknowledge)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True 