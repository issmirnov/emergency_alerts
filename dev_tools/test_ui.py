#!/usr/bin/env python3
"""
Quick Playwright test to verify Emergency Alerts UI
"""
from playwright.sync_api import sync_playwright, expect
import time

def test_emergency_alerts_ui():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to True for headless
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate to HA
        print("Navigating to http://localhost:8123")
        page.goto("http://localhost:8123")
        time.sleep(3)
        
        # Check current page state
        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")
        
        # Take screenshot
        page.screenshot(path="dev_tools/ha_screenshot_1.png")
        print("Screenshot saved: dev_tools/ha_screenshot_1.png")
        
        # Try to find and click settings
        try:
            # Wait for page to load
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Look for settings menu
            settings_button = page.locator('a[href="/config"]').first
            if settings_button.is_visible():
                print("Found settings button, clicking...")
                settings_button.click()
                time.sleep(2)
                page.screenshot(path="dev_tools/ha_screenshot_2_settings.png")
            else:
                print("Settings button not visible")
        except Exception as e:
            print(f"Error navigating: {e}")
        
        # Look for any error messages
        error_elements = page.locator('.error, [role="alert"], .notification').all()
        if error_elements:
            print(f"\nFound {len(error_elements)} potential error/notification elements:")
            for i, elem in enumerate(error_elements):
                try:
                    text = elem.text_content()
                    if text and text.strip():
                        print(f"  {i+1}. {text.strip()}")
                except:
                    pass
        
        # Check console logs
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        time.sleep(2)
        
        if console_messages:
            print("\nConsole messages:")
            for msg in console_messages:
                print(f"  {msg}")
        
        # Keep browser open for manual inspection
        print("\nBrowser will stay open for 30 seconds for manual inspection...")
        time.sleep(30)
        
        browser.close()

if __name__ == "__main__":
    test_emergency_alerts_ui()