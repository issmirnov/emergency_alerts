import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DOMAIN

SEVERITY_LEVELS = [
    selector.SelectOptionDict(
        value="info", label="ℹ️ info: General notifications"),
    selector.SelectOptionDict(
        value="warning", label="⚠️ warning: Important but not critical"),
    selector.SelectOptionDict(
        value="critical", label="🚨 critical: Urgent issues requiring immediate attention")
]
TRIGGER_TYPES = [
    selector.SelectOptionDict(
        value="simple", label="simple: Monitor one entity's state"),
    selector.SelectOptionDict(
        value="template", label="template: Use Jinja2 for complex conditions"),
    selector.SelectOptionDict(
        value="logical", label="logical: Combine multiple entity conditions")
]
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

        # Check if global hub already exists
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        global_hub_exists = any(entry.data.get(
            "hub_type") == "global" for entry in existing_entries)

        # Build options list - exclude global if already configured
        options = []
        if not global_hub_exists:
            options.append({
                "label": "Global Settings Hub - Manage notification settings and escalation (Add Once)",
                "value": "global"
            })

        options.append({
            "label": "Alert Group Hub - Create a group of related emergency alerts",
            "value": "group"
        })

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("setup_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
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

        if hub_type == "global":
            return await self.async_step_global_options(user_input)
        elif hub_type == "group":
            return await self.async_step_group_options(user_input)

        return self.async_abort(reason="invalid_hub_type")

    async def async_step_global_options(self, user_input=None):
        """Show menu for global options."""
        options = self.config_entry.options
        profile_count = len(options.get("notification_profiles", {}))

        return self.async_show_menu(
            step_id="global_options",
            menu_options=["escalation_settings", "notification_profiles", "legacy_notifications"],
            description_placeholders={
                "profile_count": str(profile_count)
            }
        )

    async def async_step_escalation_settings(self, user_input=None):
        """Configure escalation settings."""
        if user_input is not None:
            # Merge with existing options
            updated_options = dict(self.config_entry.options)
            updated_options.update(user_input)
            return self.async_create_entry(title="", data=updated_options)

        options = self.config_entry.options
        default_escalation_time = options.get("default_escalation_time", 300)

        return self.async_show_form(
            step_id="escalation_settings",
            data_schema=vol.Schema({
                vol.Optional(
                    "default_escalation_time",
                    default=default_escalation_time
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            })
        )

    async def async_step_legacy_notifications(self, user_input=None):
        """Configure legacy global notifications."""
        if user_input is not None:
            updated_options = dict(self.config_entry.options)
            updated_options.update(user_input)
            return self.async_create_entry(title="", data=updated_options)

        options = self.config_entry.options
        global_notification_service = options.get("global_notification_service", "")
        enable_global_notifications = options.get("enable_global_notifications", False)

        return self.async_show_form(
            step_id="legacy_notifications",
            data_schema=vol.Schema({
                vol.Optional(
                    "enable_global_notifications",
                    default=enable_global_notifications
                ): bool,
                vol.Optional(
                    "global_notification_service",
                    default=global_notification_service
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=self._get_available_scripts(),
                        mode=selector.SelectSelectorMode.DROPDOWN,
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

    async def async_step_notification_profiles(self, user_input=None):
        """Manage notification profiles."""
        profiles = self.config_entry.options.get("notification_profiles", {})
        profile_count = len(profiles)

        return self.async_show_menu(
            step_id="notification_profiles",
            menu_options=["add_profile"] +
            (["edit_profile", "remove_profile"] if profile_count > 0 else []),
            description_placeholders={
                "profile_count": str(profile_count)
            }
        )

    async def async_step_add_profile(self, user_input=None):
        """Add a new notification profile."""
        if user_input is not None:
            # Store profile in options
            updated_options = dict(self.config_entry.options)
            if "notification_profiles" not in updated_options:
                updated_options["notification_profiles"] = {}

            profile_name = user_input["profile_name"]
            profile_id = profile_name.lower().replace(" ", "_")

            # Build profile from form data
            profile_data = {
                "name": profile_name,
                "description": user_input.get("description", ""),
                "actions": []
            }

            # Collect up to 5 service calls
            for i in range(1, 6):
                service = user_input.get(f"service_{i}")
                if service:
                    action = {"service": service}
                    data_yaml = user_input.get(f"service_data_{i}", "")
                    if data_yaml:
                        try:
                            import yaml
                            action["data"] = yaml.safe_load(data_yaml)
                        except:
                            pass
                    profile_data["actions"].append(action)

            updated_options["notification_profiles"][profile_id] = profile_data
            return self.async_create_entry(title="", data=updated_options)

        return self.async_show_form(
            step_id="add_profile",
            data_schema=vol.Schema({
                vol.Required("profile_name"): selector.TextSelector(),
                vol.Optional("description"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_1"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
                vol.Optional("service_data_1"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                        multiline=True
                    )
                ),
                vol.Optional("service_2"): selector.TextSelector(),
                vol.Optional("service_data_2"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_3"): selector.TextSelector(),
                vol.Optional("service_data_3"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_4"): selector.TextSelector(),
                vol.Optional("service_data_4"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_5"): selector.TextSelector(),
                vol.Optional("service_data_5"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
            })
        )

    async def async_step_edit_profile(self, user_input=None):
        """Edit an existing profile."""
        profiles = self.config_entry.options.get("notification_profiles", {})

        if user_input is not None:
            profile_id = user_input.get("profile_id")
            if profile_id:
                self._editing_profile_id = profile_id
                return await self.async_step_edit_profile_form()
            return await self.async_step_notification_profiles()

        # Build profile selector
        profile_options = [
            {"label": f"{p['name']} - {p.get('description', 'No description')}",
             "value": pid}
            for pid, p in profiles.items()
        ]

        return self.async_show_form(
            step_id="edit_profile",
            data_schema=vol.Schema({
                vol.Required("profile_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=profile_options,
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            })
        )

    async def async_step_edit_profile_form(self, user_input=None):
        """Form for editing a profile."""
        profiles = self.config_entry.options.get("notification_profiles", {})
        profile = profiles.get(self._editing_profile_id, {})

        if user_input is not None:
            # Update profile
            updated_options = dict(self.config_entry.options)
            profile_name = user_input["profile_name"]
            profile_data = {
                "name": profile_name,
                "description": user_input.get("description", ""),
                "actions": []
            }

            for i in range(1, 6):
                service = user_input.get(f"service_{i}")
                if service:
                    action = {"service": service}
                    data_yaml = user_input.get(f"service_data_{i}", "")
                    if data_yaml:
                        try:
                            import yaml
                            action["data"] = yaml.safe_load(data_yaml)
                        except:
                            pass
                    profile_data["actions"].append(action)

            updated_options["notification_profiles"][self._editing_profile_id] = profile_data
            del self._editing_profile_id
            return self.async_create_entry(title="", data=updated_options)

        # Pre-fill form with current data
        defaults = {"profile_name": profile.get("name", ""),
                    "description": profile.get("description", "")}

        for i, action in enumerate(profile.get("actions", [])[:5], start=1):
            defaults[f"service_{i}"] = action.get("service", "")
            if "data" in action:
                import yaml
                defaults[f"service_data_{i}"] = yaml.dump(action["data"])

        return self.async_show_form(
            step_id="edit_profile_form",
            data_schema=vol.Schema({
                vol.Required("profile_name", default=defaults.get("profile_name")): selector.TextSelector(),
                vol.Optional("description", default=defaults.get("description", "")): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_1", default=defaults.get("service_1", "")): selector.TextSelector(),
                vol.Optional("service_data_1", default=defaults.get("service_data_1", "")): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_2", default=defaults.get("service_2", "")): selector.TextSelector(),
                vol.Optional("service_data_2", default=defaults.get("service_data_2", "")): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_3", default=defaults.get("service_3", "")): selector.TextSelector(),
                vol.Optional("service_data_3", default=defaults.get("service_data_3", "")): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_4", default=defaults.get("service_4", "")): selector.TextSelector(),
                vol.Optional("service_data_4", default=defaults.get("service_data_4", "")): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional("service_5", default=defaults.get("service_5", "")): selector.TextSelector(),
                vol.Optional("service_data_5", default=defaults.get("service_data_5", "")): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
            })
        )

    async def async_step_remove_profile(self, user_input=None):
        """Remove a notification profile."""
        profiles = self.config_entry.options.get("notification_profiles", {})

        if user_input is not None:
            profile_id = user_input.get("profile_id")
            if profile_id:
                updated_options = dict(self.config_entry.options)
                del updated_options["notification_profiles"][profile_id]
                return self.async_create_entry(title="", data=updated_options)
            return await self.async_step_notification_profiles()

        profile_options = [
            {"label": p["name"], "value": pid}
            for pid, p in profiles.items()
        ]

        return self.async_show_form(
            step_id="remove_profile",
            data_schema=vol.Schema({
                vol.Required("profile_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=profile_options,
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            })
        )

    async def async_step_group_options(self, user_input=None):
        """Show menu-style options for managing alerts in this group."""
        # Show menu-style options for managing alerts in this group
        current_alerts = self.config_entry.data.get("alerts", {})
        alert_count = len(current_alerts)

        return self.async_show_menu(
            step_id="group_options",
            menu_options=["add_alert"] +
            (["edit_alert", "remove_alert"] if alert_count > 0 else []),
            description_placeholders={
                "alert_count": str(alert_count),
                "group_name": self.config_entry.data.get("group", "Unknown")
            }
        )

    async def async_step_add_alert(self, user_input=None):
        """Add a new alert to this group - Step 1: Basic Information."""
        # Check if we're in edit mode
        is_editing = hasattr(self, '_editing_alert_id')

        if user_input is not None:
            # Store basic alert data for next steps
            self._alert_data = {
                "name": user_input["name"],
                "trigger_type": user_input["trigger_type"],
                "severity": user_input.get("severity", "warning")
            }

            # Branch to appropriate trigger configuration step
            trigger_type = user_input["trigger_type"]
            if trigger_type == "simple":
                return await self.async_step_add_alert_trigger_simple()
            elif trigger_type == "template":
                return await self.async_step_add_alert_trigger_template()
            elif trigger_type == "logical":
                return await self.async_step_add_alert_trigger_logical()

        # Get current alert data if editing
        current_alert = None
        if is_editing:
            alerts = self.config_entry.data.get("alerts", {})
            current_alert = alerts.get(self._editing_alert_id, {})

        return self.async_show_form(
            step_id="add_alert",
            data_schema=vol.Schema({
                vol.Required("name", default=current_alert.get("name", "") if current_alert else ""): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Required("trigger_type", default=current_alert.get("trigger_type", "simple") if current_alert else "simple"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TRIGGER_TYPES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("severity", default=current_alert.get("severity", "warning") if current_alert else "warning"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SEVERITY_LEVELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            })
        )

    async def async_step_add_alert_trigger_simple(self, user_input=None):
        """Add a new alert to this group - Step 2: Simple Trigger Configuration."""
        is_editing = hasattr(self, '_editing_alert_id')
        current_alert = None
        if is_editing:
            alerts = self.config_entry.data.get("alerts", {})
            current_alert = alerts.get(self._editing_alert_id, {})

        if user_input is not None:
            # Store simple trigger data
            self._alert_data["entity_id"] = user_input.get("entity_id")
            self._alert_data["trigger_state"] = user_input.get("trigger_state")

            # Continue to action configuration
            return await self.async_step_add_alert_actions()

        return self.async_show_form(
            step_id="add_alert_trigger_simple",
            data_schema=vol.Schema({
                vol.Required("entity_id", default=current_alert.get("entity_id", "") if current_alert else ""): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Required("trigger_state", default=current_alert.get("trigger_state", "") if current_alert else ""): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
            })
        )

    async def async_step_add_alert_trigger_template(self, user_input=None):
        """Add a new alert to this group - Step 2: Template Trigger Configuration."""
        is_editing = hasattr(self, '_editing_alert_id')
        current_alert = None
        if is_editing:
            alerts = self.config_entry.data.get("alerts", {})
            current_alert = alerts.get(self._editing_alert_id, {})

        if user_input is not None:
            # Store template trigger data
            self._alert_data["entity_id"] = user_input.get("entity_id")
            self._alert_data["template"] = user_input.get("template")

            # Continue to action configuration
            return await self.async_step_add_alert_actions()

        return self.async_show_form(
            step_id="add_alert_trigger_template",
            data_schema=vol.Schema({
                vol.Required("entity_id", default=current_alert.get("entity_id", "") if current_alert else ""): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Required("template", default=current_alert.get("template", "") if current_alert else ""): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),
            })
        )

    async def async_step_add_alert_trigger_logical(self, user_input=None):
        """Multi-step wizard for logical trigger configuration."""
        # Initialize wizard state if not present
        if not hasattr(self, '_logical_conditions_wizard'):
            self._logical_conditions_wizard = []
            self._logical_wizard_step = 0

        # Step 1: Add a condition
        if user_input is not None:
            # Save previous step's condition if present
            if 'entity_id' in user_input and user_input['entity_id']:
                self._logical_conditions_wizard.append({
                    'entity_id': user_input['entity_id'],
                    'state': user_input.get('state', '')
                })
            # If user chose not to add another, go to operator selection
            if user_input.get('add_another') == 'no':
                return await self.async_step_add_alert_trigger_logical_operator()

        # Show form to add a new condition
        # Try to show current state as hint if entity is selected
        current_state_hint = ''
        if user_input and user_input.get('entity_id'):
            entity_id = user_input['entity_id']
            state_obj = self.hass.states.get(entity_id)
            if state_obj:
                current_state_hint = f"Current state: {state_obj.state}"
        
        return self.async_show_form(
            step_id="add_alert_trigger_logical",
            data_schema=vol.Schema({
                vol.Required('entity_id'): selector.EntitySelector(selector.EntitySelectorConfig()),
                vol.Optional('state', default=''): str,
                vol.Required('add_another', default='no'): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value='yes', label='Add another condition'),
                            selector.SelectOptionDict(value='no', label='Done adding conditions'),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            description_placeholders={
                'current_state_hint': current_state_hint
            },
        )

    async def async_step_add_alert_trigger_logical_operator(self, user_input=None):
        """Step to select AND/OR operator and finish logical trigger config."""
        if user_input is not None:
            self._alert_data['logical_conditions'] = self._logical_conditions_wizard
            self._alert_data['logical_operator'] = user_input['logical_operator']
            # Clean up wizard state
            del self._logical_conditions_wizard
            return await self.async_step_add_alert_actions()

        return self.async_show_form(
            step_id="add_alert_trigger_logical_operator",
            data_schema=vol.Schema({
                vol.Required('logical_operator', default='and'): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value='and', label='AND - All conditions must be true'),
                            selector.SelectOptionDict(value='or', label='OR - Any condition can be true'),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            })
        )

    async def async_step_add_alert_trigger_config(self, user_input=None):
        """Add a new alert to this group - Step 2: Trigger-Specific Configuration."""
        is_editing = hasattr(self, '_editing_alert_id')
        current_alert = None
        if is_editing:
            alerts = self.config_entry.data.get("alerts", {})
            current_alert = alerts.get(self._editing_alert_id, {})

        if user_input is not None:
            # Store trigger-specific data based on type
            trigger_type = self._alert_data.get("trigger_type")

            if trigger_type == "simple":
                self._alert_data["entity_id"] = user_input.get("entity_id")
                self._alert_data["trigger_state"] = user_input.get(
                    "trigger_state")
            elif trigger_type == "template":
                self._alert_data["template"] = user_input.get("template")
            elif trigger_type == "logical":
                # Parse the logical conditions from the visual builder
                conditions = []
                operator = user_input.get("logical_operator", "and")
                
                # Extract conditions from the form
                for i in range(10):  # Support up to 10 conditions
                    entity_id = user_input.get(f"condition_{i}_entity")
                    state = user_input.get(f"condition_{i}_state")
                    if entity_id and state:
                        conditions.append({
                            "entity_id": entity_id,
                            "state": state
                        })
                
                self._alert_data["logical_conditions"] = conditions
                self._alert_data["logical_operator"] = operator

            # Continue to action configuration
            return await self.async_step_add_alert_actions()

        # Build schema based on trigger type
        trigger_type = self._alert_data.get("trigger_type")

        if trigger_type == "simple":
            schema = vol.Schema({
                vol.Required("entity_id", default=current_alert.get("entity_id", "") if current_alert else ""): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Required("trigger_state", default=current_alert.get("trigger_state", "") if current_alert else ""): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
            })
        elif trigger_type == "template":
            schema = vol.Schema({
                vol.Required("template", default=current_alert.get("template", "") if current_alert else ""): selector.TemplateSelector(
                    selector.TemplateSelectorConfig()
                ),
            })
        elif trigger_type == "logical":
            # Parse existing conditions for editing
            existing_conditions = []
            existing_operator = "and"
            if is_editing and current_alert:
                logical_data = current_alert.get("logical_conditions", [])
                if isinstance(logical_data, list):
                    existing_conditions = logical_data
                existing_operator = current_alert.get("logical_operator", "and")

            # Build schema for visual condition builder
            schema_fields = {
                vol.Required("logical_operator", default=existing_operator): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value="and", label="AND - All conditions must be true"),
                            selector.SelectOptionDict(value="or", label="OR - Any condition can be true")
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }

            # Add condition fields (up to 10 conditions)
            for i in range(10):
                condition = existing_conditions[i] if i < len(existing_conditions) else {}
                schema_fields[vol.Optional(f"condition_{i}_entity", default=condition.get("entity_id", ""))] = selector.EntitySelector(
                    selector.EntitySelectorConfig()
                )
                schema_fields[vol.Optional(f"condition_{i}_state", default=condition.get("state", ""))] = selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                )
            
            schema = vol.Schema(schema_fields)
        else:
            return self.async_abort(reason="invalid_trigger_type")

        # Build title and description based on trigger type
        if trigger_type == "simple":
            title = "➕ Add New Alert - Step 2: Simple Trigger Configuration"
            description = "Configure which entity to monitor and what state should trigger the alert."
        elif trigger_type == "template":
            title = "➕ Add New Alert - Step 2: Template Trigger Configuration"
            description = "Create a Jinja2 template that returns True when the alert should trigger."
        elif trigger_type == "logical":
            title = "➕ Add New Alert - Step 2: Logical Trigger Configuration"
            description = "Combine multiple entity conditions using AND/OR logic."
        else:
            title = "➕ Add New Alert - Step 2: Trigger Configuration"
            description = "Configure the specific trigger conditions for your alert."

        return self.async_show_form(
            step_id="add_alert_trigger_config",
            data_schema=schema,
            description_placeholders={
                "trigger_type": trigger_type.title()
            }
        )

    def _get_notification_profiles(self):
        """Get available notification profiles from global settings."""
        # Find global settings entry
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("hub_type") == "global":
                profiles = entry.options.get("notification_profiles", {})
                return profiles
        return {}

    async def async_step_add_alert_actions(self, user_input=None):
        """Add a new alert to this group - Step 3: Action Configuration."""
        is_editing = hasattr(self, '_editing_alert_id')
        current_alert = None
        if is_editing:
            alerts = self.config_entry.data.get("alerts", {})
            current_alert = alerts.get(self._editing_alert_id, {})

        if user_input is not None:
            # Parse script selections and profile references
            actions = {}

            # Process triggered actions
            triggered_value = user_input.get("on_triggered_script")
            if triggered_value:
                if triggered_value.startswith("profile:"):
                    actions["on_triggered"] = triggered_value  # Store profile reference
                else:
                    actions["on_triggered"] = [{
                        "service": triggered_value
                    }]

            # Process cleared actions
            cleared_value = user_input.get("on_cleared_script")
            if cleared_value:
                if cleared_value.startswith("profile:"):
                    actions["on_cleared"] = cleared_value
                else:
                    actions["on_cleared"] = [{
                        "service": cleared_value
                    }]

            # Process escalated actions
            escalated_value = user_input.get("on_escalated_script")
            if escalated_value:
                if escalated_value.startswith("profile:"):
                    actions["on_escalated"] = escalated_value
                else:
                    actions["on_escalated"] = [{
                        "service": escalated_value
                    }]

            # Process acknowledged actions (NEW)
            ack_value = user_input.get("on_acknowledged_script")
            if ack_value:
                if ack_value.startswith("profile:"):
                    actions["on_acknowledged"] = ack_value
                else:
                    actions["on_acknowledged"] = [{
                        "service": ack_value
                    }]

            # Process snoozed actions (NEW)
            snooze_value = user_input.get("on_snoozed_script")
            if snooze_value:
                if snooze_value.startswith("profile:"):
                    actions["on_snoozed"] = snooze_value
                else:
                    actions["on_snoozed"] = [{
                        "service": snooze_value
                    }]

            # Process resolved actions (NEW)
            resolve_value = user_input.get("on_resolved_script")
            if resolve_value:
                if resolve_value.startswith("profile:"):
                    actions["on_resolved"] = resolve_value
                else:
                    actions["on_resolved"] = [{
                        "service": resolve_value
                    }]

            # Update alert data with actions
            self._alert_data.update(actions)

            # Add or update the alert in the config entry data
            alerts = dict(self.config_entry.data.get("alerts", {}))
            alert_id = self._alert_data["name"].lower().replace(" ", "_")

            if is_editing:
                # If editing and name changed, remove old alert
                if alert_id != self._editing_alert_id:
                    del alerts[self._editing_alert_id]
                # Clean up edit mode
                delattr(self, '_editing_alert_id')
                success_message = "Alert Updated"
            else:
                success_message = "Alert Created"

            alerts[alert_id] = self._alert_data

            # Update the config entry
            new_data = dict(self.config_entry.data)
            new_data["alerts"] = alerts

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )

            # Reload the config entry to create/update entities
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title=success_message, data={})

        # Get available scripts and profiles for dropdowns
        script_options = self._get_available_scripts()
        profiles = self._get_notification_profiles()

        # Build combined options list (profiles first, then scripts)
        action_options = []
        for profile_id, profile_data in profiles.items():
            action_options.append({
                "label": f"📋 Profile: {profile_data['name']}",
                "value": f"profile:{profile_id}"
            })
        action_options.extend(script_options)

        # Extract current script/profile selections from alert data if editing
        current_triggered_script = ""
        current_cleared_script = ""
        current_escalated_script = ""
        current_acknowledged_script = ""
        current_snoozed_script = ""
        current_resolved_script = ""

        if current_alert:
            current_triggered_script = self._extract_value_from_actions(
                current_alert.get("on_triggered", []))
            current_cleared_script = self._extract_value_from_actions(
                current_alert.get("on_cleared", []))
            current_escalated_script = self._extract_value_from_actions(
                current_alert.get("on_escalated", []))
            current_acknowledged_script = self._extract_value_from_actions(
                current_alert.get("on_acknowledged", []))
            current_snoozed_script = self._extract_value_from_actions(
                current_alert.get("on_snoozed", []))
            current_resolved_script = self._extract_value_from_actions(
                current_alert.get("on_resolved", []))

        return self.async_show_form(
            step_id="add_alert_actions",
            data_schema=vol.Schema({
                # Triggered actions
                vol.Optional("on_triggered_script", default=current_triggered_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=action_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),

                # Acknowledged actions (NEW)
                vol.Optional("on_acknowledged_script", default=current_acknowledged_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=action_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),

                # Snoozed actions (NEW)
                vol.Optional("on_snoozed_script", default=current_snoozed_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=action_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),

                # Cleared actions
                vol.Optional("on_cleared_script", default=current_cleared_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=action_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),

                # Escalated actions
                vol.Optional("on_escalated_script", default=current_escalated_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=action_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),

                # Resolved actions (NEW)
                vol.Optional("on_resolved_script", default=current_resolved_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=action_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
            }),
        )

    async def async_step_edit_alert(self, user_input=None):
        """Select an alert to edit."""
        alerts = self.config_entry.data.get("alerts", {})

        if not alerts:
            return self.async_abort(reason="no_alerts_to_edit")

        if user_input is not None:
            # Extract alert_id from the selected option
            selected_alert_id = user_input["alert_id"]

            # Store the alert_id to indicate edit mode and start the unified flow
            self._editing_alert_id = selected_alert_id
            return await self.async_step_add_alert()

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

            # Explicitly remove the device from device registry
            hub_name = self.config_entry.data.get("hub_name", "unknown")
            device_id = f"{hub_name}_{alert_to_remove}"

            # Get the device registry
            device_registry = async_get_device_registry(self.hass)

            # Find and remove the device
            device = device_registry.async_get_device(
                identifiers={(DOMAIN, device_id)})
            if device:
                device_registry.async_remove_device(device.id)
                _LOGGER.debug(
                    f"Removed device {device_id} from device registry")

            # Reload the config entry to remove old entities
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="Alert Deleted", data={})

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

    def _get_available_scripts(self):
        """Get available Home Assistant scripts for dropdown selection."""
        scripts = []

        # Get all available scripts from Home Assistant
        for entity_id in self.hass.states.async_entity_ids("script"):
            # Skip system scripts
            if entity_id in ["script.turn_on", "script.turn_off", "script.reload", "script.toggle"]:
                continue

            # Get the script name from the state
            state = self.hass.states.get(entity_id)
            if state:
                script_name = state.attributes.get("friendly_name", entity_id)
                # Extract just the script name (without 'script.' prefix)
                script_name_only = entity_id.split('.')[1]
                scripts.append({
                    # Service format: script.script_name
                    "value": f"script.{script_name_only}",
                    "label": f"📜 {script_name} ({entity_id})"
                })

        # Sort by name for better organization
        return sorted(scripts, key=lambda x: x["label"])

    def _extract_value_from_actions(self, actions):
        """Helper method to extract profile reference or script service from actions.

        Returns:
            - "profile:profile_id" if actions is a profile reference string
            - "script.name" if actions is a list containing a script service call
            - "" if no valid value found
        """
        # Check if it's a profile reference (string starting with "profile:")
        if isinstance(actions, str) and actions.startswith("profile:"):
            return actions

        # Check if it's a list of action dicts
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict):
                    service = action.get("service", "")
                    if service:
                        return service

        return ""
