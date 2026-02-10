#!/bin/bash
# Live end-to-end test for Jinja numeric triggers

set -e

echo "=== LIVE TEST: Jinja Numeric Triggers ==="
echo ""

echo "Step 1: Check temperature sensor value"
docker exec ha-dev curl -s http://localhost:8123/api/states/input_number.test_temperature 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  Temperature: {data[\"state\"]}°C')
except Exception as e:
    print(f'  Error: {e}')
"
echo ""

echo "Step 2: Check alert state (should be ON since 16 < 20)"
docker exec ha-dev curl -s http://localhost:8123/api/states/binary_sensor.emergency_temperature_below_20 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    state = data['state']
    template = data['attributes'].get('template', 'N/A')
    print(f'  Alert State: {state.upper()}')
    print(f'  Template: {template}')
    if state == 'on':
        print('  ✅ PASS: Alert triggered correctly (16 < 20)')
    else:
        print('  ❌ FAIL: Alert should be ON')
except Exception as e:
    print(f'  Error: {e}')
"
echo ""

echo "Step 3: Change temperature to 25 (above threshold)"
docker exec ha-dev curl -s -X POST http://localhost:8123/api/services/input_number/set_value \
  -H 'Content-Type: application/json' \
  -d '{"entity_id": "input_number.test_temperature", "value": 25}' 2>/dev/null > /dev/null
echo "  ✓ Temperature changed to 25°C"
sleep 3
echo ""

echo "Step 4: Check alert state (should be OFF since 25 >= 20)"
docker exec ha-dev curl -s http://localhost:8123/api/states/binary_sensor.emergency_temperature_below_20 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    state = data['state']
    print(f'  Alert State: {state.upper()}')
    if state == 'off':
        print('  ✅ PASS: Alert cleared correctly (25 >= 20)')
    else:
        print('  ❌ FAIL: Alert should be OFF')
except Exception as e:
    print(f'  Error: {e}')
"
echo ""

echo "Step 5: Change temperature to 10 (below threshold)"
docker exec ha-dev curl -s -X POST http://localhost:8123/api/services/input_number/set_value \
  -H 'Content-Type: application/json' \
  -d '{"entity_id": "input_number.test_temperature", "value": 10}' 2>/dev/null > /dev/null
echo "  ✓ Temperature changed to 10°C"
sleep 3
echo ""

echo "Step 6: Check alert state (should be ON again since 10 < 20)"
docker exec ha-dev curl -s http://localhost:8123/api/states/binary_sensor.emergency_temperature_below_20 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    state = data['state']
    print(f'  Alert State: {state.upper()}')
    if state == 'on':
        print('  ✅ PASS: Alert triggered again correctly (10 < 20)')
    else:
        print('  ❌ FAIL: Alert should be ON')
except Exception as e:
    print(f'  Error: {e}')
"
echo ""

echo "=== TEST COMPLETE ==="
