# Emergency Alerts Integration: Architecture & Design

## Overview
The Emergency Alerts integration for Home Assistant provides a comprehensive, hub-based framework for organizing, managing, and responding to critical conditions in your smart home. The integration features a modern UI with group-based organization, device hierarchy, status tracking, and intuitive management interfaces.

---

## Architecture: Hub-Based Organization

### **Hub Types**

#### 1. **Global Settings Hub**
- **Purpose**: Manages notification settings that apply to all Emergency Alerts
- **Features**:
  - Default escalation times
  - Global notification services
  - Message templates
  - System-wide preferences
- **Entities**: Creates summary sensors for system-wide oversight

#### 2. **Alert Group Hubs**
- **Purpose**: Organize related alerts with custom group names (e.g., "Ivan's Security Alerts", "Kitchen Safety")
- **Features**:
  - Custom group naming (free-text, not predefined categories)
  - Device hierarchy with proper relationships
  - Group-specific summary sensors
  - Centralized management interface

### **Device Hierarchy**
```
Emergency Alerts - [Group Name] (Hub Device)
├── Emergency Alert: [Alert Name] (Individual Alert Device)
│   ├── binary_sensor.emergency_[alert_name] (Alert State)
│   ├── sensor.emergency_[alert_name]_status (Status Tracking)
│   ├── button.emergency_[alert_name]_acknowledge
│   ├── button.emergency_[alert_name]_clear
│   └── button.emergency_[alert_name]_escalate
└── sensor.emergency_[group_name]_summary (Group Summary)
```

---

## Key Components

### **1. Alert Entities (`binary_sensor.py`)**
- **Primary State**: `binary_sensor.emergency_[name]` (on = active, off = inactive)
- **Status Tracking**: Companion `sensor.emergency_[name]_status` showing:
  - `"active"` - Alert is currently triggered
  - `"inactive"` - Alert condition is not met
  - `"acknowledged"` - User has acknowledged the alert
  - `"cleared"` - User has manually cleared the alert
  - `"escalated"` - Alert was not acknowledged within escalation time

### **2. Action Buttons (`button.py`)**
- **Acknowledge**: Mark alert as seen/handled
- **Clear**: Manually resolve the alert
- **Escalate**: Force escalation actions
- **Mutual Exclusivity**: Actions update status appropriately
- **Device Grouping**: All buttons belong to their alert's device

### **3. Summary Sensors (`sensor.py`)**
- **Group Summaries**: `sensor.emergency_[group]_summary`
  - Count of active alerts in the group
  - List of triggered alert names
  - Group-level status overview
- **Environment Summary**: Global overview across all groups

---

## Trigger Types

### **Simple Triggers**
- Monitor a single entity's state
- Example: `entity_id: binary_sensor.front_door`, `trigger_state: "on"`

### **Template Triggers**
- Use Jinja2 templates for complex conditions
- Example: `{{ states('sensor.temperature')|float > 30 and states('sensor.humidity')|float < 20 }}`

### **Logical Triggers**
- Combine multiple entity conditions with AND/OR logic
- **Visual Condition Builder**: User-friendly interface for creating complex conditions
- **Dynamic Form**: Up to 10 entity/state pairs with operator selection
- **Operator Support**: AND (all conditions must be true) or OR (any condition can be true)
- Example: `sensor.openweather=rain AND sensor.garage_door=open`

---

## User Interface: Menu-Style Management

### **Modern UI Approach**
- **Menu-Style Interface**: Beautiful button-based actions instead of dropdown + submit
- **Dynamic Options**: Only shows relevant actions (edit/remove only appear when alerts exist)
- **Immediate Feedback**: Changes take effect instantly with automatic config reloading

### **Alert Management Options**
1. **➕ Add New Alert** - Create new alert with guided form
2. **✏️ Edit Alert** - Modify existing alert with pre-filled values
3. **🗑️ Remove Alert** - Delete alerts with confirmation

### **Edit Alert Workflow**
1. **Selection**: Choose alert from formatted dropdown showing name, type, and severity
2. **Edit Form**: All current values pre-filled for easy modification
3. **Action Choice**: Save changes or delete alert from same screen
4. **Smart Updates**: Alert IDs update automatically if name changes

---

## Configuration Flow (`config_flow.py`)

### **Setup Flow**
1. **Hub Type Selection**: Choose Global Settings or Alert Group
2. **Global Setup**: Configure system-wide settings
3. **Group Setup**: Create custom-named alert groups

### **Management Flow**
- **Menu Interface**: Clean button-style action selection
- **CRUD Operations**: Complete Create, Read, Update, Delete functionality
- **Form Validation**: Comprehensive validation with helpful error messages
- **Auto-Reload**: Immediate entity updates after configuration changes

### **User Experience Features**
- **Detailed Descriptions**: Helpful examples and guidance in all forms
- **Progressive Disclosure**: Fields show/hide based on trigger type selection
- **Smart Defaults**: Sensible defaults for all optional fields
- **Error Handling**: Clear error messages with actionable guidance

---

## Technical Implementation

### **State Management**
- **Dispatcher Signals**: Efficient real-time updates across components
- **Status Synchronization**: Status sensors update on every state change
- **Device Relationships**: Proper `via_device` hierarchy for clean UI organization

### **Legacy Support**
- **Backward Compatibility**: Existing installations continue to work
- **Migration Path**: Gradual migration to hub-based architecture
- **Data Preservation**: No data loss during upgrades

### **Performance Considerations**
- **Selective Updates**: Only relevant entities update on state changes
- **Efficient Queries**: Optimized entity lookup and status updates
- **Memory Management**: Clean entity registration and deregistration

---

## Data Flow

### **Alert Lifecycle**
1. **Trigger Evaluation** → State change detected
2. **State Update** → Binary sensor state changes
3. **Status Update** → Companion status sensor updates
4. **Action Execution** → Configured actions run
5. **Summary Update** → Group and global summaries refresh
6. **UI Refresh** → Interface updates automatically

### **User Interactions**
1. **Button Press** → Action button triggered
2. **State Change** → Alert status updates
3. **Entity Update** → Status sensor reflects new state
4. **Summary Refresh** → Group summary updates
5. **Dispatcher Signal** → All relevant components notified

---

## Extensibility & Future Enhancements

### **Planned Features**
- **Advanced Templating**: More template helper functions
- **Custom Escalation Times**: Per-alert escalation settings
- **Area Integration**: Tie alerts to Home Assistant areas
- **Advanced Notifications**: Rich notification formatting
- **History Integration**: Enhanced logbook entries

### **API Extensions**
- **Service Enhancements**: More granular control services
- **Event System**: Custom events for alert lifecycle
- **Webhook Support**: External system integration
- **REST API**: External application access

---

## Best Practices & Design Principles

### **User Experience First**
- **Intuitive Interface**: Menu-style, button-based interactions
- **Immediate Feedback**: Changes visible instantly
- **Progressive Enhancement**: Simple to use, powerful when needed
- **Comprehensive Help**: Detailed descriptions and examples throughout

### **Technical Excellence**
- **Clean Architecture**: Proper separation of concerns
- **Efficient Updates**: Minimal overhead, maximum responsiveness
- **Robust Error Handling**: Graceful degradation and clear error messages
- **Future-Proof Design**: Extensible architecture for continued development

### **Home Assistant Integration**
- **Platform Compliance**: Follows all Home Assistant best practices
- **UI Consistency**: Matches Home Assistant design patterns
- **Device Organization**: Proper device hierarchy and relationships
- **Service Integration**: Clean service definitions and interfaces

---

## File Structure

```
custom_components/emergency_alerts/
├── __init__.py              # Integration setup and platform forwarding
├── binary_sensor.py         # Main alert entities with status tracking
├── button.py               # Interactive action buttons
├── sensor.py               # Summary sensors and hub devices
├── config_flow.py          # Setup and management UI with CRUD operations
├── const.py                # Constants and shared definitions
├── services.yaml           # Service definitions
├── strings.json            # UI strings with detailed descriptions
├── translations/           # Internationalization support
│   └── en.json
├── manifest.json           # Integration metadata
└── README.md              # Usage and installation guide
```

---

## Security & Reliability

### **Data Validation**
- **Input Sanitization**: All user inputs validated and sanitized
- **Schema Validation**: Strict schema validation for all configurations
- **Error Boundaries**: Isolated error handling to prevent cascade failures

### **State Consistency**
- **Atomic Updates**: Configuration changes applied atomically
- **Rollback Support**: Failed updates don't corrupt existing state
- **Validation Checks**: Comprehensive validation before applying changes

---

This architecture provides a robust, user-friendly foundation for emergency alert management while maintaining the flexibility to grow and adapt to future requirements.