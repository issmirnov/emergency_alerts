from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "emergency_alerts"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Initialize the data structure for storing entities
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "entities" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["entities"] = []

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "sensor"])

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
