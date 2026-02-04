"""Unified single-page config flow for Emergency Alerts - Phase 2 Simplification."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Simplified trigger types - removed "combined" as it's redundant with logical
TRIGGER_TYPES_SIMPLIFIED = [
    {"label": "Simple - Monitor one entity's state", "value": "simple"},
    {"label": "Template - Advanced Jinja2 conditions", "value": "template"},
    {"label": "Logical - Multiple conditions with AND/OR", "value": "logical"},
]

SEVERITY_LEVELS = [
    {"label": "Warning ⚠️", "value": "warning"},
    {"label": "Error ❌", "value": "error"},
    {"label": "Critical 🚨", "value": "critical"},
]


async def async_step_add_alert_unified(self, user_input=None):
    """Unified single-page form for creating simple and template alerts.
    
    This replaces the old 3-step wizard with a single intelligent form.
    Shows different fields based on trigger type selection.
    """
    is_editing = hasattr(self, '_editing_alert_id')
    current_alert = None
    if is_editing:
        alerts = self.config_entry.data.get("alerts", {})
        current_alert = alerts.get(self._editing_alert_id, {})
    
    if user_input is not None:
        trigger_type = user_input["trigger_type"]
        
        # If user selected logical trigger, redirect to wizard
        if trigger_type == "logical":
            # Store basic info and redirect to logical wizard
            self._alert_data = {
                "name": user_input["name"],
                "trigger_type": "logical",
                "severity": user_input.get("severity", "warning")
            }
            return await self.async_step_add_alert_trigger_logical()
        
        # Build complete alert data from unified form
        alert_data = {
            "name": user_input["name"],
            "trigger_type": trigger_type,
            "severity": user_input.get("severity", "warning"),
        }
        
        # Add trigger-specific fields
        if trigger_type == "simple":
            alert_data["entity_id"] = user_input["entity_id"]
            alert_data["trigger_state"] = user_input["trigger_state"]
        elif trigger_type == "template":
            alert_data["entity_id"] = user_input.get("entity_id", "")
            alert_data["template"] = user_input["template"]
        
        # Add action fields (all optional)
        actions = {}
        for action_type in ["on_triggered", "on_acknowledged", "on_snoozed", 
                           "on_cleared", "on_escalated", "on_resolved"]:
            script_key = f"{action_type}_script"
            value = user_input.get(script_key)
            if value:
                if value.startswith("profile:"):
                    actions[action_type] = value
                else:
                    actions[action_type] = [{"service": value}]
        
        # Reminder timing
        remind_after = user_input.get("remind_after_seconds", 0)
        if remind_after:
            actions["remind_after_seconds"] = int(remind_after)
        
        alert_data.update(actions)
        
        # Save alert
        alerts = dict(self.config_entry.data.get("alerts", {}))
        alert_id = alert_data["name"].lower().replace(" ", "_")
        
        if is_editing and alert_id != self._editing_alert_id:
            del alerts[self._editing_alert_id]
        
        alerts[alert_id] = alert_data
        
        new_data = dict(self.config_entry.data)
        new_data["alerts"] = alerts
        
        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        
        # Clean up edit mode
        if is_editing:
            delattr(self, '_editing_alert_id')
        
        return self.async_create_entry(
            title="Alert Created" if not is_editing else "Alert Updated", 
            data={}
        )
    
    # Build form schema
    trigger_type = current_alert.get("trigger_type", "simple") if current_alert else "simple"
    
    # Get available actions
    script_options = self._get_available_scripts()
    profiles = self._get_notification_profiles()
    action_options = []
    for profile_id, profile_data in profiles.items():
        action_options.append({
            "label": f"📋 Profile: {profile_data['name']}",
            "value": f"profile:{profile_id}"
        })
    action_options.extend(script_options)
    
    # Build schema with all fields
    schema_fields = {
        # Basic Info Section
        vol.Required("name", default=current_alert.get("name", "") if current_alert else ""): 
            selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT
                )
            ),
        
        vol.Required("severity", default=current_alert.get("severity", "warning") if current_alert else "warning"): 
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SEVERITY_LEVELS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        
        vol.Required("trigger_type", default=trigger_type): 
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=TRIGGER_TYPES_SIMPLIFIED,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
    }
    
    # Trigger fields (shown based on type)
    if trigger_type == "simple":
        # Show current state as helper
        current_state_hint = ""
        if current_alert and current_alert.get("entity_id"):
            state_obj = self.hass.states.get(current_alert["entity_id"])
            if state_obj:
                current_state_hint = f"Current: {state_obj.state}"
        
        schema_fields[vol.Required("entity_id", default=current_alert.get("entity_id", "") if current_alert else "")] = \
            selector.EntitySelector(
                selector.EntitySelectorConfig(
                    # No domain filter = autocomplete shows ALL entities
                )
            )
        
        schema_fields[vol.Required("trigger_state", default=current_alert.get("trigger_state", "") if current_alert else "")] = \
            selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT
                )
            )
    
    elif trigger_type == "template":
        schema_fields[vol.Optional("entity_id", default=current_alert.get("entity_id", "") if current_alert else "")] = \
            selector.EntitySelector(
                selector.EntitySelectorConfig()
            )
        
        schema_fields[vol.Required("template", default=current_alert.get("template", "") if current_alert else "")] = \
            selector.TemplateSelector(
                selector.TemplateSelectorConfig()
            )
    
    # Actions Section (always shown, all optional)
    for action_type, label in [
        ("on_triggered", "When Triggered"),
        ("on_acknowledged", "When Acknowledged"),
        ("on_snoozed", "When Snoozed"),
        ("on_cleared", "When Cleared"),
        ("on_escalated", "When Escalated"),
        ("on_resolved", "When Resolved"),
    ]:
        script_key = f"{action_type}_script"
        default_val = ""
        if current_alert:
            default_val = self._extract_value_from_actions(current_alert.get(action_type, []))
        
        schema_fields[vol.Optional(script_key, default=default_val)] = \
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=action_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    custom_value=True,
                )
            )
    
    # Reminder timing
    schema_fields[vol.Optional("remind_after_seconds", default=current_alert.get("remind_after_seconds", 0) if current_alert else 0)] = \
        selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=0, label="No reminder"),
                    selector.SelectOptionDict(value=300, label="5 minutes"),
                    selector.SelectOptionDict(value=600, label="10 minutes"),
                    selector.SelectOptionDict(value=1800, label="30 minutes"),
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    
    return self.async_show_form(
        step_id="add_alert_unified",
        data_schema=vol.Schema(schema_fields),
        description_placeholders={
            "description": "Create or edit an emergency alert. Logical triggers use a separate wizard."
        }
    )