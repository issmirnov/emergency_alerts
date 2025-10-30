# Card Integration Instructions

> **Audience**: Frontend team working on lovelace-emergency-alerts-card
> **Purpose**: Instructions for updating card to work with new switch-based architecture
> **Date**: 2025-10-29

## Overview

The Emergency Alerts integration has been redesigned with a **switch-based state machine** instead of button entities. This provides clearer state visibility and better UX.

### Key Changes

**REMOVED**: ❌ Button entities (`button.emergency_[name]_acknowledge`, etc.)
**ADDED**: ✅ Switch entities with visible on/off state
**IMPROVED**: State machine with mutual exclusivity enforcement

---

## New Entity Structure

For each alert, the integration now creates:

### Binary Sensor (unchanged)
- `binary_sensor.emergency_[name]` - Alert trigger state (on = condition met)

### Status Sensor (enhanced)
- `sensor.emergency_[name]_status` - Current state text
  - Values: `inactive`, `active`, `acknowledged`, `snoozed`, `escalated`, `resolved`

### Switch Entities (**NEW**)
- `switch.emergency_[name]_acknowledged` - ON = acknowledged (prevents escalation)
- `switch.emergency_[name]_snoozed` - ON = snoozed (temporary silence, auto-off after 5 min)
- `switch.emergency_[name]_resolved` - ON = resolved (problem fixed, won't re-trigger until condition clears)

**Note:** There is NO `switch.*_escalate` entity. Escalation is automatic (via timer) or manual (via service call).

---

## State Machine Semantics

### State Transitions

```
[INACTIVE] ──(trigger met)──> [ACTIVE]
                                │
                                ├──(acknowledge)──> [ACKNOWLEDGED] ──(untoggle)──> [ACTIVE]
                                ├──(snooze)──────> [SNOOZED] ──(timer expires)──> [ACTIVE]
                                ├──(escalate)────> [ESCALATED] ──(acknowledge)──> [ACKNOWLEDGED]
                                └──(resolve)─────> [RESOLVED] ──(trigger again)──> [ACTIVE]
```

### Switch Semantics

| Switch | ON Meaning | OFF Meaning | Auto-Off? |
|--------|-----------|-------------|-----------|
| **acknowledged** | "I'm working on it" | Allow escalation | No (manual) |
| **snoozed** | "Silence for 5 minutes" | Stop snoozing | Yes (5 min timer) |
| **resolved** | "Problem fixed" | Allow triggering | No (manual, but resets when condition clears then triggers) |

### Mutual Exclusivity

**IMPORTANT**: Only ONE switch can be ON at a time per alert.

Turning on any switch automatically turns off the other two:
- Turn ON acknowledged → snooze and resolve turn OFF
- Turn ON snoozed → acknowledge and resolve turn OFF
- Turn ON resolved → acknowledge and snooze turn OFF

The integration enforces this via `STATE_EXCLUSIONS` rules.

### Escalation Behavior

**NO escalate switch** - Escalation is handled differently:

1. **Automatic Escalation** (Timer-based):
   - Default: 5 minutes after alert triggers (if not acknowledged/snoozed)
   - Configurable in Global Settings Hub: `default_escalation_time`
   - Timer cancels when: acknowledge ON or snooze ON
   - Timer restarts when: acknowledge toggles OFF while alert still active
   - Sets `escalated: true` attribute on binary sensor

2. **Manual Escalation** (Service call):
   - Service: `emergency_alerts.escalate`
   - Use for immediate escalation before timer expires
   - Called from card with custom "Escalate Now" button (optional)

3. **De-escalation**:
   - Turn ON acknowledge switch → clears `escalated` flag
   - State: `[ESCALATED] ──(acknowledge)──> [ACKNOWLEDGED]`

**For Card Implementation:**
- Read `alert.attributes.escalated` boolean from binary sensor
- Optionally provide "Escalate Now" button calling service
- Visual indicator when `escalated === true`

---

## Card Implementation Changes

### 1. Entity Discovery

**OLD**:
```typescript
const acknowledgeButton = `button.emergency_${alertName}_acknowledge`;
const clearButton = `button.emergency_${alertName}_clear`;
const escalateButton = `button.emergency_${alertName}_escalate`;
```

**NEW**:
```typescript
// Discover switch entities
const acknowledgedSwitch = `switch.emergency_${alertName}_acknowledged`;
const snoozedSwitch = `switch.emergency_${alertName}_snoozed`;
const resolvedSwitch = `switch.emergency_${alertName}_resolved`;

interface Alert {
  entity_id: string; // binary_sensor
  state: string; // on/off
  attributes: {
    severity: string;
    group: string;
    acknowledged: boolean; // NEW
    snoozed: boolean; // NEW
    resolved: boolean; // NEW
    escalated: boolean; // NEW - escalation state flag
    snooze_until?: string; // ISO timestamp when snooze expires
    status: string; // detailed status
    // ... other attributes
  };
  // Switch entity references
  acknowledgedSwitch?: HassEntity;
  snoozedSwitch?: HassEntity;
  resolvedSwitch?: HassEntity;
}
```

### 2. Action Handlers

**OLD** (service calls):
```typescript
private async _handleAcknowledge(entityId: string): Promise<void> {
  await this.hass.callService('emergency_alerts', 'acknowledge', {
    entity_id: entityId
  });
}
```

**NEW** (toggle switches):
```typescript
private async _handleAcknowledge(alertEntityId: string): Promise<void> {
  // Convert binary_sensor ID to switch ID
  const switchId = alertEntityId.replace(
    'binary_sensor.emergency_',
    'switch.emergency_'
  ) + '_acknowledged';

  // Toggle the switch
  await this.hass.callService('switch', 'toggle', {
    entity_id: switchId
  });
}

private async _handleSnooze(alertEntityId: string): Promise<void> {
  const switchId = alertEntityId.replace(
    'binary_sensor.emergency_',
    'switch.emergency_'
  ) + '_snoozed';

  // Turn ON (will auto-off after 5 minutes)
  await this.hass.callService('switch', 'turn_on', {
    entity_id: switchId
  });
}

private async _handleResolve(alertEntityId: string): Promise<void> {
  const switchId = alertEntityId.replace(
    'binary_sensor.emergency_',
    'switch.emergency_'
  ) + '_resolved';

  await this.hass.callService('switch', 'toggle', {
    entity_id: switchId
  });
}

// OPTIONAL: Manual escalation (no switch for this, uses service call)
private async _handleEscalate(alertEntityId: string): Promise<void> {
  // Call the escalate service directly (not a switch)
  await this.hass.callService('emergency_alerts', 'escalate', {
    entity_id: alertEntityId // Pass binary_sensor entity ID
  });
}
```

### 3. Button Rendering with State Visualization

Show switch state in the UI:

```typescript
private _renderAlertActions(alert: Alert): TemplateResult {
  return html`
    <div class="alert-actions">
      <!-- Acknowledge -->
      ${alert.attributes.acknowledged
        ? html`
          <button
            class="action-btn acknowledged-active"
            @click=${() => this._handleAcknowledge(alert.entity_id)}
          >
            ✓ Acknowledged
          </button>
        `
        : html`
          <button
            class="action-btn"
            @click=${() => this._handleAcknowledge(alert.entity_id)}
          >
            Acknowledge
          </button>
        `
      }

      <!-- Snooze -->
      ${alert.attributes.snoozed
        ? html`
          <button
            class="action-btn snoozed-active"
            @click=${() => this._handleSnooze(alert.entity_id)}
            title="Snoozed until ${this._formatSnoozeTime(alert)}"
          >
            🔕 Snoozed (${this._getSnoozeTimeRemaining(alert)})
          </button>
        `
        : html`
          <button
            class="action-btn"
            @click=${() => this._handleSnooze(alert.entity_id)}
          >
            Snooze (5m)
          </button>
        `
      }

      <!-- Resolve -->
      ${alert.attributes.resolved
        ? html`
          <button
            class="action-btn resolved-active"
            @click=${() => this._handleResolve(alert.entity_id)}
          >
            ✓ Resolved
          </button>
        `
        : html`
          <button
            class="action-btn"
            @click=${() => this._handleResolve(alert.entity_id)}
          >
            Resolve
          </button>
        `
      }

      <!-- OPTIONAL: Manual Escalate -->
      ${this._config.show_escalate_button && !alert.attributes.escalated
        ? html`
          <button
            class="action-btn escalate-btn"
            @click=${() => this._handleEscalate(alert.entity_id)}
            ?disabled=${alert.state !== 'on'}
          >
            ⚠️ Escalate Now
          </button>
        `
        : ''
      }
    </div>
  `;
}

private _getSnoozeTimeRemaining(alert: Alert): string {
  if (!alert.attributes.snooze_until) return '';

  const snoozeUntil = new Date(alert.attributes.snooze_until);
  const now = new Date();
  const remaining = Math.max(0, Math.floor((snoozeUntil.getTime() - now.getTime()) / 1000));

  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;

  return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
}
```

### 4. CSS Styling for Active States

```css
.action-btn {
  padding: 8px 16px;
  border: 1px solid var(--divider-color);
  background: var(--card-background-color);
  cursor: pointer;
}

.action-btn.acknowledged-active {
  background: var(--success-color);
  color: white;
  border-color: var(--success-color);
}

.action-btn.snoozed-active {
  background: var(--warning-color);
  color: white;
  border-color: var(--warning-color);
}

.action-btn.resolved-active {
  background: var(--info-color);
  color: white;
  border-color: var(--info-color);
}
```

---

## Migration Strategy

### Backward Compatibility

**NOT REQUIRED** - The integration is doing a clean break. Users with testing deployments will need to:
1. Update integration to v2.0
2. Update card to new version
3. Recreate alerts (old button entities will be removed)

### Version Requirements

- **Integration**: v2.0+ (switch-based)
- **Card**: v2.0+ (switch-aware)

---

## Testing Checklist

- [ ] Card discovers switch entities correctly
- [ ] Acknowledge button toggles `switch.emergency_[name]_acknowledged`
- [ ] Snooze button turns on `switch.emergency_[name]_snoozed`
- [ ] Resolve button toggles `switch.emergency_[name]_resolved`
- [ ] Active state shows visually (button styling changes)
- [ ] Snooze countdown timer displays correctly
- [ ] Toggling one switch turns off others (mutual exclusivity)
- [ ] Card updates in real-time when switches change
- [ ] Status sensor shows correct state text

---

## Example Alert in Home Assistant

After creating an alert "Front Door Open":

```
Entities created:
├── binary_sensor.emergency_front_door_open (trigger state)
├── sensor.emergency_front_door_open_status (status text)
├── switch.emergency_front_door_open_acknowledged
├── switch.emergency_front_door_open_snoozed
└── switch.emergency_front_door_open_resolved
```

All 5 entities belong to device: "Emergency Alert: Front Door Open"

---

## Questions?

Contact the backend integration team with any questions about:
- Switch entity behavior
- State machine transitions
- Dispatcher signals
- Binary sensor attributes
