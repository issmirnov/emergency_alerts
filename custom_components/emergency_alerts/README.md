# Emergency Alerts

A Home Assistant custom integration for defining and tracking emergency alert conditions with UI-based configuration.

## Features
- Create emergency alert sensors via the Home Assistant UI
- Monitor any entity for a specific state
- Optional: trigger a Home Assistant service when the alert is triggered

## Installation
1. Copy this folder to `config/custom_components/emergency_alerts` in your Home Assistant setup, or install via HACS (if published).
2. Restart Home Assistant.

## Usage
- Go to Settings > Devices & Services > Add Integration > Emergency Alerts
- Configure the alert name, entity to monitor, trigger state, and optional action service
- The integration will create a `binary_sensor.emergency_<name>` entity

## Example
Monitor a window sensor for an open state:
- Name: "Window Open While Raining"
- Entity: `binary_sensor.living_room_window`
- Trigger State: `on`
- Action Service: `notify.notify` (optional)

## Future Plans
- Add severity, timestamps, and acknowledgment support
- Custom Lovelace card for grouped display 