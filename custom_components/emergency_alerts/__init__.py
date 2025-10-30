from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.persistent_notification import async_create

DOMAIN = "emergency_alerts"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Emergency Alerts from a config entry."""
    # Initialize the data structure for storing entities
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "entities" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["entities"] = []

    hub_type = entry.data.get("hub_type")

    if hub_type == "global":
        # Store global options from the global settings hub
        if entry.options:
            hass.data[DOMAIN]["global_options"] = entry.options
        # For global hub, we mainly store options and don't create entities
        # The binary_sensor platform will skip entity creation for global hubs
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    elif hub_type == "group":
        # Group hub - forward to binary_sensor, sensor, and switch platforms
        await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "sensor", "switch"])

    # Register services only once (when first entry is added)
    if "services_registered" not in hass.data[DOMAIN]:
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

        # Service to add alert to a group hub
        async def handle_add_alert(call):
            """Add a new alert to a group hub via service call."""
            hub_name = call.data.get("hub_name")
            alert_data = call.data.get("alert_data", {})

            # Find the group hub entry
            for config_entry in hass.config_entries.async_entries(DOMAIN):
                if (config_entry.data.get("hub_type") == "group" and
                        config_entry.data.get("hub_name") == hub_name):

                    # Add the alert to the config entry
                    alerts = dict(config_entry.data.get("alerts", {}))
                    alert_id = alert_data["name"].lower().replace(" ", "_")
                    alerts[alert_id] = alert_data

                    new_data = dict(config_entry.data)
                    new_data["alerts"] = alerts

                    hass.config_entries.async_update_entry(
                        config_entry, data=new_data)

                    # Reload the entry to create the new entity
                    await hass.config_entries.async_reload(config_entry.entry_id)
                    break

        hass.services.async_register(DOMAIN, "acknowledge", handle_acknowledge)
        hass.services.async_register(DOMAIN, "clear", handle_clear)
        hass.services.async_register(DOMAIN, "escalate", handle_escalate)
        hass.services.async_register(DOMAIN, "add_alert", handle_add_alert)

        hass.data[DOMAIN]["services_registered"] = True

        # Notify user about available blueprint script (only shown once)
        async_create(
            hass,
            title="Emergency Alerts Integration",
            message="📋 A default emergency notification script blueprint is now available! "
            "Go to **Settings** → **Automations & Scenes** → **Blueprints** → **Scripts** to import the "
            "'Emergency Alert - Fixed Notify' script for use in your alert actions.\n\n"
            "💡 **Tip**: You can click [here](/config/blueprint/dashboard/script) to go directly to Script Blueprints!",
            notification_id="emergency_alerts_blueprint_info"
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    hub_type = entry.data.get("hub_type")

    if hub_type == "global":
        platforms = ["sensor"]
    else:
        platforms = ["binary_sensor", "sensor", "switch"]

    unload_ok = True
    for platform in platforms:
        unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, platform)

    # Clean up entities from this entry
    if DOMAIN in hass.data and "entities" in hass.data[DOMAIN]:
        entities_to_remove = []
        for entity in hass.data[DOMAIN]["entities"]:
            if hasattr(entity, "_entry") and entity._entry.entry_id == entry.entry_id:
                entities_to_remove.append(entity)

        for entity in entities_to_remove:
            hass.data[DOMAIN]["entities"].remove(entity)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
