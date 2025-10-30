import { APIRequestContext } from '@playwright/test';

/**
 * Home Assistant REST API Client
 *
 * Provides typed access to HA's REST API for test setup and validation.
 *
 * Usage:
 *   const haApi = new HomeAssistantAPI(request);
 *   const states = await haApi.getAllStates();
 *   await haApi.callService('switch', 'turn_on', { entity_id: '...' });
 */

export interface HAState {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_changed: string;
  last_updated: string;
}

export interface HAConfig {
  latitude: number;
  longitude: number;
  elevation: number;
  unit_system: Record<string, string>;
  location_name: string;
  time_zone: string;
  components: string[];
  version: string;
}

export class HomeAssistantAPI {
  private baseUrl: string;
  private request: APIRequestContext;
  private token?: string;

  constructor(request: APIRequestContext, baseUrl = 'http://localhost:8123') {
    this.request = request;
    this.baseUrl = baseUrl;
  }

  /**
   * Set long-lived access token for authentication
   */
  setToken(token: string) {
    this.token = token;
  }

  /**
   * Get all entity states from Home Assistant
   */
  async getAllStates(): Promise<HAState[]> {
    const response = await this.request.get(`${this.baseUrl}/api/states`, {
      headers: this.getHeaders(),
    });
    return response.json();
  }

  /**
   * Get state of a specific entity
   */
  async getState(entityId: string): Promise<HAState> {
    const response = await this.request.get(`${this.baseUrl}/api/states/${entityId}`, {
      headers: this.getHeaders(),
    });

    if (!response.ok()) {
      throw new Error(`Failed to get state for ${entityId}: ${response.statusText()}`);
    }

    return response.json();
  }

  /**
   * Call a Home Assistant service
   */
  async callService(
    domain: string,
    service: string,
    data?: Record<string, any>
  ): Promise<HAState[]> {
    const response = await this.request.post(
      `${this.baseUrl}/api/services/${domain}/${service}`,
      {
        headers: this.getHeaders(),
        data: data || {},
      }
    );

    if (!response.ok()) {
      throw new Error(`Service call failed: ${response.statusText()}`);
    }

    return response.json();
  }

  /**
   * Get Home Assistant configuration
   */
  async getConfig(): Promise<HAConfig> {
    const response = await this.request.get(`${this.baseUrl}/api/config`, {
      headers: this.getHeaders(),
    });
    return response.json();
  }

  /**
   * Wait for entity to reach a specific state
   */
  async waitForState(
    entityId: string,
    expectedState: string,
    timeoutMs = 10000
  ): Promise<void> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      try {
        const state = await this.getState(entityId);
        if (state.state === expectedState) {
          return;
        }
      } catch (error) {
        // Entity might not exist yet, continue waiting
      }

      await this.sleep(500);
    }

    throw new Error(
      `Timeout waiting for ${entityId} to reach state "${expectedState}"`
    );
  }

  /**
   * Wait for entity attribute to match a value
   */
  async waitForAttribute(
    entityId: string,
    attributeName: string,
    expectedValue: any,
    timeoutMs = 10000
  ): Promise<void> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      try {
        const state = await this.getState(entityId);
        if (state.attributes[attributeName] === expectedValue) {
          return;
        }
      } catch (error) {
        // Entity might not exist yet, continue waiting
      }

      await this.sleep(500);
    }

    throw new Error(
      `Timeout waiting for ${entityId}.${attributeName} to equal "${expectedValue}"`
    );
  }

  /**
   * Find all emergency alert entities
   */
  async getEmergencyAlerts(): Promise<HAState[]> {
    const states = await this.getAllStates();
    return states.filter(s => s.entity_id.startsWith('binary_sensor.emergency_'));
  }

  /**
   * Find all emergency alert switches
   */
  async getEmergencyAlertSwitches(alertId?: string): Promise<HAState[]> {
    const states = await this.getAllStates();
    const pattern = alertId
      ? `switch.emergency_${alertId}_`
      : 'switch.emergency_';
    return states.filter(s => s.entity_id.startsWith(pattern));
  }

  /**
   * Check if Home Assistant is ready
   */
  async isReady(): Promise<boolean> {
    try {
      const config = await this.getConfig();
      return !!config.version;
    } catch {
      return false;
    }
  }

  /**
   * Wait for Home Assistant to be ready
   */
  async waitForReady(timeoutMs = 60000): Promise<void> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      if (await this.isReady()) {
        return;
      }
      await this.sleep(1000);
    }

    throw new Error('Timeout waiting for Home Assistant to be ready');
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Helper to create HA API instance in tests
 */
export function createHAAPI(request: APIRequestContext): HomeAssistantAPI {
  return new HomeAssistantAPI(request);
}
