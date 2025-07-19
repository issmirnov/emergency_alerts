# Emergency Alerts Development Setup

This development environment provides a complete setup for developing both the Emergency Alerts Home Assistant integration and the companion Lovelace card.

## Quick Start

1. **Open in Dev Container**: Open this folder in VS Code and select "Reopen in Container"
2. **Wait for Setup**: The container will automatically install Home Assistant and set up the development environment
3. **Access Home Assistant**: Navigate to http://localhost:8123 once setup is complete

## What's Included

### Integration Development
- **Custom Component**: The Emergency Alerts integration is automatically symlinked to Home Assistant
- **Hot Reload**: Changes to the integration are reflected in Home Assistant
- **Debug Logging**: Enhanced logging for the emergency_alerts component

### Lovelace Card Development  
- **Visual Editor**: The card includes a comprehensive visual configuration editor
- **Auto-copy**: Built card is automatically copied to Home Assistant's www folder
- **Example Dashboard**: Pre-configured dashboard showing different card configurations

## File Structure

```
/workspaces/emergency_alerts/
├── config/                          # Home Assistant configuration (persistent)
│   ├── configuration.yaml          # Main HA config with card resources
│   ├── ui-lovelace.yaml            # Dashboard with emergency alerts examples
│   └── www/                        # Static files (cards, etc.)
│       └── emergency-alerts-card.js # Built Lovelace card
├── custom_components/emergency_alerts/ # Integration source code
├── lovelace-emergency-alerts-card/     # Card source code
└── update-card.sh                      # Helper script to rebuild card
```

## Development Workflow

### Working on the Integration
1. Make changes to files in `custom_components/emergency_alerts/`
2. Restart Home Assistant: Configuration → Server Controls → Restart
3. Changes are automatically reflected (symlinked)

### Working on the Lovelace Card
1. Make changes to `lovelace-emergency-alerts-card/src/emergency-alerts-card.ts`
2. Run the update script: `./update-card.sh`
3. Refresh your browser to see changes

### Manual Card Build
```bash
cd lovelace-emergency-alerts-card
npm run build
cp dist/emergency-alerts-card.js /workspaces/emergency_alerts/config/www/
```

## Accessing the Development Environment

- **Home Assistant**: http://localhost:8123
- **Configuration**: `/workspaces/emergency_alerts/config/`
- **Logs**: `/workspaces/emergency_alerts/config/home-assistant.log`
- **Setup Log**: `/workspaces/emergency_alerts/config/setup.log`

## Using the Card

### Adding via Visual Editor
1. Go to Dashboard → Edit → Add Card
2. Search for "Emergency Alerts Card"
3. Use the visual editor to configure all options

### Card Configuration Options
The card supports extensive configuration through the visual editor:

- **Display Options**: Show/hide different alert types, compact mode
- **Grouping & Sorting**: Group by severity/status/group, sort by various criteria  
- **Filtering**: Filter by severity, group, or status
- **Action Buttons**: Configure acknowledge, clear, and escalate buttons
- **Advanced**: Entity patterns, refresh intervals

### Example YAML Configuration
```yaml
type: custom:emergency-alerts-card
show_acknowledged: true
show_cleared: false
group_by: "severity"
severity_filter: ["critical", "warning"]
compact_mode: false
button_style: "compact"
```

## Troubleshooting

### Container Won't Start
- Check that Docker is running
- Ensure no syntax errors in `.devcontainer.json`

### Card Not Loading
- Run `./update-card.sh` to rebuild and copy the card
- Check browser console for JavaScript errors
- Verify the resource is listed in Configuration → Lovelace Dashboards → Resources

### Integration Not Loading
- Check Home Assistant logs: `/workspaces/emergency_alerts/config/home-assistant.log`
- Verify the symlink exists: `ls -la config/custom_components/`
- Restart Home Assistant after making changes

### Home Assistant Won't Start
- Check setup log: `/workspaces/emergency_alerts/config/setup.log`
- Manually start: `~/homeassistant/start_hass.sh`

## Ports
- **8123**: Home Assistant web interface
- All other ports are internal to the container

This setup provides a complete development environment for both the backend integration and frontend card components. 