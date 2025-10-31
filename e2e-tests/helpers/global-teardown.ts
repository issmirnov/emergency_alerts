import { FullConfig } from '@playwright/test';

/**
 * Global Teardown - Runs once after all tests
 *
 * Cleans up test artifacts and resources.
 */

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Running global teardown...');

  // Future: Add cleanup tasks here if needed
  // - Reset test alerts to default state
  // - Clear test data
  // - Archive test artifacts

  console.log('✅ Global teardown complete');
}

export default globalTeardown;
