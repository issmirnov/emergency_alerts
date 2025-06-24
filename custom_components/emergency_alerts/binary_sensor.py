from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_call_later,
)
from homeassistant.core import callback
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from datetime import datetime, timedelta
from homeassistant.helpers.template import Template
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)

ESCALATION_MINUTES = 5  # Default escalation time if not specified
SUMMARY_UPDATE_SIGNAL = "emergency_alerts_summary_update"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
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
    on_triggered = data.get("on_triggered")
    on_cleared = data.get("on_cleared")
    on_escalated = data.get("on_escalated")
    sensor = EmergencyBinarySensor(
        hass,
        name,
        trigger_type,
        entity_id,
        trigger_state,
        template,
        logical_conditions,
        action_service,
        severity,
        group,
        on_triggered,
        on_cleared,
        on_escalated,
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
        name,
        trigger_type,
        entity_id=None,
        trigger_state=None,
        template=None,
        logical_conditions=None,
        action_service=None,
        severity="warning",
        group="other",
        on_triggered=None,
        on_cleared=None,
        on_escalated=None,
    ):
        self.hass = hass
        self._attr_name = f"Emergency: {name}"
        self._attr_unique_id = f"emergency_{name}"
        self._trigger_type = trigger_type
        self._entity_id = entity_id
        self._trigger_state = trigger_state
        self._template = template
        self._logical_conditions = logical_conditions or []
        self._action_service = action_service
        self._severity = severity
        self._group = group
        self._on_triggered = on_triggered or []
        self._on_cleared = on_cleared or []
        self._on_escalated = on_escalated or []
        self._is_on = False
        self._first_triggered = None
        self._last_cleared = None
        self._already_triggered = False
        self._unsub = None
        self._acknowledged = False
        self._escalation_task = None
        self._escalated = False

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
                self.hass, None, state_change
            )
        # Set initial state
        self._evaluate_trigger()

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
        prev_state = self._is_on
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
                    results.append(
                        state and state.state == cond["trigger_state"]
                    )
                elif cond.get("type") == "template":
                    tpl = Template(cond["template"], self.hass)
                    try:
                        rendered = tpl.async_render()
                        results.append(
                            rendered in (True, "True", "true", 1, "1")
                        )
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
        if not actions:
            return
        for action in actions:
            try:
                domain, service = action["service"].split(".", 1)
                service_data = action.get("data", {})
                self.hass.services.async_call(
                    domain, service, service_data, blocking=False
                )
            except Exception as e:
                _LOGGER.error(f"Error calling action: {e}")

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
            self.hass, ESCALATION_MINUTES * 60, escalate
        )

    def _cancel_escalation_timer(self):
        if self._escalation_task:
            self._escalation_task()
            self._escalation_task = None

    async def async_acknowledge(self):
        self._acknowledged = True
        self._cancel_escalation_timer()
        self.async_write_ha_state()
        async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL) 