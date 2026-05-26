import json
import logging
from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send, async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_template_result,
    TrackTemplate,
)
from homeassistant.helpers.template import Template
import yaml

from .const import (
    DOMAIN,
    STATE_ACKNOWLEDGED,
    STATE_SNOOZED,
    STATE_RESOLVED,
    STATE_ACTIVE,
    STATE_INACTIVE,
    STATE_ESCALATED,
    SIGNAL_ALERT_UPDATE,
    SIGNAL_SWITCH_UPDATE,
    CONF_ON_ACKNOWLEDGED,
    CONF_ON_SNOOZED,
    CONF_ON_RESOLVED,
    # TRIGGER_TYPE_COMBINED removed in Phase 2
    COMP_EQ,
    COMP_NE,
    COMP_LT,
    COMP_LTE,
    COMP_GT,
    COMP_GTE,
)

_LOGGER = logging.getLogger(__name__)

ESCALATION_MINUTES = 5  # Default escalation time if not specified
SUMMARY_UPDATE_SIGNAL = "emergency_alerts_summary_update"


def _resolve_on_triggered(alert_data):
    """Resolve the on-trigger actions for an alert.

    Returns the explicit ``on_triggered`` action list if set, otherwise
    synthesizes one from ``on_triggered_script`` (the field exposed by the
    config_flow UI). Prior to this resolver, ``on_triggered_script`` was
    stored in alert_data but never consumed by binary_sensor, so the script
    field in the UI did nothing.

    The synthesized action emits ``entity_id`` inside ``data`` (not
    ``target``) because both ``_call_actions`` and ``_execute_action``
    forward only ``action.get("data", {})`` into ``hass.services.async_call``
    — ``target`` would be silently dropped, leaving the script call with no
    entity to operate on. HA accepts ``entity_id`` inside ``data`` for the
    ``script.turn_on`` service (legacy format).

    Output is a list of action dicts that _parse_actions can normalize.
    """
    explicit = alert_data.get("on_triggered")
    if explicit:
        return explicit
    script_entity = alert_data.get("on_triggered_script")
    if script_entity:
        return [
            {
                "service": "script.turn_on",
                "data": {"entity_id": script_entity},
            }
        ]
    return None


def _parse_actions(action_string):
    """Parse action string (JSON/YAML) into a list of action dictionaries.

    Supports:
    - Profile references: "profile:profile_id" (returns as-is for later resolution)
    - Single action dict: {"service": "...", "data": {...}}
    - List of actions: [{"service": "..."}, ...]
    - Already parsed list: [dict, ...]
    """
    if not action_string:
        return []

    if isinstance(action_string, list):
        return action_string  # Already a list

    if isinstance(action_string, str):
        # Check if it's a profile reference (starts with "profile:")
        if action_string.startswith("profile:"):
            return action_string  # Return as-is for later resolution
        
        try:
            # Try parsing as JSON first
            result = json.loads(action_string)
            # If it's a single dict, wrap it in a list
            if isinstance(result, dict):
                return [result]
            # If it's already a list, return it
            if isinstance(result, list):
                return result
            # Otherwise, return empty list (invalid format)
            return []
        except json.JSONDecodeError:
            try:
                # Try parsing as YAML
                result = yaml.safe_load(action_string)
                # If it's a single dict, wrap it in a list
                if isinstance(result, dict):
                    return [result]
                # If it's already a list, return it
                if isinstance(result, list):
                    return result
                # Otherwise, return empty list (invalid format)
                return []
            except yaml.YAMLError:
                _LOGGER.error(f"Failed to parse actions: {action_string}")
                return []

    # If it's already a dict (from config flow), wrap it in a list
    if isinstance(action_string, dict):
        return [action_string]

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
            result = json.loads(conditions_string)
            # Ensure result is a list
            if not isinstance(result, list):
                return []
            return result
        except json.JSONDecodeError:
            try:
                # Try parsing as YAML
                result = yaml.safe_load(conditions_string)
                # Ensure result is a list
                if not isinstance(result, list):
                    return []
                return result
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
            
            # Register entities for service access BEFORE async_add_entities completes
            # This ensures switches can find them immediately
            if DOMAIN not in hass.data:
                hass.data[DOMAIN] = {}
            if "entities" not in hass.data[DOMAIN]:
                hass.data[DOMAIN]["entities"] = []
            hass.data[DOMAIN]["entities"].extend(entities)


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
        self._logical_operator = alert_data.get("logical_operator", "and")
        self._combined_conditions = alert_data.get("combined_conditions", [])
        self._combined_operator = alert_data.get("combined_operator", "and")
        self._action_service = alert_data.get("action_service")
        self._severity = alert_data.get("severity", "warning")
        self._remind_after_seconds = alert_data.get("remind_after_seconds")
        # Debounce: alert fires only after the trigger has been true for this
        # many seconds continuously. 0 (default) = fire immediately. Useful for
        # "window open >5min", "garage open too long", "leak sensor on >10s
        # to debounce false positives", etc. Applies to all trigger types.
        try:
            self._for_seconds = int(alert_data.get("for_seconds") or 0)
        except (TypeError, ValueError):
            self._for_seconds = 0
        self._on_triggered = _parse_actions(
            _resolve_on_triggered(alert_data)
        )
        self._on_cleared = _parse_actions(alert_data.get("on_cleared"))
        self._on_escalated = _parse_actions(alert_data.get("on_escalated"))

        # Entity attributes
        self._attr_name = f"Emergency: {name}"
        self._attr_unique_id = f"emergency_{hub_name}_{alert_id}"
        # Force a clean entity_id on first registration. Without this, HA
        # would slugify-combine device.name + entity._attr_name and produce
        # binary_sensor.emergency_alert_<name>_emergency_<name>. Setting
        # entity_id directly is the documented way to hint a specific
        # object_id (HA's entity_platform reads this into
        # internal_integration_suggested_object_id during async_added_to_hass).
        # Existing alerts in the entity_registry keep their stored entity_id;
        # this only affects new alerts.
        self.entity_id = f"binary_sensor.emergency_{alert_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"alert_{entry.entry_id}_{alert_id}")},
            "name": f"Emergency Alert: {name}",
            "manufacturer": "Emergency Alerts",
            "model": f"{self._severity.title()} Alert",
            "sw_version": "1.0",
            "via_device": (DOMAIN, f"hub_{entry.entry_id}"),
        }

        # State tracking
        self._is_on = False
        self._first_triggered = None
        self._last_cleared = None
        self._already_triggered = False
        self._unsub = None

        # New state machine attributes
        self._acknowledged = False
        self._snoozed = False
        self._resolved = False
        self._escalated = False
        self._cleared = False  # Legacy, can be removed

        # Timers and async tasks
        self._escalation_task = None
        self._snooze_task = None
        self._snooze_until = None
        # for_seconds delay timer — armed when the trigger first goes True
        # and held for self._for_seconds before the alert actually fires.
        # Cancelled if the trigger clears before the delay elapses.
        self._pending_trigger_unsub = None

        # Store config entry for switch access
        self._config_entry = entry

    def _get_global_options(self):
        """Get global options from hass.data"""
        return self.hass.data.get(DOMAIN, {}).get("global_options", {})

    def _get_escalation_time(self):
        """Get escalation time from global options or use default"""
        if self._remind_after_seconds is not None:
            return self._remind_after_seconds
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
        # Register cleanup callback when entity is properly added to hass
        self.async_on_remove(self._cleanup_timers)
        
        # Track referenced entities so the trigger re-evaluates when they change.
        @callback
        def state_change(event):
            self._evaluate_trigger()

        if self._trigger_type == "template" and self._template:
            # Template triggers must use async_track_template_result so HA
            # subscribes to the entities the Jinja actually references — not
            # just an explicit entity_id field on the alert. Previously this
            # branch called async_track_state_change_event(hass, [], ...) with
            # an empty entity list, which subscribes to nothing and causes
            # template alerts to never re-evaluate after their initial render
            # (so they latch on/off until integration reload).
            template = Template(self._template, self.hass)

            @callback
            def template_result_change(event, updates):
                self._evaluate_trigger()

            info = async_track_template_result(
                self.hass,
                [TrackTemplate(template, None)],
                template_result_change,
            )
            self._unsub = info.async_remove
            # Kick off the initial async render so HA registers the listener
            # against the discovered entities.
            info.async_refresh()
        else:
            # simple + logical triggers: derive the explicit entity list.
            entities: set[str] = set()
            if self._trigger_type == "simple" and self._entity_id:
                entities.add(self._entity_id)
            elif self._trigger_type == "logical" and self._logical_conditions:
                for cond in self._logical_conditions:
                    if isinstance(cond, dict) and "entity_id" in cond:
                        entities.add(cond["entity_id"])

            if entities:
                self._unsub = async_track_state_change_event(
                    self.hass, list(entities), state_change
                )
            else:
                # No entities to watch (logical with no entity_ids, or an
                # otherwise unconfigured alert) — leave the listener unset.
                self._unsub = None

        # Listen for switch updates (switches will broadcast their state changes)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_SWITCH_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
                self._handle_switch_update,
            )
        )

        # Set initial state
        self._evaluate_trigger()
        # Create initial status sensor
        self._update_status_sensor()

    @callback
    def _handle_switch_update(self, switch_type: str, state: bool) -> None:
        """Handle switch state updates."""
        _LOGGER.debug(f"Alert {self._alert_id} received switch update: {switch_type}={state}")
        # Switches update our internal state directly, so just refresh UI
        self.async_write_ha_state()
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
        if self._snooze_task:
            self._snooze_task.cancel()
            self._snooze_task = None

    @property
    def is_on(self):
        """Binary sensor state - alert is actively triggered."""
        # Show as ON only if condition is met and not in a handled state
        if self._resolved:
            return False  # Resolved alerts don't show as active
        if self._snoozed:
            return False  # Snoozed alerts don't show as active
        return self._is_on

    @property
    def extra_state_attributes(self):
        attrs = {
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
            "status": self.get_status(),
            # State machine attributes
            "acknowledged": self._acknowledged,
            "snoozed": self._snoozed,
            "resolved": self._resolved,
            "escalated": self._escalated,
        }

        # Add snooze timing if snoozed
        if self._snoozed and self._snooze_until:
            attrs["snooze_until"] = self._snooze_until.isoformat()

        return attrs

    def _compare_values(self, entity_state, comparator, expected_value):
        """Compare entity state using provided comparator."""
        # Attempt numeric comparison first if both are numeric-like
        def _to_number(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        left_num = _to_number(entity_state)
        right_num = _to_number(expected_value)

        if comparator in {COMP_LT, COMP_LTE, COMP_GT, COMP_GTE} and left_num is not None and right_num is not None:
            if comparator == COMP_LT:
                return left_num < right_num
            if comparator == COMP_LTE:
                return left_num <= right_num
            if comparator == COMP_GT:
                return left_num > right_num
            if comparator == COMP_GTE:
                return left_num >= right_num

        # Fallback to string comparison
        if comparator == COMP_EQ:
            return str(entity_state) == str(expected_value)
        if comparator == COMP_NE:
            return str(entity_state) != str(expected_value)

        # Default equality if comparator unknown
        return str(entity_state) == str(expected_value)

    @callback
    def _evaluate_trigger(self):
        """Compute the current trigger truth value and route to _set_state."""
        self._set_state(self._compute_triggered())

    @callback
    def _compute_triggered(self) -> bool:
        """Pure computation: is the configured trigger condition currently true?

        Split out from _evaluate_trigger so that delay callbacks can re-check
        truth without recursing through the side-effecting state machine.
        """
        if (
            self._trigger_type == "simple"
            and self._entity_id
            and self._trigger_state is not None
        ):
            state = self.hass.states.get(self._entity_id)
            return bool(state and state.state == self._trigger_state)
        if self._trigger_type == "template" and self._template:
            tpl = Template(self._template, self.hass)
            try:
                rendered = tpl.async_render()
                return rendered in (True, "True", "true", 1, "1")
            except Exception as e:
                _LOGGER.error(f"Template evaluation error: {e}")
                return False
        if self._trigger_type == "logical" and self._logical_conditions:
            results = []
            for cond in self._logical_conditions:
                if isinstance(cond, dict) and "entity_id" in cond and "state" in cond:
                    state = self.hass.states.get(cond["entity_id"])
                    results.append(bool(state and state.state == cond["state"]))
                else:
                    _LOGGER.warning(
                        f"Invalid logical condition format: {cond}")
                    results.append(False)
            if self._logical_operator == "or":
                return any(results) if results else False
            return all(results) if results else False
        return False

    @callback
    def _cancel_pending_trigger(self):
        """Cancel the for_seconds delay timer if armed."""
        if self._pending_trigger_unsub:
            self._pending_trigger_unsub()
            self._pending_trigger_unsub = None

    @callback
    def _on_for_seconds_elapsed(self, _now):
        """Called when the for_seconds delay has elapsed.

        Re-check the trigger from scratch. If it's still true, fire the alert
        for real (bypassing the delay this time). If the condition cleared
        during the delay (and we somehow missed cancelling), don't fire.
        """
        self._pending_trigger_unsub = None
        if self._compute_triggered():
            self._set_state(True, skip_delay=True)
        # If False, do nothing — the cleared-state side already ran when the
        # underlying entity changed.

    @callback
    def _set_state(self, triggered, skip_delay: bool = False):
        """Set alert state based on trigger evaluation.

        If for_seconds > 0 and this is a fresh trigger transition, arm a
        delay timer and exit; the timer's callback will re-enter this method
        with skip_delay=True once the dwell time has elapsed.
        """
        if triggered:
            # Gate the initial transition on the debounce delay, but only
            # for fresh trigger events. If we're already firing, keep firing.
            if (
                self._for_seconds > 0
                and not skip_delay
                and not self._already_triggered
                and self._pending_trigger_unsub is None
            ):
                _LOGGER.debug(
                    f"Alert {self._alert_id} trigger met; holding for "
                    f"{self._for_seconds}s before firing"
                )
                self._pending_trigger_unsub = async_call_later(
                    self.hass, self._for_seconds, self._on_for_seconds_elapsed
                )
                return
            # for_seconds==0 OR delay already elapsed OR already firing → proceed
            self._apply_triggered_state()
        else:
            # Trigger cleared — if a delay was pending, cancel it (alert never
            # transitions to active; cleared-side cleanup runs as normal).
            self._cancel_pending_trigger()
            self._apply_cleared_state()

    @callback
    def _apply_triggered_state(self):
        """The 'triggered' branch: mark active, run on_triggered actions, arm escalation."""
        if self._resolved:
            _LOGGER.debug(
                f"Alert {self._alert_id} condition met but resolved — not triggering"
            )
            return

        if not self._already_triggered:
            # First trigger
            self._is_on = True
            self._first_triggered = datetime.now().isoformat()
            self._already_triggered = True
            self.async_write_ha_state()
            self._update_status_sensor()
            self._call_actions(self._on_triggered)

            if not self._acknowledged and not self._snoozed:
                self.hass.async_create_task(self._start_escalation_timer())

            async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)
            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
            )
        else:
            # Already triggered, just refresh state
            self._is_on = True
            self.async_write_ha_state()
            self._update_status_sensor()
            async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)

    @callback
    def _apply_cleared_state(self):
        """The 'cleared' branch: run on_cleared, drop is_on, reset flags."""
        if self._already_triggered:
            self._last_cleared = datetime.now().isoformat()
            self._call_actions(self._on_cleared)

        self._is_on = False
        self._already_triggered = False

        if self._resolved:
            self._resolved = False
            _LOGGER.debug(
                f"Alert {self._alert_id} condition cleared — reset resolved flag"
            )

        if self._escalated:
            self._escalated = False

        self.async_write_ha_state()
        self._update_status_sensor()
        self._cancel_escalation_timer()
        async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)
        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
        )

    def _resolve_profile(self, profile_ref):
        """Resolve a profile reference to its action list.

        Args:
            profile_ref: String in format "profile:profile_id"

        Returns:
            List of action dicts, or empty list if profile not found
        """
        if not isinstance(profile_ref, str) or not profile_ref.startswith("profile:"):
            return []

        profile_id = profile_ref.split(":", 1)[1]

        # Find Global Settings Hub entry
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("hub_type") == "global":
                profiles = entry.options.get("notification_profiles", {})
                profile = profiles.get(profile_id)
                if profile:
                    _LOGGER.debug(f"Resolved profile '{profile_id}' to {len(profile.get('actions', []))} actions")
                    return profile.get("actions", [])

        _LOGGER.warning(f"Profile '{profile_id}' not found in Global Settings")
        return []

    async def _execute_action(self, action_config):
        """Execute an action configuration (called by switches).

        Action config can be:
        - A list of action dicts [{"service": "...", "data": {...}}]
        - A single action dict {"service": "...", "data": {...}}
        - A profile reference string "profile:profile_id"
        """
        if not action_config:
            return

        # Check if it's a profile reference
        if isinstance(action_config, str) and action_config.startswith("profile:"):
            actions = self._resolve_profile(action_config)
        # Otherwise treat as action list
        elif isinstance(action_config, list):
            actions = action_config
        else:
            actions = [action_config]

        for action in actions:
            try:
                if isinstance(action, dict) and "service" in action:
                    domain, service = action["service"].split(".", 1)
                    service_data = action.get("data", {})
                    await self.hass.services.async_call(
                        domain, service, service_data, blocking=False
                    )
                    _LOGGER.debug(f"Executed action {action['service']} for {self._alert_id}")
            except Exception as e:
                _LOGGER.error(f"Error executing action: {e}")

    def _call_actions(self, actions):
        """Call configured actions.

        Actions can be:
        - A list of action dicts [{"service": "...", "data": {...}}]
        - A profile reference string "profile:profile_id"
        """
        if not actions:
            return

        # Resolve profile reference if needed
        action_list = actions
        if isinstance(actions, str) and actions.startswith("profile:"):
            action_list = self._resolve_profile(actions)

        # Ensure we have a list
        if not isinstance(action_list, list):
            action_list = [action_list]

        # Call configured actions
        for action in action_list:
            try:
                if isinstance(action, dict) and "service" in action:
                    domain, service = action["service"].split(".", 1)
                    service_data = action.get("data", {})
                    # Fire and forget service call - properly schedule the async call

                    async def safe_call():
                        try:
                            await self.hass.services.async_call(
                                domain, service, service_data, blocking=False
                            )
                        except Exception as e:
                            if (
                                hasattr(e, "__class__") and
                                e.__class__.__name__ == "ServiceNotFound"
                            ):
                                _LOGGER.warning(
                                    f"Service not found: {domain}.{service}, skipping action.")
                            else:
                                _LOGGER.error(f"Error calling action: {e}")
                    self.hass.async_create_task(safe_call())
            except Exception as e:
                _LOGGER.error(f"Error preparing action: {e}")

        # Send global notification if enabled and this is a trigger event
        if actions == self._on_triggered and self._should_send_global_notification():
            global_service = self._get_global_notification_service()
            if global_service:
                try:
                    domain, service = global_service.split(".", 1)
                    message = self._get_global_notification_message()
                    service_data = {"message": message}
                    # Fire and forget service call - properly schedule the async call
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            domain, service, service_data, blocking=False
                        )
                    )
                    _LOGGER.debug(
                        f"Sent global notification for {self._alert_name}")
                except Exception as e:
                    _LOGGER.error(f"Error sending global notification: {e}")

    @callback
    def _cleanup_timers(self):
        """Clean up all timers when entity is removed."""
        if self._escalation_task:
            self._escalation_task()
            self._escalation_task = None
        if self._snooze_task:
            self._snooze_task.cancel()
            self._snooze_task = None
        if self._pending_trigger_unsub:
            self._pending_trigger_unsub()
            self._pending_trigger_unsub = None

    async def _start_escalation_timer(self):
        """Start escalation timer (called by switches when un-acknowledging)."""
        remind_after = self._get_escalation_time()
        if remind_after is None or remind_after <= 0:
            return

        if self._escalation_task:
            self._escalation_task()

        @callback
        def escalate(_):
            # Only escalate if still active and not acknowledged/snoozed/resolved
            if self._is_on and not self._acknowledged and not self._snoozed and not self._resolved:
                self._escalated = True
                self.async_write_ha_state()
                self._call_actions(self._on_escalated)
                async_dispatcher_send(self.hass, SUMMARY_UPDATE_SIGNAL)
                # Notify switches
                async_dispatcher_send(
                    self.hass,
                    f"{SIGNAL_ALERT_UPDATE}_{self._entry.entry_id}_{self._alert_id}",
                )
                _LOGGER.info(f"Alert {self._alert_id} escalated due to timeout")

        self._escalation_task = async_call_later(
            self.hass, remind_after, escalate
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
        # Priority order matters
        if not self._is_on:
            return STATE_INACTIVE
        if self._resolved:
            return STATE_RESOLVED
        if self._snoozed:
            return STATE_SNOOZED
        if self._escalated:
            return STATE_ESCALATED
        if self._acknowledged:
            return STATE_ACKNOWLEDGED
        return STATE_ACTIVE

    def _update_status_sensor(self):
        """Update the companion status sensor."""
        status = self.get_status()
        status_entity_id = f"sensor.emergency_{self._alert_id}_status"
        _LOGGER.debug(f"Updating status sensor {status_entity_id} to {status}")

        attrs = {
            "friendly_name": f"Emergency {self._alert_id.replace('_', ' ').title()} Status",
            "icon": {
                STATE_ACTIVE: "mdi:alert",
                STATE_ACKNOWLEDGED: "mdi:check-circle",
                STATE_SNOOZED: "mdi:bell-sleep",
                STATE_ESCALATED: "mdi:arrow-up-circle",
                STATE_RESOLVED: "mdi:check-circle",
                STATE_INACTIVE: "mdi:circle-outline",
                "cleared": "mdi:check-circle-outline",  # Legacy
            }.get(status, "mdi:help-circle"),
            "device_class": "enum",
            "alert_id": self._alert_id,
            "alert_name": self._alert_name,
        }

        # Add snooze timing if snoozed
        if self._snoozed and self._snooze_until:
            attrs["snooze_until"] = self._snooze_until.isoformat()

        self.hass.states.async_set(status_entity_id, status, attrs)
