"""Select platform for Emergency Alerts integration - unified state control."""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    STATE_ACTIVE,
    STATE_INACTIVE,
    STATE_ACKNOWLEDGED,
    STATE_SNOOZED,
    STATE_RESOLVED,
    DEFAULT_SNOOZE_DURATION,
    SIGNAL_ALERT_UPDATE,
    EVENT_ALERT_ACKNOWLEDGED,
    EVENT_ALERT_SNOOZED,
    EVENT_ALERT_RESOLVED,
)

_LOGGER = logging.getLogger(__name__)

# Available states for the select entity
ALERT_STATES = [
    STATE_ACTIVE,
    STATE_ACKNOWLEDGED,
    STATE_SNOOZED,
    STATE_RESOLVED,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Emergency Alert select entities."""
    if entry.data.get("hub_type") != "group":
        return

    alerts_data = entry.data.get("alerts", {})
    selects = []

    for alert_id, alert_data in alerts_data.items():
        # Create single select entity per alert for state control
        selects.append(EmergencyAlertStateSelect(hass, entry, alert_id, alert_data))

    if selects:
        async_add_entities(selects, update_before_add=True)


class EmergencyAlertStateSelect(SelectEntity):
    """Select entity for unified alert state control."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        alert_id: str,
        alert_data: dict,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self._entry = entry
        self._alert_id = alert_id
        self._alert_data = alert_data
        self._attr_options = ALERT_STATES
        self._attr_current_option = STATE_ACTIVE
        self._snooze_task = None

        # Naming
        alert_name = alert_data.get("name", alert_id)
        self._attr_name = f"{alert_name} State"
        self._attr_unique_id = f"{entry.entry_id}_{alert_id}_state"
        self._attr_icon = "mdi:state-machine"

        # Device info - link to alert device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"alert_{entry.entry_id}_{alert_id}")},
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        # Listen for alert updates to sync state
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
                self._handle_alert_update,
            )
        )
        
        # Initial sync
        self._sync_state_from_binary_sensor()

    @callback
    def _handle_alert_update(self) -> None:
        """Handle alert updates - sync our state from binary sensor."""
        self._sync_state_from_binary_sensor()
        self.async_write_ha_state()

    def _sync_state_from_binary_sensor(self) -> None:
        """Sync select state from binary sensor entity attributes."""
        binary_sensor = self._get_binary_sensor_entity()
        
        if binary_sensor:
            # Determine current state based on binary sensor flags
            if binary_sensor._resolved:
                self._attr_current_option = STATE_RESOLVED
            elif binary_sensor._snoozed:
                self._attr_current_option = STATE_SNOOZED
            elif binary_sensor._acknowledged:
                self._attr_current_option = STATE_ACKNOWLEDGED
            elif binary_sensor.is_on:
                self._attr_current_option = STATE_ACTIVE
            else:
                self._attr_current_option = STATE_INACTIVE

    def _get_binary_sensor_entity(self):
        """Get the binary sensor entity instance."""
        entities = self.hass.data.get(DOMAIN, {}).get("entities", [])
        for entity in entities:
            if (
                hasattr(entity, "_alert_id")
                and entity._alert_id == self._alert_id
                and hasattr(entity, "_entry")
                and entity._entry.entry_id == self._entry.entry_id
            ):
                return entity
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the alert state."""
        binary_sensor = self._get_binary_sensor_entity()
        if not binary_sensor:
            _LOGGER.warning(f"Could not find binary sensor for alert {self._alert_id}")
            return

        _LOGGER.info(f"Setting alert {self._alert_id} state to: {option}")

        # Clear all states first
        binary_sensor._acknowledged = False
        binary_sensor._snoozed = False
        binary_sensor._resolved = False
        binary_sensor._escalated = False
        binary_sensor._snooze_until = None
        
        # Cancel any running timers
        if binary_sensor._escalation_task:
            binary_sensor._escalation_task()
            binary_sensor._escalation_task = None
        
        if self._snooze_task:
            self._snooze_task.cancel()
            self._snooze_task = None

        # Set new state and execute corresponding actions
        if option == STATE_ACKNOWLEDGED:
            binary_sensor._acknowledged = True
            self._attr_current_option = STATE_ACKNOWLEDGED
            
            # Fire event
            self.hass.bus.async_fire(
                EVENT_ALERT_ACKNOWLEDGED,
                {"entity_id": binary_sensor.entity_id, "alert_name": self._alert_data.get("name")},
            )
            
            # Execute action
            if "on_acknowledged" in self._alert_data:
                await binary_sensor._execute_action(self._alert_data["on_acknowledged"])
            
            _LOGGER.info(f"Alert {self._alert_id} acknowledged")

        elif option == STATE_SNOOZED:
            binary_sensor._snoozed = True
            snooze_duration = self._alert_data.get("snooze_duration", DEFAULT_SNOOZE_DURATION)
            binary_sensor._snooze_until = datetime.now() + timedelta(seconds=snooze_duration)
            self._attr_current_option = STATE_SNOOZED
            
            # Start snooze timer
            self._snooze_task = asyncio.create_task(
                self._snooze_timer(snooze_duration, binary_sensor)
            )
            
            # Fire event
            self.hass.bus.async_fire(
                EVENT_ALERT_SNOOZED,
                {
                    "entity_id": binary_sensor.entity_id,
                    "alert_name": self._alert_data.get("name"),
                    "snooze_until": binary_sensor._snooze_until.isoformat(),
                },
            )
            
            # Execute action
            if "on_snoozed" in self._alert_data:
                await binary_sensor._execute_action(self._alert_data["on_snoozed"])
            
            _LOGGER.info(f"Alert {self._alert_id} snoozed for {snooze_duration} seconds")

        elif option == STATE_RESOLVED:
            binary_sensor._resolved = True
            self._attr_current_option = STATE_RESOLVED
            
            # Fire event
            self.hass.bus.async_fire(
                EVENT_ALERT_RESOLVED,
                {"entity_id": binary_sensor.entity_id, "alert_name": self._alert_data.get("name")},
            )
            
            # Execute action
            if "on_resolved" in self._alert_data:
                await binary_sensor._execute_action(self._alert_data["on_resolved"])
            
            _LOGGER.info(f"Alert {self._alert_id} marked as resolved")

        elif option == STATE_ACTIVE:
            # Return to active state (clear all flags)
            self._attr_current_option = STATE_ACTIVE
            
            # Restart escalation timer if alert is still on
            if binary_sensor.is_on:
                await binary_sensor._start_escalation_timer()
            
            _LOGGER.info(f"Alert {self._alert_id} returned to active state")

        # Update all entities
        binary_sensor.async_write_ha_state()
        binary_sensor._update_status_sensor()
        self.async_write_ha_state()

        # Broadcast update
        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

    async def _snooze_timer(self, duration: int, binary_sensor) -> None:
        """Auto clear snooze after duration."""
        try:
            await asyncio.sleep(duration)
            
            # Time expired, return to active state
            binary_sensor._snoozed = False
            binary_sensor._snooze_until = None
            self._snooze_task = None
            
            # Determine new state
            if binary_sensor.is_on:
                self._attr_current_option = STATE_ACTIVE
                # Restart escalation if alert still active
                await binary_sensor._start_escalation_timer()
            else:
                self._attr_current_option = STATE_INACTIVE
            
            binary_sensor.async_write_ha_state()
            self.async_write_ha_state()

            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
            )

            _LOGGER.info(f"Snooze expired for alert {self._alert_id}")
            
        except asyncio.CancelledError:
            _LOGGER.debug(f"Snooze timer cancelled for alert {self._alert_id}")