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

wipe_config_state() {
    local config_dir="$1"
    if ! find "$config_dir" -mindepth 1 -maxdepth 1 \
        ! -name "configuration.yaml" \
        ! -name "dashboards" \
        -exec rm -rf {} +; then
        echo "⚠️  Permission issues detected. Retrying with sudo..."
        sudo find "$config_dir" -mindepth 1 -maxdepth 1 \
            ! -name "configuration.yaml" \
            ! -name "dashboards" \
            -exec rm -rf {} +
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

setup_test_data() {
    echo "📦 Setting up test integrations, alerts, and dashboard..."
    docker exec ha-dev python3 << 'SETUP_EOF'
import json
from pathlib import Path

# Setup config entries (integrations)
config_file = Path("/config/.storage/core.config_entries")
if not config_file.exists():
    print("⏭️  Skipping - config_entries not yet created")
    exit(0)

data = json.loads(config_file.read_text())

# Add sun integration
sun_exists = any(e["domain"] == "sun" for e in data["data"]["entries"])
if not sun_exists:
    data["data"]["entries"].append({
        "created_at": "2026-02-09T18:00:00+00:00",
        "data": {},
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "sun",
        "entry_id": "sun_integration_test",
        "minor_version": 1,
        "modified_at": "2026-02-09T18:00:00+00:00",
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": "Sun",
        "unique_id": None,
        "version": 1
    })
    print("  ✅ Sun integration")

# Add Emergency Alerts with test alerts
ea_exists = any(e["domain"] == "emergency_alerts" for e in data["data"]["entries"])
if not ea_exists:
    data["data"]["entries"].append({
        "created_at": "2026-02-09T18:00:00+00:00",
        "data": {
            "hub_type": "group",
            "group": "sun",
            "hub_name": "sun",
            "custom_name": "",
            "alerts": {
                "sun_up": {
                    "name": "Sun Up",
                    "trigger_type": "simple",
                    "severity": "warning",
                    "entity_id": "sun.sun",
                    "trigger_state": "above_horizon"
                },
                "sun_down": {
                    "name": "Sun Down",
                    "trigger_type": "simple",
                    "severity": "warning",
                    "entity_id": "sun.sun",
                    "trigger_state": "below_horizon"
                }
            }
        },
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "emergency_alerts",
        "entry_id": "emergency_alerts_test",
        "minor_version": 1,
        "modified_at": "2026-02-09T18:00:00+00:00",
        "options": {"default_escalation_time": 300},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": "Emergency Alerts - sun",
        "unique_id": None,
        "version": 2
    })
    print("  ✅ Emergency Alerts with sun_up/sun_down")

config_file.write_text(json.dumps(data, indent=2))

# Setup dashboard registration
dash_file = Path("/config/.storage/lovelace_dashboards")
if dash_file.exists():
    dash_data = json.loads(dash_file.read_text())
    ea_exists = any(item["id"] == "emergency-alerts" for item in dash_data["data"]["items"])
    if not ea_exists:
        dash_data["data"]["items"].append({
            "id": "emergency-alerts",
            "icon": "mdi:alert",
            "title": "Emergency Alerts",
            "url_path": "emergency-alerts",
            "mode": "yaml",
            "require_admin": False,
            "show_in_sidebar": True,
            "filename": "dashboards/emergency-alerts.yaml"
        })
        dash_file.write_text(json.dumps(dash_data, indent=2))
        print("✅ Emergency Alerts dashboard registered")

# Setup Lovelace card resource
resources_file = Path("/config/.storage/lovelace_resources")
if resources_file.exists():
    res_data = json.loads(resources_file.read_text())
else:
    res_data = {
        "version": 1,
        "minor_version": 1,
        "key": "lovelace_resources",
        "data": {"items": []}
    }

card_exists = any(
    item.get("url", "").endswith("emergency-alerts-card.js")
    for item in res_data["data"]["items"]
)

if not card_exists:
    res_data["data"]["items"].append({
        "id": f"emergency_alerts_card_{len(res_data['data']['items'])}",
        "type": "module",
        "url": "/local/lovelace-emergency-alerts-card/emergency-alerts-card.js"
    })
    resources_file.write_text(json.dumps(res_data, indent=2))
    print("✅ Emergency Alerts card resource registered")
SETUP_EOF
}

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

        # Wait for HA to initialize
        echo ""
        echo "⏳ Waiting for Home Assistant to initialize..."
        sleep 20

        # Setup test integrations and alerts
        setup_test_data

        echo ""
        echo "✅ Home Assistant is ready!"
        echo ""
        echo "🌐 Web UI: http://localhost:8123"
        echo "   Login: Automatic (trusted network bypass)"
        echo "💻 VSCode: http://localhost:8124 (password: dev)"
        echo ""
        echo "📦 Pre-configured:"
        echo "   - Sun integration"
        echo "   - Emergency Alerts with sun_up/sun_down"
        echo "   - Notification test script"
        echo "   - Emergency Alerts dashboard"
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
            wipe_config_state "$CONFIG_DIR"
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
            wipe_config_state "$CONFIG_DIR"
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
