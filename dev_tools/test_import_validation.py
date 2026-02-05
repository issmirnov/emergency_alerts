#!/usr/bin/env python3
"""Import validation tests to catch missing imports and undefined constants."""

import sys
import importlib
import ast
import os
from pathlib import Path


def test_all_modules_importable():
    """Test that all Python modules in the integration can be imported."""
    print("Testing module imports...")
    
    # Add custom_components to path
    integration_path = Path(__file__).parent.parent / "custom_components" / "emergency_alerts"
    sys.path.insert(0, str(integration_path.parent.parent))
    
    modules_to_test = [
        "custom_components.emergency_alerts",
        "custom_components.emergency_alerts.const",
        "custom_components.emergency_alerts.binary_sensor",
        "custom_components.emergency_alerts.sensor",
        "custom_components.emergency_alerts.switch",
        "custom_components.emergency_alerts.config_flow",
        "custom_components.emergency_alerts.core.trigger_evaluator",
        "custom_components.emergency_alerts.core.action_executor",
    ]
    
    failed = []
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
            failed.append((module_name, str(e)))
    
    if failed:
        print("\nFailed imports:")
        for module, error in failed:
            print(f"  - {module}: {error}")
        raise AssertionError(f"{len(failed)} modules failed to import")
    
    print("All modules imported successfully!")
    return True


def test_const_imports_valid():
    """Test that all imports from const.py actually exist in const.py."""
    print("\nValidating const.py imports...")
    
    integration_path = Path(__file__).parent.parent / "custom_components" / "emergency_alerts"
    const_file = integration_path / "const.py"
    
    # Parse const.py to get all defined names
    with open(const_file, 'r') as f:
        const_tree = ast.parse(f.read())
    
    const_definitions = set()
    for node in ast.walk(const_tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    const_definitions.add(target.id)
    
    print(f"  Found {len(const_definitions)} constants in const.py")
    
    # Check all files that import from const
    files_to_check = [
        integration_path / "binary_sensor.py",
        integration_path / "sensor.py",
        integration_path / "switch.py",
        integration_path / "config_flow.py",
        integration_path / "core" / "trigger_evaluator.py",
        integration_path / "core" / "action_executor.py",
    ]
    
    errors = []
    for file_path in files_to_check:
        if not file_path.exists():
            continue
            
        with open(file_path, 'r') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError as e:
                errors.append(f"{file_path.name}: Syntax error - {e}")
                continue
        
        # Find imports from const
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and 'const' in node.module:
                    for alias in node.names:
                        imported_name = alias.name
                        
                        # Skip comments (they appear as names starting with #)
                        if imported_name.startswith('#'):
                            continue
                        
                        if imported_name not in const_definitions:
                            errors.append(
                                f"{file_path.name} imports '{imported_name}' from const.py but it doesn't exist"
                            )
                        else:
                            print(f"  ✓ {file_path.name}: {imported_name}")
    
    if errors:
        print("\nImport validation errors:")
        for error in errors:
            print(f"  ✗ {error}")
        raise AssertionError(f"{len(errors)} invalid imports found")
    
    print("All const.py imports are valid!")
    return True


def test_removed_constants_not_referenced():
    """Test that removed constants are not referenced in code."""
    print("\nChecking for removed constant references...")
    
    integration_path = Path(__file__).parent.parent / "custom_components" / "emergency_alerts"
    
    # Known removed constants
    removed_constants = [
        "TRIGGER_TYPE_COMBINED",  # Removed in Phase 2
    ]
    
    files_to_check = [
        integration_path / "binary_sensor.py",
        integration_path / "sensor.py",
        integration_path / "switch.py",
        integration_path / "config_flow.py",
        integration_path / "core" / "trigger_evaluator.py",
        integration_path / "core" / "action_executor.py",
    ]
    
    errors = []
    for file_path in files_to_check:
        if not file_path.exists():
            continue
        
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        for removed in removed_constants:
            for i, line in enumerate(lines, 1):
                # Skip comment lines
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                
                # Check if constant is used (not just in comments)
                if removed in line and not line.strip().startswith('#'):
                    # Make sure it's not in an import comment
                    if f"# {removed}" not in line:
                        errors.append(
                            f"{file_path.name}:{i} references removed constant '{removed}': {line.strip()}"
                        )
    
    if errors:
        print("\nReferences to removed constants:")
        for error in errors:
            print(f"  ✗ {error}")
        raise AssertionError(f"{len(errors)} references to removed constants found")
    
    print("No references to removed constants found!")
    return True


def run_all_import_tests():
    """Run all import validation tests."""
    print("=" * 60)
    print("Import Validation Tests")
    print("=" * 60)
    
    tests = [
        test_all_modules_importable,
        test_const_imports_valid,
        test_removed_constants_not_referenced,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_import_tests()
    sys.exit(0 if success else 1)