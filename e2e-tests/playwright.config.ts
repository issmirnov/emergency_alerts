import { defineConfig, devices } from '@playwright/test';
import * as path from 'path';

/**
 * E2E Test Configuration for Emergency Alerts
 *
 * LLM Debugging Features:
 * - Trace viewer: See time-travel debugging of test runs
 * - Screenshots: Automatic screenshots on failure
 * - Videos: Record full test runs for visual inspection
 * - CDP: Chrome DevTools Protocol access for deep inspection
 *
 * Usage:
 * - Run tests: npm test
 * - Debug mode: npm run test:debug
 * - UI mode: npm run test:ui (interactive mode)
 * - Headed mode: npm run test:headed (see browser)
 * - View report: npm run report
 */

// Load environment variables from .env file
require('dotenv').config({ path: path.join(__dirname, '.env') });

export default defineConfig({
  testDir: './tests',

  // Maximum time one test can run
  timeout: 60 * 1000,

  // Test execution settings
  fullyParallel: false, // Run tests sequentially to avoid HA state conflicts
  forbidOnly: !!process.env.CI, // Fail CI if test.only() is left in
  retries: process.env.CI ? 2 : 0, // Retry on CI, not locally
  workers: 1, // Single worker to avoid HA state conflicts

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'reports', open: 'never' }],
    ['list'],
    ['json', { outputFile: 'reports/test-results.json' }],
  ],

  // Global test settings
  use: {
    // Base URL for all tests
    baseURL: 'http://localhost:8123',

    // Collect trace on failure for LLM inspection
    trace: 'retain-on-failure',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Slow down operations for visual debugging
    launchOptions: {
      slowMo: process.env.SLOW_MO ? parseInt(process.env.SLOW_MO) : 0,
      // Enable CDP for LLM debugging
      args: [
        '--remote-debugging-port=9222', // CDP endpoint
        '--no-sandbox',
        '--disable-setuid-sandbox',
      ],
    },

    // Viewport size
    viewport: { width: 1280, height: 720 },

    // Ignore HTTPS errors (devcontainer may use self-signed certs)
    ignoreHTTPSErrors: true,

    // Timeouts
    actionTimeout: 10 * 1000,
    navigationTimeout: 30 * 1000,
  },

  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Additional chromium-specific settings
        contextOptions: {
          // Enable console logs
          recordVideo: {
            dir: 'reports/videos/',
            size: { width: 1280, height: 720 }
          }
        }
      },
    },

    // Uncomment to test in Firefox/Safari
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    // Mobile testing (optional)
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
  ],

  // Web server configuration
  webServer: {
    // NOTE: Home Assistant should already be running in devcontainer
    // This is just a health check
    command: 'echo "Home Assistant should already be running on :8123"',
    url: 'http://localhost:8123',
    timeout: 5 * 1000,
    reuseExistingServer: true,
  },

  // Global setup/teardown
  globalSetup: require.resolve('./helpers/global-setup.ts'),
  globalTeardown: require.resolve('./helpers/global-teardown.ts'),
});
