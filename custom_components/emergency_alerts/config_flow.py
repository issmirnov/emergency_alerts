"""Config flow for Emergency Alerts integration."""

import logging
from typing import Any, Dict, Type

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from homeassistant.config_entries import ConfigSubentryFlow

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SEVERITY_LEVELS = ["info", "warning", "critical"]
TRIGGER_TYPES = ["simple", "template", "logical"]
GROUPS = ["security", "safety", "power", "lights", "environment", "other"]


class ConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Emergency Alerts."""

    VERSION = 2
    domain = DOMAIN

    async def async_step_user(self, user_input=None):
        """Handle the initial step for setting up the main hub."""
        if user_input is not None:
            # Check if integration already exists (should be single instance)
            existing_entries = self._async_current_entries()
            if existing_entries:
                return self.async_abort(reason="single_instance_allowed")
            
            return self.async_create_entry(
                title="Emergency Alerts",
                data={"configured": True}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "docs_url": "https://github.com/issmirnov/emergency_alerts"
            },
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry):
        """Return subentries supported by this integration."""
        return {"alert": EmergencyAlertSubentryFlow}


class EmergencyAlertSubentryFlow(ConfigSubentryFlow):
        """Handle subentry flow for individual emergency alerts."""

        async def async_step_user(self, user_input=None):
            """User flow to add a new alert."""
            if user_input is not None:
                # Set unique ID if possible for the subentry
                if "name" in user_input:
                    await self.async_set_unique_id(user_input["name"].lower().replace(" ", "_"))
                    self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"Alert: {user_input.get('name', 'Emergency')}",
                    data=user_input
                )

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("name"): str,
                    vol.Required("trigger_type", default="simple"): vol.In(TRIGGER_TYPES),
                    vol.Optional("entity_id"): str,
                    vol.Optional("trigger_state"): str,
                    vol.Optional("template"): str,
                    vol.Optional("severity", default="warning"): vol.In(SEVERITY_LEVELS),
                    vol.Optional("group", default="other"): vol.In(GROUPS),
                }),
            )

        async def async_step_reconfigure(self, user_input=None):
            """User flow to modify an existing alert."""
            if user_input is not None:
                # Ensure unique ID hasn't changed for the subentry
                if "name" in user_input:
                    await self.async_set_unique_id(user_input["name"].lower().replace(" ", "_"))
                    self._abort_if_unique_id_mismatch()
                
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_subentry(),
                    data_updates=user_input,
                )

            # Retrieve the specific subentry for reconfiguration
            subentry = self._get_reconfigure_subentry()
            current_data = subentry.data

            return self.async_show_form(
                step_id="reconfigure",
                data_schema=vol.Schema({
                    vol.Required("name", default=current_data.get("name", "")): str,
                    vol.Required("trigger_type", default=current_data.get("trigger_type", "simple")): vol.In(TRIGGER_TYPES),
                    vol.Optional("entity_id", default=current_data.get("entity_id", "")): str,
                    vol.Optional("trigger_state", default=current_data.get("trigger_state", "")): str,
                    vol.Optional("template", default=current_data.get("template", "")): str,
                    vol.Optional("severity", default=current_data.get("severity", "warning")): vol.In(SEVERITY_LEVELS),
                    vol.Optional("group", default=current_data.get("group", "other")): vol.In(GROUPS),
                }),
            )

