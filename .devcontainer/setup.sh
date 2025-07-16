#!/bin/bash

echo "Setting up Home Assistant development environment..."

# Create Home Assistant config directory structure in user's home
HASS_CONFIG_DIR="$HOME/homeassistant/config"
mkdir -p "$HASS_CONFIG_DIR"
mkdir -p "$HASS_CONFIG_DIR/custom_components"

# Install Home Assistant
echo "Installing Home Assistant..."
pip install homeassistant

# Create basic Home Assistant configuration
cat > "$HASS_CONFIG_DIR/configuration.yaml" << 'EOF'
# Basic Home Assistant configuration for development
default_config:

# Enable frontend
frontend:

# Enable API
api:

# Enable Home Assistant Cloud
cloud:

# Text to speech
tts:
  - platform: google_translate

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

# Create a secrets.yaml file
cat > "$HASS_CONFIG_DIR/secrets.yaml" << 'EOF'
# Secrets for Home Assistant development
# This file is for development only
EOF

# Create a script to run Home Assistant
cat > "$HOME/homeassistant/start_hass.sh" << 'EOF'
#!/bin/bash
cd "$HOME/homeassistant/config"
hass --config "$HOME/homeassistant/config" --log-file "$HOME/homeassistant/home-assistant.log"
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

echo "Home Assistant setup complete!"
echo "Configuration directory: $HASS_CONFIG_DIR"
echo "Custom components directory: $HASS_CONFIG_DIR/custom_components"
echo ""
echo "To start Home Assistant manually:"
echo "  $HOME/homeassistant/start_hass.sh"
echo ""
echo "Home Assistant will be available at: http://localhost:8123"

# Start Home Assistant in the background
echo "Starting Home Assistant in the background..."
nohup "$HOME/homeassistant/start_hass.sh" > "$HOME/homeassistant/setup.log" 2>&1 &

echo "Home Assistant is starting up. Check logs at $HOME/homeassistant/setup.log"
echo "It may take a few minutes to fully start up."