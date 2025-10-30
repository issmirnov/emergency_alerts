# Frontend Questions - ANSWERS

> **Date**: 2025-10-29
> **For**: Frontend team working on lovelace-emergency-alerts-card
> **Context**: Clarifications on v2.0 switch-based state machine

---

## 1. Escalation Mechanism (CRITICAL) ✅

### Implementation Details

**Escalation is BOTH automatic AND manual:**

1. **AUTOMATIC escalation** via timer:
   - Default: 5 minutes (300 seconds) if not acknowledged
   - Configurable in Global Settings Hub: `default_escalation_time`
   - Timer starts when alert triggers (if not acknowledged/snoozed)
   - Timer is cancelled when user acknowledges or snoozes
   - Timer restarts if user un-acknowledges (toggles acknowledge switch OFF)

2. **MANUAL escalation** via service call:
   - Service: `emergency_alerts.escalate`
   - Can be called manually from automations or UI
   - **No `switch.*_escalate` entity exists** - only 3 switches per alert

3. **De-escalation**:
   - Turn ON the acknowledge switch → de-escalates
   - State transitions: `[ESCALATED] ──(acknowledge)──> [ACKNOWLEDGED]`
   - Acknowledging clears the `escalated` flag

### Code References
- `binary_sensor.py:537-558` - Automatic escalation timer implementation
- `binary_sensor.py:590-600` - Manual escalate service handler
- `switch.py:206-209` - Acknowledge switch cancels escalation timer
- `const.py:79` - DEFAULT_ESCALATION_TIME = 300 seconds

---

## 2. Escalate Button in UI ✅

### Recommendation: **KEEP IT** (Optional)

The escalate button should:
- Call the service: `emergency_alerts.escalate`
- Be shown/hidden via config: `show_escalate_button` (optional, default: false)
- Be styled differently (not as a toggle like the switches)
- Be most useful for manual escalation in critical situations

**Implementation:**
```typescript
private async _handleEscalate(alertEntityId: string): Promise<void> {
  // Call the service (NOT a switch toggle)
  await this.hass.callService('emergency_alerts', 'escalate', {
    entity_id: alertEntityId  // Pass binary_sensor entity ID
  });
}
```

**Button rendering:**
```typescript
${this._config.show_escalate_button
  ? html`
    <button
      class="action-btn escalate-btn"
      @click=${() => this._handleEscalate(alert.entity_id)}
      ?disabled=${!alert.state === 'on' || alert.attributes.escalated}
    >
      ⚠️ Escalate Now
    </button>
  `
  : ''
}
```

### Code Reference
- `services.yaml:25-31` - Escalate service definition
- `__init__.py:45-49` - Service handler registration

---

## 3. "Escalated" Attribute on Binary Sensor ✅

### Answer: **YES**

The binary sensor DOES have an `escalated: boolean` attribute.

**Available attributes on `binary_sensor.emergency_[name]`:**
```typescript
interface Alert {
  entity_id: string; // binary_sensor entity
  state: string; // on/off
  attributes: {
    // State machine flags
    acknowledged: boolean;
    snoozed: boolean;
    resolved: boolean;
    escalated: boolean;  // ✅ YES - this exists!

    // Timing
    snooze_until?: string; // ISO timestamp

    // Metadata
    severity: string;
    group: string;
    status: string; // computed from flags

    // Other
    template?: string;
    logical_conditions?: any[];
    // ...
  };
}
```

**Status sensor also reflects escalation:**
- `sensor.emergency_[name]_status` can show value: `"escalated"`

### Code Reference
- `binary_sensor.py:310` - `"escalated": self._escalated` in extra_state_attributes
- `binary_sensor.py:610-614` - Status priority: escalated comes before acknowledged

---

## 4. Cleared vs Resolved Naming ✅

### Answer: **Use "resolved"** (Clean break)

**In v2.0:**
- Attribute name: `resolved` (boolean)
- Switch entity: `switch.emergency_[name]_resolved`
- State name: `STATE_RESOLVED = "resolved"`
- Service name: Still `clear` (legacy compat) but sets `resolved` flag

**The old "cleared" naming is gone** except:
- Legacy status sensor icon mapping (line 631 of binary_sensor.py)
- Service is still called `emergency_alerts.clear` (but it sets `resolved=True`)

**Recommendation for card:**
- Use `resolved` everywhere in new code
- Display button as "Resolve" not "Clear"
- Check attribute `alert.attributes.resolved` (not `cleared`)
- No backward compat needed - v2.0 is a clean break

### Code References
- `const.py:52` - STATE_RESOLVED = "resolved"
- `const.py:57` - SWITCH_TYPE_RESOLVE = "resolved"
- `binary_sensor.py:310` - Attribute: "resolved": self._resolved

---

## 5. Snooze Duration UI ✅

### Answer: **Configurable per alert, default 5 minutes**

**Current Implementation:**
- Global default: 5 minutes (300 seconds) - `const.py:80`
- Per-alert override: `CONF_SNOOZE_DURATION` in alert config
- Auto-expires after duration (survives HA restarts via snooze_until timestamp)

**Card Options:**

### Option A: Fixed 5m Button (Simplest - RECOMMENDED for v2.0)
```typescript
<button @click=${() => this._handleSnooze(alert.entity_id)}>
  Snooze (5m)
</button>
```

### Option B: Configurable Duration (Future enhancement)
```typescript
// Allow users to select duration in card config
interface CardConfig {
  snooze_duration?: number; // minutes, default 5
  snooze_durations?: number[]; // [5, 15, 30] for dropdown
}

// Call service with custom duration
await this.hass.callService('switch', 'turn_on', {
  entity_id: switchId,
  // Note: Duration is stored in alert config, not passed at runtime
});
```

**For v2.0: Stick with fixed 5m** shown in instructions. Duration selection can be a future enhancement.

**Important:** The switch implementation uses the duration from alert config (`CONF_SNOOZE_DURATION`), not passed at runtime. To support variable durations, you'd need to:
1. Call a new service that accepts duration parameter, OR
2. Update alert config before toggling switch (complex)

### Code References
- `const.py:80` - DEFAULT_SNOOZE_DURATION = 300
- `switch.py:270-290` - Snooze switch implementation with auto-expiry
- `binary_sensor.py:308-309` - Snooze state attributes

---

## 6. Config Schema - Clean Break or Migration Path? ✅

### Answer: **Clean Break** (No backward compat needed)

**Rationale:**
- Integration v2.0 is already a breaking change (button entities removed)
- Users must update integration AND card together
- No migration path in backend, so none needed in frontend

**Recommended v2.0 Card Config:**

```typescript
interface EmergencyAlertsCardConfig {
  type: 'custom:emergency-alerts-card';
  entity?: string; // Optional: single alert to display

  // Button visibility (all optional, default true)
  show_acknowledge_button?: boolean;  // New name (was show_acknowledge_button)
  show_snooze_button?: boolean;       // NEW - replaces nothing
  show_resolve_button?: boolean;      // New name (was show_clear_button)
  show_escalate_button?: boolean;     // OPTIONAL - manual escalate (default false)

  // Removed (no migration):
  // show_clear_button - replaced by show_resolve_button

  // Display options
  show_status?: boolean;
  show_severity?: boolean;
  compact_mode?: boolean;

  // Future enhancements
  snooze_duration?: number; // Not implemented yet
}
```

**Migration Strategy:**
```typescript
// Option 1: No migration - require users to update config
// (RECOMMENDED - simplest)

// Option 2: Console warning for deprecated config
if (config.show_clear_button !== undefined) {
  console.warn(
    'emergency-alerts-card: "show_clear_button" is deprecated. ' +
    'Use "show_resolve_button" instead. ' +
    'Integration v2.0 uses "resolve" not "clear".'
  );
  config.show_resolve_button = config.show_clear_button;
}
```

**Recommended:** Clean break. Document the config changes in card README with migration guide.

---

## Summary: Complete Entity Structure

For reference, here's the complete entity structure per alert in v2.0:

```
Emergency Alert: "Front Door Open"
├── binary_sensor.emergency_front_door_open
│   ├── state: on/off (trigger condition)
│   └── attributes:
│       ├── acknowledged: boolean
│       ├── snoozed: boolean
│       ├── resolved: boolean
│       ├── escalated: boolean  ✅
│       ├── snooze_until: ISO timestamp (if snoozed)
│       ├── severity: "critical"/"warning"/"info"
│       ├── status: computed string
│       └── ...
│
├── sensor.emergency_front_door_open_status
│   └── state: "inactive"/"active"/"acknowledged"/"snoozed"/"escalated"/"resolved"
│
├── switch.emergency_front_door_open_acknowledged
│   └── state: on/off (ON = acknowledged)
│
├── switch.emergency_front_door_open_snoozed
│   └── state: on/off (ON = snoozed, auto-off after duration)
│
└── switch.emergency_front_door_open_resolved
    └── state: on/off (ON = resolved, prevents re-trigger)
```

**Services available:**
- `emergency_alerts.acknowledge` - Same as toggling acknowledge switch
- `emergency_alerts.clear` - Same as toggling resolve switch
- `emergency_alerts.escalate` - Manual escalation (no switch for this)

---

## Implementation Checklist for Card

- [ ] Use `resolved` attribute (not `cleared`)
- [ ] Display "Resolve" button (not "Clear")
- [ ] Show `escalated: boolean` attribute from binary_sensor
- [ ] Optional: Add "Escalate Now" button calling `emergency_alerts.escalate` service
- [ ] Fixed "Snooze (5m)" button for v2.0 (configurable duration = future enhancement)
- [ ] Clean config break: `show_resolve_button` (not `show_clear_button`)
- [ ] Update documentation with v2.0 requirements
- [ ] Test escalation flow: alert → (timer) → escalated → (acknowledge) → acknowledged

---

## Questions or Issues?

If anything is still unclear, check these files:
- `custom_components/emergency_alerts/const.py` - All constants and state definitions
- `custom_components/emergency_alerts/binary_sensor.py` - Attributes, escalation logic
- `custom_components/emergency_alerts/switch.py` - Switch implementations
- `custom_components/emergency_alerts/services.yaml` - Service definitions

Or contact the backend team with specific questions!
