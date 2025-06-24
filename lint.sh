#!/bin/bash

# Emergency Alerts Integration - Local Linting Script
# This script sets up a virtual environment and runs all linting checks

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

print_section "🔍 Emergency Alerts Integration - Local Linting"

# Create or activate virtual environment
VENV_DIR="lint_venv"

if [ ! -d "$VENV_DIR" ]; then
    print_status "📦 Creating virtual environment..." "$YELLOW"
    python -m venv "$VENV_DIR"
fi

print_status "🔄 Activating virtual environment..." "$YELLOW"
source "$VENV_DIR/bin/activate"

# Install/upgrade linting tools
print_status "📥 Installing/updating linting tools..." "$YELLOW"
pip install --upgrade pip
pip install \
    black==23.12.1 \
    flake8==7.0.0 \
    isort==5.13.2 \
    mypy==1.8.0

print_section "📋 Running Linting Checks"

# Track failures
FAILED_CHECKS=0

# Black formatting check
print_status "🔍 Checking Python formatting with Black..." "$BLUE"
if black --check --diff custom_components/emergency_alerts/; then
    print_status "✅ Black formatting passed" "$GREEN"
else
    print_status "❌ Black formatting failed" "$RED"
    print_status "💡 To fix: black custom_components/emergency_alerts/" "$YELLOW"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo

# isort import sorting check
print_status "🔍 Checking Python imports with isort..." "$BLUE"
if isort --check-only --diff custom_components/emergency_alerts/; then
    print_status "✅ isort passed" "$GREEN"
else
    print_status "❌ isort failed" "$RED"
    print_status "💡 To fix: isort custom_components/emergency_alerts/" "$YELLOW"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo

# flake8 linting
print_status "🔍 Linting Python with flake8..." "$BLUE"
if flake8 custom_components/emergency_alerts/ --max-line-length=88 --extend-ignore=E203,W503; then
    print_status "✅ flake8 passed" "$GREEN"
else
    print_status "❌ flake8 failed" "$RED"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo

# mypy type checking (non-blocking)
print_status "🔍 Type checking with mypy..." "$BLUE"
if mypy custom_components/emergency_alerts/ --ignore-missing-imports; then
    print_status "✅ mypy passed" "$GREEN"
else
    print_status "⚠️  mypy issues found (non-blocking)" "$YELLOW"
fi

print_section "📊 Results"

if [ $FAILED_CHECKS -eq 0 ]; then
    print_status "🎉 All linting checks passed!" "$GREEN"
    print_status "🚀 Your code is ready for commit!" "$GREEN"
else
    print_status "❌ $FAILED_CHECKS linting check(s) failed" "$RED"
    print_status "🔧 Please fix the issues above before committing" "$YELLOW"
    
    echo
    print_status "🛠️  Quick fix commands:" "$BLUE"
    print_status "  Format code: black custom_components/emergency_alerts/" "$NC"
    print_status "  Sort imports: isort custom_components/emergency_alerts/" "$NC"
    
    exit 1
fi

# Deactivate virtual environment
deactivate 