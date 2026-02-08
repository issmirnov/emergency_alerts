#!/bin/bash
# Local HA Development Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_REPO_DIR="$PROJECT_ROOT/dev_tools/ha-frontend"

ensure_frontend_repo() {
    if [ ! -d "$FRONTEND_REPO_DIR/.git" ]; then
        echo "📦 Cloning Home Assistant frontend repo for dev cache-busting..."
        git clone https://github.com/home-assistant/frontend.git "$FRONTEND_REPO_DIR"
    fi

    if [ ! -d "$FRONTEND_REPO_DIR/dist" ] && [ ! -d "$FRONTEND_REPO_DIR/hass_frontend" ]; then
        echo "⚠️  Frontend repo found, but build artifacts are missing."
        echo "   Run: cd dev_tools/ha-frontend && script/setup && script/build_frontend"
    fi
}

echo "🏠 Home Assistant Local Development Environment"
echo "================================================"
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

case "${1:-help}" in
    start)
        echo "🚀 Starting Home Assistant..."
        cd "$PROJECT_ROOT"

        ensure_frontend_repo
        
        # Auto-create dev user if auth doesn't exist
        AUTH_FILE="dev_tools/ha-config/.storage/auth"
        if [ ! -f "$AUTH_FILE" ]; then
            echo "Creating dev user (username: dev, password: dev)..."
            mkdir -p dev_tools/ha-config/.storage
            
            # Create auth file with dev user
            cat > "$AUTH_FILE" << 'AUTHEOF'
{
  "version": 1,
  "minor_version": 1,
  "key": "auth",
  "data": {
    "users": [
      {
        "id": "devuser000000000001",
        "username": "dev",
        "name": "Developer",
        "is_owner": true,
        "is_active": true,
        "system_generated": false,
        "local_only": false,
        "group_ids": ["system-admin"]
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
        "id": "devcred000000000001",
        "user_id": "devuser000000000001",
        "auth_provider_type": "homeassistant",
        "auth_provider_id": null,
        "data": {"username": "dev"}
      }
    ],
    "refresh_tokens": []
  }
}
AUTHEOF
            
            # Create auth provider (bcrypt hash for "dev")
            cat > "dev_tools/ha-config/.storage/auth_provider.homeassistant" << 'PROVIDEREOF'
{
  "version": 1,
  "minor_version": 1,
  "key": "auth_provider.homeassistant",
  "data": {
    "users": [
      {
        "username": "dev",
        "password": "$2b$12$LWqkX15vXDEYPbYqZmZ2Z.hKKp7yVZYZYZYZYZYZYZYZYZYZYZYZYa"
      }
    ]
  }
}
PROVIDEREOF
            
            # Mark onboarding complete
            cat > "dev_tools/ha-config/.storage/onboarding" << 'ONBOARDEOF'
{
  "version": 4,
  "minor_version": 1,
  "key": "onboarding",
  "data": {
    "done": ["user", "core_config", "integration"]
  }
}
ONBOARDEOF
            
            echo "✓ Dev user created"
        fi
        
        docker-compose up -d
        echo ""
        echo "✅ Home Assistant is starting up!"
        echo ""
        echo "🌐 Web UI: http://localhost:8123"
        echo "💻 VSCode: http://localhost:8124 (password: dev)"
        echo ""
        echo "📝 On first run, create a user account in the web UI"
        echo "📦 Custom integration is auto-mounted from ./custom_components"
        echo ""
        echo "To view logs: ./dev_tools/local-dev.sh logs"
        echo "To restart: ./dev_tools/local-dev.sh restart"
        ;;
    
    stop)
        echo "🛑 Stopping Home Assistant..."
        cd "$PROJECT_ROOT"
        docker-compose down
        echo "✅ Stopped"
        ;;
    
    restart)
        echo "🔄 Restarting Home Assistant..."
        cd "$PROJECT_ROOT"
        docker-compose restart homeassistant
        echo "✅ Restarted - changes to custom_components will reload"
        ;;
    
    logs)
        echo "📋 Following logs (Ctrl+C to exit)..."
        cd "$PROJECT_ROOT"
        docker-compose logs -f homeassistant
        ;;
    
    shell)
        echo "🐚 Opening shell in HA container..."
        docker exec -it ha-dev /bin/bash
        ;;
    
    clean)
        echo "🧹 Cleaning up all data (WARNING: deletes all config entries and data)..."
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            cd "$PROJECT_ROOT"
            docker-compose down -v
            CONFIG_DIR="$PROJECT_ROOT/dev_tools/ha-config"
            find "$CONFIG_DIR" -mindepth 1 -maxdepth 1 \
                ! -name "configuration.yaml" \
                ! -name "dashboards" \
                -exec rm -rf {} +
            echo "✅ Cleaned up. Run 'start' to create fresh instance."
        else
            echo "❌ Cancelled"
        fi
        ;;

    nuke)
        echo "💣 Full wipe (docker volumes + HA config state)..."
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            cd "$PROJECT_ROOT"
            docker-compose down -v
            CONFIG_DIR="$PROJECT_ROOT/dev_tools/ha-config"
            find "$CONFIG_DIR" -mindepth 1 -maxdepth 1 \
                ! -name "configuration.yaml" \
                ! -name "dashboards" \
                -exec rm -rf {} +
            echo "✅ Full wipe complete. Run 'start' to create fresh instance."
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    install-lovelace)
        echo "📦 Installing lovelace card..."
        mkdir -p dev_tools/ha-config/www
        if [ -d "../lovelace-emergency-alerts-card" ]; then
            echo "Symlinking lovelace card..."
            ln -sf "$PROJECT_ROOT/../lovelace-emergency-alerts-card" \
                   "$PROJECT_ROOT/dev_tools/ha-config/www/lovelace-emergency-alerts-card"
            echo "✅ Lovelace card linked"
        else
            echo "❌ Lovelace card repo not found at ../lovelace-emergency-alerts-card"
        fi
        ;;
    
    test)
        echo "🧪 Running local tests..."
        cd "$PROJECT_ROOT"
        python dev_tools/test_runner.py
        ;;
    
    help|*)
        echo "Usage: ./dev_tools/local-dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start            Start HA instance with integration mounted"
        echo "  stop             Stop HA instance"
        echo "  restart          Restart HA (reload integration changes)"
        echo "  logs             Follow HA logs"
        echo "  shell            Open shell in HA container"
        echo "  clean            Delete all data and start fresh"
        echo "  nuke             Full wipe of volumes + HA config state"
        echo "  install-lovelace Install lovelace card"
        echo "  test             Run local unit tests"
        echo "  help             Show this help"
        echo ""
        echo "Quick Start:"
        echo "  1. ./dev_tools/local-dev.sh start"
        echo "  2. Open http://localhost:8123"
        echo "  3. Create user account"
        echo "  4. Add Emergency Alerts integration"
        echo ""
        ;;
esac
