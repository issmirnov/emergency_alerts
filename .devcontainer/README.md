# Home Assistant Development Container

A simple development environment for the Emergency Alerts integration.

## 🚀 Quick Start

1. **Rebuild Container**: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"
2. **Access Home Assistant**: http://localhost:8123 (starts automatically)

## 📁 Persistent Data

Everything is stored in your workspace `config/` directory, which persists because it's part of your project folder. This includes:

- Configuration files (`configuration.yaml`, etc.)
- Home Assistant database
- User accounts and settings
- Installed integrations

## 🔧 Manual Commands

```bash
# Start Home Assistant (if not running)
cd /workspaces/emergency_alerts && hass -c config

# Check if running
ps aux | grep hass

# View logs
tail -f config/home-assistant.log

# Stop Home Assistant
pkill -f hass
```

## 🧪 Development

Your `emergency_alerts` integration is automatically symlinked into Home Assistant's `custom_components` directory. Changes to your code are immediately available - just restart Home Assistant or reload the integration.

To add the integration:
1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Emergency Alerts"

## 🗑️ Reset

To start fresh, delete the `config/` directory and rebuild the container.