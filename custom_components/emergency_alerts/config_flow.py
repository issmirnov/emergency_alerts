"""Config flow for Emergency Alerts - Simplified single-page approach."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector


def _slugify_alert_id(name: str) -> str:
    """Derive a clean alert_id from a display name.

    Strips/collapses non-alphanumeric characters so names like
    "Smoke/CO Detector (Triggered)" don't produce alert_ids with
    slashes or parens (which break remove_alert lookups and pollute
    entity_id derivation).
    """
    slug = re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_")
    return re.sub(r"_+", "_", slug)


def _optional(key: str, value: Any = None) -> vol.Optional:
    """Build a vol.Optional that pre-fills via `suggested_value`, not `default`.

    `EntitySelector` rejects empty strings ("Entity not found"), so passing
    `default=""` to an Optional EntitySelector breaks form submission whenever
    the field is left blank. The HA-idiomatic alternative is to pre-fill the
    visible value via `description={"suggested_value": ...}` and leave the
    schema default unset. When `value` is falsy we omit even the suggestion so
    the field renders truly empty.
    """
    if value:
        return vol.Optional(key, description={"suggested_value": value})
    return vol.Optional(key)

from .const import (
    DOMAIN,
    CONF_HUB_TYPE,
    CONF_GROUP,
    CONF_HUB_NAME,
    CONF_CUSTOM_NAME,
    CONF_ALERTS,
)

_LOGGER = logging.getLogger(__name__)


class EmergencyAlertsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Emergency Alerts."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Handle the initial step - directly to group setup."""
        return await self.async_step_group_setup(user_input)

    async def async_step_group_setup(self, user_input=None):
        """Create alert group hub."""
        errors = {}

        if user_input is not None:
            group_name = user_input["group_name"].strip()
            hub_name = group_name.lower()

            for entry in self._async_current_entries():
                if (entry.data.get(CONF_HUB_TYPE) == "group" and 
                    entry.data.get(CONF_HUB_NAME, "").lower() == hub_name):
                    errors["group_name"] = "group_already_configured"
                    break

            if not errors:
                return self.async_create_entry(
                    title=f"Emergency Alerts - {group_name}",
                    data={
                        CONF_HUB_TYPE: "group",
                        CONF_GROUP: group_name,
                        CONF_HUB_NAME: hub_name,
                        CONF_CUSTOM_NAME: "",
                        CONF_ALERTS: {},
                    },
                    options={"default_escalation_time": 300},
                )

        return self.async_show_form(
            step_id="group_setup",
            data_schema=vol.Schema({
                vol.Required("group_name", default="Security"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return EmergencyOptionsFlow()


class EmergencyOptionsFlow(config_entries.OptionsFlow):
    """Options flow - UNIFIED SINGLE PAGE APPROACH."""

    async def async_step_init(self, user_input=None):
        """Handle options."""
        hub_type = self.config_entry.data.get(CONF_HUB_TYPE)

        if hub_type == "global":
            return await self.async_step_global_options(user_input)
        return await self.async_step_group_options(user_input)

    async def async_step_global_options(self, user_input=None):
        """Global settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="global_options",
            data_schema=vol.Schema({
                vol.Optional(
                    "default_escalation_time",
                    default=self.config_entry.options.get("default_escalation_time", 300),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            }),
        )

    async def async_step_group_options(self, user_input=None):
        """Show menu."""
        alerts = self.config_entry.data.get(CONF_ALERTS, {})
        alert_count = len(alerts)

        if user_input is not None:
            action = user_input.get("action")
            if action == "add_alert":
                return await self.async_step_add_alert()
            elif action == "edit_alert":
                return await self.async_step_edit_alert()
            elif action == "remove_alert":
                return await self.async_step_remove_alert()

        return self.async_show_form(
            step_id="group_options",
            data_schema=vol.Schema({
                vol.Required("action"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "add_alert", "label": "➕ Add New Alert"},
                            {"value": "edit_alert", "label": "✏️ Edit Alert"},
                            {"value": "remove_alert", "label": "🗑️ Remove Alert"},
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }),
            description_placeholders={"alert_count": str(alert_count)},
        )

    async def async_step_add_alert(self, user_input=None):
        """Add or edit alert - SINGLE PAGE with ALL fields.

        Doubles as the form-submission handler for `edit_alert_form` because
        that step reuses `step_id="add_alert"` for the form rendering. When
        `self._editing_alert_id` is set we treat the submission as an edit:
        the existing alert_id is allowed (it's the one being edited) and we
        drop the old key if the name change produces a different slug.
        """
        errors = {}
        editing_id = getattr(self, "_editing_alert_id", None)

        if user_input is not None:
            try:
                alert_id = _slugify_alert_id(user_input["name"])
                alerts = dict(self.config_entry.data.get(CONF_ALERTS, {}))

                # Duplicate-name guard: only applies to adds, or to edits where
                # the user renamed the alert into a slug that collides with a
                # different existing alert.
                if alert_id in alerts and alert_id != editing_id:
                    errors["name"] = "already_configured"
                else:
                    # When editing with a renamed alert (slug changed), remove
                    # the old key so we don't leave two copies behind.
                    if editing_id and editing_id != alert_id:
                        alerts.pop(editing_id, None)

                    alerts[alert_id] = self._build_alert_data(user_input)
                    new_data = dict(self.config_entry.data)
                    new_data[CONF_ALERTS] = alerts

                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=new_data
                    )

                    # Clear edit state so a subsequent add isn't treated as edit
                    self._editing_alert_id = None

                    # Reload entry to create/update entities instantly
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                    return self.async_create_entry(title="", data={})

            except Exception as err:
                _LOGGER.error("Error %s alert: %s", "editing" if editing_id else "creating", err)
                errors["base"] = "invalid_input"

        return self.async_show_form(
            step_id="add_alert",
            data_schema=self._build_alert_schema(
                defaults=user_input if editing_id else None
            ),
            errors=errors,
        )

    def _build_alert_schema(self, defaults=None):
        """Build UNIFIED schema - ALL fields on ONE page."""
        defaults = defaults or {}

        return vol.Schema({
            vol.Required("name", default=defaults.get("name", "")): str,
            vol.Required(
                "severity", default=defaults.get("severity", "warning")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["info", "warning", "critical"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                "trigger_type", default=defaults.get("trigger_type", "simple")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["simple", "template"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            _optional("entity_id", defaults.get("entity_id")): selector.EntitySelector(),
            vol.Optional(
                "trigger_state", default=defaults.get("trigger_state", "on")
            ): str,
            vol.Optional("template", default=defaults.get("template", "")): selector.TemplateSelector(),
            # Debounce / sustain duration: alert only fires after the trigger
            # condition has been true for this many seconds continuously. 0 =
            # no debounce (fire immediately). Useful for "window open >5min",
            # "garage open too long", "leak sensor on >10s to avoid false
            # positives", etc. Applies to all trigger types.
            vol.Optional(
                "for_seconds", default=defaults.get("for_seconds", 0)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),
            _optional("on_triggered_script", defaults.get("on_triggered_script")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="script")
            ),
            _optional("on_escalated_script", defaults.get("on_escalated_script")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="script")
            ),
        })

    def _build_alert_data(self, user_input):
        """Build alert data from form."""
        trigger_type = user_input["trigger_type"]

        alert_data = {
            "name": user_input["name"],
            "trigger_type": trigger_type,
            "severity": user_input.get("severity", "warning"),
        }

        if trigger_type == "simple":
            # Entity ID is required for simple triggers
            if not user_input.get("entity_id"):
                raise vol.Invalid("Entity ID is required for simple triggers")
            alert_data["entity_id"] = user_input["entity_id"]
            alert_data["trigger_state"] = user_input.get("trigger_state", "on")
        elif trigger_type == "template":
            # Template is required for template triggers
            if not user_input.get("template"):
                raise vol.Invalid("Template is required for template triggers")
            alert_data["template"] = user_input["template"]
            # Entity ID is optional for template triggers
            if user_input.get("entity_id"):
                alert_data["entity_id"] = user_input["entity_id"]

        # Store script entity_id as string (binary sensor will build action)
        if user_input.get("on_triggered_script"):
            alert_data["on_triggered_script"] = user_input["on_triggered_script"]
        if user_input.get("on_escalated_script"):
            alert_data["on_escalated_script"] = user_input["on_escalated_script"]

        # Persist the debounce duration only if non-zero (keeps the stored
        # config tidy and matches how older alerts will load — int(...) treats
        # missing key as 0 in binary_sensor.py).
        for_seconds = user_input.get("for_seconds")
        if for_seconds:
            try:
                for_seconds = int(for_seconds)
            except (TypeError, ValueError):
                for_seconds = 0
            if for_seconds > 0:
                alert_data["for_seconds"] = for_seconds

        return alert_data

    async def async_step_edit_alert(self, user_input=None):
        """Edit existing alert."""
        alerts = self.config_entry.data.get(CONF_ALERTS, {})

        if not alerts:
            return self.async_abort(reason="no_alerts_to_edit")

        # Step 1: Select which alert to edit
        if user_input is not None and "alert_id" in user_input:
            alert_id = user_input["alert_id"]
            alert_data = alerts.get(alert_id)

            if not alert_data:
                return self.async_abort(reason="alert_not_found")

            # Store for next step
            self._editing_alert_id = alert_id
            return await self.async_step_edit_alert_form()

        # Show alert selection
        alert_options = [
            {"value": alert_id, "label": alert_data.get("name", alert_id)}
            for alert_id, alert_data in alerts.items()
        ]

        return self.async_show_form(
            step_id="edit_alert",
            data_schema=vol.Schema({
                vol.Required("alert_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=alert_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_edit_alert_form(self, user_input=None):
        """Render the edit form with current values pre-filled.

        Form submission routes to `async_step_add_alert` because we reuse
        `step_id="add_alert"` for translation/UX consistency. `add_alert`
        detects edit mode via `self._editing_alert_id` set in
        `async_step_edit_alert`.
        """
        alerts = dict(self.config_entry.data.get(CONF_ALERTS, {}))
        current_alert = alerts.get(self._editing_alert_id, {})
        defaults = dict(current_alert)

        # Migrate old script array format to string
        if "on_triggered_script" in defaults and isinstance(defaults["on_triggered_script"], list):
            try:
                defaults["on_triggered_script"] = defaults["on_triggered_script"][0]["data"]["entity_id"]
            except (KeyError, IndexError, TypeError):
                defaults["on_triggered_script"] = ""

        return self.async_show_form(
            step_id="add_alert",
            data_schema=self._build_alert_schema(defaults=defaults),
        )

    async def async_step_remove_alert(self, user_input=None):
        """Remove an alert."""
        alerts = self.config_entry.data.get(CONF_ALERTS, {})

        if not alerts:
            return self.async_abort(reason="no_alerts_to_remove")

        if user_input is not None:
            alert_id = user_input["alert_id"]

            # Remove alert
            new_alerts = dict(alerts)
            del new_alerts[alert_id]

            new_data = dict(self.config_entry.data)
            new_data[CONF_ALERTS] = new_alerts

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )

            # Reload to remove entities
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Show alert selection
        alert_options = [
            {"value": alert_id, "label": alert_data.get("name", alert_id)}
            for alert_id, alert_data in alerts.items()
        ]

        return self.async_show_form(
            step_id="remove_alert",
            data_schema=vol.Schema({
                vol.Required("alert_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=alert_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )
