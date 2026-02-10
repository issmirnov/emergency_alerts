#!/usr/bin/env python3
"""
Setup live end-to-end test for Jinja numeric triggers.
Creates alert with template trigger and provides commands to test it.
"""
import json
from pathlib import Path

config_path = Path('dev_tools/ha-config/.storage/core.config_entries')

print("🔧 Setting up live Jinja numeric trigger test...")
print()

# Read config
with open(config_path, 'r') as f:
    config = json.load(f)

# Find emergency_alerts entry
for entry in config['data']['entries']:
    if entry['domain'] == 'emergency_alerts':
        # Configure test alert
        entry['data']['alerts'] = {
            'temp_below_20': {
                'name': 'Temperature Below 20',
                'trigger_type': 'template',
                'template': "{{ states('input_number.test_temperature') | float(20) < 20 }}",
                'severity': 'warning',
                'on_triggered': [
                    {
                        'service': 'script.turn_on',
                        'data': {
                            'entity_id': 'script.alert_notification_test'
                        }
                    }
                ]
            }
        }
        print("✅ Configured alert: 'Temperature Below 20'")
        print("   Template: {{ states('input_number.test_temperature') | float(20) < 20 }}")
        print("   Triggers when: input_number.test_temperature < 20")
        print("   Action: Calls script.alert_notification_test (creates persistent notification)")
        print("   Note: Uses float(20) default to handle unknown states gracefully")
        break

# Write config
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("\n✅ Configuration saved!")
print()
print("=" * 70)
print("TEST PROCEDURE")
print("=" * 70)
print()
print("1. Restart Home Assistant:")
print("   docker-compose restart homeassistant")
print()
print("2. Wait 30 seconds for HA to initialize")
print()
print("3. Check alert status (should be TRIGGERED since initial value is 16 < 20):")
print("   docker exec ha-dev curl -s http://localhost:8123/api/states/binary_sensor.emergency_temperature_below_20 | python3 -m json.tool")
print()
print("4. Change temperature to 25 (above threshold):")
print("   docker exec ha-dev curl -X POST http://localhost:8123/api/services/input_number/set_value \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{\"entity_id\": \"input_number.test_temperature\", \"value\": 25}'")
print()
print("5. Wait 2 seconds, then check alert (should be OFF):")
print("   docker exec ha-dev curl -s http://localhost:8123/api/states/binary_sensor.emergency_temperature_below_20 | python3 -m json.tool")
print()
print("6. Change temperature back to 15 (below threshold):")
print("   docker exec ha-dev curl -X POST http://localhost:8123/api/services/input_number/set_value \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{\"entity_id\": \"input_number.test_temperature\", \"value\": 15}'")
print()
print("7. Wait 2 seconds, then check alert (should be ON and trigger notification):")
print("   docker exec ha-dev curl -s http://localhost:8123/api/states/binary_sensor.emergency_temperature_below_20 | python3 -m json.tool")
print()
print("=" * 70)
print()
print("Expected Results:")
print("  ✅ Alert ON when temperature < 20 (values: 16, 15)")
print("  ✅ Alert OFF when temperature >= 20 (value: 25)")
print("  ✅ Notification created each time alert triggers")
print()
