#!/usr/bin/env python3
"""Set up test environment with sun integration and sample alerts."""

import json
from pathlib import Path

# Paths
CONFIG_DIR = Path(__file__).parent / "ha-config" / ".storage"
CONFIG_ENTRIES_FILE = CONFIG_DIR / "core.config_entries"

# Load current config entries
config_entries = json.loads(CONFIG_ENTRIES_FILE.read_text())

# Add sun integration if not present
sun_exists = any(e["domain"] == "sun" for e in config_entries["data"]["entries"])
if not sun_exists:
    sun_entry = {
        "created_at": "2026-02-09T18:00:00.000000+00:00",
        "data": {},
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "sun",
        "entry_id": "sun_integration_01",
        "minor_version": 1,
        "modified_at": "2026-02-09T18:00:00.000000+00:00",
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": "Sun",
        "unique_id": None,
        "version": 1,
    }
    config_entries["data"]["entries"].append(sun_entry)
    print("✅ Added sun integration")

# Add Emergency Alerts integration with 2 alerts
ea_exists = any(e["domain"] == "emergency_alerts" for e in config_entries["data"]["entries"])
if not ea_exists:
    ea_entry = {
        "created_at": "2026-02-09T18:00:00.000000+00:00",
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
                    "trigger_state": "above_horizon",
                    "on_triggered_script": [{
                        "service": "script.turn_on",
                        "data": {"entity_id": "script.alert_notification_test"}
                    }]
                },
                "sun_down": {
                    "name": "Sun Down",
                    "trigger_type": "simple",
                    "severity": "warning",
                    "entity_id": "sun.sun",
                    "trigger_state": "below_horizon",
                    "on_triggered_script": [{
                        "service": "script.turn_on",
                        "data": {"entity_id": "script.alert_notification_test"}
                    }]
                }
            }
        },
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "emergency_alerts",
        "entry_id": "emergency_alerts_01",
        "minor_version": 1,
        "modified_at": "2026-02-09T18:00:00.000000+00:00",
        "options": {"default_escalation_time": 300},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": "Emergency Alerts - sun",
        "unique_id": None,
        "version": 2,
    }
    config_entries["data"]["entries"].append(ea_entry)
    print("✅ Added Emergency Alerts integration with 2 alerts")
    print("   - sun_up: triggers on above_horizon")
    print("   - sun_down: triggers on below_horizon")
    print("   - Both connected to notification script")

# Save config
CONFIG_ENTRIES_FILE.write_text(json.dumps(config_entries, indent=2))
print("\n✅ Configuration saved!")
print("Restart HA to load: ./dev_tools/local-dev.sh restart")
