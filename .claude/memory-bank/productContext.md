# Product Context

> **Derived from**: projectbrief.md
> **Purpose**: Explains why this project exists and what user value it provides

## Problem Statement
### Current Situation
Home Assistant users need to monitor critical conditions (door left open, water leaks, security breaches, etc.) but lack a unified, user-friendly system for managing these alerts. Current options require:
- Complex YAML automations for each alert condition
- Custom template sensors for status tracking
- Manual organization across multiple unrelated entities
- Technical expertise to set up and maintain

### Pain Points
- **YAML Complexity**: Creating alert logic requires writing and maintaining YAML automations
- **Poor Organization**: Alerts scattered across entity registry with no grouping mechanism
- **Limited Status Tracking**: No built-in way to track alert acknowledgment, escalation, or lifecycle
- **Difficult Management**: No UI for editing alert configurations - must edit YAML files
- **Fragmented Actions**: Acknowledgment and clearing require custom scripts/automations
- **No Hierarchy**: Flat entity structure makes it hard to find and manage related alerts

### Impact
Users either:
1. Avoid creating comprehensive alert systems due to complexity
2. Build brittle, unmaintainable YAML automations
3. Spend excessive time managing alert configurations
4. Miss critical events due to alert fatigue from poor organization

This affects home security, safety monitoring, and peace of mind for users relying on Home Assistant for critical monitoring.

## Solution Overview
### Our Approach
Provide a **hub-based integration** with **UI-driven configuration** that makes alert management as easy as filling out forms:

1. **Hub Organization**: Separate global settings from alert groups, allowing users to organize alerts logically
2. **Visual Configuration**: Multi-step forms with progressive disclosure - no YAML needed
3. **Built-in Status Tracking**: First-class support for alert lifecycle (active, acknowledged, cleared, escalated)
4. **Device Hierarchy**: Proper device relationships in Home Assistant for clean organization
5. **Interactive Buttons**: One-click acknowledge, clear, and escalate actions

### Key Differentiators
- **Zero YAML Required**: Complete UI-driven configuration through Home Assistant's native interface
- **Hub-Based Architecture**: Unique two-tier hub system (global settings + alert groups) not found in other integrations
- **Visual Condition Builder**: Logical triggers use form-based interface instead of JSON or YAML
- **Status Sensors**: Dedicated status entities tracking full alert lifecycle
- **Device Organization**: Each alert is a proper device with related entities, not loose entities
- **Menu-Style Management**: Modern button-based interface instead of dropdown menus
- **Multi-Step Forms**: Progressive disclosure prevents overwhelming users with too many fields at once

## User Experience
### Target Users
- **Primary**: Home Assistant enthusiasts who want sophisticated alerts without YAML expertise
  - Comfortable with Home Assistant UI
  - Want security/safety/environmental monitoring
  - Prefer visual configuration over code

- **Secondary**: Power users who want organized alert architecture
  - Have complex alert needs
  - Value clean device hierarchy
  - Want to build on a solid foundation rather than reinvent

### User Workflows

1. **Initial Setup**
   - User goal: Get the integration installed and ready
   - Steps:
     1. Install via HACS
     2. Add "Global Settings Hub" through Settings → Devices & Services
     3. Configure default notification preferences (optional)
     4. Add first "Alert Group Hub" with custom name (e.g., "Security Alerts")
   - Outcome: Ready to create alerts within organized groups

2. **Creating an Alert**
   - User goal: Monitor a condition (e.g., "Front door open while away")
   - Steps:
     1. Click gear icon on Alert Group Hub device
     2. Select "➕ Add New Alert"
     3. **Step 1**: Enter name, choose trigger type (simple/template/logical), select severity
     4. **Step 2**: Configure trigger (varies by type - entity selector, template editor, or visual condition builder)
     5. **Step 3**: Optionally configure actions (triggered/cleared/escalated service calls)
   - Outcome: Alert device created immediately with binary sensor, status sensor, and action buttons

3. **Managing Active Alert**
   - User goal: Respond to triggered alert
   - Steps:
     1. Alert fires - binary sensor goes "on", status becomes "active"
     2. User sees notification/automation triggered
     3. User clicks "Acknowledge" button to mark as seen
     4. Status updates to "acknowledged"
     5. When condition clears or user clicks "Clear", status becomes "cleared"
   - Outcome: Alert lifecycle tracked, automation can respond to status changes

4. **Editing Existing Alert**
   - User goal: Modify alert configuration
   - Steps:
     1. Click gear icon on Alert Group Hub
     2. Select "✏️ Edit Alert"
     3. Choose alert from dropdown (shows name, type, severity)
     4. Edit form appears with all current values pre-filled
     5. Modify desired fields and save
   - Outcome: Alert updated immediately, entities reload with new configuration

### User Interface Principles
- **Progressive Disclosure**: Show only relevant fields based on selections (trigger type determines step 2 form)
- **Helpful Guidance**: Every field includes description with examples
- **Visual Clarity**: Emojis for trigger types (🔍 Simple, 📝 Template, 🔗 Logical) and severity (🚨 Critical, ⚠️ Warning, ℹ️ Info)
- **Immediate Feedback**: Changes take effect instantly with auto-reload
- **Graceful Degradation**: Clear error messages with actionable guidance
- **Home Assistant Native**: Follows platform design patterns and conventions

## Product Requirements
### Must Have
- ✅ Hub-based architecture (global + groups)
- ✅ Three trigger types (simple, template, logical)
- ✅ Visual condition builder for logical triggers
- ✅ Status sensors (active, inactive, acknowledged, cleared, escalated)
- ✅ Action buttons (acknowledge, clear, escalate)
- ✅ Multi-step configuration with progressive disclosure
- ✅ Edit alert functionality
- ✅ Device hierarchy with proper relationships
- ✅ Automatic entity reloading on config changes

### Should Have
- ✅ Service calls for automation integration
- ✅ Summary sensors showing group overview
- ✅ HACS compliance
- ⏳ Blueprint/script templates for common notification patterns
- ⏳ Area integration (tie alerts to Home Assistant areas)

### Could Have
- ⏳ Alert history visualization
- ⏳ Advanced escalation policies (repeat notifications, escalation chains)
- ⏳ Integration with Home Assistant alert system
- ⏳ Rich notification formatting templates
- ⏳ Custom alert widgets/cards (separate Lovelace card project exists)

## Success Metrics
- **Adoption**: HACS installs and active users
- **Usability**: Users can create first alert within 5 minutes of installation
- **Reliability**: Zero data loss during upgrades, <1% error rate in alert evaluation
- **Maintainability**: Test coverage >90%, CI passing consistently
- **Community**: Positive feedback, feature requests indicate engagement

## Evolution

### Phase 1: Simple Alerts (Initial)
- Basic entity monitoring with YAML configuration
- Single flat structure

### Phase 2: Global Settings (Early Refactor)
- Added global notification settings
- Still one hub per alert (organizational failure)

### Phase 3: Hub Architecture (Major Pivot)
- Recognized organizational problem
- Complete restructure to two-tier hub system
- Global Settings Hub + Alert Group Hubs
- Proper device hierarchy

### Phase 4: UI Modernization
- Replaced dropdown menus with button-style interface
- Multi-step forms for alert creation
- Visual condition builder for logical triggers
- Edit functionality with pre-filled forms

### Phase 5: Polish & Stability (Current)
- Defensive coding practices
- Cleanup of legacy patterns
- Documentation updates
- Memory bank establishment for better AI collaboration
- Focus on reliability over new features
