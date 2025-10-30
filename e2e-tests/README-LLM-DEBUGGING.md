# LLM Debugging Guide for E2E Tests

This guide explains how an LLM (like Claude) can effectively debug E2E test failures by interacting with the devcontainer environment.

## Overview

The E2E testing infrastructure is designed to be **LLM-inspectable**:
- All test artifacts are files that can be read
- Screenshots and videos are available for visual inspection
- Trace files provide time-travel debugging
- Chrome DevTools Protocol (CDP) endpoint is exposed
- Comprehensive logging at every level

## Quick Start for LLMs

When a test fails, here's your debugging workflow:

### 1. Check Test Output
```bash
# See what tests failed
cat e2e-tests/reports/test-results.json | jq '.suites[].specs[] | select(.ok == false)'

# View human-readable report
# (LLM can read the HTML, parse it, or just read test output)
```

### 2. Inspect Screenshots
```bash
# List all screenshots from failed tests
find e2e-tests/test-results -name "*.png"

# View specific screenshot (if LLM has vision capabilities)
# Or describe the file path for human inspection
ls -lh e2e-tests/test-results/*/test-failed-1.png
```

### 3. Examine Trace Files
```bash
# List trace files (these contain full test execution data)
find e2e-tests/test-results -name "trace.zip"

# Extract trace for inspection
cd e2e-tests/test-results/<test-name>/
unzip trace.zip
# Now you can read network.json, actions.json, etc.
```

### 4. Check Home Assistant State
```bash
# Check if HA is running
curl -s http://localhost:8123/api/ | jq '.'

# Get all entity states
curl -s http://localhost:8123/api/states | jq '.[] | select(.entity_id | startswith("binary_sensor.emergency_"))'

# Get specific entity
curl -s http://localhost:8123/api/states/binary_sensor.emergency_test_alert | jq '.'

# Call a service (for testing)
curl -X POST http://localhost:8123/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.emergency_test_alert_acknowledged"}'
```

### 5. Inspect Browser State via CDP
```bash
# Chrome DevTools Protocol is exposed on port 9222
# Connect to get debugging info
curl -s http://localhost:9222/json | jq '.'

# Get page console logs (if browser is running)
# Note: This requires a running Playwright session
```

### 6. Read Test Logs
```bash
# Check Home Assistant logs
tail -f /workspaces/emergency_alerts/config/home-assistant.log

# Check setup logs
cat /workspaces/emergency_alerts/config/setup.log

# Check test stdout/stderr (in CI artifacts or local runs)
```

## File Locations

All test artifacts are in predictable locations:

### Test Results
- `e2e-tests/test-results/` - Per-test directories with artifacts
- `e2e-tests/test-results/<test-name>/test-failed-1.png` - Screenshot
- `e2e-tests/test-results/<test-name>/test-failed-1.webm` - Video
- `e2e-tests/test-results/<test-name>/trace.zip` - Full trace

### Screenshots
- `e2e-tests/.screenshots/` - Named screenshots from tests
- `e2e-tests/.screenshots/smoke-test-dashboard.png` - Example

### Reports
- `e2e-tests/reports/index.html` - Human-readable HTML report
- `e2e-tests/reports/test-results.json` - Machine-readable JSON
- `e2e-tests/reports/videos/` - Video recordings

### Configuration
- `e2e-tests/playwright.config.ts` - Playwright configuration
- `e2e-tests/helpers/` - Test helper utilities
- `e2e-tests/tests/` - Actual test files

## Debugging Commands for LLMs

### Run Tests with Maximum Artifacts
```bash
# Run with tracing, video, and screenshots
cd e2e-tests
npm test -- --trace on --video on --screenshot on
```

### Run Single Test
```bash
# Run specific test for focused debugging
npm test -- --grep "Acknowledge switch updates backend state"
```

### Run in Headed Mode (for visual inspection)
```bash
# Opens actual browser window
npm run test:headed
```

### Run in UI Mode (interactive)
```bash
# Interactive test runner with time-travel debugging
npm run test:ui
```

### Generate Test Code
```bash
# Record user interactions to generate test code
npm run codegen
```

## Understanding Test Failures

### Common Failure Patterns

#### 1. Element Not Found
```
Error: locator.click: Target closed
```
**Debugging**:
- Check screenshot: Was the page fully loaded?
- Check trace: What was the DOM state when the locator was called?
- Check HA state: Was the entity actually created?

**LLM Actions**:
```bash
# Check if entity exists in HA
curl -s http://localhost:8123/api/states | jq '.[] | select(.entity_id == "switch.emergency_test_alert_acknowledged")'

# Look at screenshot
ls -lh e2e-tests/test-results/*/test-failed-1.png
```

#### 2. Timeout Waiting for State
```
Error: Timeout waiting for switch.emergency_test_alert_acknowledged to reach state "on"
```
**Debugging**:
- Backend didn't update: Check HA logs for errors
- Race condition: Check trace for timing issues
- Selector wrong: Check if element actually exists

**LLM Actions**:
```bash
# Check HA logs for errors around that entity
grep "emergency_test_alert_acknowledged" /workspaces/emergency_alerts/config/home-assistant.log | tail -20

# Check current state
curl -s http://localhost:8123/api/states/switch.emergency_test_alert_acknowledged | jq '.'
```

#### 3. Unexpected State
```
Expected: "on", Received: "off"
```
**Debugging**:
- Mutual exclusivity kicked in?
- Another test left state dirty?
- Backend logic bug?

**LLM Actions**:
```bash
# Check all switches for this alert
curl -s http://localhost:8123/api/states | jq '.[] | select(.entity_id | contains("emergency_test_alert"))'

# Read the test's beforeEach to see if cleanup happened
cat e2e-tests/tests/02-integration.spec.ts | grep -A 20 "beforeEach"
```

## Visual Inspection for LLMs with Vision

If the LLM has vision capabilities (like Claude with image understanding):

### 1. Analyze Screenshots
```bash
# Get screenshot path
find e2e-tests/test-results -name "*.png" | head -1

# LLM can then read this image file and analyze:
# - Is the card visible?
# - Is the alert displayed?
# - Are the switches in the correct state?
# - Are there any error messages?
```

### 2. Compare Screenshots
```bash
# Get baseline screenshot
ls e2e-tests/.screenshots/alert-default-state.png

# Get failed test screenshot
ls e2e-tests/test-results/*/test-failed-1.png

# LLM can compare these to identify visual regressions
```

## Programmatic Inspection

LLMs can execute these commands to gather debugging info:

### Check Test Environment
```bash
#!/bin/bash
# environment-check.sh

echo "=== Home Assistant Status ==="
curl -sf http://localhost:8123/api/ && echo "✓ HA is running" || echo "✗ HA is down"

echo -e "\n=== Emergency Alert Entities ==="
curl -s http://localhost:8123/api/states | jq -r '.[] | select(.entity_id | startswith("binary_sensor.emergency_")) | .entity_id'

echo -e "\n=== Emergency Alert Switches ==="
curl -s http://localhost:8123/api/states | jq -r '.[] | select(.entity_id | startswith("switch.emergency_")) | .entity_id + " = " + .state'

echo -e "\n=== Recent HA Logs (last 20 lines) ==="
tail -20 /workspaces/emergency_alerts/config/home-assistant.log

echo -e "\n=== Test Results Summary ==="
if [ -f "e2e-tests/reports/test-results.json" ]; then
    cat e2e-tests/reports/test-results.json | jq '{
      total: .suites[].specs | length,
      passed: [.suites[].specs[] | select(.ok == true)] | length,
      failed: [.suites[].specs[] | select(.ok == false)] | length
    }'
fi
```

### Extract Failure Details
```bash
#!/bin/bash
# get-failure-details.sh <test-name>

TEST_NAME=$1
TEST_DIR="e2e-tests/test-results/${TEST_NAME}"

if [ ! -d "$TEST_DIR" ]; then
    echo "Test directory not found: $TEST_DIR"
    exit 1
fi

echo "=== Test: $TEST_NAME ==="
echo ""
echo "Screenshots:"
ls -lh "$TEST_DIR"/*.png 2>/dev/null || echo "No screenshots"

echo -e "\nVideos:"
ls -lh "$TEST_DIR"/*.webm 2>/dev/null || echo "No videos"

echo -e "\nTrace:"
ls -lh "$TEST_DIR"/trace.zip 2>/dev/null || echo "No trace"

echo -e "\nExtract trace for detailed inspection:"
echo "cd $TEST_DIR && unzip trace.zip && cat trace/network.json"
```

## Trace File Analysis

Trace files contain complete test execution data. Here's how to extract useful info:

```bash
cd e2e-tests/test-results/<test-name>/
unzip trace.zip

# Network requests
cat trace/network.json | jq '.[] | select(.url | contains("api/services"))'

# Actions taken
cat trace/actions.json | jq '.[] | {type: .type, selector: .selector}'

# Console messages
cat trace/console.json | jq '.[] | {type: .type, text: .text}'

# Page events
cat trace/events.json | jq '.[] | {type: .type, timestamp: .timestamp}'
```

## Advanced Debugging

### Connect to Running Browser
If a test is running in headed or UI mode:

```bash
# Get WebSocket URL for CDP
curl -s http://localhost:9222/json | jq -r '.[0].webSocketDebuggerUrl'

# Can use Chrome DevTools Protocol to:
# - Get DOM snapshot
# - Execute JavaScript
# - Get computed styles
# - Access console logs
```

### Modify Test on the Fly
```typescript
// In any test file, add this for debugging:
await page.pause(); // Pauses test, opens inspector

// Or take a screenshot at any point:
await page.screenshot({ path: '.screenshots/debug-here.png' });

// Or dump state to console:
const state = await page.evaluate(() => {
  return {
    alerts: Array.from(document.querySelectorAll('[data-alert-id]')).map(el => ({
      id: el.dataset.alertId,
      visible: el.offsetParent !== null,
    }))
  };
});
console.log('Current state:', state);
```

## Common LLM Debugging Workflows

### Workflow 1: Test Fails, Unknown Why
```bash
# 1. Check what failed
cat e2e-tests/reports/test-results.json | jq '.suites[].specs[] | select(.ok == false) | {title, error}'

# 2. Get screenshot
find e2e-tests/test-results -name "*failed*.png" -exec ls -lh {} \;

# 3. Check HA logs for errors
grep -i "error\|exception" /workspaces/emergency_alerts/config/home-assistant.log | tail -20

# 4. Check entity states
curl -s http://localhost:8123/api/states | jq '.[] | select(.entity_id | contains("emergency"))'
```

### Workflow 2: Element Not Found
```bash
# 1. Take current screenshot of page
cd e2e-tests
npx playwright screenshot http://localhost:8123/lovelace/emergency current-state.png

# 2. Check if card is loaded
curl -s http://localhost:8123/lovelace/emergency 2>&1 | grep -i "emergency-alerts-card"

# 3. Check browser console for errors (if test is running)
# This requires Playwright to be actively running
```

### Workflow 3: Backend State Mismatch
```bash
# 1. Get all switches for the alert
ALERT_ID="test_alert"
curl -s http://localhost:8123/api/states | jq ".[] | select(.entity_id | contains(\"emergency_${ALERT_ID}\") and contains(\"switch\"))"

# 2. Check binary sensor state
curl -s http://localhost:8123/api/states/binary_sensor.emergency_${ALERT_ID} | jq '.'

# 3. Check integration logs
grep "emergency_alerts" /workspaces/emergency_alerts/config/home-assistant.log | tail -30
```

## Tips for Effective LLM Debugging

1. **Always check artifacts first**: Screenshots and traces tell the story
2. **Verify HA is running**: Many failures are just "HA crashed"
3. **Check state before/after**: Use HA API to verify backend state
4. **Read the test code**: Understanding what the test expects is key
5. **Check recent commits**: Did code changes break something?
6. **Run test locally**: CI environment might differ from local
7. **Use headed mode**: Seeing the browser helps tremendously

## Getting Help

If you (the LLM) are stuck:
1. Take screenshots at every step of the failing test
2. Dump all entity states to a file
3. Extract and analyze the trace file
4. Check if it's a timing issue (add waits)
5. Verify the card is actually loaded (check custom element registry)
6. Check browser console for JavaScript errors

Remember: You have filesystem access, can exec commands, and can read images. Use these powers to debug effectively!
