#!/bin/bash

# Emergency Alerts E2E Test Runner
#
# This script runs end-to-end tests for the Emergency Alerts integration and card.
#
# Usage:
#   ./scripts/run-e2e.sh              # Run all tests
#   ./scripts/run-e2e.sh --headed     # Run with visible browser
#   ./scripts/run-e2e.sh --debug      # Run in debug mode
#   ./scripts/run-e2e.sh --ui         # Run in interactive UI mode
#   ./scripts/run-e2e.sh --grep smoke # Run only smoke tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${2}${1}${NC}"
}

print_status "🧪 Emergency Alerts E2E Test Suite" "$BLUE"
print_status "====================================" "$BLUE"
echo ""

# Check if we're in the right directory
if [ ! -d "e2e-tests" ]; then
    print_status "❌ Please run this script from the project root" "$RED"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_status "❌ Node.js is not installed. Please install Node.js 18+" "$RED"
    exit 1
fi

# Check if Home Assistant is running
print_status "📡 Checking Home Assistant..." "$YELLOW"
if ! curl -sf http://localhost:8123 > /dev/null 2>&1; then
    print_status "❌ Home Assistant is not running on localhost:8123" "$RED"
    print_status "   Start it with: hass --config ./config" "$YELLOW"
    exit 1
fi
print_status "✓ Home Assistant is running" "$GREEN"

# Install dependencies if needed
if [ ! -d "e2e-tests/node_modules" ]; then
    print_status "📦 Installing test dependencies..." "$YELLOW"
    cd e2e-tests
    npm install
    npx playwright install --with-deps chromium
    cd ..
    print_status "✓ Dependencies installed" "$GREEN"
fi

# Check if card is built
CARD_PATH="../lovelace-emergency-alerts-card/dist/emergency-alerts-card.js"
if [ ! -f "$CARD_PATH" ]; then
    print_status "⚠️  Emergency Alerts Card not found at: $CARD_PATH" "$YELLOW"
    print_status "   Building card..." "$YELLOW"

    if [ -d "../lovelace-emergency-alerts-card" ]; then
        cd ../lovelace-emergency-alerts-card
        npm run build
        cd - > /dev/null
        print_status "✓ Card built successfully" "$GREEN"
    else
        print_status "❌ Card repository not found. Clone it next to this repo." "$RED"
        exit 1
    fi
fi

# Copy card to HA www directory if needed
if [ -f "$CARD_PATH" ]; then
    mkdir -p config/www
    cp "$CARD_PATH" config/www/
    print_status "✓ Card copied to Home Assistant www directory" "$GREEN"
fi

# Run tests
print_status "🚀 Running E2E tests..." "$BLUE"
echo ""

cd e2e-tests

# Pass all arguments to playwright
npm test -- "$@"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_status "✅ All tests passed!" "$GREEN"
else
    print_status "❌ Some tests failed" "$RED"
    print_status "" ""
    print_status "Debugging tips:" "$YELLOW"
    print_status "  - View HTML report: npm run report (in e2e-tests/)" "$BLUE"
    print_status "  - Check screenshots: e2e-tests/.screenshots/" "$BLUE"
    print_status "  - Check traces: e2e-tests/test-results/" "$BLUE"
    print_status "  - Run headed: ./scripts/run-e2e.sh --headed" "$BLUE"
    print_status "  - Run UI mode: ./scripts/run-e2e.sh --ui" "$BLUE"
fi

cd ..
exit $TEST_EXIT_CODE
