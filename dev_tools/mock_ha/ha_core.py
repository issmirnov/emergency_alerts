"""Mock Home Assistant core for local testing."""
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from collections import defaultdict


class MockState:
    """Mock HA state object."""
    
    def __init__(self, entity_id: str, state: str, attributes: Dict[str, Any] = None):
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}
        self.last_changed = datetime.now()
        self.last_updated = datetime.now()


class MockStates:
    """Mock HA states manager."""
    
    def __init__(self):
        self._states: Dict[str, MockState] = {}
    
    def get(self, entity_id: str) -> Optional[MockState]:
        return self._states.get(entity_id)
    
    def async_set(self, entity_id: str, state: str, attributes: Dict[str, Any] = None):
        """Set entity state."""
        self._states[entity_id] = MockState(entity_id, state, attributes)
    
    def async_entity_ids(self, domain: str = None) -> List[str]:
        """Get all entity IDs optionally filtered by domain."""
        if domain:
            return [eid for eid in self._states.keys() if eid.startswith(f"{domain}.")]
        return list(self._states.keys())
    
    def async_all(self) -> List[MockState]:
        """Get all states."""
        return list(self._states.values())


class MockServices:
    """Mock HA services."""
    
    def __init__(self):
        self._services: Dict[str, Dict[str, callable]] = defaultdict(dict)
        self._calls: List[Dict[str, Any]] = []
    
    def async_register(self, domain: str, service: str, handler: callable):
        """Register a service."""
        self._services[domain][service] = handler
    
    async def async_call(
        self, domain: str, service: str, service_data: Dict[str, Any] = None, blocking: bool = True
    ):
        """Call a service."""
        self._calls.append({
            "domain": domain,
            "service": service,
            "data": service_data or {},
            "timestamp": datetime.now()
        })
        
        handler = self._services.get(domain, {}).get(service)
        if handler and blocking:
            return await handler(service_data or {})
    
    def get_calls(self, domain: str = None, service: str = None) -> List[Dict[str, Any]]:
        """Get service calls for testing."""
        calls = self._calls
        if domain:
            calls = [c for c in calls if c["domain"] == domain]
        if service:
            calls = [c for c in calls if c["service"] == service]
        return calls
    
    def clear_calls(self):
        """Clear call history."""
        self._calls.clear()


class MockBus:
    """Mock event bus."""
    
    def __init__(self):
        self._events: List[Dict[str, Any]] = []
    
    def async_fire(self, event_type: str, event_data: Dict[str, Any] = None):
        """Fire an event."""
        self._events.append({
            "type": event_type,
            "data": event_data or {},
            "timestamp": datetime.now()
        })
    
    def get_events(self, event_type: str = None) -> List[Dict[str, Any]]:
        """Get events for testing."""
        if event_type:
            return [e for e in self._events if e["type"] == event_type]
        return self._events
    
    def clear_events(self):
        """Clear event history."""
        self._events.clear()


class MockConfigEntries:
    """Mock config entries manager."""
    
    def __init__(self, hass):
        self.hass = hass
        self._entries: List[Any] = []
    
    def async_entries(self, domain: str = None) -> List[Any]:
        """Get config entries."""
        if domain:
            return [e for e in self._entries if hasattr(e, 'domain') and e.domain == domain]
        return self._entries
    
    def async_update_entry(self, entry, **kwargs):
        """Update config entry."""
        for key, value in kwargs.items():
            setattr(entry, key, value)
    
    async def async_reload(self, entry_id: str):
        """Reload config entry."""
        # Mock reload - in real testing we'd trigger platform reload
        pass
    
    async def async_forward_entry_setups(self, entry, platforms: List[str]):
        """Forward entry setup to platforms."""
        # Mock platform setup
        pass
    
    async def async_forward_entry_unload(self, entry, platform: str) -> bool:
        """Unload platform."""
        return True


class MockHomeAssistant:
    """Mock Home Assistant instance for testing."""
    
    def __init__(self):
        self.states = MockStates()
        self.services = MockServices()
        self.bus = MockBus()
        self.config_entries = MockConfigEntries(self)
        self.data: Dict[str, Any] = {}
        self.loop = asyncio.get_event_loop()
    
    async def async_block_till_done(self):
        """Block until all pending tasks are done."""
        await asyncio.sleep(0)
    
    def async_create_task(self, coro):
        """Create async task."""
        return self.loop.create_task(coro)
    
    async def async_add_executor_job(self, func, *args):
        """Run sync function in executor."""
        return func(*args)


def create_mock_hass() -> MockHomeAssistant:
    """Create a mock HA instance."""
    return MockHomeAssistant()