#!/usr/bin/env python3
"""Inject temperature test alerts with Jinja template triggers"""
import json
from pathlib import Path

# Read current config
config_path = Path('dev_tools/ha-config/.storage/core.config_entries')
with open(config_path, 'r') as f:
    config = json.load(f)

# Find emergency_alerts entry
for entry in config['data']['entries']:
    if entry['domain'] == 'emergency_alerts':
        # Inject template trigger alerts for testing numeric comparisons
        entry['data']['alerts'] = {
            'temp_below_20': {
                'name': 'Temperature Below 20',
                'trigger_type': 'template',
                'entity_id': 'sensor.test_temperature',
                'template': "{{ states('sensor.test_temperature') | float < 20 }}",
                'severity': 'warning'
            },
            'temp_above_20': {
                'name': 'Temperature Above 20',
                'trigger_type': 'template',
                'entity_id': 'sensor.test_temperature_high',
                'template': "{{ states('sensor.test_temperature_high') | float > 20 }}",
                'severity': 'info'
            },
            'temp_equals_16': {
                'name': 'Temperature Equals 16',
                'trigger_type': 'template',
                'entity_id': 'sensor.test_temperature',
                'template': "{{ states('sensor.test_temperature') | float == 16 }}",
                'severity': 'critical'
            }
        }
        print("✓ Injected temperature test alerts:")
        print("  - temp_below_20: sensor.test_temperature (16°C) < 20")
        print("  - temp_above_20: sensor.test_temperature_high (25°C) > 20")
        print("  - temp_equals_16: sensor.test_temperature (16°C) == 16")
        break

# Write back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Storage file updated")
print("\nExpected results after HA restart:")
print("  ✅ temp_below_20 should TRIGGER (16 < 20 = True)")
print("  ✅ temp_above_20 should TRIGGER (25 > 20 = True)")
print("  ✅ temp_equals_16 should TRIGGER (16 == 16 = True)")
