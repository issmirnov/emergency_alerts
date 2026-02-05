# Changelog

All notable changes to the Emergency Alerts integration will be documented in this file.

## [4.0.0] - 2026-02-04

### Major Changes - State Machine Simplification

**BREAKING CHANGE**: Replaced 3 switches per alert with 1 select entity for unified state control.

#### Migration Guide
- Old: `switch.{alert_name}_acknowledged`, `switch.{alert_name}_snoozed`, `switch.{alert_name}_resolved`
- New: `select.{alert_name}_state` with options: `active`, `acknowledged`, `snoozed`, `resolved`

**What you need to do:**
1. Update automations referencing the old switches to use the new select entity
2. Change from `switch.turn_on` to `select.select_option` service calls
3. Example: `service: select.select_option` with `data: { entity_id: select.door_alert_state, option: acknowledged }`

#### Benefits
- 67% fewer entities (1 vs 3 per alert)
- Cleaner UI (single dropdown instead of 3 toggles)
- Simpler state management
- Better follows Home Assistant 2026.2 patterns

### Added
- New `select` platform for unified alert state control
- Automatic state syncing with binary sensor
- All existing events and actions preserved

### Changed
- Replaced `switch` platform with `select` platform
- State transitions now use select options instead of switch toggles

### Deprecated
- `switch.py` is deprecated and will be removed in v5.0.0
- Users should migrate to the new select entity

---

## [3.0.3] - 2026-02-04

### Fixed
- Added auto-migration for old config entries missing 'group' field
- Fixed translation error: 'group_name was not provided'
- Added debug logging for config entry diagnostics

### Added
- Local Docker-based development environment
- Development testing framework with mock HA
- Translation audit tool
- Import validation tests

---

## [3.0.2] - 2026-02-04

### Fixed
- Translation placeholder errors in config flow
- Added missing `group_name` to description_placeholders

---

## [3.0.1] - 2026-02-04

### Fixed
- ImportError for removed TRIGGER_TYPE_COMBINED constant

---

## [3.0.0] - 2026-02-04

### Major Changes - Config Flow Simplification

**Removed Global Settings Hub** - No longer required, simplifies setup significantly

#### Added
- Unified single-page alert creation form
- Smart form that adapts based on trigger type
- Entity autocomplete for better UX
- Notification profiles at group level
- Modular trigger evaluator and action executor
- Comprehensive local testing framework

#### Changed
- Config flow now goes directly to alert group creation
- Simplified alert creation: single form for simple/template triggers
- Logical triggers use multi-step wizard
- Removed "combined" trigger type (superseded by logical)

#### Improved
- Better entity selector with autocomplete
- Profile management at group level
- Cleaner code organization with core/ modules
- Comprehensive testing infrastructure

---

## [2.x.x] - Previous Versions

See git history for older versions