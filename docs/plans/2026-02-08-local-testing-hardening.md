# Local Testing Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a lightweight local smoke test and an E2E test that verifies the add‑alert flow and catches translation errors.

**Architecture:** Implement a small dev_tools script that runs Playwright UI checks plus a log scan for translation failures. Extend the existing Playwright E2E suite with a dedicated add‑alert config flow test using the existing login/global setup.

**Tech Stack:** Bash, Python (optional), Playwright (@playwright/test), Home Assistant UI.

---

### Task 1: Add a Local Smoke Test Script (UI + Log Scan)

**Files:**
- Create: `dev_tools/smoke_add_alert.sh`
- Create: `dev_tools/check_ha_logs.sh`
- Modify: `dev_tools/local-dev.sh`
- Test: Manual run of `dev_tools/smoke_add_alert.sh`

**Step 1: Write the failing test (script stub)**

Create `dev_tools/smoke_add_alert.sh` that calls `dev_tools/check_ha_logs.sh` and runs a Playwright script (to be added in Task 2). Leave placeholders so it fails with a clear message until the Playwright script exists.

```bash
#!/bin/bash
set -euo pipefail

./dev_tools/check_ha_logs.sh || exit 1

if [ ! -f dev_tools/playwright_add_alert.py ]; then
  echo "Missing dev_tools/playwright_add_alert.py" >&2
  exit 1
fi

python3 dev_tools/playwright_add_alert.py
```

**Step 2: Run to verify it fails**

Run:
```
./dev_tools/smoke_add_alert.sh
```
Expected: FAIL with “Missing dev_tools/playwright_add_alert.py”.

**Step 3: Implement `check_ha_logs.sh`**

Create `dev_tools/check_ha_logs.sh` to scan HA logs for translation errors:

```bash
#!/bin/bash
set -euo pipefail

LOGS=$(docker-compose logs --tail 300 homeassistant | rg -n "Failed to format translation" || true)

if [ -n "$LOGS" ]; then
  echo "Translation errors detected:" >&2
  echo "$LOGS" >&2
  exit 1
fi

echo "✓ No translation errors in recent HA logs"
```

**Step 4: Wire into local-dev help**

Add a `smoke` command to `dev_tools/local-dev.sh`:

```bash
smoke)
  echo "🧪 Running UI smoke test (add-alert flow + log scan)..."
  ./dev_tools/smoke_add_alert.sh
  ;;
```

**Step 5: Run again to verify it still fails**

Run:
```
./dev_tools/local-dev.sh smoke
```
Expected: FAIL with “Missing dev_tools/playwright_add_alert.py”.

**Step 6: Commit**

```bash
git add dev_tools/smoke_add_alert.sh dev_tools/check_ha_logs.sh dev_tools/local-dev.sh

git commit -m "chore: add local smoke harness for add-alert flow"
```

---

### Task 2: Add Playwright Script for Add‑Alert Flow (Local)

**Files:**
- Create: `dev_tools/playwright_add_alert.py`
- Test: `dev_tools/smoke_add_alert.sh`

**Step 1: Write the failing test (Playwright script)**

Create `dev_tools/playwright_add_alert.py` that logs in (dev/dev), navigates to Integrations, opens Emergency Alerts, and tries to add an alert. Initially stub to fail with a clear error if UI steps aren’t yet implemented.

**Step 2: Run to verify it fails**

Run:
```
python3 dev_tools/playwright_add_alert.py
```
Expected: FAIL with an explicit “Not implemented” message.

**Step 3: Implement minimal Playwright steps**

Use Playwright sync API to:
- Go to `http://localhost:8123`
- Login if needed (dev/dev)
- Navigate to Settings → Devices & Services
- Find Emergency Alerts integration
- Open its config flow menu
- Select “Add New Alert”
- Fill basic fields (name, severity, simple trigger entity + state)
- Submit
- Verify success by checking for new entity in UI or lack of error modal
- Capture screenshot on failure

**Step 4: Run smoke script**

Run:
```
./dev_tools/smoke_add_alert.sh
```
Expected: PASS (no translation error + successful flow).

**Step 5: Commit**

```bash
git add dev_tools/playwright_add_alert.py

git commit -m "test: add local Playwright add-alert smoke"
```

---

### Task 3: Add E2E Test for Add‑Alert Flow

**Files:**
- Create: `e2e-tests/tests/03-config-flow.spec.ts`
- Modify: `e2e-tests/helpers/alert-helpers.ts` (if needed)
- Test: `./scripts/run-e2e.sh --grep "add alert" --headed`

**Step 1: Write the failing test**

Create `e2e-tests/tests/03-config-flow.spec.ts` with a test that navigates the UI and attempts to add an alert (same flow as the local smoke script).

```ts
import { test, expect } from '@playwright/test';
import { createAlertHelpers } from '../helpers/alert-helpers';
import { createHAAPI } from '../helpers/ha-api';

test('Add alert flow works', async ({ page, request }) => {
  const haApi = createHAAPI(request);
  const helpers = createAlertHelpers(page, haApi);

  await page.goto('/config/integrations');
  // ... steps ...
  await expect(page.locator('text=Alert created')).toBeVisible();
});
```

**Step 2: Run to verify it fails**

Run:
```
./scripts/run-e2e.sh --grep "Add alert" --headed
```
Expected: FAIL due to missing selectors/steps.

**Step 3: Implement minimal selectors**

Add helpers to `alert-helpers.ts` if needed (e.g., `openEmergencyAlertsIntegration()`, `startAddAlertFlow()`). Use stable selectors and text labels from `strings.json`.

**Step 4: Run to verify it passes**

Run:
```
./scripts/run-e2e.sh --grep "Add alert" --headed
```
Expected: PASS.

**Step 5: Commit**

```bash
git add e2e-tests/tests/03-config-flow.spec.ts e2e-tests/helpers/alert-helpers.ts

git commit -m "test: add e2e add-alert config flow"
```

---

### Task 4: Verify Add‑Alert Flow Manually

**Files:**
- None

**Step 1: Run local smoke**

```
./dev_tools/local-dev.sh smoke
```
Expected: PASS.

**Step 2: Run E2E add‑alert test**

```
./scripts/run-e2e.sh --grep "Add alert" --headed
```
Expected: PASS.

**Step 3: Commit notes to memory bank (optional)**

Update `.claude/memory-bank/activeContext.md` if any new issues discovered.

---

## Notes / Constraints

- This plan assumes HA is running locally on `http://localhost:8123` with dev/dev credentials.
- If selectors change, update the UI test selectors in both the local Playwright script and the E2E test.
- We are staying on the current branch per user request (no worktree created).
