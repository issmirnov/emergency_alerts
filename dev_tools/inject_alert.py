#!/usr/bin/env python3
"""Inject test alert into HA storage to bypass UI"""
import json

# Read current config
with open('dev_tools/ha-config/.storage/core.config_entries', 'r') as f:
    config = json.load(f)

# Find emergency_alerts entry
for entry in config['data']['entries']:
    if entry['domain'] == 'emergency_alerts':
        # Inject test alert
        entry['data']['alerts'] = {
            'test_door': {
                'name': 'Test Door Alert',
                'trigger_type': 'simple',
                'entity_id': 'input_boolean.test_door',
                'trigger_state': 'on',
                'severity': 'warning'
            }
        }
        print("✓ Injected test alert into emergency_alerts entry")
        break

# Write back
with open('dev_tools/ha-config/.storage/core.config_entries', 'w') as f:
    json.dump(config, f, indent=2)
    
print("✓ Storage file updated")
print("✓ Test alert 'test_door' added")
print("✓ This will create select.test_door_state entity")