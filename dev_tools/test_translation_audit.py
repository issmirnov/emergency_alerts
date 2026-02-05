#!/usr/bin/env python3
"""Audit translation placeholders and verify they're provided in config_flow.py"""

import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Set


def extract_translation_placeholders() -> Dict[str, Set[str]]:
    """Extract all {variable} placeholders from translation files."""
    translations_path = Path("custom_components/emergency_alerts/translations/en.json")
    
    with open(translations_path, 'r') as f:
        translations = json.load(f)
    
    placeholders = {}
    
    def find_placeholders(obj, path=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f'{path}.{key}' if path else key
                find_placeholders(value, new_path)
        elif isinstance(obj, str):
            # Find {variable} patterns, but exclude JSON examples
            # Only match simple variable names, not JSON syntax
            matches = re.findall(r'\{([a-z_]+)\}', obj)
            if matches:
                placeholders[path] = set(matches)
    
    find_placeholders(translations)
    return placeholders


def extract_config_flow_calls() -> List[Dict]:
    """Extract all async_show_form/async_show_menu calls with description_placeholders."""
    config_flow_path = Path("custom_components/emergency_alerts/config_flow.py")
    
    with open(config_flow_path, 'r') as f:
        content = f.read()
    
    # Find all async_show_form and async_show_menu calls
    calls = []
    
    # Pattern to match async_show_form/menu calls with their parameters
    # This is complex because we need to handle multi-line calls
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for async_show_form or async_show_menu
        if 'async_show_form(' in line or 'async_show_menu(' in line:
            # Extract the full call (may span multiple lines)
            call_type = 'form' if 'async_show_form(' in line else 'menu'
            
            # Find step_id
            step_id = None
            description_vars = set()
            
            # Look ahead for step_id and description_placeholders
            j = i
            paren_count = line.count('(') - line.count(')')
            full_call = line
            
            while paren_count > 0 and j < len(lines) - 1:
                j += 1
                full_call += '\n' + lines[j]
                paren_count += lines[j].count('(') - lines[j].count(')')
            
            # Extract step_id
            step_match = re.search(r'step_id=["\']([^"\']+)["\']', full_call)
            if step_match:
                step_id = step_match.group(1)
            
            # Extract description_placeholders variables
            desc_match = re.search(
                r'description_placeholders=\{([^}]+)\}',
                full_call,
                re.DOTALL
            )
            if desc_match:
                desc_content = desc_match.group(1)
                # Find all variable names (keys in dict)
                var_matches = re.findall(r'["\']([a-z_]+)["\']:', desc_content)
                description_vars = set(var_matches)
            
            if step_id:
                calls.append({
                    'line': i + 1,
                    'type': call_type,
                    'step_id': step_id,
                    'provided_vars': description_vars
                })
            
            i = j
        
        i += 1
    
    return calls


def audit_translations():
    """Perform comprehensive translation placeholder audit."""
    print("=" * 80)
    print("Translation Placeholder Audit")
    print("=" * 80)
    print()
    
    # Get translation placeholders
    print("[1/3] Extracting translation placeholders...")
    translation_placeholders = extract_translation_placeholders()
    
    print(f"Found {len(translation_placeholders)} translation keys with placeholders:")
    for path, vars in sorted(translation_placeholders.items()):
        if 'options.step' in path or 'config.step' in path:
            print(f"  - {path}: {{{', '.join(sorted(vars))}}}")
    print()
    
    # Get config flow calls
    print("[2/3] Extracting config_flow.py form/menu calls...")
    config_calls = extract_config_flow_calls()
    
    print(f"Found {len(config_calls)} form/menu calls with description_placeholders:")
    for call in config_calls:
        print(f"  - Line {call['line']}: {call['step_id']} provides {{{', '.join(sorted(call['provided_vars']))}}}")
    print()
    
    # Validate
    print("[3/3] Validating placeholder coverage...")
    errors = []
    warnings = []
    
    # Build map of step_id to required placeholders
    step_requirements = {}
    for path, vars in translation_placeholders.items():
        # Extract step_id from path (e.g., options.step.group_options.title -> group_options)
        if '.step.' in path:
            parts = path.split('.step.')
            if len(parts) > 1:
                step_id = parts[1].split('.')[0]
                if step_id not in step_requirements:
                    step_requirements[step_id] = set()
                step_requirements[step_id].update(vars)
    
    # Check each config flow call
    for call in config_calls:
        step_id = call['step_id']
        provided = call['provided_vars']
        required = step_requirements.get(step_id, set())
        
        if required:
            missing = required - provided
            if missing:
                errors.append({
                    'line': call['line'],
                    'step_id': step_id,
                    'missing': missing,
                    'provided': provided,
                    'required': required
                })
    
    # Report results
    if errors:
        print(f"\n❌ Found {len(errors)} translation placeholder errors:\n")
        for error in errors:
            print(f"  Line {error['line']}: {error['step_id']}")
            print(f"    Required: {{{', '.join(sorted(error['required']))}}}")
            print(f"    Provided: {{{', '.join(sorted(error['provided']))}}}")
            print(f"    Missing: {{{', '.join(sorted(error['missing']))}}}")
            print()
    else:
        print("✅ All translation placeholders are properly provided!")
    
    print("=" * 80)
    return len(errors) == 0


if __name__ == "__main__":
    import sys
    success = audit_translations()
    sys.exit(0 if success else 1)