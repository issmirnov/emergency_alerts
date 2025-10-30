"""Switch platform for Emergency Alerts integration."""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    SWITCH_TYPE_ACKNOWLEDGE,
    SWITCH_TYPE_SNOOZE,
    SWITCH_TYPE_RESOLVE,
    STATE_EXCLUSIONS,
    STATE_ACKNOWLEDGED,
    STATE_SNOOZED,
    STATE_RESOLVED,
    DEFAULT_SNOOZE_DURATION,
    SIGNAL_SWITCH_UPDATE,
    SIGNAL_ALERT_UPDATE,
    EVENT_ALERT_ACKNOWLEDGED,
    EVENT_ALERT_SNOOZED,
    EVENT_ALERT_RESOLVED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Emergency Alert switch entities."""
    if entry.data.get("hub_type") != "group":
        return

    alerts_data = entry.data.get("alerts", {})
    switches = []

    for alert_id, alert_data in alerts_data.items():
        # Create 3 switches per alert: acknowledge, snooze, resolve
        switches.append(EmergencyAlertAcknowledgeSwitch(hass, entry, alert_id, alert_data))
        switches.append(EmergencyAlertSnoozeSwitch(hass, entry, alert_id, alert_data))
        switches.append(EmergencyAlertResolveSwitch(hass, entry, alert_id, alert_data))

    if switches:
        async_add_entities(switches, update_before_add=True)


class BaseEmergencyAlertSwitch(SwitchEntity):
    """Base class for Emergency Alert switches."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        alert_id: str,
        alert_data: dict,
        switch_type: str,
        switch_name: str,
    ) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._entry = entry
        self._alert_id = alert_id
        self._alert_data = alert_data
        self._switch_type = switch_type
        self._attr_is_on = False

        # Naming
        alert_name = alert_data.get("name", alert_id)
        self._attr_name = f"{alert_name} {switch_name}"
        self._attr_unique_id = f"{entry.entry_id}_{alert_id}_{switch_type}"

        # Device info - link to alert device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"alert_{entry.entry_id}_{alert_id}")},
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        # Listen for switch updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_SWITCH_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
                self._handle_switch_update,
            )
        )

        # Listen for alert updates (to sync state)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
                self._handle_alert_update,
            )
        )

    @callback
    def _handle_switch_update(self, switch_type: str, state: bool) -> None:
        """Handle switch state updates from binary sensor."""
        if switch_type == self._switch_type:
            self._attr_is_on = state
            self.async_write_ha_state()

    @callback
    def _handle_alert_update(self) -> None:
        """Handle alert updates - sync our state from binary sensor."""
        self._sync_state_from_binary_sensor()
        self.async_write_ha_state()

    def _sync_state_from_binary_sensor(self) -> None:
        """Sync switch state from binary sensor entity attributes."""
        # Use the same entity ID pattern as binary sensor: emergency_{hub_name}_{alert_id}
        hub_name = self._entry.data.get("hub_name", "")
        binary_sensor_id = f"binary_sensor.emergency_{hub_name}_{self._alert_id}"
        entity = self.hass.states.get(binary_sensor_id)

        if entity:
            # Get state from attributes
            if self._switch_type == SWITCH_TYPE_ACKNOWLEDGE:
                self._attr_is_on = entity.attributes.get("acknowledged", False)
            elif self._switch_type == SWITCH_TYPE_SNOOZE:
                self._attr_is_on = entity.attributes.get("snoozed", False)
            elif self._switch_type == SWITCH_TYPE_RESOLVE:
                self._attr_is_on = entity.attributes.get("resolved", False)

    def _get_binary_sensor_entity(self):
        """Get the binary sensor entity instance."""
        entities = self.hass.data.get(DOMAIN, {}).get("entities", [])
        for entity in entities:
            if (
                hasattr(entity, "_alert_id")
                and entity._alert_id == self._alert_id
                and hasattr(entity, "_config_entry")
                and entity._config_entry.entry_id == self._entry.entry_id
            ):
                return entity
        return None

    async def _enforce_state_exclusions(self, new_state: str) -> None:
        """Enforce mutual exclusivity of states."""
        if new_state in STATE_EXCLUSIONS:
            excluded_states = STATE_EXCLUSIONS[new_state]
            binary_sensor = self._get_binary_sensor_entity()

            if binary_sensor:
                # Turn off excluded switches
                for excluded_state in excluded_states:
                    if excluded_state == STATE_ACKNOWLEDGED and binary_sensor._acknowledged:
                        binary_sensor._acknowledged = False
                        _LOGGER.debug(f"Turning off acknowledged for {self._alert_id} due to {new_state}")
                    elif excluded_state == STATE_SNOOZED and binary_sensor._snoozed:
                        binary_sensor._snoozed = False
                        binary_sensor._snooze_until = None
                        if binary_sensor._snooze_task:
                            binary_sensor._snooze_task.cancel()
                        _LOGGER.debug(f"Turning off snoozed for {self._alert_id} due to {new_state}")
                    elif excluded_state == STATE_RESOLVED and binary_sensor._resolved:
                        binary_sensor._resolved = False
                        _LOGGER.debug(f"Turning off resolved for {self._alert_id} due to {new_state}")

                # Update binary sensor
                binary_sensor.async_write_ha_state()

                # Broadcast switch updates
                async_dispatcher_send(
                    self.hass,
                    f"{SIGNAL_SWITCH_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
                    self._switch_type,
                    True,
                )


class EmergencyAlertAcknowledgeSwitch(BaseEmergencyAlertSwitch):
    """Switch to acknowledge an alert (prevents escalation)."""

    def __init__(self, hass, entry, alert_id, alert_data):
        """Initialize acknowledge switch."""
        super().__init__(
            hass, entry, alert_id, alert_data,
            SWITCH_TYPE_ACKNOWLEDGE,
            "Acknowledged"
        )
        self._attr_icon = "mdi:check-circle-outline"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Acknowledge the alert."""
        binary_sensor = self._get_binary_sensor_entity()
        if not binary_sensor:
            _LOGGER.warning(f"Could not find binary sensor for alert {self._alert_id}")
            return

        # Enforce state exclusions
        await self._enforce_state_exclusions(STATE_ACKNOWLEDGED)

        # Set acknowledged state
        binary_sensor._acknowledged = True
        self._attr_is_on = True

        # Cancel escalation timer
        if binary_sensor._escalation_task:
            binary_sensor._escalation_task.cancel()
            binary_sensor._escalation_task = None

        # Fire event
        self.hass.bus.async_fire(
            EVENT_ALERT_ACKNOWLEDGED,
            {"entity_id": binary_sensor.entity_id, "alert_name": self._alert_data.get("name")},
        )

        # Execute on_acknowledged action if configured
        if "on_acknowledged" in self._alert_data:
            await binary_sensor._execute_action(self._alert_data["on_acknowledged"])

        # Update states
        binary_sensor.async_write_ha_state()
        self.async_write_ha_state()

        # Broadcast update
        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

        _LOGGER.info(f"Alert {self._alert_id} acknowledged")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Un-acknowledge the alert (allow escalation again)."""
        binary_sensor = self._get_binary_sensor_entity()
        if not binary_sensor:
            return

        binary_sensor._acknowledged = False
        self._attr_is_on = False

        # Restart escalation timer if alert is still active
        if binary_sensor.is_on:
            await binary_sensor._start_escalation_timer()

        binary_sensor.async_write_ha_state()
        self.async_write_ha_state()

        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

        _LOGGER.info(f"Alert {self._alert_id} un-acknowledged")


class EmergencyAlertSnoozeSwitch(BaseEmergencyAlertSwitch):
    """Switch to snooze an alert (temporary silence)."""

    def __init__(self, hass, entry, alert_id, alert_data):
        """Initialize snooze switch."""
        super().__init__(
            hass, entry, alert_id, alert_data,
            SWITCH_TYPE_SNOOZE,
            "Snoozed"
        )
        self._attr_icon = "mdi:bell-sleep"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Snooze the alert for configured duration."""
        binary_sensor = self._get_binary_sensor_entity()
        if not binary_sensor:
            _LOGGER.warning(f"Could not find binary sensor for alert {self._alert_id}")
            return

        # Enforce state exclusions
        await self._enforce_state_exclusions(STATE_SNOOZED)

        # Set snooze state
        binary_sensor._snoozed = True
        snooze_duration = self._alert_data.get("snooze_duration", DEFAULT_SNOOZE_DURATION)
        binary_sensor._snooze_until = datetime.now() + timedelta(seconds=snooze_duration)
        self._attr_is_on = True

        # Start snooze timer (auto turn off)
        if binary_sensor._snooze_task:
            binary_sensor._snooze_task.cancel()
        binary_sensor._snooze_task = asyncio.create_task(self._snooze_timer(snooze_duration, binary_sensor))

        # Fire event
        self.hass.bus.async_fire(
            EVENT_ALERT_SNOOZED,
            {
                "entity_id": binary_sensor.entity_id,
                "alert_name": self._alert_data.get("name"),
                "snooze_until": binary_sensor._snooze_until.isoformat(),
            },
        )

        # Execute on_snoozed action if configured
        if "on_snoozed" in self._alert_data:
            await binary_sensor._execute_action(self._alert_data["on_snoozed"])

        # Update states
        binary_sensor.async_write_ha_state()
        self.async_write_ha_state()

        # Broadcast update
        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

        _LOGGER.info(f"Alert {self._alert_id} snoozed for {snooze_duration} seconds")

    async def _snooze_timer(self, duration: int, binary_sensor) -> None:
        """Auto turn off snooze after duration."""
        try:
            await asyncio.sleep(duration)
            # Time expired, turn off snooze
            binary_sensor._snoozed = False
            binary_sensor._snooze_until = None
            binary_sensor._snooze_task = None
            self._attr_is_on = False

            binary_sensor.async_write_ha_state()
            self.async_write_ha_state()

            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
            )

            _LOGGER.info(f"Snooze expired for alert {self._alert_id}")
        except asyncio.CancelledError:
            _LOGGER.debug(f"Snooze timer cancelled for alert {self._alert_id}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Cancel snooze immediately."""
        binary_sensor = self._get_binary_sensor_entity()
        if not binary_sensor:
            return

        binary_sensor._snoozed = False
        binary_sensor._snooze_until = None
        self._attr_is_on = False

        # Cancel snooze task
        if binary_sensor._snooze_task:
            binary_sensor._snooze_task.cancel()
            binary_sensor._snooze_task = None

        binary_sensor.async_write_ha_state()
        self.async_write_ha_state()

        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

        _LOGGER.info(f"Snooze cancelled for alert {self._alert_id}")


class EmergencyAlertResolveSwitch(BaseEmergencyAlertSwitch):
    """Switch to mark alert as resolved."""

    def __init__(self, hass, entry, alert_id, alert_data):
        """Initialize resolve switch."""
        super().__init__(
            hass, entry, alert_id, alert_data,
            SWITCH_TYPE_RESOLVE,
            "Resolved"
        )
        self._attr_icon = "mdi:check-circle"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mark alert as resolved."""
        binary_sensor = self._get_binary_sensor_entity()
        if not binary_sensor:
            _LOGGER.warning(f"Could not find binary sensor for alert {self._alert_id}")
            return

        # Enforce state exclusions
        await self._enforce_state_exclusions(STATE_RESOLVED)

        # Set resolved state
        binary_sensor._resolved = True
        self._attr_is_on = True

        # Cancel escalation timer
        if binary_sensor._escalation_task:
            binary_sensor._escalation_task.cancel()
            binary_sensor._escalation_task = None

        # Fire event
        self.hass.bus.async_fire(
            EVENT_ALERT_RESOLVED,
            {"entity_id": binary_sensor.entity_id, "alert_name": self._alert_data.get("name")},
        )

        # Execute on_resolved action if configured
        if "on_resolved" in self._alert_data:
            await binary_sensor._execute_action(self._alert_data["on_resolved"])

        # Update states
        binary_sensor.async_write_ha_state()
        self.async_write_ha_state()

        # Broadcast update
        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

        _LOGGER.info(f"Alert {self._alert_id} marked as resolved")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Un-resolve the alert (allow triggering again)."""
        binary_sensor = self._get_binary_sensor_entity()
        if not binary_sensor:
            return

        binary_sensor._resolved = False
        self._attr_is_on = False

        binary_sensor.async_write_ha_state()
        self.async_write_ha_state()

        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

        _LOGGER.info(f"Alert {self._alert_id} un-resolved")
