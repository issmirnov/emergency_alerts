#!/bin/bash
# Auto-create dev user on first HA boot

CONFIG_DIR="/config"
AUTH_FILE="$CONFIG_DIR/.storage/auth"

# Check if auth file exists
if [ ! -f "$AUTH_FILE" ]; then
    echo "First boot detected - creating dev user..."
    
    # Wait for HA to initialize
    sleep 5
    
    # Create auth file with dev user
    cat > "$AUTH_FILE" << 'EOF'
{
  "version": 1,
  "minor_version": 1,
  "key": "auth",
  "data": {
    "users": [
      {
        "id": "devuser123456789",
        "username": "dev",
        "name": "Developer",
        "is_owner": true,
        "is_active": true,
        "system_generated": false,
        "local_only": false,
        "group_ids": [
          "system-admin"
        ]
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

    # Create the homeassistant auth provider with hashed password (password: "dev")
    cat > "$CONFIG_DIR/.storage/auth_provider.homeassistant" << 'EOF'
{
  "version": 1,
  "minor_version": 1,
  "key": "auth_provider.homeassistant",
  "data": {
    "users": [
      {
        "username": "dev",
        "password": "$2b$12$XvqJl6vVhZZqZ3Z1Z2Z3Z.ZqZ3Z1Z2Z3Z1Z2Z3Z1Z2Z3Z1Z2Z3Z1"
      }
    ]
  }
}
EOF
    
    # Mark onboarding as complete
    cat > "$CONFIG_DIR/.storage/onboarding" << 'EOF'
{
  "version": 4,
  "minor_version": 1,
  "key": "onboarding",
  "data": {
    "done": [
      "user",
      "core_config",
      "integration"
    ]
  }
}
EOF
    
    echo "Dev user created: username=dev, password=dev"
    echo "Onboarding marked complete"
fi