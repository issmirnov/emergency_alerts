#!/bin/bash

# Emergency Alerts Integration Test Runner
# Tests the Home Assistant backend integration

set -e

echo "🧪 Emergency Alerts Integration Test Suite"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

# Function to run backend tests
run_backend_tests() {
    print_status "📦 Running Backend Tests..." "$YELLOW"
    
    cd custom_components/emergency_alerts
    
    # Check if test requirements are installed
    if ! python -c "import pytest" 2>/dev/null; then
        print_status "Installing test dependencies..." "$YELLOW"
        if [ -n "$VIRTUAL_ENV" ]; then
            pip install -r test_requirements.txt
        else
            pip install --user -r test_requirements.txt
        fi
    fi
    
    # Run pytest with coverage
    print_status "Running backend unit tests..." "$YELLOW"
    python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html:htmlcov
    
    if [ $? -eq 0 ]; then
        print_status "✅ Backend tests passed!" "$GREEN"
    else
        print_status "❌ Backend tests failed!" "$RED"
        exit 1
    fi
    
    cd ../..
}

# Function to run integration sanity checks
run_integration_tests() {
    print_status "🔗 Running Integration Sanity Checks..." "$YELLOW"
    
    # Check that all required files exist
    print_status "Checking file structure..." "$YELLOW"
    
    required_backend_files=(
        "custom_components/emergency_alerts/__init__.py"
        "custom_components/emergency_alerts/manifest.json"
        "custom_components/emergency_alerts/binary_sensor.py"
        "custom_components/emergency_alerts/config_flow.py"
        "custom_components/emergency_alerts/sensor.py"
    )
    
    for file in "${required_backend_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_status "❌ Missing backend file: $file" "$RED"
            exit 1
        fi
    done
    
    # Check that Python files can be imported
    print_status "Checking Python imports..." "$YELLOW"
    cd custom_components/emergency_alerts
    python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from const import DOMAIN
    from binary_sensor import EmergencyBinarySensor
    from config_flow import EmergencyConfigFlow
    print('✅ All Python imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_status "✅ Python imports successful!" "$GREEN"
    else
        print_status "❌ Python import errors!" "$RED"
        exit 1
    fi
    
    cd ../..
    
    print_status "✅ Integration sanity checks passed!" "$GREEN"
}

# Function to run linting
run_linting() {
    print_status "🔍 Running Code Quality Checks..." "$YELLOW"
    
    # Backend linting (basic Python syntax check)
    print_status "Checking Python syntax..." "$YELLOW"
    find custom_components/emergency_alerts -name "*.py" -exec python -m py_compile {} \;
    
    if [ $? -eq 0 ]; then
        print_status "✅ Python syntax check passed!" "$GREEN"
    else
        print_status "❌ Python syntax errors found!" "$RED"
        exit 1
    fi
}

# Main execution
main() {
    # Parse command line arguments
    SKIP_LINT=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-lint)
                SKIP_LINT=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-lint    Skip linting checks"
                echo "  -h, --help     Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
    
    print_status "🚀 Starting Emergency Alerts Integration tests..." "$YELLOW"
    
    # Run integration tests first
    run_integration_tests
    
    # Run backend tests
    run_backend_tests
    
    # Run linting if not skipped
    if [ "$SKIP_LINT" = false ]; then
        run_linting
    fi
    
    print_status "🎉 All tests completed successfully!" "$GREEN"
    print_status "📊 Check coverage report: custom_components/emergency_alerts/htmlcov/index.html" "$YELLOW"
}

# Run main function with all arguments
main "$@" 