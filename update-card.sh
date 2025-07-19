#!/bin/bash

echo "Updating Emergency Alerts Card..."

# Build the card
cd "/workspaces/emergency_alerts/lovelace-emergency-alerts-card"
npm run build

# Copy to Home Assistant www folder
if [ -f "dist/emergency-alerts-card.js" ]; then
    cp "dist/emergency-alerts-card.js" "/workspaces/emergency_alerts/config/www/"
    echo "✓ Card updated successfully!"
    echo "Refresh your browser or restart Home Assistant to see changes."
else
    echo "✗ Build failed - no output file found"
    exit 1
fi 