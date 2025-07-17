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
        """Handle the initial step where user chooses to create a group hub or global settings."""
        _LOGGER.debug(
            "Entered async_step_user with user_input: %s", user_input)

        errors = {}

        if user_input is not None:
            setup_type = user_input["setup_type"]

            if setup_type == "global":
                return await self.async_step_global_setup(user_input)
            elif setup_type == "group":
                return await self.async_step_group_setup()  # Pass None instead of user_input

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("setup_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["global", "group"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            errors=errors,
        )

    async def async_step_global_setup(self, user_input=None):
        """Handle global settings setup."""
        if user_input is not None:
            # Check if global hub already exists
            existing_entries = self.hass.config_entries.async_entries(DOMAIN)
            for entry in existing_entries:
                if entry.data.get("hub_type") == "global":
                    return self.async_abort(reason="global_already_configured")

            return self.async_create_entry(
                title="Emergency Alerts - Global Settings",
                data={
                    "hub_type": "global",
                    "name": "Global Settings"
                }
            )

        return self.async_show_form(
            step_id="global_setup",
            data_schema=vol.Schema({}),
        )

    async def async_step_group_setup(self, user_input=None):
        """Handle group hub setup."""
        if user_input is not None:
            group_name = user_input["group_name"]

            # Create a unique title and hub name
            title = f"Emergency Alerts - {group_name}"
            hub_name = group_name.lower().replace(' ', '_')

            # Check if this group hub already exists
            existing_entries = self.hass.config_entries.async_entries(DOMAIN)
            for entry in existing_entries:
                if (entry.data.get("hub_type") == "group" and
                        entry.data.get("hub_name") == hub_name):
                    return self.async_abort(reason="group_already_configured")

            return self.async_create_entry(
                title=title,
                data={
                    "hub_type": "group",
                    "group": group_name,
                    "hub_name": hub_name,
                    "custom_name": "",
                    "alerts": {}  # Will store individual alerts
                }
            )

        return self.async_show_form(
            step_id="group_setup",
            data_schema=vol.Schema({
                vol.Required("group_name"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
            }),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return EmergencyOptionsFlow()


class EmergencyOptionsFlow(config_entries.OptionsFlow):

    async def async_step_init(self, user_input=None):
        """Manage options based on hub type."""
        hub_type = self.config_entry.data.get("hub_type")

        # Handle legacy entries that don't have hub_type set
        if hub_type is None:
            # Check if this looks like a global settings hub
            if self.config_entry.title == "Emergency Alerts - Global Settings":
                hub_type = "global"
            else:
                # Assume it's a legacy group hub
                hub_type = "group"

        if hub_type == "global":
            return await self.async_step_global_options(user_input)
        elif hub_type == "group":
            return await self.async_step_group_options(user_input)

        return self.async_abort(reason="invalid_hub_type")

    async def async_step_global_options(self, user_input=None):
        """Manage global Emergency Alerts options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options or set defaults
        options = self.config_entry.options
        default_escalation_time = options.get(
            "default_escalation_time", 300)  # 5 minutes
        global_notification_service = options.get(
            "global_notification_service", "")
        enable_global_notifications = options.get(
            "enable_global_notifications", False)

        return self.async_show_form(
            step_id="global_options",
            data_schema=vol.Schema({
                vol.Optional(
                    "default_escalation_time",
                    default=default_escalation_time
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                vol.Optional(
                    "enable_global_notifications",
                    default=enable_global_notifications
                ): bool,
                vol.Optional(
                    "global_notification_service",
                    default=global_notification_service
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional(
                    "global_notification_message",
                    default=options.get(
                        "global_notification_message", "Emergency Alert: {alert_name} - {severity}")
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                        multiline=True
                    )
                ),
            })
        )

    async def async_step_group_options(self, user_input=None):
        """Manage group hub options - add/remove alerts."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add_alert":
                return await self.async_step_add_alert()
            elif action == "remove_alert":
                return await self.async_step_remove_alert()
            elif action == "edit_alert":
                return await self.async_step_edit_alert()

        # Show options for managing alerts in this group
        current_alerts = self.config_entry.data.get("alerts", {})
        alert_count = len(current_alerts)

        # Create action options
        options = ["add_alert"]

        if alert_count > 0:
            options.extend(["edit_alert", "remove_alert"])

        return self.async_show_form(
            step_id="group_options",
            data_schema=vol.Schema({
                vol.Required("action"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            description_placeholders={
                "alert_count": str(alert_count),
                "group_name": self.config_entry.data.get("group", "Unknown")
            }
        )

    async def async_step_add_alert(self, user_input=None):
        """Add a new alert to this group."""
        if user_input is not None:
            # Add the alert to the config entry data
            alerts = dict(self.config_entry.data.get("alerts", {}))
            alert_id = user_input["name"].lower().replace(" ", "_")
            alerts[alert_id] = user_input

            # Update the config entry
            new_data = dict(self.config_entry.data)
            new_data["alerts"] = alerts

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )

            # Reload the config entry to create new entities
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_alert",
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
                vol.Optional("severity", default="warning"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SEVERITY_LEVELS,
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
            })
        )

    async def async_step_edit_alert(self, user_input=None):
        """Select an alert to edit."""
        alerts = self.config_entry.data.get("alerts", {})

        if not alerts:
            return self.async_abort(reason="no_alerts_to_edit")

        if user_input is not None:
            # Extract alert_id from the selected option (format: "alert_id")
            selected_alert_id = user_input["alert_id"]

            # Store the alert_id for the next step
            self._alert_to_edit = selected_alert_id
            return await self.async_step_edit_alert_form()

        # Create better formatted options showing alert info
        alert_options = []
        for alert_id, alert_data in alerts.items():
            name = alert_data.get('name', alert_id)
            trigger_type = alert_data.get('trigger_type', 'simple')
            severity = alert_data.get('severity', 'warning')

            # Format: "Alert Name (Type: simple, Severity: warning)"
            display_text = f"{name} (Type: {trigger_type}, Severity: {severity})"
            alert_options.append({"value": alert_id, "label": display_text})

        return self.async_show_form(
            step_id="edit_alert",
            data_schema=vol.Schema({
                vol.Required("alert_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=alert_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            })
        )

    async def async_step_edit_alert_form(self, user_input=None):
        """Edit the selected alert."""
        alerts = self.config_entry.data.get("alerts", {})
        alert_to_edit = getattr(self, '_alert_to_edit', None)

        if not alert_to_edit or alert_to_edit not in alerts:
            return self.async_abort(reason="alert_not_found")

        current_alert = alerts[alert_to_edit]

        if user_input is not None:
            action = user_input.get("action", "save")

            if action == "delete":
                # Delete the alert
                new_alerts = dict(alerts)
                del new_alerts[alert_to_edit]

                # Update the config entry
                new_data = dict(self.config_entry.data)
                new_data["alerts"] = new_alerts

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )

                # Reload the config entry to remove entities
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                return self.async_create_entry(title="Alert Deleted", data={})

            else:  # action == "save"
                # Update the alert in the config entry data
                new_alerts = dict(alerts)

                # If the name changed, we need to update the alert_id
                new_name = user_input["name"]
                new_alert_id = new_name.lower().replace(" ", "_")

                # Remove the action field from user_input before saving
                alert_data = dict(user_input)
                del alert_data["action"]

                if new_alert_id != alert_to_edit:
                    # Remove old alert and add with new id
                    del new_alerts[alert_to_edit]
                    new_alerts[new_alert_id] = alert_data
                else:
                    # Update existing alert
                    new_alerts[alert_to_edit] = alert_data

                # Update the config entry
                new_data = dict(self.config_entry.data)
                new_data["alerts"] = new_alerts

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )

                # Reload the config entry to update entities
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                return self.async_create_entry(title="Alert Updated", data={})

        return self.async_show_form(
            step_id="edit_alert_form",
            data_schema=vol.Schema({
                vol.Required("action", default="save"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "save", "label": "💾 Save Changes"},
                            {"value": "delete", "label": "🗑️ Delete This Alert"}
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("name", default=current_alert.get("name", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Required("trigger_type", default=current_alert.get("trigger_type", "simple")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TRIGGER_TYPES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("entity_id", default=current_alert.get("entity_id", "")): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Optional("trigger_state", default=current_alert.get("trigger_state", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("template", default=current_alert.get("template", "")): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),
                vol.Optional("logical_conditions", default=current_alert.get("logical_conditions", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("severity", default=current_alert.get("severity", "warning")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SEVERITY_LEVELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("on_triggered", default=current_alert.get("on_triggered", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("on_cleared", default=current_alert.get("on_cleared", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Optional("on_escalated", default=current_alert.get("on_escalated", "")): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
            })
        )

    async def async_step_remove_alert(self, user_input=None):
        """Remove an alert from this group."""
        alerts = self.config_entry.data.get("alerts", {})

        if not alerts:
            return self.async_abort(reason="no_alerts_to_remove")

        if user_input is not None:
            # Extract alert_id from the selected option (format: "alert_id: name (type)")
            selected_option = user_input["alert_id"]
            alert_to_remove = selected_option.split(":")[0].strip()
            new_alerts = {k: v for k, v in alerts.items() if k !=
                          alert_to_remove}

            # Update the config entry
            new_data = dict(self.config_entry.data)
            new_data["alerts"] = new_alerts

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )

            # Reload the config entry to remove old entities
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        alert_options = [
            f"{alert_id}: {alert_data['name']} ({alert_data.get('trigger_type', 'simple')})"
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
            })
        )
