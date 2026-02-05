#!/usr/bin/env python3
"""Remote Home Assistant inspector - diagnose live HA state without restarting."""

import requests
import json
import sys
from typing import Optional

class HAInspector:
    """Inspect live Home Assistant instance remotely."""
    
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def get_config_entries(self, domain: str = "emergency_alerts"):
        """Get all config entries for a domain."""
        response = requests.get(
            f"{self.url}/api/config/config_entries/entry",
            headers=self.headers
        )
        response.raise_for_status()
        entries = response.json()
        
        return [e for e in entries if e.get("domain") == domain]
    
    def get_entry_details(self, entry_id: str):
        """Get detailed info about a specific entry."""
        response = requests.get(
            f"{self.url}/api/config/config_entries/entry/{entry_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def inspect_emergency_alerts(self):
        """Inspect Emergency Alerts config entries and diagnose issues."""
        print("=" * 80)
        print("Emergency Alerts Remote Inspector")
        print("=" * 80)
        
        entries = self.get_config_entries()
        
        if not entries:
            print("\nNo Emergency Alerts config entries found!")
            return
        
        print(f"\nFound {len(entries)} Emergency Alerts config entries:\n")
        
        for i, entry in enumerate(entries, 1):
            print(f"\n{i}. Entry: {entry.get('title', 'Unknown')}")
            print(f"   Entry ID: {entry.get('entry_id')}")
            print(f"   Hub Type: {entry.get('data', {}).get('hub_type', 'MISSING')}")
            
            # Check for translation bug
            data = entry.get('data', {})
            has_group = 'group' in data
            group_value = data.get('group', 'MISSING')
            
            print(f"   Has 'group' field: {has_group}")
            if has_group:
                print(f"   Group name: {group_value}")
            else:
                print("   ⚠️  MISSING 'group' field - THIS CAUSES TRANSLATION ERROR!")
            
            # Show full data structure
            print(f"\n   Full data structure:")
            print(f"   {json.dumps(data, indent=6)}")
            
            # Show options
            options = entry.get('options', {})
            if options:
                print(f"\n   Options:")
                print(f"   {json.dumps(options, indent=6)}")
        
        print("\n" + "=" * 80)
    
    def fix_missing_group_fields(self, dry_run: bool = True):
        """Add missing 'group' field to config entries."""
        entries = self.get_config_entries()
        
        print("\n" + "=" * 80)
        print("Config Entry Migration: Add missing 'group' fields")
        print("=" * 80)
        
        needs_fix = []
        for entry in entries:
            data = entry.get('data', {})
            if data.get('hub_type') == 'group' and 'group' not in data:
                needs_fix.append(entry)
        
        if not needs_fix:
            print("\nAll config entries have 'group' field. No migration needed!")
            return
        
        print(f"\nFound {len(needs_fix)} entries needing migration:\n")
        
        for entry in needs_fix:
            title = entry.get('title', 'Unknown')
            entry_id = entry.get('entry_id')
            
            # Extract group name from title
            # "Emergency Alerts - Sun" -> "Sun"
            group_name = title.replace("Emergency Alerts - ", "").strip()
            
            print(f"  • {title}")
            print(f"    Entry ID: {entry_id}")
            print(f"    Will add: group = '{group_name}'")
            
            if not dry_run:
                # Update the entry
                new_data = dict(entry.get('data', {}))
                new_data['group'] = group_name
                
                response = requests.post(
                    f"{self.url}/api/config/config_entries/entry/{entry_id}",
                    headers=self.headers,
                    json={"data": new_data}
                )
                
                if response.status_code == 200:
                    print(f"    ✓ Updated successfully")
                else:
                    print(f"    ✗ Update failed: {response.status_code}")
                    print(f"      {response.text}")
        
        if dry_run:
            print("\n⚠️  DRY RUN - No changes made")
            print("Run with --fix to apply changes")
        else:
            print("\n✓ Migration complete!")
            print("Restart Home Assistant to apply changes")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Inspect and fix Emergency Alerts config entries in live HA"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8123",
        help="Home Assistant URL (default: http://localhost:8123)"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Long-lived access token from HA"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply fixes (default: dry run only)"
    )
    
    args = parser.parse_args()
    
    try:
        inspector = HAInspector(args.url, args.token)
        
        # Always show current state
        inspector.inspect_emergency_alerts()
        
        # Optionally fix issues
        inspector.fix_missing_group_fields(dry_run=not args.fix)
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nMake sure:")
        print("  1. Home Assistant is running")
        print("  2. URL is correct")
        print("  3. Token is valid (create at: Profile > Security > Long-Lived Access Tokens)")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()