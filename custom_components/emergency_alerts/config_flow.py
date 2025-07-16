import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN

SEVERITY_LEVELS = ["info", "warning", "critical"]
TRIGGER_TYPES = ["simple", "template", "logical"]
GROUPS = ["security", "safety", "power", "lights", "environment", "other"]

_LOGGER = logging.getLogger(__name__)


class EmergencyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        _LOGGER.debug(
            "Entered async_step_user with user_input: %s", user_input)
        try:
            if user_input is not None:
                _LOGGER.info("Creating entry with user_input: %s", user_input)
                return self.async_create_entry(
                    title=user_input["name"], data=user_input
                )
            _LOGGER.debug("Showing config form to user.")
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("name"): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.TEXT)
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
                                type=selector.TextSelectorType.TEXT)
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
                                type=selector.TextSelectorType.TEXT)
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
                    }
                ),
            )
        except Exception as e:
            _LOGGER.exception("Exception in async_step_user: %s", e)
            raise
