import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    if entry.data.get("hub_type") != "group":
        return

    alerts_data = entry.data.get("alerts", {})
    switches = []
    for alert_id, alert_data in alerts_data.items():
        switches.append(EmergencyAlertToggleSwitch(hass, entry, alert_id, alert_data, "acknowledged"))
        switches.append(EmergencyAlertToggleSwitch(hass, entry, alert_id, alert_data, "escalated"))
    if switches:
        async_add_entities(switches, update_before_add=True)

class EmergencyAlertToggleSwitch(SwitchEntity):
    def __init__(self, hass, entry, alert_id, alert_data, toggle_type):
        self.hass = hass
        self._entry = entry
        self._alert_id = alert_id
        self._alert_data = alert_data
        self._toggle_type = toggle_type  # 'acknowledged' or 'escalated'
        self._attr_name = f"Emergency: {alert_data['name']} - {toggle_type.title()}"
        self._attr_unique_id = f"emergency_{entry.data.get('hub_name', 'group')}_{alert_id}_{toggle_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.data.get('hub_name', 'group')}_{alert_id}")},
            "name": f"Emergency Alert: {alert_data['name']}",
            "manufacturer": "Emergency Alerts",
            "model": f"{alert_data.get('severity', 'warning').title()} Alert",
            "sw_version": "1.0",
            "via_device": (DOMAIN, f"{entry.data.get('hub_name', 'group')}_hub"),
        }

    @property
    def is_on(self):
        entity_id = f"binary_sensor.emergency_{self._entry.data.get('hub_name', 'group')}_{self._alert_id}"
        entity = self.hass.states.get(entity_id)
        if entity and self._toggle_type in entity.attributes:
            return bool(entity.attributes[self._toggle_type])
        return False

    async def async_turn_on(self, **kwargs):
        await self._set_toggle(True)

    async def async_turn_off(self, **kwargs):
        await self._set_toggle(False)

    async def _set_toggle(self, value: bool):
        entity_id = f"binary_sensor.emergency_{self._entry.data.get('hub_name', 'group')}_{self._alert_id}"
        entity = self.hass.data[DOMAIN]["entities"]
        for e in entity:
            if getattr(e, "entity_id", None) == entity_id:
                setattr(e, f"_{self._toggle_type}", value)
                e.async_write_ha_state()
                _LOGGER.info(f"Set {self._toggle_type} for {entity_id} to {value}")
                break 