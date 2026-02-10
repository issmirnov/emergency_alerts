"""Config flow for Emergency Alerts - Simplified single-page approach."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

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
        """Add alert - SINGLE PAGE with ALL fields."""
        errors = {}

        if user_input is not None:
            try:
                alert_id = user_input["name"].lower().replace(" ", "_")
                alerts = dict(self.config_entry.data.get(CONF_ALERTS, {}))

                if alert_id in alerts:
                    errors["name"] = "already_configured"
                else:
                    alerts[alert_id] = self._build_alert_data(user_input)
                    new_data = dict(self.config_entry.data)
                    new_data[CONF_ALERTS] = alerts

                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=new_data
                    )

                    # Reload entry to create new entities instantly
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                    return self.async_create_entry(title="", data={})

            except Exception as err:
                _LOGGER.error("Error creating alert: %s", err)
                errors["base"] = "invalid_input"

        return self.async_show_form(
            step_id="add_alert",
            data_schema=self._build_alert_schema(),
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
            vol.Optional("entity_id", default=defaults.get("entity_id", "")): selector.EntitySelector(),
            vol.Optional(
                "trigger_state", default=defaults.get("trigger_state", "on")
            ): str,
            vol.Optional("template", default=defaults.get("template", "")): selector.TemplateSelector(),
            vol.Optional("on_triggered_script", default=defaults.get("on_triggered_script", "")): selector.EntitySelector(
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

        # Add optional action scripts
        if user_input.get("on_triggered_script"):
            alert_data["on_triggered_script"] = [{
                "service": "script.turn_on",
                "data": {"entity_id": user_input["on_triggered_script"]}
            }]

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
        """Show edit form with current values."""
        alerts = dict(self.config_entry.data.get(CONF_ALERTS, {}))
        alert_id = self._editing_alert_id
        current_alert = alerts.get(alert_id, {})

        # Extract script entity_id from action array for form defaults
        defaults = dict(current_alert)
        if "on_triggered_script" in defaults and isinstance(defaults["on_triggered_script"], list):
            # Extract entity_id from action: [{'service': 'script.turn_on', 'data': {'entity_id': 'script.X'}}]
            try:
                extracted_script = defaults["on_triggered_script"][0]["data"]["entity_id"]
                defaults["on_triggered_script"] = extracted_script
                _LOGGER.info(f"Extracted script for editing: {extracted_script}")
            except (KeyError, IndexError) as e:
                _LOGGER.warning(f"Could not extract script entity_id: {e}")
                defaults["on_triggered_script"] = ""
        else:
            defaults["on_triggered_script"] = ""

        if user_input is not None:
            try:
                # Update alert data
                alerts[alert_id] = self._build_alert_data(user_input)
                new_data = dict(self.config_entry.data)
                new_data[CONF_ALERTS] = alerts

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )

                # Reload to update entities
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                return self.async_create_entry(title="", data={})

            except Exception as err:
                _LOGGER.error("Error updating alert: %s", err)
                return self.async_abort(reason="update_failed")

        # Show form pre-filled with current values
        return self.async_show_form(
            step_id="edit_alert_form",
            data_schema=self._build_alert_schema(defaults=current_alert),
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
