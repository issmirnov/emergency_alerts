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

    async def async_step_add_alert_actions(self, user_input=None):
        """Add a new alert to this group - Step 3: Action Configuration."""
        is_editing = hasattr(self, '_editing_alert_id')
        current_alert = None
        if is_editing:
            alerts = self.config_entry.data.get("alerts", {})
            current_alert = alerts.get(self._editing_alert_id, {})

        if user_input is not None:
            # Parse script selections
            actions = {}

            # Process triggered actions
            if user_input.get("on_triggered_script"):
                actions["on_triggered"] = [{
                    "service": user_input["on_triggered_script"]
                }]

            # Process cleared actions
            if user_input.get("on_cleared_script"):
                actions["on_cleared"] = [{
                    "service": user_input["on_cleared_script"]
                }]

            # Process escalated actions
            if user_input.get("on_escalated_script"):
                actions["on_escalated"] = [{
                    "service": user_input["on_escalated_script"]
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

        # Get available scripts for dropdowns
        script_options = self._get_available_scripts()

        # Extract current script selections from alert data if editing
        current_triggered_script = ""
        current_cleared_script = ""
        current_escalated_script = ""

        if current_alert:
            current_triggered_script = self._extract_script_from_actions(
                current_alert.get("on_triggered", []))
            current_cleared_script = self._extract_script_from_actions(
                current_alert.get("on_cleared", []))
            current_escalated_script = self._extract_script_from_actions(
                current_alert.get("on_escalated", []))

        return self.async_show_form(
            step_id="add_alert_actions",
            data_schema=vol.Schema({
                # Triggered actions
                vol.Optional("on_triggered_script", default=current_triggered_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=script_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),

                # Cleared actions
                vol.Optional("on_cleared_script", default=current_cleared_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=script_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),

                # Escalated actions
                vol.Optional("on_escalated_script", default=current_escalated_script): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=script_options,
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

    def _extract_script_from_actions(self, actions):
        """Helper method to extract script service from actions list."""
        for action in actions:
            service = action.get("service", "")
            if service.startswith("script."):
                # Convert service format (script.script_name) to entity_id format (script.script_name)
                # The service format is already correct, just return it
                return service
        return ""
