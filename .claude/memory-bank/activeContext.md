# Active Context

> **Synthesizes**: productContext.md, systemPatterns.md, techContext.md
> **Purpose**: Documents current work focus and immediate next steps
> **Update Frequency**: Very frequently - after every significant change

## Current Focus

**Phase: v2.0 State Machine Redesign - COMPLETE (2025-10-29)**

Completed major architectural redesign from button-based to switch-based state machine. Integration now provides rich, visible state management with mutual exclusivity and auto-expiring snooze functionality.

Recent work completed:
1. ✅ Complete switch-based state machine implementation (switch.py - 433 lines)
2. ✅ Removed button platform, added 3 switch types per alert
3. ✅ Enhanced binary sensor with state tracking and dispatcher integration
4. ✅ Added comprehensive test suite for switches (15+ tests)
5. ✅ Created frontend integration guide (cardInstructions.md)
6. ✅ Created notification examples with 12 configurations
7. ✅ Updated memory bank with v2.0 architecture

**Current**: v2.0 State Machine Redesign FULLY COMPLETE with notification profiles (2025-10-29)

## Recent Changes

### 2025-10-29: Notification Profiles System (v2.0 Feature)
- **Changed**: Added reusable notification profiles in Global Settings Hub
- **Why**: Reduce duplication, enable consistent notification patterns across alerts
- **Impact**: Users can define notification profiles once and reference them in multiple alerts
- **Files**:
  - config_flow.py: Added profile management UI (add/edit/remove profiles)
  - config_flow.py: Updated alert actions to support "profile:profile_id" references
  - config_flow.py: Added _extract_value_from_actions helper for profile/script extraction
  - binary_sensor.py: Added _resolve_profile() method to lookup profile actions
  - binary_sensor.py: Updated _execute_action() to resolve profile references
  - binary_sensor.py: Updated _call_actions() to resolve profile references
  - manifest.json: Version bumped to 2.0.0
- **Features**:
  - Create named profiles with up to 5 service calls
  - Edit existing profiles
  - Remove unused profiles
  - Reference profiles in alert actions using "profile:profile_id" syntax
  - Profiles stored in Global Settings Hub options
  - Automatic resolution when actions execute

### 2025-10-29: v2.0 State Machine Redesign (MAJOR)
- **Changed**: Complete redesign from buttons to switches with rich state machine
- **Why**: Button-based interaction hid state and created UX confusion
- **Impact**: Users now have visible, toggleable state with mutual exclusivity
- **Files**:
  - const.py: Added 20+ new constants for states, switches, exclusion rules
  - switch.py: 433 lines - 3 switch types (acknowledge, snooze, resolve)
  - binary_sensor.py: Enhanced with state tracking, dispatcher integration
  - button.py: REMOVED (breaking change)
  - tests/test_switch.py: Comprehensive test suite (15+ tests)
  - .claude/memory-bank/cardInstructions.md: Frontend integration guide
  - .claude/memory-bank/notificationExamples.md: 12 example configurations

### 2025-10-29: Memory Bank Establishment
- **Changed**: Added .claude/memory-bank/ system
- **Why**: Enable persistent context across AI sessions
- **Impact**: Full project context available for all future work

### 2025-01-22: Visual Condition Builder
- **Changed**: Replaced JSON input with visual form builder for logical triggers
- **Why**: JSON syntax was error-prone and difficult for non-technical users
- **Impact**: Logical triggers now accessible to all users, significantly better UX
- **Files**:
  - custom_components/emergency_alerts/config_flow.py:339-400
  - custom_components/emergency_alerts/binary_sensor.py:344-362
  - custom_components/emergency_alerts/strings.json:140-160

### Recent Commits (Last 20):
- d89b5a6: add memory bank
- 81c3beb: Update README.md
- 2e13d71: defensive coding
- 8094372: cleanup legacy
- 5a8c8a9: various fixes
- bfea13b: various fixes
- 9f22806: clean up runtime errors for alert trigger

## Active Decisions

### Decision in Progress: Notification Profile Implementation
- **Question**: How complex should notification profiles be?
- **Options**:
  1. **Simple** - Just named groups of service calls
  2. **Advanced** - Include variables, templating, conditional logic
  3. **Hybrid** - Start simple, add features later
- **Leaning Towards**: Hybrid - simple named profiles first
- **Status**: In implementation

### Recently Resolved Decisions

#### Switch Platform Implementation ✅
- **Decision**: Complete rewrite with 3 switch types
- **Result**: acknowledge, snooze (auto-expiring), resolve implemented
- **Impact**: Major UX improvement, visible state management

#### Button Platform Removal ✅
- **Decision**: Clean break, no backward compatibility
- **Result**: Removed button.py entirely
- **Impact**: Breaking change for v2.0, requires user migration

## Next Steps

### Immediate (Current Session) - COMPLETE ✅
- [x] Complete v2.0 state machine redesign
- [x] Implement switch platform (433 lines)
- [x] Update binary_sensor.py integration
- [x] Create comprehensive test suite
- [x] Write frontend integration guide
- [x] Create notification examples
- [x] Update memory bank documentation
- [x] Implement notification profiles (COMPLETE)
- [x] Update alert action config for profiles (COMPLETE)
- [x] Update binary_sensor to resolve profiles (COMPLETE)
- [x] Version bump to 2.0.0 (COMPLETE)

### Short Term (Next Few Sessions)
- [ ] Review and address any defensive coding improvements needed
- [ ] Verify test coverage is still >90%
- [ ] Consider removing switch.py if truly unused
- [ ] Clean up any remaining legacy code paths
- [ ] Update HACS metadata if needed

### Future Considerations
- [ ] Add area integration (tie alerts to HA areas)
- [ ] Expand blueprint library based on user feedback
- [ ] Consider alert history/statistics tracking
- [ ] Evaluate advanced escalation policies
- [ ] Multi-language support (infrastructure exists, needs translations)

### Blocked/Waiting
- [ ] HACS listing approval - **Blocked by**: Need to submit to HACS store
- [ ] User feedback collection - **Blocked by**: Need wider distribution

## Current Challenges

- **Testing Runtime Behavior**: Some issues only appear in full Home Assistant runtime, not in pytest
  - **Approach**: Using devcontainer for live testing, diagnostics.py for debugging

- **Balancing Features vs Simplicity**: Temptation to add more features vs keeping integration focused
  - **Approach**: Deferring non-critical features, focusing on stability and core experience

- **Documentation Drift**: Multiple doc files (README, ARCHITECTURE, cursor.context.md) can get out of sync
  - **Approach**: Memory bank now serves as canonical source, other docs reference it

## Open Questions

- Should global settings hub be more integrated with alert groups? Currently underutilized
- Is the hub architecture clear to users, or does it need better onboarding docs/tutorial?
- What's the migration path for users who installed during pre-hub era?
- Should we provide UI for viewing alert history, or rely on HA's history integration?

## Recently Resolved

- **Button-based state confusion (v2.0)** - **Solution**: Complete redesign to switch-based state machine with mutual exclusivity
- **Snooze timing persistence (v2.0)** - **Solution**: Store snooze_until timestamp, survives HA restarts
- **Visual condition builder complexity** - **Solution**: Implemented form-based interface with dynamic entity/state pairs (2025-01-22)
- **Config entry reload timing** - **Solution**: Call async_reload immediately after updating config entry data for instant entity creation
- **Status sensor duplication** - **Solution**: Check entity registry before creating companion status sensors
- **Legacy hub-per-alert problem** - **Solution**: Complete architecture restructure to two-tier hub system (Phase 3)

## Context Notes

### AI Development Approach
This project is intentionally developed with heavy AI assistance (Claude/Cursor). The maintainer has limited deep knowledge of the codebase, which makes memory bank critical for continuity. AI sessions should:
1. Always read memory bank first
2. Reference memory bank files for context
3. Update memory bank after significant changes
4. Use defensive coding patterns due to limited human oversight

### Testing Philosophy
- Maintain >90% coverage
- Focus on critical paths (alert evaluation, state transitions)
- Use pytest for unit/integration tests
- Manual testing in devcontainer for runtime behavior
- Diagnostics available for troubleshooting user issues

### Code Quality Standards
- Follow Home Assistant best practices
- Use defensive coding (extensive error handling)
- Log errors but don't crash HA
- Validate all user inputs
- No external dependencies

### User Communication
- Be transparent about AI-assisted development
- Encourage community contributions
- Provide clear, helpful error messages
- Document decisions and rationale
- Maintain detailed changelog (cursor.context.md)

### Current Project Health
- ✅ Core features complete
- ✅ Tests passing
- ✅ HACS validation passing
- ✅ No known critical bugs
- ✅ Documentation updated
- ⏳ Awaiting wider user feedback
- ⏳ Monitoring for edge cases in real-world usage
