# Response to Frontend Team Questions

**Date**: 2025-10-29
**Status**: ✅ All questions answered

## Summary

The frontend LLM raised excellent questions about the v2.0 state machine implementation. After thorough code review, I've identified some gaps in the original documentation and provided comprehensive answers.

## Key Findings

### What Was Missing from Original Instructions

1. **Escalation mechanism details** - The cardInstructions.md didn't explain:
   - That there's NO escalate switch (only 3 switches exist)
   - How automatic vs manual escalation works
   - How to de-escalate

2. **The `escalated` attribute** - Not shown in the Alert interface example

3. **Cleared vs Resolved naming** - Mixed usage in codebase (status sensor has legacy "cleared" reference)

4. **Escalate button guidance** - Should it exist? How should it work?

5. **Snooze duration configurability** - Is it fixed or variable?

6. **Config schema migration** - Clean break vs backward compat?

## What I Created

### 1. frontendQuestions-ANSWERS.md
**Location**: `.claude/memory-bank/frontendQuestions-ANSWERS.md`

Comprehensive answers to all 6 questions with:
- Code references (file:line)
- Implementation recommendations
- Example TypeScript code
- Complete entity structure reference

### 2. Updated cardInstructions.md
**Changes made**:
- Added note that NO escalate switch exists
- Added `escalated: boolean` to Alert interface
- Added escalation behavior section (automatic vs manual)
- Added `_handleEscalate()` example for manual escalation button
- Added optional escalate button to rendering example

## Answers at a Glance

| Question | Answer |
|----------|--------|
| **1. Escalation mechanism** | Both automatic (timer) AND manual (service call). No escalate switch. |
| **2. Escalate button** | Keep it (optional). Calls `emergency_alerts.escalate` service. |
| **3. `escalated` attribute** | YES - exists on binary sensor (`alert.attributes.escalated`) |
| **4. Cleared vs Resolved** | Use `resolved` everywhere. Clean break from `cleared`. |
| **5. Snooze duration** | Fixed 5m for v2.0. Configurable per alert in backend, not at runtime. |
| **6. Config schema** | Clean break. No backward compat needed. |

## Implementation Recommendations

### Essential Changes
1. ✅ Use `resolved` (not `cleared`) in all new code
2. ✅ Read `alert.attributes.escalated` from binary sensor
3. ✅ Display "Resolve" button (not "Clear")
4. ✅ Fixed "Snooze (5m)" for v2.0

### Optional Features
5. ⏸️ "Escalate Now" button (calls service, not switch)
6. ⏸️ Configurable snooze duration (future enhancement)

## Code References

All answers include specific code references:
- `binary_sensor.py:310` - escalated attribute
- `binary_sensor.py:537-558` - automatic escalation timer
- `binary_sensor.py:590-600` - manual escalate service
- `switch.py:206-209` - acknowledge cancels escalation
- `const.py:51` - STATE_ESCALATED constant
- `const.py:79-80` - Default times (escalation & snooze)

## Files Modified

1. **Created**: `.claude/memory-bank/frontendQuestions-ANSWERS.md` (new, 400+ lines)
2. **Updated**: `.claude/memory-bank/cardInstructions.md` (4 edits)
   - Added escalation note
   - Added `escalated` attribute
   - Added `_handleEscalate()` handler
   - Added escalation behavior section

## Next Steps

### For Frontend Team
1. Read `frontendQuestions-ANSWERS.md` for detailed answers
2. Review updated `cardInstructions.md` for escalation section
3. Implement changes per recommendations
4. Reach out if any remaining questions

### For This Project
- No backend changes needed - implementation is correct
- Documentation gap is now filled
- Memory bank updated with clarifications

## Notes

The frontend team's questions revealed that the original cardInstructions.md was incomplete. The implementation itself is solid - this was purely a documentation issue. The v2.0 state machine works exactly as designed; it just wasn't fully explained.

### What Works Well
- Automatic escalation timer (5 min default, configurable)
- Manual escalation service call
- Escalation cancellation via acknowledge switch
- De-escalation by acknowledging
- All state attributes present on binary sensor

### No Bugs Found
All questions were about understanding the design, not bugs. The implementation matches the design intent.

---

**Status**: Ready for frontend card implementation
**Documentation**: Complete
**Backend Changes**: None needed
