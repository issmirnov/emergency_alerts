import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

SEVERITY_LEVELS = ["info", "warning", "critical"]
TRIGGER_TYPES = ["simple", "template", "logical"]
GROUPS = ["security", "safety", "power", "lights", "environment", "other"]

_LOGGER = logging.getLogger(__name__)


class EmergencyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the main Emergency Alerts integration setup."""
    VERSION = 2

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step for setting up the main integration."""
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


class EmergencyAlertSubentryConfigFlow(config_entries.ConfigSubentryFlow, domain=DOMAIN):
    """Handle config subentry flow for individual emergency alerts."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle config subentry creation for individual emergency alerts."""
        _LOGGER.debug("Alert subentry flow with user_input: %s", user_input)
        
        if user_input is not None:
            # Create config subentry for the individual alert
            return self.async_create_entry(
                title=f"Emergency: {user_input['name']}",
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
        )
