# Docker Linting Setup

This document explains how to use Docker for linting the Emergency Alerts integration, which is especially useful on Arch Linux or other systems where installing Python packages can be challenging.

## 🐳 Docker Option

### Build the Linting Container

```bash
# Build the linting Docker image
docker build -f Dockerfile.lint -t emergency-alerts-lint .
```

### Run Linting Checks

```bash
# Run all linting checks
docker run --rm -v $(pwd):/app emergency-alerts-lint
```

### Fix Formatting Issues

```bash
# Auto-fix Black formatting
docker run --rm -v $(pwd):/app emergency-alerts-lint black custom_components/emergency_alerts/

# Auto-fix import sorting
docker run --rm -v $(pwd):/app emergency-alerts-lint isort custom_components/emergency_alerts/
```

### Run Individual Tools

```bash
# Just Black check
docker run --rm -v $(pwd):/app emergency-alerts-lint black --check --diff custom_components/emergency_alerts/

# Just flake8
docker run --rm -v $(pwd):/app emergency-alerts-lint flake8 custom_components/emergency_alerts/ --max-line-length=88 --extend-ignore=E203,W503

# Just mypy
docker run --rm -v $(pwd):/app emergency-alerts-lint mypy custom_components/emergency_alerts/ --ignore-missing-imports
```

## 🐍 Local Virtual Environment Option

If you prefer to use a local virtual environment instead of Docker:

### Quick Setup and Check

```bash
# Run linting checks (creates venv if needed)
./lint.sh

# Auto-fix formatting issues
./fix-format.sh
```

### Manual Setup

```bash
# Create virtual environment
python -m venv lint_venv
source lint_venv/bin/activate

# Install tools
pip install black==23.12.1 flake8==7.0.0 isort==5.13.2 mypy==1.8.0

# Run checks
black --check custom_components/emergency_alerts/
flake8 custom_components/emergency_alerts/ --max-line-length=88 --extend-ignore=E203,W503
isort --check-only custom_components/emergency_alerts/
mypy custom_components/emergency_alerts/ --ignore-missing-imports
```

## 🔧 Configuration

The linting tools use these configurations:

- **Black**: Line length 88 characters (default)
- **flake8**: Max line length 88, ignores E203 (whitespace before ':') and W503 (line break before binary operator)
- **isort**: Compatible with Black formatting
- **mypy**: Ignores missing imports (for Home Assistant components)

## 📝 Integration with Git Hooks

You can set up a pre-commit hook to automatically run linting:

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running linting checks..."
if docker images emergency-alerts-lint &> /dev/null; then
    docker run --rm -v $(pwd):/app emergency-alerts-lint
else
    ./lint.sh
fi
EOF

chmod +x .git/hooks/pre-commit
```

## 🚀 Continuous Integration

The GitHub Actions workflow uses the same tools and configuration as the local setup, ensuring consistency between local development and CI/CD. 