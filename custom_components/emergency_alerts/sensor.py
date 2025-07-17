import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    hub_type = entry.data.get("hub_type")
    _LOGGER.debug(
        f"Setting up sensor for entry {entry.title}, hub_type: {hub_type}")

    # Only create global summary sensor once (when first config entry is added)
    current_domain_data = hass.data.get(DOMAIN, {})
    _LOGGER.debug(f"Current domain data: {current_domain_data}")

    if "summary_sensors_created" not in current_domain_data:
        _LOGGER.debug("Creating global summary sensor...")
        # Create global summary sensor
        global_sensor = EmergencyGlobalSummarySensor(hass)
        async_add_entities([global_sensor], update_before_add=True)

        # Mark that global summary sensor has been created
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        hass.data[DOMAIN]["summary_sensors_created"] = True
        _LOGGER.debug("Global summary sensor created and flag set")

    # Create group-specific summary sensor if this is a group hub AND it has alerts
    if hub_type == "group":
        alerts_data = entry.data.get("alerts", {})
        _LOGGER.debug(f"Group hub detected, alerts_data: {alerts_data}")

        # Only create group summary sensor if there are actual alerts
        if alerts_data:
            group_name = entry.data.get("group", "other")
            hub_name = entry.data.get("hub_name", group_name)
            _LOGGER.debug(f"Creating group summary sensor for {group_name}")

            # Create a summary sensor for this specific group
            group_sensor = EmergencyGroupSummarySensor(
                hass, group_name, hub_name)
            async_add_entities([group_sensor], update_before_add=True)
        else:
            _LOGGER.debug("Group has no alerts, skipping group summary sensor")


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

    def __init__(self, hass, group_name, hub_name):
        self.hass = hass
        self._group_name = group_name
        self._hub_name = hub_name
        self._attr_name = f"Emergency Alerts {group_name.title()}"
        self._attr_unique_id = f"emergency_alerts_{hub_name}_summary"
        self._attr_icon = "mdi:alert-circle"
        self._active_alerts = []
        self._unsub = None

        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{hub_name}_hub")},
            "name": f"Emergency Alerts - {group_name.title()}",
            "manufacturer": "Emergency Alerts",
            "model": f"{group_name.title()} Hub",
            "sw_version": "1.0",
        }

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
            "group": self._group_name,
            "hub_name": self._hub_name,
            "active_alerts": self._active_alerts,
            "alert_count": len(self._active_alerts),
        }

    def _update_active_alerts(self):
        entities = self.hass.data.get(DOMAIN, {}).get("entities", [])
        self._active_alerts = [
            e.entity_id for e in entities if e.is_on and e._hub_name == self._hub_name
        ]
