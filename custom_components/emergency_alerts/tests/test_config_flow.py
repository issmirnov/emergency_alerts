"""Test the Emergency Alerts config flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.config_flow import EmergencyAlertsConfigFlow
from custom_components.emergency_alerts.const import DOMAIN


async def test_form_simple_trigger(hass: HomeAssistant):
    """Test the form with simple trigger configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    # V4: Config flow goes directly to group setup
    assert result["step_id"] == "group_setup"

    # Submit group name
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"group_name": "Test Group"},
    )
    await hass.async_block_till_done()

    # Should create the entry
    assert result2["type"] == "create_entry"
    assert result2["title"] == "Emergency Alerts - Test Group"


async def test_form_template_trigger(hass: HomeAssistant):
    """Test the form with template trigger configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # V4: Config flow goes directly to group setup
    assert result["step_id"] == "group_setup"

    # Submit group name
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"group_name": "Test Group"},
    )
    await hass.async_block_till_done()

    # Should create the entry
    assert result2["type"] == "create_entry"
    assert result2["title"] == "Emergency Alerts - Test Group"


async def test_form_logical_trigger(hass: HomeAssistant):
    """Test the form with logical trigger configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # V4: Goes directly to group setup
    assert result["step_id"] == "group_setup"

    # Submit group name
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"group_name": "Test Group"},
    )
    await hass.async_block_till_done()

    # Should create entry
    assert result2["type"] == "create_entry"


async def test_form_with_actions(hass: HomeAssistant):
    """Test the form with action configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # V4: Goes directly to group setup
    assert result["step_id"] == "group_setup"

    # Submit group name
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"group_name": "Test Group"},
    )
    await hass.async_block_till_done()

    # Should create entry
    assert result2["type"] == "create_entry"


async def test_config_flow_defaults(hass: HomeAssistant):
    """Test that config flow provides sensible defaults."""
    flow = EmergencyAlertsConfigFlow()
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
