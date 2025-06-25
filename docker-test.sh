#!/bin/bash
set -e

echo "🛠️  Building Emergency Alerts test image..."
docker build -f Dockerfile.test -t emergency-alerts-test .

echo "🚦 Running backend tests in Docker..."
docker run --rm emergency-alerts-test 