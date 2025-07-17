import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Emergency Alert button entities from a config entry."""
    hub_type = entry.data.get("hub_type")

    if hub_type == "global":
        # Global settings hub doesn't create any button entities
        return
    elif hub_type == "group":
        # Group hub - create button entities for all alerts in this group
        group = entry.data.get("group", "other")
        hub_name = entry.data.get("hub_name", group)
        alerts_data = entry.data.get("alerts", {})

        buttons = []
        for alert_id, alert_data in alerts_data.items():
            # Create acknowledge, clear, and escalate buttons for each alert
            acknowledge_button = EmergencyAcknowledgeButton(
                hass, entry, alert_id, alert_data, group, hub_name
            )
            clear_button = EmergencyClearButton(
                hass, entry, alert_id, alert_data, group, hub_name
            )
            escalate_button = EmergencyEscalateButton(
                hass, entry, alert_id, alert_data, group, hub_name
            )

            buttons.extend([acknowledge_button, clear_button, escalate_button])

        if buttons:
            async_add_entities(buttons, update_before_add=True)
    else:
        # Legacy support - individual alert entry (backward compatibility)
        data = entry.data
        name = data["name"]
        group = data.get("group", "other")

        # Create buttons for legacy alert
        acknowledge_button = EmergencyAcknowledgeButton(
            hass, entry, "legacy", data, group, "legacy"
        )
        clear_button = EmergencyClearButton(
            hass, entry, "legacy", data, group, "legacy"
        )
        escalate_button = EmergencyEscalateButton(
            hass, entry, "legacy", data, group, "legacy"
        )

        async_add_entities([acknowledge_button, clear_button,
                           escalate_button], update_before_add=True)


class EmergencyButtonBase(ButtonEntity):
    """Base class for Emergency Alert buttons."""

    def __init__(
        self,
        hass,
        entry: ConfigEntry,
        alert_id: str,
        alert_data: dict,
        group: str,
        hub_name: str,
        action_name: str,
    ):
        self.hass = hass
        self._entry = entry
        self._alert_id = alert_id
        self._group = group
        self._hub_name = hub_name
        self._action_name = action_name
        self._alert_name = alert_data["name"]

        # Entity attributes
        self._attr_name = f"Emergency: {self._alert_name} - {action_name.title()}"
        if alert_id == "legacy":
            self._attr_unique_id = f"emergency_{self._alert_name.lower().replace(' ', '_')}_{action_name}"
        else:
            self._attr_unique_id = f"emergency_{hub_name}_{alert_id}_{action_name}"

        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{hub_name}_hub")},
            "name": f"Emergency Alerts - {group.title()}" + (f" ({entry.data.get('custom_name')})" if entry.data.get("custom_name") else ""),
            "manufacturer": "Emergency Alerts",
            "model": f"{group.title()} Hub",
            "sw_version": "1.0",
        }

    def _get_alert_entity(self):
        """Get the corresponding binary sensor entity."""
        entities = self.hass.data.get(DOMAIN, {}).get("entities", [])
        for entity in entities:
            if (entity._alert_id == self._alert_id and
                    entity._hub_name == self._hub_name):
                return entity
        return None


class EmergencyAcknowledgeButton(EmergencyButtonBase):
    """Button to acknowledge an emergency alert."""

    def __init__(self, hass, entry, alert_id, alert_data, group, hub_name):
        super().__init__(hass, entry, alert_id, alert_data, group, hub_name, "acknowledge")
        self._attr_icon = "mdi:check-circle"

    async def async_press(self) -> None:
        """Handle the button press."""
        alert_entity = self._get_alert_entity()
        if alert_entity:
            await alert_entity.async_acknowledge()
            _LOGGER.info(f"Acknowledged alert: {self._alert_name}")


class EmergencyClearButton(EmergencyButtonBase):
    """Button to clear an emergency alert."""

    def __init__(self, hass, entry, alert_id, alert_data, group, hub_name):
        super().__init__(hass, entry, alert_id, alert_data, group, hub_name, "clear")
        self._attr_icon = "mdi:close-circle"

    async def async_press(self) -> None:
        """Handle the button press."""
        alert_entity = self._get_alert_entity()
        if alert_entity:
            await alert_entity.async_clear()
            _LOGGER.info(f"Cleared alert: {self._alert_name}")


class EmergencyEscalateButton(EmergencyButtonBase):
    """Button to escalate an emergency alert."""

    def __init__(self, hass, entry, alert_id, alert_data, group, hub_name):
        super().__init__(hass, entry, alert_id, alert_data, group, hub_name, "escalate")
        self._attr_icon = "mdi:arrow-up-circle"

    async def async_press(self) -> None:
        """Handle the button press."""
        alert_entity = self._get_alert_entity()
        if alert_entity:
            await alert_entity.async_escalate()
            _LOGGER.info(f"Escalated alert: {self._alert_name}")
