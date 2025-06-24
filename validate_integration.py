#!/usr/bin/env python3
"""
Emergency Alerts Integration Validation Script

This script validates the integration structure and basic functionality
without requiring Home Assistant to be installed.
"""

import json
import os
import sys
from pathlib import Path


def validate_manifest():
    """Validate the manifest.json file."""
    print("🔍 Validating manifest.json...")
    
    manifest_path = Path("custom_components/emergency_alerts/manifest.json")
    if not manifest_path.exists():
        print("❌ manifest.json not found")
        return False
    
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        required_fields = ["domain", "name", "version", "documentation", "requirements"]
        for field in required_fields:
            if field not in manifest:
                print(f"❌ Missing required field in manifest: {field}")
                return False
        
        if manifest["domain"] != "emergency_alerts":
            print(f"❌ Domain mismatch: expected 'emergency_alerts', got '{manifest['domain']}'")
            return False
        
        print(f"✅ Manifest valid - Domain: {manifest['domain']}, Version: {manifest['version']}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in manifest: {e}")
        return False


def validate_file_structure():
    """Validate that all required files exist."""
    print("🔍 Validating file structure...")
    
    required_files = [
        "custom_components/emergency_alerts/__init__.py",
        "custom_components/emergency_alerts/manifest.json",
        "custom_components/emergency_alerts/binary_sensor.py",
        "custom_components/emergency_alerts/sensor.py",
        "custom_components/emergency_alerts/config_flow.py",
        "custom_components/emergency_alerts/const.py",
        "custom_components/emergency_alerts/strings.json",
        "custom_components/emergency_alerts/services.yaml",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    return True


def validate_python_syntax():
    """Validate Python syntax for all Python files."""
    print("🔍 Validating Python syntax...")
    
    python_files = [
        "custom_components/emergency_alerts/__init__.py",
        "custom_components/emergency_alerts/binary_sensor.py", 
        "custom_components/emergency_alerts/sensor.py",
        "custom_components/emergency_alerts/config_flow.py",
        "custom_components/emergency_alerts/const.py",
        "custom_components/emergency_alerts/helpers.py",
        "custom_components/emergency_alerts/diagnostics.py",
    ]
    
    import py_compile
    
    errors = []
    for file_path in python_files:
        if Path(file_path).exists():
            try:
                py_compile.compile(file_path, doraise=True)
                print(f"✅ {file_path}")
            except py_compile.PyCompileError as e:
                print(f"❌ {file_path}: {e}")
                errors.append(file_path)
        else:
            print(f"⚠️  {file_path} (optional file missing)")
    
    if errors:
        print(f"❌ {len(errors)} files have syntax errors")
        return False
    
    print("✅ All Python files have valid syntax")
    return True


def validate_json_files():
    """Validate JSON files."""
    print("🔍 Validating JSON files...")
    
    json_files = [
        "custom_components/emergency_alerts/strings.json",
        "custom_components/emergency_alerts/translation/en.json",
    ]
    
    errors = []
    for file_path in json_files:
        if Path(file_path).exists():
            try:
                with open(file_path) as f:
                    json.load(f)
                print(f"✅ {file_path}")
            except json.JSONDecodeError as e:
                print(f"❌ {file_path}: {e}")
                errors.append(file_path)
        else:
            print(f"⚠️  {file_path} (optional file missing)")
    
    if errors:
        print(f"❌ {len(errors)} JSON files have syntax errors")
        return False
    
    print("✅ All JSON files are valid")
    return True


def validate_constants():
    """Validate constants and basic imports."""
    print("🔍 Validating constants...")
    
    try:
        # Check if constants file exists and has basic structure
        const_file = Path("custom_components/emergency_alerts/const.py")
        if not const_file.exists():
            print("❌ const.py file not found")
            return False
        
        # Read the file and check for required constants
        with open(const_file) as f:
            content = f.read()
        
        required_constants = ["DOMAIN", "CONF_TRIGGER_TYPE", "CONF_SEVERITY", "CONF_GROUP"]
        missing_constants = []
        
        for constant in required_constants:
            if f"{constant} =" not in content and f'{constant} =' not in content:
                missing_constants.append(constant)
        
        if missing_constants:
            print(f"❌ Missing constants: {', '.join(missing_constants)}")
            return False
        
        print("✅ Constants file structure valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating constants: {e}")
        return False


def validate_hacs_files():
    """Validate HACS configuration files."""
    print("🔍 Validating HACS files...")
    
    # Backend HACS
    backend_hacs = Path("custom_components/emergency_alerts/hacs.json")
    if backend_hacs.exists():
        try:
            with open(backend_hacs) as f:
                hacs_config = json.load(f)
            
            if hacs_config.get("name") != "Emergency Alerts":
                print(f"❌ Backend HACS name mismatch")
                return False
            
            print(f"✅ Backend HACS config valid")
        except json.JSONDecodeError as e:
            print(f"❌ Backend HACS config invalid: {e}")
            return False
    
    print("✅ HACS configuration files valid")
    return True


def main():
    """Run all validation checks."""
    print("🧪 Emergency Alerts Integration Validation")
    print("=" * 50)
    
    checks = [
        ("File Structure", validate_file_structure),
        ("Manifest", validate_manifest),
        ("Python Syntax", validate_python_syntax),
        ("JSON Files", validate_json_files),
        ("Constants", validate_constants),
        ("HACS Config", validate_hacs_files),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n📋 {name}")
        print("-" * 30)
        if check_func():
            passed += 1
        else:
            print(f"❌ {name} check failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All validation checks passed!")
        print("✅ Integration is ready for testing with Home Assistant")
        return 0
    else:
        print("❌ Some validation checks failed")
        print("🔧 Please fix the issues above before deploying")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 