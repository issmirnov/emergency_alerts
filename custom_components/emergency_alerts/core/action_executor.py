"""Action execution logic extracted from binary_sensor.py.

This module handles service calls and action execution.
"""
import logging
from typing import Dict, Any, List, Union
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class ActionExecutor:
    """Executes alert actions."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the action executor."""
        self.hass = hass
    
    async def execute(self, actions: Union[str, List[Dict[str, Any]], Dict[str, Any]]):
        """Execute action configuration.
        
        Args:
            actions: Can be:
                - Profile reference string: "profile:profile_id"
                - List of action dicts: [{"service": "...", "data": {...}}]
                - Single action dict: {"service": "...", "data": {...}}
        """
        if not actions:
            return
        
        # Check if it's a profile reference
        if isinstance(actions, str) and actions.startswith("profile:"):
            action_list = await self._resolve_profile(actions)
        elif isinstance(actions, list):
            action_list = actions
        else:
            action_list = [actions]
        
        # Execute each action
        for action in action_list:
            await self._execute_single_action(action)
    
    async def _execute_single_action(self, action: Dict[str, Any]):
        """Execute a single service call action."""
        if not isinstance(action, dict) or "service" not in action:
            _LOGGER.warning(f"Invalid action format: {action}")
            return
        
        try:
            domain, service = action["service"].split(".", 1)
            service_data = action.get("data", {})
            
            await self.hass.services.async_call(
                domain, service, service_data, blocking=False
            )
            _LOGGER.debug(f"Executed action: {action['service']}")
        except Exception as e:
            _LOGGER.error(f"Error executing action {action.get('service')}: {e}")
    
    async def _resolve_profile(self, profile_ref: str, group_entry=None) -> List[Dict[str, Any]]:
        """Resolve a profile reference to its action list.
        
        Args:
            profile_ref: String in format "profile:profile_id"
            group_entry: The alert group's config entry (to access profiles)
        
        Returns:
            List of action dicts, or empty list if profile not found
        """
        if not isinstance(profile_ref, str) or not profile_ref.startswith("profile:"):
            return []
        
        profile_id = profile_ref.split(":", 1)[1]
        
        # Profiles are now stored at group level, not global
        # First, try the provided group_entry
        if group_entry:
            profiles = group_entry.options.get("notification_profiles", {})
            profile = profiles.get(profile_id)
            if profile:
                _LOGGER.debug(f"Resolved profile '{profile_id}' from group to {len(profile.get('actions', []))} actions")
                return profile.get("actions", [])
        
        # Fallback: search all group entries for the profile
        from ..const import DOMAIN
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("hub_type") == "group":
                profiles = entry.options.get("notification_profiles", {})
                profile = profiles.get(profile_id)
                if profile:
                    _LOGGER.debug(f"Resolved profile '{profile_id}' from group '{entry.data.get('group')}' to {len(profile.get('actions', []))} actions")
                    return profile.get("actions", [])
        
        _LOGGER.warning(f"Profile '{profile_id}' not found in any group")
        return []