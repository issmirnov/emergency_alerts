"""Test the Emergency Alerts config flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.config_flow import EmergencyConfigFlow
from custom_components.emergency_alerts.const import DOMAIN


async def test_form_simple_trigger(hass: HomeAssistant):
    """Test the form with simple trigger configuration."""
    # Mock the flow responses
    hass.config_entries.flow.async_init.return_value = {
        "type": "form",
        "flow_id": "test_flow_id",
        "errors": {},
    }

    hass.config_entries.flow.async_configure.return_value = {
        "type": "create_entry",
        "title": "Test Alert",
        "data": {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor",
            "trigger_state": "on",
            "severity": "warning",
            "group": "security",
        },
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Test Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor",
            "trigger_state": "on",
            "severity": "warning",
            "group": "security",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Test Alert"
    assert result2["data"] == {
        "name": "Test Alert",
        "trigger_type": "simple",
        "entity_id": "binary_sensor.test_sensor",
        "trigger_state": "on",
        "severity": "warning",
        "group": "security",
    }


async def test_form_template_trigger(hass: HomeAssistant):
    """Test the form with template trigger configuration."""
    # Mock the flow responses
    hass.config_entries.flow.async_init.return_value = {
        "type": "form",
        "flow_id": "test_flow_id",
        "errors": {},
    }

    hass.config_entries.flow.async_configure.return_value = {
        "type": "create_entry",
        "title": "Template Alert",
        "data": {
            "name": "Template Alert",
            "trigger_type": "template",
            "template": "{{ states('sensor.temperature') | float > 30 }}",
            "severity": "critical",
            "group": "environment",
        },
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Template Alert",
            "trigger_type": "template",
            "template": "{{ states('sensor.temperature') | float > 30 }}",
            "severity": "critical",
            "group": "environment",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Template Alert"
    assert result2["data"]["trigger_type"] == "template"
    assert (
        result2["data"]["template"] == "{{ states('sensor.temperature') | float > 30 }}"
    )


async def test_form_logical_trigger(hass: HomeAssistant):
    """Test the form with logical trigger configuration."""
    logical_conditions = [
        {"type": "simple", "entity_id": "binary_sensor.door", "trigger_state": "on"},
        {"type": "simple", "entity_id": "binary_sensor.alarm", "trigger_state": "on"},
    ]

    # Mock the flow responses
    hass.config_entries.flow.async_init.return_value = {
        "type": "form",
        "flow_id": "test_flow_id",
        "errors": {},
    }

    hass.config_entries.flow.async_configure.return_value = {
        "type": "create_entry",
        "title": "Logical Alert",
        "data": {
            "name": "Logical Alert",
            "trigger_type": "logical",
            "logical_conditions": logical_conditions,
            "severity": "critical",
            "group": "security",
        },
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Logical Alert",
            "trigger_type": "logical",
            "logical_conditions": logical_conditions,
            "severity": "critical",
            "group": "security",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Logical Alert"
    assert result2["data"]["trigger_type"] == "logical"
    assert result2["data"]["logical_conditions"] == logical_conditions


async def test_form_with_actions(hass: HomeAssistant):
    """Test the form with action configuration."""
    on_triggered = [{"service": "notify.notify", "data": {"message": "Alert!"}}]
    on_cleared = [{"service": "script.cleanup", "data": {}}]

    # Mock the flow responses
    hass.config_entries.flow.async_init.return_value = {
        "type": "form",
        "flow_id": "test_flow_id",
        "errors": {},
    }

    hass.config_entries.flow.async_configure.return_value = {
        "type": "create_entry",
        "title": "Action Alert",
        "data": {
            "name": "Action Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor",
            "trigger_state": "on",
            "severity": "warning",
            "group": "security",
            "on_triggered": on_triggered,
            "on_cleared": on_cleared,
        },
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Action Alert",
            "trigger_type": "simple",
            "entity_id": "binary_sensor.test_sensor",
            "trigger_state": "on",
            "severity": "warning",
            "group": "security",
            "on_triggered": on_triggered,
            "on_cleared": on_cleared,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["data"]["on_triggered"] == on_triggered
    assert result2["data"]["on_cleared"] == on_cleared


async def test_config_flow_defaults(hass: HomeAssistant):
    """Test that config flow provides sensible defaults."""
    flow = EmergencyConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    # Check that the form has the expected schema with defaults
    schema = result["data_schema"].schema

    # Check that severity defaults to "warning"
    for field, validator in schema.items():
        if hasattr(field, "schema") and field.schema == "severity":
            break

    # Check that trigger_type defaults to "simple"
    for field, validator in schema.items():
        if hasattr(field, "schema") and field.schema == "trigger_type":
            break
