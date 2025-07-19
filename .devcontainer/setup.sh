#!/bin/bash

echo "Setting up Home Assistant development environment..."

# Use the config directory within our workspace
HASS_CONFIG_DIR="/workspaces/emergency_alerts/config"
mkdir -p "$HASS_CONFIG_DIR"
mkdir -p "$HASS_CONFIG_DIR/custom_components"

# Install Home Assistant
echo "Installing Home Assistant..."
pip install homeassistant

# Only create configuration if it doesn't exist (preserve existing config)
if [ ! -f "$HASS_CONFIG_DIR/configuration.yaml" ]; then
    echo "Creating new Home Assistant configuration..."
    # Create basic Home Assistant configuration
    cat > "$HASS_CONFIG_DIR/configuration.yaml" << 'EOF'
# Basic Home Assistant configuration for development
default_config:

# Enable frontend
frontend:

# Enable API
api:

# Lovelace configuration for development
lovelace:
  mode: yaml
  resources:
    - url: /local/emergency-alerts-card.js
      type: module

# Example automation for testing
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

# Logger configuration for development
logger:
  default: info
  logs:
    custom_components.emergency_alerts: debug

# Enable the recorder (uses SQLite by default)
recorder:

# Enable history
history:

# Enable logbook
logbook:
EOF

    # Create empty files that Home Assistant expects
    touch "$HASS_CONFIG_DIR/automations.yaml"
    touch "$HASS_CONFIG_DIR/scripts.yaml"
    touch "$HASS_CONFIG_DIR/scenes.yaml"

    # Create basic Lovelace dashboard with Emergency Alerts Card
    cat > "$HASS_CONFIG_DIR/ui-lovelace.yaml" << 'EOF'
title: Emergency Alerts Development
views:
  - title: Emergency Dashboard
    path: emergency
    icon: mdi:alert
    cards:
      # Emergency Alerts Card - Basic Configuration
      - type: custom:emergency-alerts-card
        title: "Emergency Alerts"
        
      # Emergency Alerts Card - Compact Mode
      - type: custom:emergency-alerts-card
        title: "Compact Alerts"
        compact_mode: true
        show_timestamps: false
        button_style: "icons_only"
        max_alerts_per_group: 5
        
      # Emergency Alerts Card - Critical Only
      - type: custom:emergency-alerts-card
        title: "Critical Alerts Only"
        severity_filter: ["critical"]
        show_acknowledge_button: false
        show_escalate_button: false

  - title: Overview
    path: overview
    icon: mdi:home
    cards:
      - type: entities
        title: "Emergency Sensors"
        entities:
          - entity: binary_sensor.emergency_door_open
            name: "Door Emergency"
          - entity: binary_sensor.emergency_window_broken  
            name: "Window Emergency"
          - entity: binary_sensor.emergency_fire_alarm
            name: "Fire Alarm"
          - entity: binary_sensor.emergency_security_breach
            name: "Security Breach"
EOF

    # Create a secrets.yaml file
    cat > "$HASS_CONFIG_DIR/secrets.yaml" << 'EOF'
# Secrets for Home Assistant development
# This file is for development only
EOF
else
    echo "Using existing Home Assistant configuration..."
fi

# Create a script to run Home Assistant
mkdir -p "$HOME/homeassistant"
cat > "$HOME/homeassistant/start_hass.sh" << 'EOF'
#!/bin/bash
cd "/workspaces/emergency_alerts/config"
hass --config "/workspaces/emergency_alerts/config" --log-file "/workspaces/emergency_alerts/config/home-assistant.log"
EOF

chmod +x "$HOME/homeassistant/start_hass.sh"

# Create symlink from emergency_alerts custom component to Home Assistant config
echo "Creating symlink for emergency_alerts custom component..."
if [ -d "/workspaces/emergency_alerts/custom_components/emergency_alerts" ]; then
    ln -sf "/workspaces/emergency_alerts/custom_components/emergency_alerts" "$HASS_CONFIG_DIR/custom_components/emergency_alerts"
    echo "✓ Symlinked emergency_alerts component to Home Assistant config"
else
    echo "⚠ Emergency alerts component not found at /workspaces/emergency_alerts/custom_components/emergency_alerts"
fi

# Set up Lovelace card development
echo "Setting up Lovelace card..."
mkdir -p "$HASS_CONFIG_DIR/www"

# Copy the built emergency alerts card if it exists
if [ -f "/workspaces/emergency_alerts/lovelace-emergency-alerts-card/dist/emergency-alerts-card.js" ]; then
    cp "/workspaces/emergency_alerts/lovelace-emergency-alerts-card/dist/emergency-alerts-card.js" "$HASS_CONFIG_DIR/www/"
    echo "✓ Copied emergency-alerts-card.js to www folder"
else
    echo "⚠ Emergency alerts card not built yet. Run 'cd lovelace-emergency-alerts-card && npm run build' to build it."
fi

echo "Home Assistant setup complete!"
echo "Configuration directory: $HASS_CONFIG_DIR (mounted, persistent)"
echo "Custom components directory: $HASS_CONFIG_DIR/custom_components"
echo ""
echo "To start Home Assistant manually:"
echo "  $HOME/homeassistant/start_hass.sh"
echo ""
echo "Home Assistant will be available at: http://localhost:8123"

# Start Home Assistant in the background
echo "Starting Home Assistant..."
nohup "$HOME/homeassistant/start_hass.sh" > "/workspaces/emergency_alerts/config/setup.log" 2>&1 &

echo "Home Assistant is starting up. Check logs at /workspaces/emergency_alerts/config/setup.log"
echo "It may take a few minutes to fully start up."