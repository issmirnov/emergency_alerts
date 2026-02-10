#!/usr/bin/env python3
"""Validate that strings.json and translations/en.json are in sync.

This ensures that the UI strings (strings.json) match the translation file,
preventing translation errors and missing keys at runtime.
"""

import json
import sys
from pathlib import Path


def load_json(file_path: Path) -> dict:
    """Load JSON file and return parsed content."""
    try:
        return json.loads(file_path.read_text())
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def compare_dicts(dict1: dict, dict2: dict, path: str = "") -> list[str]:
    """Recursively compare two dictionaries and return list of differences."""
    differences = []

    # Check keys in dict1
    for key in dict1:
        current_path = f"{path}.{key}" if path else key

        if key not in dict2:
            differences.append(f"Key missing in translations/en.json: {current_path}")
        elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
            # Recursively compare nested dicts
            differences.extend(compare_dicts(dict1[key], dict2[key], current_path))
        elif dict1[key] != dict2[key]:
            differences.append(
                f"Value mismatch at {current_path}:\n"
                f"  strings.json: {dict1[key]}\n"
                f"  translations/en.json: {dict2[key]}"
            )

    # Check for keys in dict2 that aren't in dict1
    for key in dict2:
        current_path = f"{path}.{key}" if path else key
        if key not in dict1:
            differences.append(f"Extra key in translations/en.json: {current_path}")

    return differences


def main():
    """Main validation function."""
    print("🔍 Validating translation sync...")
    print()

    base_path = Path(__file__).parent / "custom_components" / "emergency_alerts"
    strings_path = base_path / "strings.json"
    translations_path = base_path / "translations" / "en.json"

    # Load both files
    print(f"📄 Loading {strings_path}")
    strings = load_json(strings_path)

    print(f"📄 Loading {translations_path}")
    translations = load_json(translations_path)
    print()

    # Compare the contents
    differences = compare_dicts(strings, translations)

    if not differences:
        print("✅ Translation files are in sync!")
        print()
        print("strings.json and translations/en.json match perfectly.")
        sys.exit(0)
    else:
        print("❌ Translation files are out of sync!")
        print()
        print("Differences found:")
        for diff in differences:
            print(f"  • {diff}")
        print()
        print("Action required:")
        print("  1. Update translations/en.json to match strings.json")
        print("  2. Or update strings.json if translation is correct")
        print("  3. Ensure both files stay in sync for all changes")
        sys.exit(1)


if __name__ == "__main__":
    main()
