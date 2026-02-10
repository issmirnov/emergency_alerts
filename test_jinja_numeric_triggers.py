#!/usr/bin/env python3
"""
Test Jinja2 template numeric triggers to verify they work correctly.
This tests the logic used in binary_sensor.py for template-based alerts.
"""
from jinja2 import Template

def test_numeric_comparison_templates():
    """Test that Jinja templates correctly evaluate numeric comparisons."""

    # Simulate what Home Assistant does - create a mock states() function
    test_states = {
        'sensor.test_temperature': '16',
        'sensor.test_temperature_high': '25',
    }

    def states(entity_id):
        """Mock states() function"""
        return test_states.get(entity_id, 'unknown')

    # Test cases matching our alert configuration
    test_cases = [
        {
            'name': 'Temperature Below 20 (16 < 20)',
            'template': "{{ states('sensor.test_temperature') | float < 20 }}",
            'expected': True,
            'description': 'Should trigger when temp is 16'
        },
        {
            'name': 'Temperature Above 20 (25 > 20)',
            'template': "{{ states('sensor.test_temperature_high') | float > 20 }}",
            'expected': True,
            'description': 'Should trigger when temp is 25'
        },
        {
            'name': 'Temperature Equals 16 (16 == 16)',
            'template': "{{ states('sensor.test_temperature') | float == 16 }}",
            'expected': True,
            'description': 'Should trigger when temp equals 16'
        },
        {
            'name': 'Temperature Below 10 (16 < 10)',
            'template': "{{ states('sensor.test_temperature') | float < 10 }}",
            'expected': False,
            'description': 'Should NOT trigger when temp is 16'
        },
    ]

    print("=" * 70)
    print("Testing Jinja2 Template Numeric Triggers")
    print("=" * 70)

    passed = 0
    failed = 0

    for test in test_cases:
        # Create Jinja2 template
        tpl = Template(test['template'])

        # Render with our mock states function
        try:
            result = tpl.render(states=states, float=float)

            # Convert result to boolean (same logic as binary_sensor.py:419)
            triggered = result in (True, "True", "true", 1, "1")

            # Check if it matches expected
            status = "✅ PASS" if triggered == test['expected'] else "❌ FAIL"
            if triggered == test['expected']:
                passed += 1
            else:
                failed += 1

            print(f"\n{status}: {test['name']}")
            print(f"  Template: {test['template']}")
            print(f"  Expected: {test['expected']}, Got: {triggered}")
            print(f"  Raw result: {result} (type: {type(result).__name__})")
            print(f"  Description: {test['description']}")

        except Exception as e:
            failed += 1
            print(f"\n❌ ERROR: {test['name']}")
            print(f"  Template: {test['template']}")
            print(f"  Error: {e}")

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0

if __name__ == '__main__':
    success = test_numeric_comparison_templates()
    exit(0 if success else 1)
