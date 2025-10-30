import { test, expect } from '@playwright/test';
import { createHAAPI } from '../helpers/ha-api';
import { createAlertHelpers } from '../helpers/alert-helpers';

/**
 * Smoke Tests - Basic Functionality
 *
 * These tests verify that the fundamental pieces are working:
 * 1. Home Assistant is accessible
 * 2. Emergency Alerts integration is loaded
 * 3. Emergency Alerts Card renders
 * 4. Basic alert display works
 *
 * If these fail, something is fundamentally broken.
 */

test.describe('Smoke Tests', () => {
  test('Home Assistant is accessible', async ({ page }) => {
    await page.goto('/');

    // Wait for HA to load
    await page.waitForSelector('home-assistant', { timeout: 30000 });

    // Verify title
    await expect(page).toHaveTitle(/Home Assistant/);

    // Verify we can see the main UI
    const homeAssistant = page.locator('home-assistant');
    await expect(homeAssistant).toBeVisible();
  });

  test('Emergency Alerts integration is loaded', async ({ request }) => {
    const haApi = createHAAPI(request);

    // Check HA is ready
    const isReady = await haApi.isReady();
    expect(isReady).toBe(true);

    // Get config and verify emergency_alerts is in components
    const config = await haApi.getConfig();
    expect(config.components).toContain('emergency_alerts');

    // Verify we can get emergency alert entities
    const alerts = await haApi.getEmergencyAlerts();
    // We don't require any alerts to exist, just that the API works
    expect(Array.isArray(alerts)).toBe(true);
  });

  test('Emergency Alerts Card is available', async ({ page }) => {
    await page.goto('/');

    // Check if the card's JS file is loaded
    const cardScript = page.locator('script[src*="emergency-alerts-card"]');
    const scriptCount = await cardScript.count();

    if (scriptCount === 0) {
      // Card might be loaded via resources or not on this page yet
      // Let's check if the custom element is defined
      const isCardDefined = await page.evaluate(() => {
        return customElements.get('emergency-alerts-card') !== undefined;
      });

      expect(isCardDefined).toBe(true);
    }
  });

  test('Emergency dashboard loads', async ({ page }) => {
    // Navigate to the emergency dashboard (created by devcontainer setup)
    await page.goto('/lovelace/emergency');

    // Wait for Lovelace to load
    await page.waitForSelector('hui-view', { timeout: 10000 });

    // Verify the page loaded
    const view = page.locator('hui-view');
    await expect(view).toBeVisible();
  });

  test('Emergency Alerts Card renders on dashboard', async ({ page }) => {
    await page.goto('/lovelace/emergency');

    // Wait for the custom card to appear
    const card = page.locator('emergency-alerts-card');
    await expect(card).toBeVisible({ timeout: 15000 });

    // Verify card has rendered content
    const hasContent = await card.evaluate((el) => {
      return el.shadowRoot !== null && el.shadowRoot.children.length > 0;
    });

    expect(hasContent).toBe(true);
  });

  test('Can interact with Home Assistant API', async ({ request }) => {
    const haApi = createHAAPI(request);

    // Test getting all states
    const states = await haApi.getAllStates();
    expect(states.length).toBeGreaterThan(0);

    // Test getting config
    const config = await haApi.getConfig();
    expect(config.version).toBeDefined();
    expect(config.components).toBeDefined();
    expect(config.components.length).toBeGreaterThan(0);
  });

  test('Alert helpers can locate card elements', async ({ page, request }) => {
    const haApi = createHAAPI(request);
    const alertHelpers = createAlertHelpers(page, haApi);

    await page.goto('/lovelace/emergency');

    // Wait for card to be ready
    await alertHelpers.waitForCardReady();

    // Verify we can find the card element
    const card = alertHelpers.getEmergencyAlertsCard();
    await expect(card).toBeVisible();
  });

  test('Can take screenshots for LLM inspection', async ({ page }) => {
    await page.goto('/lovelace/emergency');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Take a screenshot
    const screenshot = await page.screenshot({
      path: '.screenshots/smoke-test-dashboard.png',
      fullPage: true,
    });

    expect(screenshot).toBeDefined();
    expect(screenshot.length).toBeGreaterThan(0);
  });
});
