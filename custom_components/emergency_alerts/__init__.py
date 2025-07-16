from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

DOMAIN = "emergency_alerts"


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Emergency Alerts component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Emergency Alerts from a config entry."""
    # Initialize the data structure for storing entities and subentries
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    # Check if this is the main integration entry or a subentry
    if entry.data.get("configured"):
        # This is the main integration entry
        hass.data[DOMAIN]["main_entry"] = entry
        hass.data[DOMAIN]["entities"] = []
        hass.data[DOMAIN]["subentries"] = []
        
        # Set up global services only once for the main entry
        await _setup_services(hass)
        
        # Set up global summary sensors
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
        
        # Create device entry for the integration
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "emergency_alerts_hub")},
            name="Emergency Alerts Hub",
            manufacturer="Emergency Alerts Integration",
            model="Alert Manager",
            sw_version="0.2.0",
        )
        
        return True
    else:
        # This is a config subentry for an individual alert
        hass.data[DOMAIN]["subentries"].append(entry)
        
        # Forward to binary sensor platform for the individual alert
        await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor"])
        
        return True


async def _setup_services(hass: HomeAssistant):
    """Set up the emergency alerts services."""
    async def handle_acknowledge(call):
        entity_id = call.data.get("entity_id")
        for entity in hass.data.get(DOMAIN, {}).get("entities", []):
            if entity.entity_id == entity_id:
                await entity.async_acknowledge()
                break

    async def handle_clear(call):
        entity_id = call.data.get("entity_id")
        for entity in hass.data.get(DOMAIN, {}).get("entities", []):
            if entity.entity_id == entity_id:
                await entity.async_clear()
                break

    async def handle_escalate(call):
        entity_id = call.data.get("entity_id")
        for entity in hass.data.get(DOMAIN, {}).get("entities", []):
            if entity.entity_id == entity_id:
                await entity.async_escalate()
                break

    hass.services.async_register(DOMAIN, "acknowledge", handle_acknowledge)
    hass.services.async_register(DOMAIN, "clear", handle_clear)
    hass.services.async_register(DOMAIN, "escalate", handle_escalate)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if entry.data.get("configured"):
        # This is the main integration entry
        # Unload all subentries first
        unload_ok = True
        for subentry in hass.data[DOMAIN].get("subentries", []):
            if not await hass.config_entries.async_unload_platforms(subentry, ["binary_sensor"]):
                unload_ok = False
        
        # Unload the main sensor platform
        if not await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
            unload_ok = False
            
        # Clean up services
        hass.services.async_remove(DOMAIN, "acknowledge")
        hass.services.async_remove(DOMAIN, "clear") 
        hass.services.async_remove(DOMAIN, "escalate")
        
        # Clean up data
        if DOMAIN in hass.data:
            hass.data.pop(DOMAIN)
            
        return unload_ok
    else:
        # This is a subentry
        return await hass.config_entries.async_unload_platforms(entry, ["binary_sensor"])
