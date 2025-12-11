## 2025-12-10 – v3 trigger and reminder model (AI)
- Added combined trigger type (two conditions, comparator-based, AND/OR) to simplify common cases (window+rain, car home+low charge) while keeping template as advanced.
- Introduced per-alert reminder timing (`remind_after_seconds`) that re-runs on-trigger actions instead of sticky escalation state; escalation flag now cleared on acknowledge/snooze/resolve/clear.
- Status semantics tightened: escalated badge only when entity is on; frontend gates status on entity state to avoid stale escalations.
