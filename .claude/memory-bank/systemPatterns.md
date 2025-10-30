# System Patterns

> **Derived from**: projectbrief.md
> **Purpose**: Documents how the system is architected and key technical patterns

## Architecture Overview

### High-Level Structure
```
Home Assistant Core
    └── Emergency Alerts Integration (DOMAIN)
        ├── Global Settings Hub (config entry: hub_type="global")
        │   └── Global summary sensor
        │
        └── Alert Group Hubs (config entries: hub_type="group")
            ├── Hub Device (Emergency Alerts - [Group Name])
            │   └── Group summary sensor
            │
            └── Alert Devices (Emergency Alert: [Alert Name])
                ├── binary_sensor.emergency_[name] (Alert State)
                ├── sensor.emergency_[name]_status (Status Tracking)
                ├── button.emergency_[name]_acknowledge
                ├── button.emergency_[name]_clear
                └── button.emergency_[name]_escalate
```

### Component Breakdown
- **__init__.py**: Integration entry point, service registration, platform forwarding
- **config_flow.py**: Multi-step UI flows for hub creation and alert CRUD operations
- **binary_sensor.py**: Core alert entities, trigger evaluation, lifecycle management
- **sensor.py**: Summary sensors for groups and global overview
- **button.py**: Action buttons for alert interaction (acknowledge/clear/escalate)
- **switch.py**: Minimal implementation, currently unused
- **const.py**: Constants, configuration keys, event types, dispatcher signals
- **helpers.py**: Utility functions for common operations
- **diagnostics.py**: Diagnostics data collection for debugging

### Data Flow

#### Alert Creation Flow
```
User clicks gear icon
    → config_flow.py: async_step_user()
    → Menu selection (Add/Edit/Remove)
    → async_step_add_alert_basic()
        → Step 1: Name, trigger type, severity
    → async_step_add_alert_trigger_[type]()
        → Step 2: Type-specific trigger config
    → async_step_add_alert_actions()
        → Step 3: Action configuration
    → Data stored in config entry
    → hass.config_entries.async_reload()
    → Entities created immediately
```

#### Alert Trigger Evaluation Flow
```
HA State Change Event
    → binary_sensor.py: async_update()
    → _evaluate_trigger() based on trigger_type
        → simple: Check entity state
        → template: Evaluate Jinja2 template
        → logical: Evaluate AND/OR conditions
    → State change (on/off)
    → _update_status_sensor() updates status
    → _handle_state_change()
        → Execute on_triggered or on_cleared actions
        → Fire dispatcher signal SIGNAL_ALERT_UPDATE
    → Summary sensors update
```

## Design Patterns

### Pattern: Hub-Based Device Hierarchy
**Where Used**: __init__.py:8-27, sensor.py, binary_sensor.py
**Why**: Organizes alerts into logical groups with proper Home Assistant device relationships
**Example**:
```python
# In sensor.py - Creating hub device
device_info = DeviceInfo(
    identifiers={(DOMAIN, f"hub_{config_entry.entry_id}")},
    name=f"Emergency Alerts - {hub_name}",
    manufacturer="Emergency Alerts",
    model="Alert Group Hub",
    entry_type=DeviceEntryType.SERVICE,
)

# In binary_sensor.py - Creating alert device under hub
device_info = DeviceInfo(
    identifiers={(DOMAIN, f"alert_{self._config_entry.entry_id}_{self._alert_id}")},
    name=f"Emergency Alert: {self._name}",
    manufacturer="Emergency Alerts",
    model=f"{severity} Alert",
    via_device=(DOMAIN, f"hub_{self._config_entry.entry_id}"),  # Links to hub
)
```

### Pattern: Dispatcher Signals for Real-Time Updates
**Where Used**: binary_sensor.py:220-225, sensor.py
**Why**: Enables efficient real-time updates across components without tight coupling
**Example**:
```python
# In binary_sensor.py - Sending signal
from homeassistant.helpers.dispatcher import async_dispatcher_send

async def _handle_state_change(self):
    # ... state change logic ...
    async_dispatcher_send(
        self.hass,
        SIGNAL_ALERT_UPDATE,
        self._config_entry.entry_id
    )

# In sensor.py - Listening to signal
from homeassistant.helpers.dispatcher import async_dispatcher_connect

async def async_added_to_hass(self):
    self.async_on_remove(
        async_dispatcher_connect(
            self.hass,
            SIGNAL_ALERT_UPDATE,
            self._handle_alert_update,
        )
    )
```

### Pattern: Multi-Step Config Flow with Progressive Disclosure
**Where Used**: config_flow.py:150-400
**Why**: Breaks complex alert creation into digestible steps, shows only relevant fields
**Example**:
```python
# Step 1: Basic info
async def async_step_add_alert_basic(self, user_input=None):
    if user_input is not None:
        # Store step 1 data, route to step 2 based on trigger_type
        self._add_alert_data = user_input
        trigger_type = user_input["trigger_type"]
        return await getattr(self, f"async_step_add_alert_trigger_{trigger_type}")()

    # Show step 1 form
    return self.async_show_form(...)

# Step 2: Trigger-specific config
async def async_step_add_alert_trigger_simple(self, user_input=None):
    # Only shown if trigger_type == "simple"
    # Form shows entity selector and state field
    ...
```

### Pattern: Visual Form Builder for Logical Conditions
**Where Used**: config_flow.py:339-400
**Why**: Eliminates JSON syntax errors, makes logical conditions accessible to all users
**Example**:
```python
# Building dynamic schema for up to 10 entity/state pairs
schema_dict = {
    vol.Required("logical_operator", default="and"): selector.SelectSelector(...)
}
for i in range(1, 11):
    schema_dict[vol.Optional(f"entity_{i}")] = selector.EntitySelector()
    schema_dict[vol.Optional(f"state_{i}")] = selector.TextSelector()

# Parsing form data into logical_conditions list
conditions = []
for i in range(1, 11):
    entity_id = user_input.get(f"entity_{i}")
    state = user_input.get(f"state_{i}")
    if entity_id and state:
        conditions.append({"entity_id": entity_id, "state": state})
```

## Key Technical Decisions

### Decision: Config Entry Data vs Options
- **Context**: Need to store alert configurations
- **Options Considered**:
  1. Store in config entry options (accessed via entry.options)
  2. Store in config entry data (accessed via entry.data)
- **Decision**: Store in config entry data
- **Rationale**: Data is available immediately on reload without waiting for options flow; entities need alert configs during setup
- **Consequences**: Requires async_update_entry() to modify, but provides reliable immediate access
- **Location**: __init__.py:64-72, config_flow.py throughout

### Decision: Button Entities vs Switch Entities for Actions
- **Context**: Need UI controls for acknowledge/clear/escalate
- **Options Considered**:
  1. Switch entities (toggle on/off)
  2. Button entities (one-time press)
- **Decision**: Button entities
- **Rationale**: Actions are one-time events, not stateful toggles; buttons better represent this semantic
- **Consequences**: Simpler logic, clearer user intent, no confusing "on" state for actions
- **Date**: Early development (documented in cursor.context.md:217-218)

### Decision: Companion Status Sensor Pattern
- **Context**: Binary sensor only shows on/off, need richer status info
- **Options Considered**:
  1. Store status in binary sensor attributes only
  2. Create companion status sensor entity
- **Decision**: Companion status sensor (sensor.emergency_[name]_status)
- **Rationale**: Makes status easily accessible in automations, UI cards, and dashboards as a first-class entity
- **Consequences**: Creates two entities per alert, but significantly improves usability
- **Location**: binary_sensor.py:280-310

## Component Relationships

### config_flow.py ↔ binary_sensor.py
- **Interaction**: Config flow creates alert definitions, binary sensors consume them
- **Dependencies**: Config flow produces alert configs in specific schema, binary sensor expects that schema
- **Interface**: Config entry data structure with keys from const.py (CONF_TRIGGER_TYPE, CONF_ENTITY_ID, etc.)

### binary_sensor.py ↔ button.py
- **Interaction**: Buttons call methods on binary sensor entities
- **Dependencies**: Buttons need access to alert entity instances
- **Interface**: Methods: async_acknowledge(), async_clear(), async_escalate() on EmergencyAlert class

### binary_sensor.py ↔ sensor.py
- **Interaction**: Binary sensors fire dispatcher signals, summary sensors listen and update
- **Dependencies**: Summary sensors need to query all alerts in their group
- **Interface**: SIGNAL_ALERT_UPDATE dispatcher signal with config_entry.entry_id

## Code Organization

### Directory Structure
```
custom_components/emergency_alerts/
├── __init__.py              # Integration setup, service registration
├── binary_sensor.py         # Alert entities (400+ lines) - CORE LOGIC
├── button.py               # Action buttons (150 lines)
├── sensor.py               # Summary sensors (200 lines)
├── config_flow.py          # UI flows (800+ lines) - LARGEST FILE
├── const.py                # Constants (50 lines)
├── helpers.py              # Utilities (minimal)
├── diagnostics.py          # Debug data collection
├── switch.py               # Unused/minimal
├── services.yaml           # Service definitions for automations
├── strings.json            # UI text (300+ lines)
├── manifest.json           # Metadata
├── translations/en.json    # I18n (mirrors strings.json)
├── blueprints/             # Script templates
└── tests/                  # Pytest suite
```

### Module Responsibilities
- **binary_sensor.py**: Alert logic ONLY - trigger evaluation, state management, action execution
- **config_flow.py**: UI ONLY - user interaction, form validation, data persistence
- **sensor.py**: Aggregation ONLY - summary statistics, no alert logic
- **button.py**: Interaction ONLY - bridge between UI and alert entities

## Conventions

### Naming
- **Entity IDs**: `{platform}.emergency_{alert_name}` (snake_case from alert name)
- **Device IDs**: `hub_{entry_id}` for hubs, `alert_{entry_id}_{alert_id}` for alerts
- **Config Keys**: Use constants from const.py (CONF_TRIGGER_TYPE, etc.)
- **Private Methods**: Prefix with underscore (_evaluate_trigger, _handle_state_change)
- **Async Methods**: Prefix with async_ (async_update, async_acknowledge)

### Error Handling
- **Config Flow**: Return errors dict with field-specific messages, log warnings
- **Alert Evaluation**: Log errors, continue operation (don't break HA), show status in diagnostics
- **Template Errors**: Catch TemplateError, log with context, treat as condition not met
- **Service Calls**: Wrapped in try/except, logged but not re-raised (graceful degradation)

### State Management
- **Alert State**: Stored in binary sensor _attr_is_on (bool)
- **Status State**: Computed property get_status() based on _acknowledged, _cleared, _escalated flags
- **Config State**: Stored in config entry data (persistent), accessed via self._config_entry.data
- **Global State**: Shared via hass.data[DOMAIN] dict

### Testing
- **Fixtures**: Mock config entries in conftest.py
- **Unit Tests**: Test individual trigger types, status transitions, button actions
- **Integration Tests**: Test config entry setup/teardown, service registration
- **Coverage Target**: >90% overall, 100% for critical paths (alert evaluation)

## Critical Paths

### Alert Trigger Evaluation
**File**: binary_sensor.py:330-390
**Flow**:
1. async_update() called by HA coordinator
2. _evaluate_trigger() called based on trigger_type
3. For simple: Check states.get(entity_id).state == trigger_state
4. For template: Use self.hass.helpers.template.Template().async_render()
5. For logical: Iterate conditions, check all/any based on operator
6. Compare old state vs new state
7. If changed: Call _handle_state_change()
8. Update status sensor via _update_status_sensor()

**Gotchas**:
- Template errors must be caught and logged (don't crash HA)
- State changes only trigger actions if state actually changed (prevent spam)
- Logical operator must handle both "and" and "or" with defensive defaults

### Config Entry Reload for Immediate Entity Creation
**File**: config_flow.py:250-260, __init__.py:74-76
**Flow**:
1. User submits final step of add/edit alert
2. Config flow updates config entry data via hass.config_entries.async_update_entry()
3. Immediately call hass.config_entries.async_reload(entry.entry_id)
4. Integration unloads and reloads
5. New entities appear immediately in UI

**Gotchas**:
- Must reload entire config entry (not just update data)
- Reload is async - UI may briefly show old state
- All entities in the group reload, not just new/changed ones

### Status Sensor Creation and Updates
**File**: binary_sensor.py:280-310
**Flow**:
1. Alert entity added to hass (async_added_to_hass)
2. _update_status_sensor() called
3. Check if status sensor already exists via entity registry
4. If not: Create EmergencyAlertStatusSensor dynamically
5. Add to hass via async_add_entities()
6. On every state change: Call _update_status_sensor() to refresh

**Gotchas**:
- Status sensors created dynamically, not during platform setup
- Must check entity registry to avoid duplicates
- Status sensor must have same device_info as parent alert

## Anti-Patterns

### ❌ Don't: Directly modify config entry options in platform code
**Why**: Config entry modifications should happen in config_flow.py only
**Instead**: Read from entry.data, use services or config flow for modifications

### ❌ Don't: Store state in global variables or module-level attrs
**Why**: Home Assistant can reload integrations, state would be lost
**Instead**: Store in entity attributes, config entry data, or hass.data

### ❌ Don't: Block async functions with synchronous operations
**Why**: Breaks Home Assistant's event loop, causes UI freezes
**Instead**: Use hass.async_add_executor_job() for sync operations or make everything async

### ❌ Don't: Create entities in __init__.py directly
**Why**: Violates Home Assistant platform pattern, breaks device organization
**Instead**: Forward to platforms via async_forward_entry_setups()

### ❌ Don't: Hardcode entity IDs or service names
**Why**: Makes code brittle and hard to maintain
**Instead**: Use constants from const.py, build IDs from config data
