import { test, expect } from '@playwright/test';
import { createHAAPI } from '../helpers/ha-api';
import { createAlertHelpers } from '../helpers/alert-helpers';

/**
 * Integration Tests - Card ↔ Backend Interaction
 *
 * These tests verify that the card and integration work together:
 * 1. Clicking switches updates backend state
 * 2. Backend state changes update card UI
 * 3. Mutual exclusivity is enforced
 * 4. Status badges display correctly
 *
 * Prerequisites: At least one test alert must be configured in HA
 */

test.describe('Integration Tests', () => {
  let testAlertId: string;

  test.beforeAll(async ({ request }) => {
    // Find a test alert to use
    const haApi = createHAAPI(request);
    const alerts = await haApi.getEmergencyAlerts();

    if (alerts.length === 0) {
      throw new Error(
        'No emergency alerts found. Please configure at least one test alert in Home Assistant.'
      );
    }

    // Use the first alert, extract ID from entity_id
    // binary_sensor.emergency_test_alert → test_alert
    testAlertId = alerts[0].entity_id.replace('binary_sensor.emergency_', '');
    console.log(`Using test alert: ${testAlertId}`);
  });

  test.beforeEach(async ({ page, request }) => {
    // Reset all switches to off before each test
    const haApi = createHAAPI(request);
    const switches = await haApi.getEmergencyAlertSwitches(testAlertId);

    for (const sw of switches) {
      if (sw.state === 'on') {
        await haApi.callService('switch', 'turn_off', {
          entity_id: sw.entity_id,
        });
      }
    }

    // Navigate to emergency dashboard
    await page.goto('/lovelace/emergency');
    await page.waitForLoadState('networkidle');
  });

  test('Acknowledge switch updates backend state', async ({ page, request }) => {
    const haApi = createHAAPI(request);
    const alertHelpers = createAlertHelpers(page, haApi);

    await alertHelpers.waitForCardReady();
    await alertHelpers.waitForAlertVisible(testAlertId);

    // Click acknowledge switch
    const ackSwitch = alertHelpers.getAcknowledgeSwitch(testAlertId);
    await ackSwitch.click();

    // Verify backend state updated
    const state = await haApi.getState(
      `switch.emergency_${testAlertId}_acknowledged`
    );
    expect(state.state).toBe('on');
  });

  test('Backend acknowledge updates card UI', async ({ page, request }) => {
    const haApi = createHAAPI(request);
    const alertHelpers = createAlertHelpers(page, haApi);

    await alertHelpers.waitForCardReady();
    await alertHelpers.waitForAlertVisible(testAlertId);

    // Turn on acknowledge via API
    await haApi.callService('switch', 'turn_on', {
      entity_id: `switch.emergency_${testAlertId}_acknowledged`,
    });

    // Wait for UI to update
    await page.waitForTimeout(1000);

    // Verify UI shows acknowledged state
    const statusBadge = alertHelpers.getStatusBadge(testAlertId);
    await expect(statusBadge).toContainText('ACKNOWLEDGED', {
      ignoreCase: true,
      timeout: 5000,
    });
  });

  test('Snooze switch updates backend and shows timer', async ({
    page,
    request,
  }) => {
    const haApi = createHAAPI(request);
    const alertHelpers = createAlertHelpers(page, haApi);

    await alertHelpers.waitForCardReady();
    await alertHelpers.waitForAlertVisible(testAlertId);

    // Click snooze switch
    const snoozeSwitch = alertHelpers.getSnoozeSwitch(testAlertId);
    await snoozeSwitch.click();

    // Verify backend state
    const state = await haApi.getState(
      `switch.emergency_${testAlertId}_snoozed`
    );
    expect(state.state).toBe('on');

    // Verify snooze timer appears in UI
    const statusBadge = alertHelpers.getStatusBadge(testAlertId);
    await expect(statusBadge).toContainText('SNOOZED', {
      ignoreCase: true,
      timeout: 5000,
    });
  });

  test('Resolve switch updates backend and fades alert', async ({
    page,
    request,
  }) => {
    const haApi = createHAAPI(request);
    const alertHelpers = createAlertHelpers(page, haApi);

    await alertHelpers.waitForCardReady();
    await alertHelpers.waitForAlertVisible(testAlertId);

    // Click resolve switch
    const resolveSwitch = alertHelpers.getResolveSwitch(testAlertId);
    await resolveSwitch.click();

    // Verify backend state
    const state = await haApi.getState(
      `switch.emergency_${testAlertId}_resolved`
    );
    expect(state.state).toBe('on');

    // Verify UI shows resolved state
    const statusBadge = alertHelpers.getStatusBadge(testAlertId);
    await expect(statusBadge).toContainText('RESOLVED', {
      ignoreCase: true,
      timeout: 5000,
    });

    // Verify alert card has reduced opacity (faded)
    const alertCard = alertHelpers.getAlertCard(testAlertId);
    const opacity = await alertCard.evaluate((el) => {
      return window.getComputedStyle(el).opacity;
    });
    expect(parseFloat(opacity)).toBeLessThan(1.0);
  });

  test('Mutual exclusivity: turning on one switch turns off others', async ({
    page,
    request,
  }) => {
    const haApi = createHAAPI(request);
    const alertHelpers = createAlertHelpers(page, haApi);

    await alertHelpers.waitForCardReady();
    await alertHelpers.waitForAlertVisible(testAlertId);

    // Turn on acknowledge
    await alertHelpers.acknowledgeAlert(testAlertId);

    // Verify acknowledge is on
    let ackState = await haApi.getState(
      `switch.emergency_${testAlertId}_acknowledged`
    );
    expect(ackState.state).toBe('on');

    // Turn on snooze
    await alertHelpers.snoozeAlert(testAlertId);

    // Verify snooze is on and acknowledge is now off
    const snoozeState = await haApi.getState(
      `switch.emergency_${testAlertId}_snoozed`
    );
    expect(snoozeState.state).toBe('on');

    ackState = await haApi.getState(
      `switch.emergency_${testAlertId}_acknowledged`
    );
    expect(ackState.state).toBe('off');

    // Turn on resolve
    await alertHelpers.resolveAlert(testAlertId);

    // Verify resolve is on and snooze is now off
    const resolveState = await haApi.getState(
      `switch.emergency_${testAlertId}_resolved`
    );
    expect(resolveState.state).toBe('on');

    const newSnoozeState = await haApi.getState(
      `switch.emergency_${testAlertId}_snoozed`
    );
    expect(newSnoozeState.state).toBe('off');
  });

  test('Visual regression: alert card appearance', async ({ page, request }) => {
    const alertHelpers = createAlertHelpers(page, createHAAPI(request));

    await alertHelpers.waitForCardReady();
    await alertHelpers.waitForAlertVisible(testAlertId);

    // Take screenshot for visual comparison
    await alertHelpers.screenshotAlert(testAlertId, 'alert-default-state');

    // This creates a baseline - future runs will compare against it
    // Playwright will fail if the UI changes significantly
  });

  test('LLM Debugging: can inspect element states', async ({
    page,
    request,
  }) => {
    const haApi = createHAAPI(request);
    const alertHelpers = createAlertHelpers(page, haApi);

    await alertHelpers.waitForCardReady();
    await alertHelpers.waitForAlertVisible(testAlertId);

    // Get alert card element info for LLM inspection
    const cardInfo = await page.evaluate((alertId) => {
      const card = document.querySelector(`[data-alert-id="${alertId}"]`);
      if (!card) return null;

      return {
        tagName: card.tagName,
        className: card.className,
        innerHTML: card.innerHTML.substring(0, 500), // First 500 chars
        boundingBox: card.getBoundingClientRect(),
        computedStyle: {
          display: window.getComputedStyle(card).display,
          opacity: window.getComputedStyle(card).opacity,
          visibility: window.getComputedStyle(card).visibility,
        },
      };
    }, testAlertId);

    // This test documents what's available for LLM debugging
    expect(cardInfo).not.toBeNull();
    console.log('Alert Card Info for LLM:', JSON.stringify(cardInfo, null, 2));

    // Get backend state for comparison
    const backendState = await haApi.getAlertState(testAlertId);
    console.log('Backend State:', JSON.stringify(backendState, null, 2));
  });
});
