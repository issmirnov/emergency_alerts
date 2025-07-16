# Home Assistant Configuration Access

This directory provides access to your Home Assistant configuration files from the host machine.

## Important Files

- `configuration.yaml` - Main Home Assistant configuration
- `automations.yaml` - Automations (managed via UI)
- `scripts.yaml` - Scripts (managed via UI)
- `scenes.yaml` - Scenes (managed via UI)
- `secrets.yaml` - Secret values (passwords, API keys, etc.)

## Database and State

The Home Assistant database (`home-assistant_v2.db`) and other runtime files are stored in the Docker volume and persist between container rebuilds.

## Custom Components

Your `emergency_alerts` integration is symlinked from the workspace, so changes to the code are immediately reflected in Home Assistant.

## Logs

Home Assistant logs are available at: `/home/vscode/homeassistant/home-assistant.log`
