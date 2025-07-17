import json
import logging
from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.template import Template
import yaml

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ESCALATION_MINUTES = 5  # Default escalation time if not specified
SUMMARY_UPDATE_SIGNAL = "emergency_alerts_summary_update"


def _parse_actions(action_string):
    """Parse action string (JSON/YAML) into a list of action dictionaries."""
    if not action_string:
        return []

    if isinstance(action_string, list):
        return action_string  # Already a list

    if isinstance(action_string, str):
        try:
            # Try parsing as JSON first
            return json.loads(action_string)
        except json.JSONDecodeError:
            try:
                # Try parsing as YAML
                return yaml.safe_load(action_string) or []
            except yaml.YAMLError:
                _LOGGER.error(f"Failed to parse actions: {action_string}")
                return []

    return []


def _parse_logical_conditions(conditions_string):
    """Parse logical conditions string (JSON/YAML) into a list of condition dictionaries."""
    if not conditions_string:
        return []

    if isinstance(conditions_string, list):
        return conditions_string  # Already a list

    if isinstance(conditions_string, str):
        try:
            # Try parsing as JSON first
            return json.loads(conditions_string)
        except json.JSONDecodeError:
            try:
                # Try parsing as YAML
                return yaml.safe_load(conditions_string) or []
            except yaml.YAMLError:
                _LOGGER.error(
                    f"Failed to parse logical conditions: {conditions_string}")
                return []

    return []


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Emergency Alert binary sensors from a config entry."""
    hub_type = entry.data.get("hub_type")

    if hub_type == "global":
        # Global settings hub doesn't create any entities directly
        return
    elif hub_type == "group":
        # Group hub - create entities for all alerts in this group
        group = entry.data.get("group", "other")
        hub_name = entry.data.get("hub_name", group)
        alerts_data = entry.data.get("alerts", {})

        entities = []
        for alert_id, alert_data in alerts_data.items():
            sensor = EmergencyBinarySensor(
                hass=hass,
                entry=entry,
                alert_id=alert_id,
                alert_data=alert_data,
                group=group,
                hub_name=hub_name,
            )
            entities.append(sensor)

        if entities:
            async_add_entities(entities, update_before_add=True)

        # Register entities for service access
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        if "entities" not in hass.data[DOMAIN]:
            hass.data[DOMAIN]["entities"] = []
        hass.data[DOMAIN]["entities"].extend(entities)
    else:
        # Legacy support - individual alert entry (backward compatibility)
        data = entry.data
        name = data["name"]
        trigger_type = data.get("trigger_type", "simple")
        entity_id = data.get("entity_id")
        trigger_state = data.get("trigger_state")
        template = data.get("template")
        logical_conditions = data.get("logical_conditions")
        action_service = data.get("action_service")
        severity = data.get("severity", "warning")
        group = data.get("group", "other")
        # Parse action fields from strings to lists
        on_triggered = _parse_actions(data.get("on_triggered"))
        on_cleared = _parse_actions(data.get("on_cleared"))
        on_escalated = _parse_actions(data.get("on_escalated"))

        # Parse logical conditions from string to list
        logical_conditions = _parse_logical_conditions(
            data.get("logical_conditions"))

        # Create legacy alert data format
        alert_data = {
            "name": name,
            "trigger_type": trigger_type,
            "entity_id": entity_id,
            "trigger_state": trigger_state,
            "template": template,
            "logical_conditions": logical_conditions,
            "action_service": action_service,
            "severity": severity,
            "on_triggered": on_triggered,
            "on_cleared": on_cleared,
            "on_escalated": on_escalated,
        }

        sensor = EmergencyBinarySensor(
            hass=hass,
            entry=entry,
            alert_id="legacy",
            alert_data=alert_data,
            group=group,
            hub_name="legacy",
        )
        async_add_entities([sensor], update_before_add=True)

        # Register entity for service access
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        if "entities" not in hass.data[DOMAIN]:
            hass.data[DOMAIN]["entities"] = []
        hass.data[DOMAIN]["entities"].append(sensor)


class EmergencyBinarySensor(BinarySensorEntity):
    _attr_should_poll = False

    def __init__(
        self,
        hass,
        entry: ConfigEntry,
        alert_id: str,
        alert_data: dict,
        group: str,
        hub_name: str,
    ):
        self.hass = hass
        self._entry = entry
        self._alert_id = alert_id
        self._group = group
        self._hub_name = hub_name

        # Extract alert configuration
        name = alert_data["name"]
        self._alert_name = name
        self._trigger_type = alert_data.get("trigger_type", "simple")
        self._entity_id = alert_data.get("entity_id")
        self._trigger_state = alert_data.get("trigger_state")
        self._template = alert_data.get("template")
        self._logical_conditions = _parse_logical_conditions(
            alert_data.get("logical_conditions"))
        self._action_service = alert_data.get("action_service")
        self._severity = alert_data.get("severity", "warning")
        self._on_triggered = _parse_actions(alert_data.get("on_triggered"))
        self._on_cleared = _parse_actions(alert_data.get("on_cleared"))
        self._on_escalated = _parse_actions(alert_data.get("on_escalated"))

        # Entity attributes
        self._attr_name = f"Emergency: {name}"
        if alert_id == "legacy":
            self._attr_unique_id = f"emergency_{name.lower().replace(' ', '_')}"
        else:
            self._attr_unique_id = f"emergency_{hub_name}_{alert_id}"

        # Device info - each alert gets its own device under the hub
        if alert_id == "legacy":
            # Legacy single alert - create as hub device
            self._attr_device_info = {
                "identifiers": {(DOMAIN, f"{hub_name}_hub")},
                "name": f"Emergency Alerts - {group.title()}" + (f" ({entry.data.get('custom_name')})" if entry.data.get("custom_name") else ""),
                "manufacturer": "Emergency Alerts",
                "model": f"{group.title()} Hub",
                "sw_version": "1.0",
            }
        else:
            # Group alert - create individual device under the hub
            self._attr_device_info = {
                "identifiers": {(DOMAIN, f"{hub_name}_{alert_id}")},
                "name": f"Emergency Alert: {name}",
                "manufacturer": "Emergency Alerts",
                "model": f"{self._severity.title()} Alert",
                "sw_version": "1.0",
                "via_device": (DOMAIN, f"{hub_name}_hub"),
            }

        # State tracking
        self._is_on = False
        self._first_triggered = None
        self._last_cleared = None
        self._already_triggered = False
        self._unsub = None
        self._acknowledged = False
        self._escalation_task = None
        self._escalated = False
        self._cleared = False

    def _get_global_options(self):
        """Get global options from hass.data"""
        return self.hass.data.get(DOMAIN, {}).get("global_options", {})

    def _get_escalation_time(self):
        """Get escalation time from global options or use default"""
        global_options = self._get_global_options()
        return global_options.get("default_escalation_time", ESCALATION_MINUTES * 60)

    def _should_send_global_notification(self):
        """Check if global notifications are enabled"""
        global_options = self._get_global_options()
        return global_options.get("enable_global_notifications", False)

    def _get_global_notification_service(self):
        """Get global notification service"""
        global_options = self._get_global_options()
        return global_options.get("global_notification_service", "")

    def _get_global_notification_message(self):
        """Get global notification message template"""
        global_options = self._get_global_options()
        template = global_options.get(
            "global_notification_message", "Emergency Alert: {alert_name} - {severity}")
        return template.format(
            alert_name=self._alert_name,
            severity=self._severity,
            group=self._group,
            entity_id=self._entity_id or "N/A"
        )

    async def async_added_to_hass(self):
        # Track all referenced entities for state changes
        entities = set()
        if self._trigger_type == "simple" and self._entity_id:
            entities.add(self._entity_id)
        elif self._trigger_type == "logical" and self._logical_conditions:
            for cond in self._logical_conditions:
                if isinstance(cond, dict) and "entity_id" in cond:
                    entities.add(cond["entity_id"])
        # For template, we can't know all entities, so listen to all changes
        if self._trigger_type == "template":
            entities = None

        @callback
        def state_change(event):
            self._evaluate_trigger()

        if entities:
            self._unsub = async_track_state_change_event(
                self.hass, list(entities), state_change
            )
        else:
            # Listen to all state changes for template triggers
            self._unsub = async_track_state_change_event(
                self.hass, [], state_change)
        # Set initial state
        self._evaluate_trigger()
        # Create initial status sensor
        self._update_status_sensor()

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()
            self._unsub = None
        if DOMAIN in self.hass.data and "entities" in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]["entities"] = [
                e for e in self.hass.data[DOMAIN]["entities"] if e != self
            ]
        if self._escalation_task:
            self._escalation_task()
            self._escalation_task = None

    @property
    def is_on(self):
        return self._is_on and not self._acknowledged

    @property
    def extra_state_attributes(self):
        return {
            "first_triggered": self._first_triggered,
            "last_cleared": self._last_cleared,
            "monitored_entity": self._entity_id,
            "trigger_type": self._trigger_type,
            "trigger_state": self._trigger_state,
            "template": self._template,
            "logical_conditions": self._logical_conditions,
            "action_service": self._action_service,
            "severity": self._severity,
            "group": self._group,
            "acknowledged": self._acknowledged,
            "escalated": self._escalated,
        }

    @callback
    def _evaluate_trigger(self):
        triggered = False
        if (
            self._trigger_type == "simple"
            and self._entity_id
            and self._trigger_state is not None
        ):
            state = self.hass.states.get(self._entity_id)
            triggered = state and state.state == self._trigger_state
        elif self._trigger_type == "template" and self._template:
            tpl = Template(self._template, self.hass)
            try:
                rendered = tpl.async_render()
                triggered = rendered in (True, "True", "true", 1, "1")
            except Exception as e:
                _LOGGER.error(f"Template evaluation error: {e}")
                triggered = False
        elif self._trigger_type == "logical" and self._logical_conditions:
            # Each condition is a dict: {"type": "simple"/"template", ...}
            results = []
            for cond in self._logical_conditions:
                if cond.get("type") == "simple":
                    state = self.hass.states.get(cond["entity_id"])
                    results.append(state and state.state ==
                                   cond["trigger_state"])
                elif cond.get("type") == "template":
                    tpl = Template(cond["template"], self.hass)
                    try:
                        rendered = tpl.async_render()
                        results.append(rendered in (
                            True, "True", "true", 1, "1"))
                    except Exception as e:
                        _LOGGER.error(f"Logical template error: {e}")
                        results.append(False)
            # Default to AND logic; could add OR support in future
            triggered = all(results)
        self._set_state(triggered)

    @callback
    def _set_state(self, triggered):
        if triggered:
            if not self._already_triggered:
                self._is_on = True
                self._first_triggered = datetime.now().isoformat()
                self._already_triggered = True
                self._acknowledged = False
                self._escalated = False
                self.async_write_ha_state()
                self._call_actions(self._on_triggered)
                self._start_escalation_timer()
                async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)
            else:
                self._is_on = True
                self.async_write_ha_state()
                async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)
        else:
            if self._already_triggered:
                self._last_cleared = datetime.now().isoformat()
                self._call_actions(self._on_cleared)
            self._is_on = False
            self._already_triggered = False
            self._acknowledged = False
            self._escalated = False
            self.async_write_ha_state()
            self._cancel_escalation_timer()
            async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)

    def _call_actions(self, actions):
        # Call configured actions
        if actions:
            for action in actions:
                try:
                    domain, service = action["service"].split(".", 1)
                    service_data = action.get("data", {})
                    # Fire and forget service call
                    _ = self.hass.services.async_call(
                        domain, service, service_data, blocking=False
                    )
                except Exception as e:
                    _LOGGER.error(f"Error calling action: {e}")

        # Send global notification if enabled and this is a trigger event
        if actions == self._on_triggered and self._should_send_global_notification():
            global_service = self._get_global_notification_service()
            if global_service:
                try:
                    domain, service = global_service.split(".", 1)
                    message = self._get_global_notification_message()
                    service_data = {"message": message}
                    _ = self.hass.services.async_call(
                        domain, service, service_data, blocking=False
                    )
                    _LOGGER.debug(
                        f"Sent global notification for {self._alert_name}")
                except Exception as e:
                    _LOGGER.error(f"Error sending global notification: {e}")

    def _start_escalation_timer(self):
        if self._escalation_task:
            self._escalation_task()

        @callback
        def escalate(_):
            if self._is_on and not self._acknowledged:
                self._escalated = True
                self.async_write_ha_state()
                self._call_actions(self._on_escalated)
                async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)

        self._escalation_task = async_call_later(
            self.hass, self._get_escalation_time(), escalate
        )

    def _cancel_escalation_timer(self):
        if self._escalation_task:
            self._escalation_task()
            self._escalation_task = None

    async def async_acknowledge(self):
        self._acknowledged = True
        self._cleared = False
        self._escalated = False
        self._cancel_escalation_timer()
        self.async_write_ha_state()
        self._update_status_sensor()
        async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)

    async def async_clear(self):
        """Manually clear the alert."""
        if self._already_triggered:
            self._last_cleared = datetime.now().isoformat()
            self._call_actions(self._on_cleared)
        self._is_on = False
        self._already_triggered = False
        self._acknowledged = False
        self._escalated = False
        self._cleared = True
        self.async_write_ha_state()
        self._cancel_escalation_timer()
        self._update_status_sensor()
        async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)

    async def async_escalate(self):
        """Manually escalate the alert."""
        if self._is_on and not self._escalated:
            self._escalated = True
            self._acknowledged = False
            self._cleared = False
            self.async_write_ha_state()
            self._call_actions(self._on_escalated)
            self._update_status_sensor()
            async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)

    def get_status(self):
        """Get current alert status."""
        if self._cleared:
            return "cleared"
        elif self._acknowledged:
            return "acknowledged"
        elif self._escalated:
            return "escalated"
        elif self._is_on:
            return "active"
        else:
            return "inactive"

    def _update_status_sensor(self):
        """Update the companion status sensor."""
        status = self.get_status()
        status_entity_id = f"sensor.emergency_{self._alert_id}_status"
        _LOGGER.debug(f"Updating status sensor {status_entity_id} to {status}")
        self.hass.states.async_set(
            status_entity_id,
            status,
            {
                "friendly_name": f"Emergency {self._alert_id.replace('_', ' ').title()} Status",
                "icon": {
                    "active": "mdi:alert",
                    "acknowledged": "mdi:check-circle",
                    "cleared": "mdi:check-circle-outline",
                    "escalated": "mdi:arrow-up-circle",
                    "inactive": "mdi:circle-outline"
                }.get(status, "mdi:help-circle"),
                "device_class": "enum"
            }
        )
