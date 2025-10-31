# Active Context

> **Synthesizes**: productContext.md, systemPatterns.md, techContext.md
> **Purpose**: Documents current work focus and immediate next steps
> **Update Frequency**: Very frequently - after every significant change

## Current Focus

**Phase: Bug Fix Complete - Ready for Release (2025-10-31)**

Successfully fixed and verified critical bug in Lovelace card where button clicks weren't updating alert states.

**COMPLETED WORK (2025-10-30 to 2025-10-31)**:
1. ✅ Identified root cause: _convertToSwitchId() not stripping "emergency_" prefix
2. ✅ Fixed bug in lovelace-emergency-alerts-card/src/services/alert-service.ts:37-46
3. ✅ Updated all unit tests to match new behavior (90/90 tests passing)
4. ✅ Built updated card with npm run build
5. ✅ Created build-and-deploy.sh helper script for future deploys
6. ✅ Deployed to HA container (config/www/emergency-alerts-card.js)
7. ✅ Solved browser caching with query parameter: `?v=2.0.3-bugfix`
8. ✅ Manually verified button clicks work correctly
9. ✅ Documented E2E testing insights from external LLM
10. ✅ Committed and pushed both repos

**Status**: ✅ BUG FIXED AND VERIFIED - Ready for release as v2.0.3

**Previous Phase Complete**: E2E Testing Infrastructure (2025-10-30)

**Previous Phase Complete**: v2.0 State Machine Redesign with notification profiles (2025-10-29)

## Recent Changes

### 2025-10-30: Lovelace Card Button Click Bug Fix (CRITICAL)
- **Changed**: Fixed _convertToSwitchId() in alert-service.ts to strip "emergency_" prefix
- **Why**: Button clicks (acknowledge/snooze/resolve) were calling wrong entity IDs, causing state updates to fail
- **Bug Details**:
  - Binary sensors: `binary_sensor.emergency_critical_test_alert`
  - Old code generated: `switch.emergency_critical_test_alert_acknowledged` ❌
  - Actual switch entities: `switch.critical_test_alert_acknowledged` ✅
  - Root cause: Integration creates switches WITHOUT "emergency_" prefix
- **Files**:
  - lovelace-emergency-alerts-card/src/services/alert-service.ts:37-46 (added prefix stripping)
  - lovelace-emergency-alerts-card/build-and-deploy.sh (new helper script)
  - lovelace-emergency-alerts-card/dist/emergency-alerts-card.js (rebuilt)
  - emergency-alerts-integration/config/www/emergency-alerts-card.js (deployed)
- **Status**: ✅ Fix complete and deployed, ⚠️ Browser cache issue preventing verification
- **Testing**: User manually clicked buttons, confirmed state not updating (browser loading old JS)

### 2025-10-30: E2E Testing Infrastructure (MAJOR)
- **Changed**: Built comprehensive Playwright-based E2E testing infrastructure
- **Why**: No automated way to test integration + card working together, required manual testing
- **Impact**: LLM-debuggable testing with filesystem access, screenshots, and browser inspection
- **Files**:
  - e2e-tests/: Complete test infrastructure (~1900 lines, 16 files)
  - e2e-tests/tests/01-smoke.spec.ts: Basic functionality tests
  - e2e-tests/tests/02-integration.spec.ts: Integration tests (switches, mutual exclusivity)
  - e2e-tests/helpers/ha-api.ts: Typed Home Assistant REST API client
  - e2e-tests/helpers/alert-helpers.ts: Alert-specific test helpers
  - e2e-tests/helpers/global-setup.ts: Pre-test environment validation
  - e2e-tests/helpers/global-teardown.ts: Post-test cleanup
  - e2e-tests/playwright.config.ts: Playwright config with LLM debugging features
  - e2e-tests/package.json: Dependencies and test scripts
  - e2e-tests/README.md: Comprehensive testing documentation
  - e2e-tests/README-LLM-DEBUGGING.md: LLM debugging guide
  - e2e-tests/.gitignore: Test artifact exclusions
  - docker-compose.yml: Docker Compose setup for HA testing
  - scripts/bypass-onboarding.sh: Automated HA onboarding bypass (dev/dev credentials)
  - scripts/run-e2e.sh: E2E test runner with environment checks
  - .devcontainer/devcontainer.json: Simplified all-in-one devcontainer config
  - .devcontainer/setup.sh: Updated with Node.js and Playwright installation
- **Features**:
  - Playwright with TypeScript for browser automation
  - Chrome DevTools Protocol (CDP) on port 9222 for deep inspection
  - Automatic screenshots, videos, and traces on test failure
  - Home Assistant REST API client with type safety
  - Alert-specific helpers (acknowledgeAlert, snoozeAlert, resolveAlert, etc.)
  - Global setup validates HA running, integration loaded, card available
  - Smoke tests verify basic functionality
  - Integration tests verify switch clicks → backend updates, mutual exclusivity
  - LLM debugging guide with CLI commands for inspection
  - Docker Compose for reproducible HA environment
  - Onboarding bypass script creates default admin user (username: dev, password: dev)
  - Run script with environment checks and helpful error messages

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

### Immediate (Current Session) - E2E Testing ✅
- [x] Build E2E testing infrastructure (~1900 lines, 16 files)
- [x] Create Playwright test suite (smoke + integration tests)
- [x] Build LLM debugging infrastructure (screenshots, traces, CDP)
- [x] Create HA API client with type safety
- [x] Create alert-specific test helpers
- [x] Fix devcontainer.json for Cursor compatibility
- [x] Create docker-compose.yml for HA testing
- [x] Build onboarding bypass script (dev/dev credentials)
- [x] Successfully start Home Assistant in Docker with integration

### Immediate Next (Current Session) - Lovelace Card Testing
- [x] Identify root cause of button click failures
- [x] Fix _convertToSwitchId() bug in alert-service.ts
- [x] Build and deploy updated card
- [x] Restart HA container to clear cache
- [ ] **Clear browser cache to load updated JavaScript** - Critical blocker
- [ ] **Verify button clicks update alert states** - Manual or automated testing
- [ ] **Test all three button types** - Acknowledge, snooze, resolve
- [ ] **Update card version** - Bump to v2.0.3 after verification
- [ ] **Document fix in card changelog** - Update lovelace card repo

### Short Term (After Card Fix)
- [ ] **Run E2E tests with Playwright MCP** - Execute smoke tests and integration tests
- [ ] **Demonstrate LLM debugging** - Use screenshots, API inspection, log analysis
- [ ] **Fix any test failures** - Debug using LLM-friendly artifacts
- [ ] **Document test results** - Update memory bank with findings
- [ ] **Create CI/CD workflow** - Automate E2E tests in GitHub Actions

### Short Term (Next Few Sessions)
- [ ] Review backend test suite (35/35 passing after teardown fix)
- [ ] Verify integration test coverage is >90%
- [ ] Create PR for E2E testing infrastructure on cicd branch
- [ ] Update HACS metadata if needed
- [ ] Clean up any remaining legacy code paths

### Future Considerations
- [ ] Add area integration (tie alerts to HA areas)
- [ ] Expand blueprint library based on user feedback
- [ ] Consider alert history/statistics tracking
- [ ] Evaluate advanced escalation policies
- [ ] Multi-language support (infrastructure exists, needs translations)

### Blocked/Waiting
- [ ] HACS listing approval - **Blocked by**: Need to submit to HACS store
- [ ] User feedback collection - **Blocked by**: Need wider distribution

## Lessons Learned (2025-10-31 Bug Fix Session)

### What Worked Brilliantly ✅

1. **Cache-Busting Query Parameters**: Standard HA pattern solved browser caching instantly
   - Added `?v=2.0.3-bugfix` to resource URL in configuration.yaml
   - Browser treated it as completely new file
   - **Lesson**: Always use query params for HA frontend development

2. **Systematic Debugging**: Root cause identified through console interceptors
   - Wrapped alertService methods with logging
   - Traced exact entity IDs being generated vs actual entity IDs
   - **Lesson**: Console interceptors are invaluable for frontend debugging

3. **Docker Development Stack**: Environment worked perfectly
   - Volume mounts correct
   - Integration loaded properly
   - Card deployment working
   - **Lesson**: Docker Compose setup is solid, keep using it

4. **Build Pipeline**: npm + build-and-deploy.sh script efficient
   - `npm run build` → `build-and-deploy.sh` → restart HA
   - **Lesson**: Helper scripts save time and reduce errors

### What Didn't Work ❌

1. **Hard Refresh for Cache Clearing**: Insufficient for JavaScript modules
   - Ctrl+Shift+R didn't clear cache
   - Container restart didn't help
   - **Lesson**: Modern browsers cache aggressively, need query params

2. **Playwright Shadow DOM Traversal**: Cannot access HA's nested shadow DOM
   - partial-panel-resolver lacks accessible shadowRoot
   - Cannot automate button clicks
   - **Lesson**: Manual testing required for HA Lovelace cards, or use specialized tools

3. **Going in Circles**: Spent time on wrong problem (automation vs caching)
   - Tried to automate testing when caching was the real issue
   - **Lesson**: Identify the actual blocker first, don't over-engineer

### Key Technical Insights 🔍

1. **Integration Entity Naming**: Backend strips "emergency_" prefix from switch entity IDs
   - Binary sensors: `binary_sensor.emergency_*`
   - Switches: `switch.*_acknowledged` (NO emergency_ prefix)
   - **Root cause of bug**

2. **Browser Caching Layers**: Multiple cache levels to consider
   - Browser HTTP cache
   - Service worker cache
   - Query parameters bypass all of them
   - **Solution for HA dev**

3. **Testing Strategy**: E2E testing for HA cards requires different approach
   - Playwright limited for shadow DOM
   - hass-taste-test mentioned in external LLM notes as specialized tool
   - Manual testing still valuable and often faster
   - **Hybrid approach best**

### Process Improvements 📝

1. **Memory Bank System**: Extremely effective for context preservation
   - External LLM notes integrated via e2e-testing-notes.md
   - Active context tracking prevented re-work
   - **Keep using aggressively**

2. **Commit Frequency**: Regular commits with detailed messages helpful
   - Committed after fix, after tests, after config changes
   - Easy to track progress
   - **Best practice**

3. **Planning Mode**: Helped break "going in circles" pattern
   - Forced analysis of actual problem
   - Simplified solution emerged
   - **Use when stuck**

### Resolved Challenges ✅

- **Browser Cache Issues**: SOLVED with query parameter approach
- **Playwright Shadow DOM Access**: ACCEPTED limitation, use manual testing
- **Button Click Bug**: FIXED by stripping "emergency_" prefix in _convertToSwitchId()

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
