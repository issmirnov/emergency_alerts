"""Constants for the Emergency Alerts integration."""

DOMAIN = "emergency_alerts"

# Hub configuration keys
CONF_HUB_TYPE = "hub_type"
CONF_HUB_NAME = "hub_name"
CONF_CUSTOM_NAME = "custom_name"
CONF_ALERTS = "alerts"

# Configuration keys
CONF_TRIGGER_TYPE = "trigger_type"
CONF_ENTITY_ID = "entity_id"
CONF_TRIGGER_STATE = "trigger_state"
CONF_TEMPLATE = "template"
CONF_LOGICAL_CONDITIONS = "logical_conditions"
CONF_LOGICAL_OPERATOR = "logical_operator"
CONF_SEVERITY = "severity"
CONF_GROUP = "group"
CONF_ON_TRIGGERED = "on_triggered"
CONF_ON_CLEARED = "on_cleared"
CONF_ON_ESCALATED = "on_escalated"
CONF_ON_ACKNOWLEDGED = "on_acknowledged"
CONF_ON_SNOOZED = "on_snoozed"
CONF_ON_RESOLVED = "on_resolved"
CONF_SNOOZE_DURATION = "snooze_duration"

# Notification profiles
CONF_NOTIFICATION_PROFILES = "notification_profiles"
CONF_USE_PROFILE = "use_profile"
CONF_PROFILE_NAME = "profile_name"
CONF_PROFILE_SERVICES = "profile_services"

# Trigger types
TRIGGER_TYPE_SIMPLE = "simple"
TRIGGER_TYPE_TEMPLATE = "template"
TRIGGER_TYPE_LOGICAL = "logical"
# TRIGGER_TYPE_COMBINED removed in Phase 2 - redundant with logical

# Comparators for combined triggers
COMP_EQ = "=="
COMP_NE = "!="
COMP_LT = "<"
COMP_LTE = "<="
COMP_GT = ">"
COMP_GTE = ">="
COMPARATORS = [COMP_EQ, COMP_NE, COMP_LT, COMP_LTE, COMP_GT, COMP_GTE]

# Severity levels
SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"

# Groups
GROUP_SECURITY = "security"
GROUP_SAFETY = "safety"
GROUP_POWER = "power"
GROUP_LIGHTS = "lights"
GROUP_ENVIRONMENT = "environment"
GROUP_OTHER = "other"

# Alert states (for status sensor)
STATE_INACTIVE = "inactive"
STATE_ACTIVE = "active"
STATE_ACKNOWLEDGED = "acknowledged"
STATE_SNOOZED = "snoozed"
STATE_ESCALATED = "escalated"
STATE_RESOLVED = "resolved"

# Switch types
SWITCH_TYPE_ACKNOWLEDGE = "acknowledged"
SWITCH_TYPE_SNOOZE = "snoozed"
SWITCH_TYPE_RESOLVE = "resolved"

# Services
SERVICE_ACKNOWLEDGE = "acknowledge"
SERVICE_CLEAR = "clear"
SERVICE_ESCALATE = "escalate"

# Event types
EVENT_ALERT_TRIGGERED = f"{DOMAIN}_alert_triggered"
EVENT_ALERT_CLEARED = f"{DOMAIN}_alert_cleared"
EVENT_ALERT_ACKNOWLEDGED = f"{DOMAIN}_alert_acknowledged"
EVENT_ALERT_ESCALATED = f"{DOMAIN}_alert_escalated"
EVENT_ALERT_SNOOZED = f"{DOMAIN}_alert_snoozed"
EVENT_ALERT_RESOLVED = f"{DOMAIN}_alert_resolved"

# Dispatcher signals
SIGNAL_ALERT_UPDATE = f"{DOMAIN}_alert_update"
SIGNAL_SWITCH_UPDATE = f"{DOMAIN}_switch_update"

# Default values
DEFAULT_SEVERITY = SEVERITY_WARNING
DEFAULT_GROUP = GROUP_OTHER
DEFAULT_ESCALATION_TIME = 300  # 5 minutes in seconds
DEFAULT_SNOOZE_DURATION = 300  # 5 minutes in seconds

# State transition rules (what states can coexist)
# Format: {primary_state: [states_that_must_be_off]}
STATE_EXCLUSIONS = {
    STATE_ACKNOWLEDGED: [STATE_SNOOZED, STATE_RESOLVED],
    STATE_SNOOZED: [STATE_ACKNOWLEDGED, STATE_RESOLVED],
    STATE_RESOLVED: [STATE_ACKNOWLEDGED, STATE_SNOOZED],
}
