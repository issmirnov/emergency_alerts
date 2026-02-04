/**
 * Create a long-lived access token for Home Assistant API
 * Uses Playwright to log in and create a token
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function createToken() {
  console.log('🔐 Creating Home Assistant API token...');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to HA
    await page.goto('http://localhost:8123');
    
    // Check if we need to log in
    const loginForm = await page.$('input[type="text"]');
    if (loginForm) {
      console.log('  ✓ Logging in...');
      await page.fill('input[type="text"]', 'dev');
      await page.fill('input[type="password"]', 'dev');
      await page.keyboard.press('Enter');
      await page.waitForURL('**/lovelace/**', { timeout: 10000 });
    }
    
    // Navigate to profile page
    console.log('  ✓ Navigating to profile...');
    await page.goto('http://localhost:8123/profile');
    await page.waitForLoadState('networkidle');
    
    // Find and click "Long-Lived Access Tokens"
    console.log('  ✓ Looking for token section...');
    await page.waitForTimeout(2000);
    
    // Try to find the token section - it might be in a shadow DOM or specific selector
    const tokenSection = await page.locator('text=Long-Lived Access Tokens').first();
    if (await tokenSection.count() > 0) {
      await tokenSection.click();
      await page.waitForTimeout(1000);
      
      // Click "Create Token"
      const createButton = await page.locator('text=Create Token').first();
      if (await createButton.count() > 0) {
        await createButton.click();
        await page.waitForTimeout(1000);
        
        // Fill in token name
        const nameInput = await page.locator('input[type="text"]').last();
        await nameInput.fill('E2E Tests');
        
        // Submit
        const submitButton = await page.locator('mwc-button[label="OK"], button:has-text("OK")').first();
        await submitButton.click();
        
        // Wait for token to appear
        await page.waitForTimeout(2000);
        
        // Try to get the token from the page
        const tokenElement = await page.locator('ha-textfield[value], input[value]').last();
        const token = await tokenElement.inputValue();
        
        if (token && token.length > 20) {
          console.log('  ✓ Token created!');
          
          // Save to .env file
          const envPath = path.join(__dirname, '../e2e-tests/.env');
          const envContent = `HA_BASE_URL=http://localhost:8123\nHA_TOKEN=${token}\n`;
          fs.writeFileSync(envPath, envContent);
          console.log(`  ✓ Token saved to ${envPath}`);
          console.log(`\n✅ Token: ${token.substring(0, 20)}...`);
          return token;
        }
      }
    }
    
    console.log('  ⚠️  Could not create token automatically');
    console.log('  Please create it manually:');
    console.log('    1. Go to http://localhost:8123/profile');
    console.log('    2. Scroll to "Long-Lived Access Tokens"');
    console.log('    3. Click "Create Token"');
    console.log('    4. Name it "E2E Tests"');
    console.log('    5. Copy the token and save it to e2e-tests/.env as HA_TOKEN=...');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await browser.close();
  }
}

createToken().catch(console.error);
