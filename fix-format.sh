#!/bin/bash

# Emergency Alerts Integration - Auto-fix Formatting Script
# This script automatically fixes formatting and import sorting issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

print_section() {
    echo
    echo -e "${BLUE}$1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

# Check if we're in the right directory
if [ ! -f "custom_components/emergency_alerts/manifest.json" ]; then
    print_status "❌ Error: Must be run from the emergency-alerts-integration root directory" "$RED"
    exit 1
fi

print_section "🛠️  Emergency Alerts Integration - Auto-fix Formatting"

# Create or activate virtual environment
VENV_DIR="lint_venv"

if [ ! -d "$VENV_DIR" ]; then
    print_status "📦 Creating virtual environment..." "$YELLOW"
    python -m venv "$VENV_DIR"
fi

print_status "🔄 Activating virtual environment..." "$YELLOW"
source "$VENV_DIR/bin/activate"

# Install/upgrade linting tools
print_status "📥 Installing/updating formatting tools..." "$YELLOW"
pip install --upgrade pip
pip install \
    black==23.12.1 \
    isort==5.13.2

print_section "🔧 Fixing Formatting Issues"

# Fix Black formatting
print_status "🎨 Formatting Python code with Black..." "$BLUE"
black custom_components/emergency_alerts/
print_status "✅ Black formatting applied" "$GREEN"

echo

# Fix import sorting
print_status "📚 Sorting Python imports with isort..." "$BLUE"
isort custom_components/emergency_alerts/
print_status "✅ Import sorting applied" "$GREEN"

print_section "🎉 Formatting Complete"

print_status "✨ All formatting fixes have been applied!" "$GREEN"
print_status "📝 Review the changes with: git diff" "$BLUE"
print_status "🚀 Run ./lint.sh to verify all checks pass" "$YELLOW"

# Deactivate virtual environment
deactivate 