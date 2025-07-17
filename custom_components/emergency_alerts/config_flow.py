import logging
from typing import Any, Dict, Type, Optional, Union

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigEntry, ConfigSubentryFlow
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback

from .const import DOMAIN

SEVERITY_LEVELS = ["info", "warning", "critical"]
TRIGGER_TYPES = ["simple", "template", "logical"]
GROUPS = ["security", "safety", "power", "lights", "environment", "other"]

_LOGGER = logging.getLogger(__name__)


class EmergencyConfigFlow(ConfigFlow):
    """Handle config flow for Emergency Alerts."""
    
    VERSION = 2
    domain = DOMAIN

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # For backward compatibility, treat this as an alert configuration
            # if it contains alert-specific fields
            if any(key in user_input for key in ["name", "trigger_type", "entity_id"]):
                # This is an individual alert configuration (legacy)
                return self.async_create_entry(
                    title=f"Emergency: {user_input.get('name', 'Alert')}",
                    data=user_input
                )
            else:
                # This is the main integration setup
                existing_entries = self._async_current_entries()
                if existing_entries:
                    return self.async_abort(reason="single_instance_allowed")
                
                return self.async_create_entry(
                    title="Emergency Alerts",
                    data={"configured": True}
                )

        # Show the full alert configuration form for backward compatibility
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Required("trigger_type", default="simple"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TRIGGER_TYPES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Optional("trigger_state"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("template"): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),
                vol.Optional("logical_conditions"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("action_service"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("severity", default="warning"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SEVERITY_LEVELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("group", default="other"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("on_triggered"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("on_cleared"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("on_escalated"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
            }),
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/issmirnov/emergency_alerts"
            },
        )

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Handle reconfiguration of an existing entry."""
        config_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None:
            return self.async_update_reload_and_abort(
                config_entry,
                data_updates=user_input,
                reason="reconfigure_successful"
            )

        current_data = config_entry.data
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required("name", default=current_data.get("name", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Required("trigger_type", default=current_data.get("trigger_type", "simple")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TRIGGER_TYPES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("entity_id", default=current_data.get("entity_id", "")): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Optional("trigger_state", default=current_data.get("trigger_state", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("template", default=current_data.get("template", "")): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),
                vol.Optional("severity", default=current_data.get("severity", "warning")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SEVERITY_LEVELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("group", default=current_data.get("group", "other")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> Dict[str, Type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"alert": EmergencyAlertSubentryFlow}


class EmergencyAlertSubentryFlow(ConfigSubentryFlow):
    """Handle subentry flow for individual emergency alerts."""

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
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
                vol.Required("name"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Required("trigger_type", default="simple"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TRIGGER_TYPES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Optional("trigger_state"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("template"): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),
                vol.Optional("severity", default="warning"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SEVERITY_LEVELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("group", default="other"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_reconfigure(self, user_input: Optional[Dict[str, Any]] = None):
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
                vol.Required("name", default=current_data.get("name", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Required("trigger_type", default=current_data.get("trigger_type", "simple")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TRIGGER_TYPES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("entity_id", default=current_data.get("entity_id", "")): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Optional("trigger_state", default=current_data.get("trigger_state", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("template", default=current_data.get("template", "")): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),
                vol.Optional("severity", default=current_data.get("severity", "warning")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SEVERITY_LEVELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("group", default=current_data.get("group", "other")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )
