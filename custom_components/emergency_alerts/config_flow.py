import voluptuous as vol
from homeassistant import config_entries
import logging

from .const import DOMAIN

SEVERITY_LEVELS = ["info", "warning", "critical"]
TRIGGER_TYPES = ["simple", "template", "logical"]
GROUPS = ["security", "safety", "power", "lights", "environment", "other"]

_LOGGER = logging.getLogger(__name__)


class EmergencyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("Entered async_step_user with user_input: %s", user_input)
        try:
            if user_input is not None:
                _LOGGER.info("Creating entry with user_input: %s", user_input)
                return self.async_create_entry(title=user_input["name"], data=user_input)
            _LOGGER.debug("Showing config form to user.")
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("name"): str,
                        vol.Required("trigger_type", default="simple"): vol.In(
                            TRIGGER_TYPES
                        ),
                        vol.Optional("entity_id"): str,
                        vol.Optional("trigger_state"): str,
                        vol.Optional("template"): str,
                        vol.Optional("logical_conditions"): list,
                        vol.Optional("action_service"): str,
                        vol.Optional("severity", default="warning"): vol.In(
                            SEVERITY_LEVELS
                        ),
                        vol.Optional("group", default="other"): vol.In(GROUPS),
                        vol.Optional("on_triggered"): list,
                        vol.Optional("on_cleared"): list,
                        vol.Optional("on_escalated"): list,
                    }
                ),
            )
        except Exception as e:
            _LOGGER.exception("Exception in async_step_user: %s", e)
            raise
