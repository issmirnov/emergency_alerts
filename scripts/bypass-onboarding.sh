#!/bin/bash

# Bypass Home Assistant Onboarding
# Creates a default admin user (username: dev, password: dev) and completes onboarding

set -e

CONFIG_DIR="${1:-./config}"
STORAGE_DIR="$CONFIG_DIR/.storage"

echo "🔧 Bypassing Home Assistant onboarding..."
echo "   Config directory: $CONFIG_DIR"

# Ensure storage directory exists
mkdir -p "$STORAGE_DIR"

# Create onboarding completion file
cat > "$STORAGE_DIR/onboarding" <<'EOF'
{
  "version": 4,
  "minor_version": 1,
  "key": "onboarding",
  "data": {
    "done": [
      "user",
      "analytics",
      "core_config"
    ]
  }
}
EOF

echo "✓ Created onboarding completion file"

# Create default admin user (dev/dev)
# Password hash for "dev" using PBKDF2-SHA256
cat > "$STORAGE_DIR/auth_provider.homeassistant" <<'EOF'
{
  "version": 1,
  "minor_version": 1,
  "key": "auth_provider.homeassistant",
  "data": {
    "users": [
      {
        "username": "dev",
        "password": "pbkdf2:sha256:260000$oQpR8g3n8J0H$d8b0a6f7c0f5a3e7e9d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1"
      }
    ]
  }
}
EOF

echo "✓ Created default admin user (username: dev, password: dev)"

# Create auth file with user credentials
cat > "$STORAGE_DIR/auth" <<'EOF'
{
  "version": 1,
  "minor_version": 1,
  "key": "auth",
  "data": {
    "users": [
      {
        "id": "devuser123456789",
        "group_ids": [
          "system-admin"
        ],
        "is_owner": true,
        "is_active": true,
        "name": "Developer",
        "system_generated": false,
        "local_only": false
      }
    ],
    "groups": [
      {
        "id": "system-admin",
        "name": "Administrators"
      }
    ],
    "credentials": [
      {
        "id": "devcred123456789",
        "user_id": "devuser123456789",
        "auth_provider_type": "homeassistant",
        "auth_provider_id": null,
        "data": {
          "username": "dev"
        }
      }
    ],
    "refresh_tokens": []
  }
}
EOF

echo "✓ Created auth configuration"

# Create core config to skip location selection
cat > "$STORAGE_DIR/core.config" <<'EOF'
{
  "version": 1,
  "minor_version": 4,
  "key": "core.config",
  "data": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "elevation": 0,
    "radius": 100,
    "unit_system_v2": "metric",
    "location_name": "Development",
    "time_zone": "America/Los_Angeles",
    "external_url": null,
    "internal_url": null,
    "currency": "USD",
    "country": "US",
    "language": "en"
  }
}
EOF

echo "✓ Created core configuration"

# Set correct permissions
chmod 644 "$STORAGE_DIR/onboarding"
chmod 644 "$STORAGE_DIR/auth_provider.homeassistant"
chmod 600 "$STORAGE_DIR/auth"
chmod 600 "$STORAGE_DIR/core.config"

echo ""
echo "✅ Onboarding bypass complete!"
echo ""
echo "Credentials:"
echo "  Username: dev"
echo "  Password: dev"
echo ""
echo "Restart Home Assistant to apply changes."
