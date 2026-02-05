#!/usr/bin/env python3
"""Test config flow locally to reproduce translation error"""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))
sys.path.insert(0, str(Path(__file__).parent))

from mock_ha.ha_core import create_mock_hass

async def test_group_options_translation():
    """Test that group_options provides all required translation placeholders"""
    print("Testing group_options translation placeholders...")
    
    hass = create_mock_hass()
    
    # Import after hass is set up
    from emergency_alerts.config_flow import EmergencyOptionsFlow
    
    # Create a mock config entry for a group hub
    class MockConfigEntry:
        def __init__(self):
            self.entry_id = "test_group_hub"
            self.data = {
                "hub_type": "group",
                "group": "Test Group",
                "alerts": {
                    "test_alert": {
                        "name": "Test Alert",
                        "trigger_type": "simple"
                    }
                }
            }
            self.options = {
                "notification_profiles": {
                    "profile1": {
                        "name": "Test Profile"
                    }
                }
            }
    
    # Create options flow
    options_flow = EmergencyOptionsFlow()
    options_flow.hass = hass
    options_flow.config_entry = MockConfigEntry()
    
    # Call async_step_init (this is what HA does)
    print("\nCalling async_step_init(None)...")
    result = await options_flow.async_step_init(None)
    
    print(f"\nResult type: {result.get('type')}")
    print(f"Step ID: {result.get('step_id')}")
    print(f"Description placeholders: {result.get('description_placeholders')}")
    
    # Check if all required placeholders are present
    placeholders = result.get('description_placeholders', {})
    required = {'group_name', 'alert_count'}
    
    missing = required - set(placeholders.keys())
    if missing:
        print(f"\nERROR: Missing required placeholders: {missing}")
        return False
    else:
        print(f"\nSUCCESS: All required placeholders provided")
        print(f"  group_name: {placeholders.get('group_name')}")
        print(f"  alert_count: {placeholders.get('alert_count')}")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_group_options_translation())
    sys.exit(0 if success else 1)