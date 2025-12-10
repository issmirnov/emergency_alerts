"""Factory for creating test entities using MockConfigEntry."""

from typing import Any, Dict
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.const import DOMAIN


def create_group_hub_entry(
    hass: HomeAssistant | None = None,
    hub_name: str = "test_hub",
    group: str = "security",
    alerts: Dict[str, Dict[str, Any]] | None = None,
    **kwargs
) -> MockConfigEntry:
    """Create a MockConfigEntry for a group hub."""
    if alerts is None:
        alerts = {}
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title=f"Emergency Alerts - {group.title()}",
        data={
            "hub_type": "group",
            "group": group,
            "hub_name": hub_name,
            "alerts": alerts,
            **kwargs
        },
    )
    if hass is not None:
        entry.add_to_hass(hass)
    return entry


def create_global_hub_entry(
    hass: HomeAssistant,
    options: Dict[str, Any] | None = None,
    **kwargs
) -> MockConfigEntry:
    """Create a MockConfigEntry for a global settings hub."""
    if options is None:
        options = {
            "default_escalation_time": 300,
            "enable_global_notifications": False,
            "notification_profiles": {}
        }
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Emergency Alerts - Global Settings",
        data={
            "hub_type": "global",
            "name": "Global Settings",
            **kwargs
        },
        options=options,
    )
    entry.add_to_hass(hass)
    return entry


def create_alert_config(
    name: str = "Test Alert",
    trigger_type: str = "simple",
    entity_id: str = "binary_sensor.test_sensor",
    trigger_state: str = "on",
    severity: str = "warning",
    **kwargs
) -> Dict[str, Any]:
    """Create an alert configuration dictionary."""
    config: Dict[str, Any] = {
        "name": name,
        "trigger_type": trigger_type,
        "severity": severity,
    }
    
    if trigger_type == "simple":
        config["entity_id"] = entity_id
        config["trigger_state"] = trigger_state
    elif trigger_type == "template":
        config["template"] = kwargs.get("template", "{{ True }}")
    elif trigger_type == "logical":
        config["logical_conditions"] = kwargs.get("logical_conditions", [])
        config["logical_operator"] = kwargs.get("logical_operator", "and")
    
    # Add optional fields
    for key in ["on_triggered", "on_cleared", "on_escalated", "on_acknowledged", 
               "on_snoozed", "on_resolved", "snooze_duration"]:
        if key in kwargs:
            config[key] = kwargs[key]
    
    return config
