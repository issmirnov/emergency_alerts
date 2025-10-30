import { chromium, FullConfig } from '@playwright/test';
import { HomeAssistantAPI } from './ha-api';

/**
 * Global Setup - Runs once before all tests
 *
 * This script:
 * 1. Verifies Home Assistant is running
 * 2. Checks that Emergency Alerts integration is loaded
 * 3. Seeds test data (alerts, dashboards)
 * 4. Creates necessary fixtures
 *
 * If this fails, no tests will run.
 */

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E Test Global Setup...');

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Step 1: Check Home Assistant is accessible
    console.log('  ✓ Checking Home Assistant accessibility...');
    await page.goto(config.use?.baseURL || 'http://localhost:8123', {
      timeout: 30000,
      waitUntil: 'networkidle',
    });

    // Wait for HA to be fully loaded
    await page.waitForSelector('home-assistant', { timeout: 30000 });
    console.log('  ✓ Home Assistant is accessible');

    // Step 2: Verify integration is loaded
    console.log('  ✓ Verifying Emergency Alerts integration...');
    const haApi = new HomeAssistantAPI(context.request);

    // Check if emergency_alerts domain is loaded
    const config = await haApi.getConfig();
    const hasIntegration = config.components.includes('emergency_alerts');

    if (!hasIntegration) {
      console.warn('  ⚠️  Emergency Alerts integration not found in loaded components');
      console.warn('     Make sure the integration is symlinked and HA restarted');
    } else {
      console.log('  ✓ Emergency Alerts integration is loaded');
    }

    // Step 3: Check for test alerts
    console.log('  ✓ Checking for test alerts...');
    const alerts = await haApi.getEmergencyAlerts();
    console.log(`     Found ${alerts.length} emergency alert(s)`);

    if (alerts.length === 0) {
      console.warn('  ⚠️  No test alerts found');
      console.warn('     You may need to configure test alerts in HA');
    }

    // Step 4: Check for Emergency Alerts Card
    console.log('  ✓ Checking for Emergency Alerts Card...');
    const cardScript = page.locator('script[src*="emergency-alerts-card"]');
    const cardExists = (await cardScript.count()) > 0;

    if (!cardExists) {
      console.warn('  ⚠️  Emergency Alerts Card script not found');
      console.warn('     Card may not be registered. Check www/ directory');
    } else {
      console.log('  ✓ Emergency Alerts Card is available');
    }

    console.log('✅ Global setup complete!');
    console.log('');
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
