import { Page, Locator } from '@playwright/test';
import { HomeAssistantAPI } from './ha-api';

/**
 * Alert Test Helpers
 *
 * High-level helpers for interacting with Emergency Alerts in tests.
 */

export class AlertHelpers {
  constructor(
    private page: Page,
    private haApi: HomeAssistantAPI
  ) {}

  /**
   * Find an alert card element by alert ID
   */
  getAlertCard(alertId: string): Locator {
    return this.page.locator(`[data-alert-id="${alertId}"]`);
  }

  /**
   * Get acknowledge switch for an alert
   */
  getAcknowledgeSwitch(alertId: string): Locator {
    return this.page.locator(
      `[data-alert-id="${alertId}"] .switch-acknowledge, ` +
        `[data-alert-id="${alertId}"] [data-switch-type="acknowledge"]`
    );
  }

  /**
   * Get snooze switch for an alert
   */
  getSnoozeSwitch(alertId: string): Locator {
    return this.page.locator(
      `[data-alert-id="${alertId}"] .switch-snooze, ` +
        `[data-alert-id="${alertId}"] [data-switch-type="snooze"]`
    );
  }

  /**
   * Get resolve switch for an alert
   */
  getResolveSwitch(alertId: string): Locator {
    return this.page.locator(
      `[data-alert-id="${alertId}"] .switch-resolve, ` +
        `[data-alert-id="${alertId}"] [data-switch-type="resolve"]`
    );
  }

  /**
   * Get alert status badge
   */
  getStatusBadge(alertId: string): Locator {
    return this.page.locator(`[data-alert-id="${alertId}"] .badge, [data-alert-id="${alertId}"] .status-badge`);
  }

  /**
   * Click acknowledge switch and wait for state update
   */
  async acknowledgeAlert(alertId: string): Promise<void> {
    const switchLocator = this.getAcknowledgeSwitch(alertId);
    await switchLocator.click();

    // Wait for backend state to update
    await this.haApi.waitForState(
      `switch.emergency_${alertId}_acknowledged`,
      'on',
      5000
    );
  }

  /**
   * Click snooze switch and wait for state update
   */
  async snoozeAlert(alertId: string): Promise<void> {
    const switchLocator = this.getSnoozeSwitch(alertId);
    await switchLocator.click();

    // Wait for backend state to update
    await this.haApi.waitForState(
      `switch.emergency_${alertId}_snoozed`,
      'on',
      5000
    );
  }

  /**
   * Click resolve switch and wait for state update
   */
  async resolveAlert(alertId: string): Promise<void> {
    const switchLocator = this.getResolveSwitch(alertId);
    await switchLocator.click();

    // Wait for backend state to update
    await this.haApi.waitForState(
      `switch.emergency_${alertId}_resolved`,
      'on',
      5000
    );
  }

  /**
   * Trigger an alert via backend API
   */
  async triggerAlert(alertId: string): Promise<void> {
    // Get the binary sensor entity
    const entityId = `binary_sensor.emergency_${alertId}`;

    // For testing, we can use input_boolean or directly set state
    // This assumes you have a way to trigger the alert condition
    // You may need to adjust based on your actual trigger type

    await this.haApi.callService('homeassistant', 'update_entity', {
      entity_id: entityId,
    });
  }

  /**
   * Wait for alert to appear in UI
   */
  async waitForAlertVisible(alertId: string, timeoutMs = 10000): Promise<void> {
    await this.getAlertCard(alertId).waitFor({
      state: 'visible',
      timeout: timeoutMs,
    });
  }

  /**
   * Get alert state from backend
   */
  async getAlertState(alertId: string) {
    return await this.haApi.getState(`binary_sensor.emergency_${alertId}`);
  }

  /**
   * Get all alert switch states for an alert
   */
  async getAlertSwitches(alertId: string) {
    const switches = await this.haApi.getEmergencyAlertSwitches(alertId);
    return {
      acknowledged: switches.find(s => s.entity_id.includes('_acknowledged')),
      snoozed: switches.find(s => s.entity_id.includes('_snoozed')),
      resolved: switches.find(s => s.entity_id.includes('_resolved')),
    };
  }

  /**
   * Take screenshot of alert card for visual inspection
   */
  async screenshotAlert(alertId: string, name: string): Promise<Buffer> {
    const card = this.getAlertCard(alertId);
    return await card.screenshot({ path: `.screenshots/${name}.png` });
  }

  /**
   * Get the Emergency Alerts Card custom element
   */
  getEmergencyAlertsCard(): Locator {
    return this.page.locator('emergency-alerts-card');
  }

  /**
   * Wait for card to be loaded and rendered
   */
  async waitForCardReady(timeoutMs = 10000): Promise<void> {
    const card = this.getEmergencyAlertsCard();
    await card.waitFor({ state: 'attached', timeout: timeoutMs });

    // Wait for the card to finish initial render
    await this.page.waitForTimeout(500);
  }

  /**
   * Navigate to emergency dashboard
   */
  async navigateToEmergencyDashboard(): Promise<void> {
    await this.page.goto('/lovelace/emergency');
    await this.waitForCardReady();
  }
}

/**
 * Create AlertHelpers instance
 */
export function createAlertHelpers(
  page: Page,
  haApi: HomeAssistantAPI
): AlertHelpers {
  return new AlertHelpers(page, haApi);
}
