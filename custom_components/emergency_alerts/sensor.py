from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    # Only create global summary sensors once (when first config entry is added)
    if "summary_sensors_created" not in hass.data.get(DOMAIN, {}):
        # Create global summary sensor
        global_sensor = EmergencyGlobalSummarySensor(hass)

        # Create group-specific summary sensors
        groups = ["security", "safety", "power",
                  "lights", "environment", "other"]
        group_sensors = [EmergencyGroupSummarySensor(
            hass, group) for group in groups]

        all_sensors = [global_sensor] + group_sensors
        async_add_entities(all_sensors, update_before_add=True)

        # Mark that summary sensors have been created
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        hass.data[DOMAIN]["summary_sensors_created"] = True


class EmergencyGlobalSummarySensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "Emergency Alerts Summary"
        self._attr_unique_id = "emergency_alerts_global_summary"
        self._attr_icon = "mdi:alert-circle"
        self._active_alerts = []
        self._unsub = None

    async def async_added_to_hass(self):
        from .binary_sensor import SUMMARY_UPDATE_SIGNAL

        @callback
        def update_summary():
            self._update_active_alerts()
            self.async_write_ha_state()

        self._unsub = async_dispatcher_connect(
            self.hass, SUMMARY_UPDATE_SIGNAL, update_summary
        )
        self._update_active_alerts()

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()

    @property
    def native_value(self):
        return len(self._active_alerts)

    @property
    def extra_state_attributes(self):
        return {
            "active_alerts": self._active_alerts,
            "alert_count": len(self._active_alerts),
        }

    def _update_active_alerts(self):
        entities = self.hass.data.get(DOMAIN, {}).get("entities", [])
        self._active_alerts = [e.entity_id for e in entities if e.is_on]


class EmergencyGroupSummarySensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, hass, group):
        self.hass = hass
        self._group = group
        self._attr_name = f"Emergency Alerts {group.title()}"
        self._attr_unique_id = f"emergency_alerts_{group}_summary"
        self._attr_icon = "mdi:alert-circle"
        self._active_alerts = []
        self._unsub = None

    async def async_added_to_hass(self):
        from .binary_sensor import SUMMARY_UPDATE_SIGNAL

        @callback
        def update_summary():
            self._update_active_alerts()
            self.async_write_ha_state()

        self._unsub = async_dispatcher_connect(
            self.hass, SUMMARY_UPDATE_SIGNAL, update_summary
        )
        self._update_active_alerts()

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()

    @property
    def native_value(self):
        return len(self._active_alerts)

    @property
    def extra_state_attributes(self):
        return {
            "group": self._group,
            "active_alerts": self._active_alerts,
            "alert_count": len(self._active_alerts),
        }

    def _update_active_alerts(self):
        entities = self.hass.data.get(DOMAIN, {}).get("entities", [])
        self._active_alerts = [
            e.entity_id for e in entities if e.is_on and e._group == self._group
        ]
