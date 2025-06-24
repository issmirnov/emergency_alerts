from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

SUMMARY_UPDATE_SIGNAL = "emergency_alerts_summary_update"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    # Only add one global summary sensor per HA instance
    if not hass.data[DOMAIN].get("summary_sensor_added"):
        global_sensor = EmergencyAlertsSummarySensor(hass)
        async_add_entities([global_sensor], update_before_add=True)
        hass.data[DOMAIN]["summary_sensor_added"] = True
    # Add group summary sensors for each group present in config entries
    groups = set()
    for entity in hass.data[DOMAIN]["entities"]:
        groups.add(entity._group)
    group_sensors = [EmergencyAlertsGroupSummarySensor(hass, group) for group in groups]
    async_add_entities(group_sensors, update_before_add=True)

class EmergencyAlertsSummarySensor(SensorEntity):
    _attr_name = "Emergency Alerts Active"
    _attr_unique_id = "emergency_alerts_active_summary"
    _attr_icon = "mdi:alert"

    def __init__(self, hass):
        self.hass = hass
        self._active_alerts = []
        self._groups = {}
        self._unsubscribe = None

    async def async_added_to_hass(self):
        self._unsubscribe = async_dispatcher_connect(
            self.hass, SUMMARY_UPDATE_SIGNAL, self.async_write_ha_state
        )
        self._update_state()

    async def async_will_remove_from_hass(self):
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def state(self):
        self._update_state()
        return len(self._active_alerts)

    @property
    def extra_state_attributes(self):
        return {
            "active_count": len(self._active_alerts),
            "active_alerts": self._active_alerts,
            "groups": self._groups,
        }

    def _update_state(self):
        entities = self.hass.data[DOMAIN]["entities"]
        self._active_alerts = [e.entity_id for e in entities if e.is_on]
        group_counts = {}
        for e in entities:
            if e.is_on:
                group_counts[e._group] = group_counts.get(e._group, 0) + 1
        self._groups = group_counts

class EmergencyAlertsGroupSummarySensor(SensorEntity):
    def __init__(self, hass, group):
        self.hass = hass
        self._group = group
        self._attr_name = f"Emergency Alerts {group.title()} Active"
        self._attr_unique_id = f"emergency_alerts_{group}_active_summary"
        self._attr_icon = "mdi:alert"
        self._active_alerts = []
        self._unsubscribe = None

    async def async_added_to_hass(self):
        self._unsubscribe = async_dispatcher_connect(
            self.hass, SUMMARY_UPDATE_SIGNAL, self.async_write_ha_state
        )
        self._update_state()

    async def async_will_remove_from_hass(self):
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @property
    def state(self):
        self._update_state()
        return len(self._active_alerts)

    @property
    def extra_state_attributes(self):
        return {
            "active_count": len(self._active_alerts),
            "active_alerts": self._active_alerts,
            "group": self._group,
        }

    def _update_state(self):
        entities = self.hass.data[DOMAIN]["entities"]
        self._active_alerts = [e.entity_id for e in entities if e.is_on and e._group == self._group] 