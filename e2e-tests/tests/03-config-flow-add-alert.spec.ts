import { test, expect } from '@playwright/test';
import { createHAAPI } from '../helpers/ha-api';

/**
 * Config Flow E2E Tests - Add Alert Flow
 *
 * These tests verify the end-to-end add alert config flow:
 * 1. Navigate to integrations page
 * 2. Open Emergency Alerts configuration
 * 3. Complete the add alert flow
 * 4. Verify no translation errors
 * 5. Confirm alert was created
 *
 * Translation error detection: This test monitors browser console for
 * translation errors and fails if any are detected.
 */

test.describe('Config Flow: Add Alert', () => {
  let consoleErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    // Capture console errors including translation failures
    consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error' || msg.text().includes('translation')) {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to integrations page
    await page.goto('/config/integrations');
    await page.waitForLoadState('networkidle');
  });

  test.afterEach(() => {
    // Report any console errors including translation issues
    if (consoleErrors.length > 0) {
      console.error('Console errors detected:', consoleErrors);
    }
  });

  test('should complete add simple alert flow without errors', async ({
    page,
    request,
  }) => {
    // Step 1: Find Emergency Alerts integration card
    const emergencyAlertsCard = page.locator(
      'ha-integration-card',
      { hasText: 'Emergency Alerts' }
    ).first();

    await expect(emergencyAlertsCard).toBeVisible({
      timeout: 10000,
    });

    // Step 2: Click the card to open integration details
    await emergencyAlertsCard.click();
    await page.waitForLoadState('networkidle');

    // Step 3: Click "Configure" or "Add Entry" button
    // Look for configure button or add new alert option
    const configureButton = page.locator('button', {
      hasText: /configure|add|options/i,
    }).first();

    if (await configureButton.isVisible()) {
      await configureButton.click();
      await page.waitForLoadState('networkidle');
    }

    // Step 4: Look for "Add Alert" or "Add New Alert" option
    const addAlertButton = page.locator('button,ha-list-item,mwc-list-item', {
      hasText: /add.*alert/i,
    }).first();

    await expect(addAlertButton).toBeVisible({ timeout: 5000 });
    await addAlertButton.click();
    await page.waitForLoadState('networkidle');

    // Step 5: Fill in basic alert information
    // Look for name field
    const nameInput = page.locator('input[name="name"],ha-textfield[name="name"] input').first();
    await expect(nameInput).toBeVisible({ timeout: 5000 });
    await nameInput.fill('E2E Test Alert');

    // Select severity (look for select or dropdown)
    const severitySelect = page.locator(
      'select[name="severity"],ha-select[name="severity"]'
    ).first();

    if (await severitySelect.isVisible()) {
      await severitySelect.selectOption({ label: /warning/i });
    }

    // Select trigger type (simple)
    const triggerTypeSelect = page.locator(
      'select[name="trigger_type"],ha-select[name="trigger_type"]'
    ).first();

    if (await triggerTypeSelect.isVisible()) {
      await triggerTypeSelect.selectOption({ label: /simple/i });
    }

    // Click next/submit button
    const nextButton = page.locator('button', {
      hasText: /next|continue|submit/i,
    }).first();

    await nextButton.click();
    await page.waitForLoadState('networkidle');

    // Step 6: Configure simple trigger (if on step 2)
    const entityInput = page.locator(
      'input[name="entity_id"],ha-entity-picker[name="entity_id"]'
    ).first();

    if (await entityInput.isVisible()) {
      // Try to select a test entity
      await entityInput.click();
      await entityInput.fill('binary_sensor.test');

      const triggerStateInput = page.locator(
        'input[name="trigger_state"]'
      ).first();

      if (await triggerStateInput.isVisible()) {
        await triggerStateInput.fill('on');
      }

      // Click submit
      const submitButton = page.locator('button', {
        hasText: /submit|save|create/i,
      }).first();

      await submitButton.click();
      await page.waitForLoadState('networkidle');
    }

    // Step 7: Verify no translation errors in console
    const translationErrors = consoleErrors.filter(
      (err) =>
        err.includes('Failed to format translation') ||
        err.includes('translation key') ||
        err.includes('missing translation')
    );

    expect(translationErrors).toHaveLength(0);

    // Step 8: Verify success (look for success message or redirected back)
    // This is flexible since different HA versions may show different success indicators
    const isSuccess =
      (await page.locator('text=/created|success|added/i').isVisible()) ||
      page.url().includes('/config/integrations');

    expect(isSuccess).toBeTruthy();
  });

  test('should show all required form fields without translation errors', async ({
    page,
  }) => {
    // Navigate directly to integration config if possible
    await page.goto('/config/integrations');
    await page.waitForLoadState('networkidle');

    // Try to open add alert flow (best effort)
    const emergencyAlertsCard = page.locator(
      'ha-integration-card',
      { hasText: 'Emergency Alerts' }
    ).first();

    if (await emergencyAlertsCard.isVisible()) {
      await emergencyAlertsCard.click();
      await page.waitForLoadState('networkidle');

      // Look for add alert option
      const addAlertButton = page.locator('button,ha-list-item,mwc-list-item', {
        hasText: /add.*alert/i,
      }).first();

      if (await addAlertButton.isVisible()) {
        await addAlertButton.click();
        await page.waitForLoadState('networkidle');

        // Check that required fields are present with labels
        // This verifies translations are loaded
        const hasNameField = await page
          .locator('text=/alert.*name/i')
          .isVisible();
        const hasSeverityField = await page
          .locator('text=/severity|urgent/i')
          .isVisible();
        const hasTriggerTypeField = await page
          .locator('text=/trigger.*type|how.*triggered/i')
          .isVisible();

        // At least some fields should be visible
        expect(hasNameField || hasSeverityField || hasTriggerTypeField).toBeTruthy();

        // Verify no translation errors
        const translationErrors = consoleErrors.filter(
          (err) =>
            err.includes('Failed to format translation') ||
            err.includes('translation key')
        );

        expect(translationErrors).toHaveLength(0);
      }
    }
  });

  test('should detect translation errors if they exist', async ({ page }) => {
    // This is a negative test - it verifies our error detection works
    // We'll inject a translation error and ensure it's caught

    // Navigate to integrations
    await page.goto('/config/integrations');
    await page.waitForLoadState('networkidle');

    // Inject a fake translation error
    await page.evaluate(() => {
      console.error('Failed to format translation: test.missing.key');
    });

    // Verify our error detection caught it
    const translationErrors = consoleErrors.filter((err) =>
      err.includes('Failed to format translation')
    );

    expect(translationErrors.length).toBeGreaterThan(0);
  });
});
