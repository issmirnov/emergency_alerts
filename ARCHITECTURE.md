# Emergency Alerts Integration: Architecture & Design

## Overview
The Emergency Alerts integration for Home Assistant provides a modular, extensible framework for defining, tracking, and responding to critical conditions in your smart home. It is inspired by best practices from integrations like Adaptive Lighting and Scheduler Card, but introduces a meta-abstraction for emergency state, grouping, and escalation.

---

## Key Concepts

### 1. **Emergency Alert Entity**
- Each alert is a `binary_sensor` entity (on = active, off = inactive).
- Alerts are configured via the UI (config flow) and support:
  - **Simple triggers** (entity+state)
  - **Jinja template triggers**
  - **Logical triggers** (AND of multiple conditions, each simple or template)
- Alerts can be assigned to a **group/category** (e.g., security, safety, power).
- Each alert exposes attributes: severity, timestamps, group, acknowledged/escalated state, and more.

### 2. **Actions & Escalation**
- Each alert can define actions (service calls) for:
  - `on_triggered`: when the alert becomes active
  - `on_cleared`: when the alert is cleared
  - `on_escalated`: if the alert is not acknowledged within a set time (default: 5 minutes)
- Actions are lists of service calls (with optional data) and are executed at the appropriate lifecycle event.
- Alerts can be acknowledged via a service (`emergency_alerts.acknowledge`).

### 3. **Grouping & Summary Sensors**
- Alerts can be grouped (security, safety, power, etc.).
- The integration creates:
  - A **global summary sensor** (`sensor.emergency_alerts_active`) showing the count and list of all active alerts, with group breakdowns.
  - **Group summary sensors** (`sensor.emergency_alerts_<group>_active`) for each group, showing the count and list of active alerts in that group.
- Summary sensors update automatically via Home Assistant's dispatcher when any alert changes state.

---

## Implementation Details

### **Config Flow**
- UI-driven setup using Home Assistant's config flow system.
- Fields:
  - Name
  - Trigger type (simple, template, logical)
  - Entity and state (for simple)
  - Jinja template (for template)
  - List of conditions (for logical)
  - Severity (info, warning, critical)
  - Group/category
  - Actions: on_triggered, on_cleared, on_escalated (lists of service calls)

### **Entity Logic**
- Each alert is a subclass of `BinarySensorEntity`.
- Triggers are evaluated on relevant entity state changes:
  - Simple: track the specified entity
  - Template: listen to all state changes (for full reactivity)
  - Logical: track all referenced entities
- When triggered, the alert:
  - Sets state to on, records timestamp, resets acknowledgment/escalation
  - Executes `on_triggered` actions
  - Starts escalation timer (if configured)
- When cleared, the alert:
  - Sets state to off, records timestamp, resets acknowledgment/escalation
  - Executes `on_cleared` actions
  - Cancels escalation timer
- If not acknowledged within the escalation window, executes `on_escalated` actions and sets escalated state.
- Alerts can be acknowledged via service, which cancels escalation and marks the alert as acknowledged.

### **Summary Sensors**
- Implemented as `SensorEntity` subclasses.
- Global summary sensor tracks all active alerts and group breakdowns.
- Group summary sensors track active alerts in their group.
- Sensors update via dispatcher signal sent by any alert entity on state change.

### **Data Model**
- All alert entities are tracked in `hass.data[DOMAIN]["entities"]` for service and summary access.
- Groups are dynamically discovered from configured alerts.

---

## Extensibility & Future Plans
- **OR logic** for logical triggers (currently AND only).
- **Custom escalation times** per alert.
- **History/logbook integration** for alert lifecycle events.
- **Custom Lovelace card** for grouped, interactive display and acknowledgment.
- **Area/device assignment** for better UI filtering.
- **Multi-language support** for all UI and service strings.
- **Diagnostics**: `diagnostics.py` stub included for future Home Assistant compliance.
- **Helpers**: `helpers.py` stub for shared logic and future expansion.

---

## Rationale & Best Practices
- **Binary sensor platform**: Ensures alerts are compatible with Home Assistant's UI, automations, and ecosystem.
- **UI-first config**: Modern Home Assistant best practice, with YAML as a possible future option for power users.
- **Dispatcher-based updates**: Efficient, real-time summary sensor updates.
- **Service-based acknowledgment**: Clean, automation-friendly way to silence/acknowledge alerts.
- **Action hooks**: Flexible, user-defined responses to alert lifecycle events.

---

## Example Use Cases
- Security: "Any door open while alarm armed" (group: security, on_triggered: notify, escalate: siren)
- Safety: "Water leak detected in basement" (group: safety, on_triggered: notify, escalate: persistent notification)
- Power: "Fridge door open > 5 min" (group: power, on_triggered: notify, on_cleared: log event)

---

## File Structure
- `__init__.py`: Integration setup, service registration, platform forwarding
- `binary_sensor.py`: Emergency alert entity logic
- `sensor.py`: Summary/group sensor logic
- `config_flow.py`: UI config flow
- `const.py`: Constants
- `services.yaml`: Service definitions
- `diagnostics.py`: Diagnostics stub
- `helpers.py`: Helpers stub
- `strings.json`, `translation/en.json`: UI strings and translations

---

## Contributing & Feedback
- Issues and PRs welcome!
- See README for install and usage instructions. 