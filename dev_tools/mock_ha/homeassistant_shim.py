"""Shim homeassistant modules for local testing without HA installation."""
import sys
from pathlib import Path
from types import ModuleType

# Import our mock HA core
from .ha_core import MockHomeAssistant, MockState, MockConfigEntries


class ConfigEntry:
    """Mock config entry."""
    def __init__(self, domain, data, options=None, entry_id=None, version=1):
        self.domain = domain
        self.data = data
        self.options = options or {}
        self.entry_id = entry_id or "test_entry_id"
        self.version = version


# Create mock modules
def create_mock_modules():
    """Create mock homeassistant modules."""
    
    # homeassistant
    ha_module = ModuleType('homeassistant')
    sys.modules['homeassistant'] = ha_module
    
    # homeassistant.core
    core_module = ModuleType('homeassistant.core')
    core_module.HomeAssistant = MockHomeAssistant
    core_module.callback = lambda func: func  # Simple passthrough decorator
    sys.modules['homeassistant.core'] = core_module
    ha_module.core = core_module
    
    # homeassistant.config_entries
    config_entries_module = ModuleType('homeassistant.config_entries')
    config_entries_module.ConfigEntry = ConfigEntry
    
    # ConfigFlow with domain support (Python 3.10+ __init_subclass__)
    class ConfigFlowBase:
        def __init_subclass__(cls, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)
            if domain:
                cls._domain = domain
    
    config_entries_module.ConfigFlow = ConfigFlowBase
    config_entries_module.OptionsFlow = object  # Base class
    sys.modules['homeassistant.config_entries'] = config_entries_module
    ha_module.config_entries = config_entries_module
    
    # homeassistant.helpers
    helpers_module = ModuleType('homeassistant.helpers')
    sys.modules['homeassistant.helpers'] = helpers_module
    ha_module.helpers = helpers_module
    
    # homeassistant.helpers.template
    template_module = ModuleType('homeassistant.helpers.template')
    
    class Template:
        """Mock template."""
        def __init__(self, template_str, hass):
            self.template = template_str
            self.hass = hass
        
        async def async_render_to_info(self):
            """Render template."""
            # Simple eval for testing - NOT SECURE, only for dev
            class Result:
                def __init__(self, value):
                    self._value = value
                def result(self):
                    return self._value
            
            # Very basic template rendering for testing
            # In real implementation, this would use Jinja2
            template_str = self.template.replace('{{', '').replace('}}', '').strip()
            
            # Handle states() function with |float filter
            if 'states(' in template_str:
                import re
                # Match states('entity.id')|float or states('entity.id')
                match = re.search(r"states\('([^']+)'\)(?:\|float)?", template_str)
                if match:
                    entity_id = match.group(1)
                    state = self.hass.states.get(entity_id)
                    if state:
                        # Determine if we need float conversion
                        if '|float' in template_str:
                            try:
                                value = float(state.state)
                                template_str = template_str.replace(
                                    match.group(0),
                                    str(value)
                                )
                            except ValueError:
                                template_str = template_str.replace(
                                    match.group(0),
                                    '0'
                                )
                        else:
                            template_str = template_str.replace(
                                match.group(0),
                                f"'{state.state}'"
                            )
            
            try:
                result = eval(template_str)
                return Result(result)
            except Exception as e:
                return Result(False)
    
    template_module.Template = Template
    sys.modules['homeassistant.helpers.template'] = template_module
    helpers_module.template = template_module
    
    # homeassistant.helpers.entity_platform
    entity_platform_module = ModuleType('homeassistant.helpers.entity_platform')
    entity_platform_module.AddEntitiesCallback = object
    sys.modules['homeassistant.helpers.entity_platform'] = entity_platform_module
    helpers_module.entity_platform = entity_platform_module
    
    # homeassistant.helpers.dispatcher
    dispatcher_module = ModuleType('homeassistant.helpers.dispatcher')
    dispatcher_module.async_dispatcher_send = lambda hass, signal, *args: None
    dispatcher_module.async_dispatcher_connect = lambda hass, signal, callback: lambda: None
    sys.modules['homeassistant.helpers.dispatcher'] = dispatcher_module
    helpers_module.dispatcher = dispatcher_module
    
    # homeassistant.helpers.event
    event_module = ModuleType('homeassistant.helpers.event')
    event_module.async_call_later = lambda hass, delay, callback: lambda: None
    event_module.async_track_state_change_event = lambda hass, entities, callback: lambda: None
    sys.modules['homeassistant.helpers.event'] = event_module
    helpers_module.event = event_module
    
    # homeassistant.helpers.device_registry
    device_registry_module = ModuleType('homeassistant.helpers.device_registry')
    device_registry_module.async_get = lambda hass: None
    sys.modules['homeassistant.helpers.device_registry'] = device_registry_module
    helpers_module.device_registry = device_registry_module
    
    # homeassistant.helpers.entity
    entity_module = ModuleType('homeassistant.helpers.entity')
    entity_module.DeviceInfo = dict
    sys.modules['homeassistant.helpers.entity'] = entity_module
    helpers_module.entity = entity_module
    
    # homeassistant.helpers import selector
    selector_module = ModuleType('homeassistant.helpers.selector')
    
    class MockSelector:
        """Mock selector for config flow."""
        def __init__(self, config=None):
            self.config = config or {}
    
    selector_module.SelectSelector = MockSelector
    selector_module.EntitySelector = MockSelector
    selector_module.TextSelector = MockSelector
    selector_module.TemplateSelector = MockSelector
    selector_module.SelectSelectorConfig = dict
    selector_module.EntitySelectorConfig = dict
    selector_module.TextSelectorConfig = dict
    selector_module.TemplateSelectorConfig = dict
    selector_module.SelectOptionDict = dict
    selector_module.SelectSelectorMode = type('SelectSelectorMode', (), {
        'DROPDOWN': 'dropdown',
        'LIST': 'list'
    })
    selector_module.TextSelectorType = type('TextSelectorType', (), {
        'TEXT': 'text',
        'MULTILINE': 'multiline'
    })
    
    sys.modules['homeassistant.helpers.selector'] = selector_module
    helpers_module.selector = selector_module
    
    # homeassistant.components
    components_module = ModuleType('homeassistant.components')
    sys.modules['homeassistant.components'] = components_module
    ha_module.components = components_module
    
    # homeassistant.components.binary_sensor
    binary_sensor_module = ModuleType('homeassistant.components.binary_sensor')
    binary_sensor_module.BinarySensorEntity = object
    sys.modules['homeassistant.components.binary_sensor'] = binary_sensor_module
    components_module.binary_sensor = binary_sensor_module
    
    # homeassistant.components.sensor
    sensor_module = ModuleType('homeassistant.components.sensor')
    sensor_module.SensorEntity = object
    sys.modules['homeassistant.components.sensor'] = sensor_module
    components_module.sensor = sensor_module
    
    # homeassistant.components.switch
    switch_module = ModuleType('homeassistant.components.switch')
    switch_module.SwitchEntity = object
    switch_module.SwitchDeviceClass = type('SwitchDeviceClass', (), {})
    sys.modules['homeassistant.components.switch'] = switch_module
    components_module.switch = switch_module
    
    # homeassistant.components.persistent_notification
    notification_module = ModuleType('homeassistant.components.persistent_notification')
    notification_module.async_create = lambda hass, message, title=None, notification_id=None: None
    sys.modules['homeassistant.components.persistent_notification'] = notification_module
    components_module.persistent_notification = notification_module
    
    # voluptuous (used by config_flow)
    vol_module = ModuleType('voluptuous')
    vol_module.Required = lambda key, default=None: key
    vol_module.Optional = lambda key, default=None: key
    vol_module.Schema = dict
    vol_module.All = lambda *args: args[0] if args else None
    vol_module.Coerce = lambda type_: type_
    vol_module.Range = lambda min=None, max=None: lambda x: x
    sys.modules['voluptuous'] = vol_module
    
    # yaml
    import yaml as real_yaml
    sys.modules['yaml'] = real_yaml


def setup_test_environment():
    """Set up the test environment with mocked modules."""
    create_mock_modules()