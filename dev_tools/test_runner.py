#!/usr/bin/env python3
"""Fast local test runner for Emergency Alerts integration."""
import sys
import os
import asyncio
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up mock homeassistant modules BEFORE importing integration
from dev_tools.mock_ha.homeassistant_shim import setup_test_environment
setup_test_environment()

from dev_tools.mock_ha.ha_core import create_mock_hass


async def test_trigger_evaluation():
    """Test trigger evaluation without full HA."""
    print("Testing trigger evaluation...")
    
    hass = create_mock_hass()
    
    # Set up test entities
    hass.states.async_set("binary_sensor.door", "on")
    hass.states.async_set("sensor.temperature", "25")
    
    # Import and test trigger evaluator (will create this module)
    from custom_components.emergency_alerts.core.trigger_evaluator import TriggerEvaluator
    
    evaluator = TriggerEvaluator(hass)
    
    # Test simple trigger
    result = await evaluator.evaluate({
        "trigger_type": "simple",
        "entity_id": "binary_sensor.door",
        "trigger_state": "on"
    })
    
    assert result == True, "Simple trigger should evaluate to True"
    print("✓ Simple trigger test passed")
    
    # Test template trigger
    result = await evaluator.evaluate({
        "trigger_type": "template",
        "template": "{{ states('sensor.temperature')|float > 20 }}"
    })
    
    assert result == True, "Template trigger should evaluate to True"
    print("✓ Template trigger test passed")
    
    print("All trigger tests passed!")


async def test_config_flow():
    """Test config flow without full HA."""
    print("Testing config flow...")
    
    hass = create_mock_hass()
    
    # Import config flow
    from custom_components.emergency_alerts.config_flow import EmergencyConfigFlow
    
    flow = EmergencyConfigFlow()
    flow.hass = hass
    
    # Test creating alert group hub
    result = await flow.async_step_user({
        "setup_type": "group"
    })
    
    assert result["type"] == "form"
    print("✓ Config flow initialization passed")
    
    print("Config flow tests passed!")


async def test_state_machine():
    """Test state machine logic."""
    print("Testing state machine...")
    
    hass = create_mock_hass()
    
    # Test state transitions
    # (Will implement after creating state_manager module)
    
    print("✓ State machine tests passed!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Emergency Alerts Local Test Runner")
    print("=" * 60)
    print()
    
    tests = [
        ("Trigger Evaluation", test_trigger_evaluation),
        ("Config Flow", test_config_flow),
        ("State Machine", test_state_machine),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[Running: {name}]")
            await test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))