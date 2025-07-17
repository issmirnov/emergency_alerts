# Emergency Alerts Integration

[![Test Emergency Alerts Integration](https://github.com/issmirnov/emergency_alerts/actions/workflows/test.yml/badge.svg)](https://github.com/issmirnov/emergency_alerts/actions/workflows/test.yml)
[![HACS Validation](https://github.com/issmirnov/emergency_alerts/actions/workflows/test.yml/badge.svg?event=schedule)](https://github.com/issmirnov/emergency_alerts/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/issmirnov/emergency_alerts/branch/main/graph/badge.svg)](https://github.com/issmirnov/emergency-alerts-integration)

A comprehensive Home Assistant custom integration for managing emergency alerts with hub-based organization, group management, and intuitive status tracking.

## ✨ Features

### 🏗️ **Hub-Based Organization**
- **Global Settings Hub**: Manage system-wide notification preferences and escalation settings
- **Alert Group Hubs**: Organize alerts with custom group names (e.g., "Ivan's Security Alerts", "Kitchen Safety")
- **Device Hierarchy**: Clean organization in Home Assistant's device registry

### 🎯 **Alert Management**
- **Multiple Trigger Types**: Simple entity monitoring, Jinja2 templates, and logical combinations
- **Severity Levels**: Critical, warning, and info classifications
- **Status Tracking**: Real-time status with dedicated status sensors
- **Action Buttons**: Acknowledge, clear, and escalate alerts with button entities

### 🎨 **Modern User Interface**
- **Menu-Style Management**: Beautiful button-based interface instead of dropdown menus
- **Immediate Updates**: Changes take effect instantly with automatic config reloading
- **Smart Forms**: Pre-filled edit forms with helpful descriptions and examples
- **Progressive Disclosure**: Forms adapt based on your selections

### 📊 **Comprehensive Monitoring**
- **Status Sensors**: Track alert states (active, acknowledged, cleared, escalated)
- **Group Summaries**: Overview of active alerts per group
- **Device Organization**: Each alert gets its own device with related entities

## 🚀 Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the "+" button and search for "Emergency Alerts"
4. Install the integration
5. Restart Home Assistant
6. Add the integration via **Settings** → **Devices & Services**

### Manual Installation

1. Copy the `custom_components/emergency_alerts` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via **Settings** → **Devices & Services**

## ⚙️ Setup

### 1. Choose Hub Type

When adding the integration, you'll choose between:

#### **Global Settings Hub**
- Configure system-wide notification settings
- Set default escalation times
- Manage global message templates
- One per Home Assistant instance

#### **Alert Group Hub**
- Create custom-named groups for organizing alerts
- Example group names: "Security Alerts", "Kitchen Safety", "Ivan's Monitors"
- Multiple groups supported

### 2. Manage Alerts

After setup, click the gear icon on any Alert Group Hub to access the management menu:

- **➕ Add New Alert** - Create a new alert
- **✏️ Edit Alert** - Modify existing alerts (appears when alerts exist)
- **🗑️ Remove Alert** - Delete alerts (appears when alerts exist)

## 📋 Alert Configuration

### **Trigger Types**

#### **Simple Triggers**
Monitor a single entity's state:
```yaml
# Example: Front door left open
Entity ID: binary_sensor.front_door
Trigger State: "on"
Severity: warning
```

#### **Template Triggers**
Use Jinja2 templates for complex conditions:
```yaml
# Example: High temperature with low humidity
Template: "{{ states('sensor.temperature')|float > 30 and states('sensor.humidity')|float < 20 }}"
Severity: critical
```

#### **Logical Triggers**
Combine multiple conditions:
```yaml
# Example: Multiple motion sensors triggered
Conditions: [
  {"entity_id": "binary_sensor.motion_kitchen", "state": "on"},
  {"entity_id": "binary_sensor.motion_living_room", "state": "on"}
]
Operator: and
Severity: info
```

### **Alert Properties**
- **Name**: Descriptive alert name (e.g., "Front Door Open", "High Temperature")
- **Severity**: Critical, Warning, or Info
- **Escalation Time**: Minutes before escalating if not acknowledged
- **Actions**: Service calls for triggered, cleared, and escalated states

## 🎛️ Entities Created

For each alert in a group, the integration creates:

### **Alert Device: "Emergency Alert: [Name]"**
- `binary_sensor.emergency_[name]` - Alert state (on/off)
- `sensor.emergency_[name]_status` - Current status (active, acknowledged, cleared, escalated, inactive)
- `button.emergency_[name]_acknowledge` - Acknowledge the alert
- `button.emergency_[name]_clear` - Manually clear the alert
- `button.emergency_[name]_escalate` - Force escalation

### **Hub Device: "Emergency Alerts - [Group Name]"**
- `sensor.emergency_[group]_summary` - Group overview and active alert count

## 🔄 Alert Lifecycle

1. **Triggered** → Alert becomes active, status = "active"
2. **User Action** → Use buttons to acknowledge, clear, or escalate
3. **Status Updates** → Status sensor reflects current state
4. **Automatic Clearing** → Alert clears when condition is no longer met
5. **Escalation** → If not acknowledged within escalation time

## 🎯 Example Use Cases

### **Security Monitoring**
```yaml
Group: "Home Security"
Alert: "Door Open While Armed"
Trigger: Template - "{{ states('alarm_control_panel.home') == 'armed_away' and states('binary_sensor.front_door') == 'on' }}"
Severity: Critical
Actions: Notify mobile app, trigger siren
```

### **Safety Alerts**
```yaml
Group: "Safety Monitors"
Alert: "Water Leak Detected"
Trigger: Simple - binary_sensor.water_leak_basement = "on"
Severity: Critical
Actions: Send notifications, shut off water valve
```

### **Maintenance Reminders**
```yaml
Group: "Maintenance"
Alert: "Fridge Door Open"
Trigger: Simple - binary_sensor.fridge_door = "on" (with delay)
Severity: Warning
Actions: Notify family members
```

## 🔧 Services

The integration provides several services for automation:

- `emergency_alerts.acknowledge` - Acknowledge an active alert
- `emergency_alerts.clear` - Manually clear an alert
- `emergency_alerts.test` - Test an alert configuration

## 🏠 Home Assistant Integration

### **Device Organization**
- Alerts appear as individual devices under their group hub
- Clean hierarchy in the device registry
- Proper device relationships for easy navigation

### **Automation Friendly**
- All entities work seamlessly in automations
- Status sensors provide detailed state information
- Button entities can be triggered from automations

### **UI Consistency**
- Follows Home Assistant design patterns
- Integrates cleanly with the native interface
- Professional look and feel

## 🧪 Development & Testing

### **Running Tests**
```bash
# Run all tests
./run_tests.sh

# Run validation only
python validate_integration.py

# Run specific test
cd custom_components/emergency_alerts
python -m pytest tests/test_binary_sensor.py -v
```

### **Test Coverage**
The integration maintains high test coverage:
- Overall: >90%
- Critical paths: 100%
- Config flow: >85%

## 📊 HACS Compliance

This integration is designed to be fully HACS compliant:

- ✅ Repository structure follows HACS requirements
- ✅ Proper manifest.json with all required fields
- ✅ HACS validation passes in CI/CD
- ✅ GitHub topics configured for discoverability

## 📚 Documentation

- [**Architecture Guide**](ARCHITECTURE.md) - Technical implementation details
- [**Testing Guide**](TESTING.md) - Comprehensive testing documentation
- [**Change Log**](cursor.context.md) - Development history and feature evolution

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### **Development Guidelines**
- Follow Home Assistant integration best practices
- Maintain high test coverage
- Update documentation for new features
- Use meaningful commit messages

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- [**GitHub Issues**](https://github.com/issmirnov/emergency-alerts-integration/issues) - Bug reports and feature requests
- [**GitHub Discussions**](https://github.com/issmirnov/emergency-alerts-integration/discussions) - General questions and community support
- [**Home Assistant Community Forum**](https://community.home-assistant.io/) - Community discussions

## 🙏 Acknowledgments

Special thanks to the Home Assistant community and core developers for providing the excellent framework and documentation that made this integration possible.

---

**Emergency Alerts Integration** - Making your smart home safer and more responsive, one alert at a time. 🚨✨
