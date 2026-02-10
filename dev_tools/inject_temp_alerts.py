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
        # Uses input_number.test_temperature defined in configuration.yaml
        entry['data']['alerts'] = {
            'temp_below_20': {
                'name': 'Temperature Below 20',
                'trigger_type': 'template',
                'template': "{{ states('input_number.test_temperature') | float(20) < 20 }}",
                'severity': 'warning'
            },
            'temp_above_25': {
                'name': 'Temperature Above 25',
                'trigger_type': 'template',
                'template': "{{ states('input_number.test_temperature') | float(20) > 25 }}",
                'severity': 'info'
            },
            'temp_equals_16': {
                'name': 'Temperature Equals 16',
                'trigger_type': 'template',
                'template': "{{ states('input_number.test_temperature') | float(20) == 16 }}",
                'severity': 'critical'
            }
        }
        print("✓ Injected temperature test alerts:")
        print("  - temp_below_20: input_number.test_temperature (initial: 16°C) < 20")
        print("  - temp_above_25: input_number.test_temperature (initial: 16°C) > 25")
        print("  - temp_equals_16: input_number.test_temperature (initial: 16°C) == 16")
        break

# Write back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Storage file updated")
print("\nExpected results after HA restart:")
print("  ✅ temp_below_20 should TRIGGER (16 < 20 = True)")
print("  ❌ temp_above_25 should NOT trigger (16 > 25 = False)")
print("  ✅ temp_equals_16 should TRIGGER (16 == 16 = True)")
