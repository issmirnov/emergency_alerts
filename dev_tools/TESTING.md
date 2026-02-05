# Testing Guide

## Local Development Testing

### Quick Start
```bash
# Start HA instance
./dev_tools/local-dev.sh start

# Open browser
http://localhost:8123

# Create user account (first time only)
# Then: Settings > Devices & Services > Add Integration > Emergency Alerts
```

### What to Test

1. **Config Flow**
   - Add Emergency Alerts integration
   - Create an alert group
   - Verify NO translation errors appear
   - Check logs for [DEBUG] and [MIGRATION] messages

2. **Translation Validation**
   - The group_options screen should show: "Manage [Group Name] Alerts"
   - NOT show: translation error about missing group_name variable

3. **Alert Creation**
   - Use unified single-page form for simple/template triggers
   - Test logical trigger wizard
   - Verify autocomplete works for entities

### Check Logs
```bash
./dev_tools/local-dev.sh logs | grep emergency_alerts
```

### Look For
- `[DEBUG] Setting up entry:` - shows entry.data structure
- `[MIGRATION] Entry 'X' missing 'group' field` - migration ran
- NO translation errors

## Production HA Fix

If your production HA has the translation error:

### Method 1: Delete and Re-add (Recommended)
1. Settings > Devices & Services
2. Remove Emergency Alerts integration completely
3. Restart HA
4. Re-add Emergency Alerts integration
5. This creates a FRESH config entry with correct structure

### Method 2: Storage File Fix
Run `dev_tools/fix_production_storage.py` (see script for details)

## Test Results

Local tests: ALL PASS
- Import validation: PASS
- Trigger evaluation: PASS  
- Config flow: PASS
- State machine: PASS

Code verification: CORRECT
- Line 469: group_name provided in description_placeholders
- Migration logic: present in __init__.py
- Debug logging: enabled