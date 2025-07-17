from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

DOMAIN = "emergency_alerts"
PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Emergency Alerts component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Emergency Alerts from a config entry."""
    # Initialize the data structure
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    # Store the entry data
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Set up the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up services
    await _setup_services(hass)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove entry data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
    return unload_ok


async def _setup_services(hass: HomeAssistant):
    """Set up the emergency alerts services."""
    
    async def acknowledge_service(call):
        """Handle acknowledge service call."""
        entity_id = call.data.get("entity_id")
        if entity_id:
            # Get the entity and call its acknowledge method
            entity = hass.states.get(entity_id)
            if entity and hasattr(entity, "async_acknowledge"):
                await entity.async_acknowledge()

    async def clear_service(call):
        """Handle clear service call.""" 
        entity_id = call.data.get("entity_id")
        if entity_id:
            entity = hass.states.get(entity_id)
            if entity and hasattr(entity, "async_clear"):
                await entity.async_clear()

    async def escalate_service(call):
        """Handle escalate service call."""
        entity_id = call.data.get("entity_id") 
        if entity_id:
            entity = hass.states.get(entity_id)
            if entity and hasattr(entity, "async_escalate"):
                await entity.async_escalate()

    # Register services
    hass.services.async_register(DOMAIN, "acknowledge", acknowledge_service)
    hass.services.async_register(DOMAIN, "clear", clear_service)
    hass.services.async_register(DOMAIN, "escalate", escalate_service)
