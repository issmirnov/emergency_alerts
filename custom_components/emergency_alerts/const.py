"""Constants for the Emergency Alerts integration."""

DOMAIN = "emergency_alerts"

# Configuration keys
CONF_TRIGGER_TYPE = "trigger_type"
CONF_ENTITY_ID = "entity_id"
CONF_TRIGGER_STATE = "trigger_state"
CONF_TEMPLATE = "template"
CONF_LOGICAL_CONDITIONS = "logical_conditions"
CONF_SEVERITY = "severity"
CONF_GROUP = "group"
CONF_ON_TRIGGERED = "on_triggered"
CONF_ON_CLEARED = "on_cleared"
CONF_ON_ESCALATED = "on_escalated"

# Trigger types
TRIGGER_TYPE_SIMPLE = "simple"
TRIGGER_TYPE_TEMPLATE = "template"
TRIGGER_TYPE_LOGICAL = "logical"

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

# Services
SERVICE_ACKNOWLEDGE = "acknowledge"

# Event types
EVENT_ALERT_TRIGGERED = f"{DOMAIN}_alert_triggered"
EVENT_ALERT_CLEARED = f"{DOMAIN}_alert_cleared"
EVENT_ALERT_ACKNOWLEDGED = f"{DOMAIN}_alert_acknowledged"
EVENT_ALERT_ESCALATED = f"{DOMAIN}_alert_escalated"

# Dispatcher signals
SIGNAL_ALERT_UPDATE = f"{DOMAIN}_alert_update"

# Default values
DEFAULT_SEVERITY = SEVERITY_WARNING
DEFAULT_GROUP = GROUP_OTHER
DEFAULT_ESCALATION_TIME = 300  # 5 minutes in seconds 