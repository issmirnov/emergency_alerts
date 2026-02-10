# Active Context

> **Last Updated**: 2026-02-09
> **Current Focus**: V4 Release - Simplified Architecture Complete

## Current Sprint: V4.0 Release Preparation

### Completed Work

**Testing Infrastructure (2026-02-09)**
- ✅ Added hassfest validation to CI
- ✅ Created `validate_translations.py` - syncs strings.json ↔ translations/en.json
- ✅ Fixed 40+ translation mismatches
- ✅ Added pytest fixture for auto-detecting translation errors
- ✅ Created E2E test for config flow (03-config-flow-add-alert.spec.ts)
- ✅ Comprehensive testing docs in docs/TESTING.md
- ✅ Updated to HA 2026.2 in docker-compose

**Config Flow Simplification (2026-02-09)**
- ✅ Redesigned to single-page form (Adaptive Lighting pattern)
- ✅ Reduced code: 1,371 → 245 lines (82% reduction)
- ✅ All alert options visible on one scrollable page
- ✅ Modern selectors (EntitySelector, TemplateSelector)
- ✅ Fixed HA 2026.2 compatibility issues
- ✅ Successfully tested creating alerts via UI

**Card V4 Update (2026-02-09)**
- ✅ Updated Lovelace card to use select entities (v4 architecture)
- ✅ Changed from switch.toggle → select.select_option
- ✅ All 90 tests passing
- ✅ Fixed cache-busting with ?v=4.0.0 parameter

**Automated Development Environment (2026-02-09)**
- ✅ Updated local-dev.sh with automated setup
- ✅ Trusted network auth bypass for localhost
- ✅ Auto-creates sun integration + 2 test alerts on start
- ✅ Registers dashboard and card resources automatically
- ✅ Notification test script pre-configured

### Architecture Changes

**V4 Simplifications:**
1. **Config Flow**: Multi-step wizard → Single-page unified form
2. **Card**: Switch-based controls → Select entity controls
3. **Testing**: Ad-hoc → Comprehensive (hassfest + pytest + E2E + translation validation)

### Key Learnings

**HA Caching Issues:**
- Service Worker caching is extremely aggressive
- MUST use version parameters for resources: `?v=4.0.0`
- Hard refresh alone isn't enough - need to clear service worker
- Incognito mode is best for quick testing during development
- Always increment version param when updating card JavaScript

**HA 2026.2 Compatibility:**
- OptionsFlow `config_entry` is now a read-only property
- Cannot set in `__init__` - parent class handles it automatically
- Must remove custom `__init__` from OptionsFlow subclasses
- `async_show_menu` doesn't support `description_placeholders` - use `async_show_form` instead

**Testing Best Practices:**
- Keep strings.json and translations/en.json in perfect sync
- Run `python validate_translations.py` before every commit
- Use hassfest for integration structure validation
- Pytest for unit/integration tests
- Minimal E2E tests for critical user flows only
- Docker Compose for manual testing with latest HA version

**Config Flow UX:**
- Single-page forms > Multi-step wizards
- Show all options at once (Adaptive Lighting pattern)
- Use modern selectors for better UX
- Optional fields should truly be optional (no empty string defaults)

## Current Status

**Branch:** `tests`

**Ready for PR:**
- All changes committed
- Tests passing
- Config flow working in HA 2026.2
- Card updated to v4
- Automated setup complete

**Next Steps:**
1. Test notification script (trigger on state change)
2. Test snooze mechanism via card buttons
3. Update memory bank ✓
4. Create PR to main for v4.0 release

## Active Files

**Modified Recently:**
- `.github/workflows/test.yml` - Added hassfest + translation validation
- `custom_components/emergency_alerts/config_flow.py` - Complete rewrite (245 lines)
- `custom_components/emergency_alerts/const.py` - Added hub config constants
- `custom_components/emergency_alerts/translations/en.json` - Synced with strings.json
- `custom_components/emergency_alerts/tests/conftest.py` - Translation error detection
- `validate_translations.py` - New validation script
- `docs/TESTING.md` - Complete testing guide
- `dev_tools/local-dev.sh` - Automated setup function
- `dev_tools/ha-config/configuration.yaml` - Trusted auth + dashboard config
- `docker-compose.yml` - Updated to HA 2026.2
- `../lovelace-emergency-alerts-card/src/services/alert-service.ts` - V4 select-based controls

## Known Issues

None! V4 is working cleanly.

## Testing Status

**What Works:**
- ✅ Translation validation
- ✅ Config flow (single-page form)
- ✅ Alert creation via UI
- ✅ Entities created correctly
- ✅ Card buttons (acknowledge/snooze/resolve with select entities)

**Needs Testing:**
- ⏳ Notification script on trigger (requires state transition)
- ⏳ Snooze auto-expiry mechanism
- ⏳ Full E2E flow with state changes

## Notes for Next Session

- Remember to always use `?v=X.X.X` for card resources
- Incognito mode for testing card changes
- Translation sync is critical - run validator before commits
- HA 2026.2+ required - always specify version in docker-compose
