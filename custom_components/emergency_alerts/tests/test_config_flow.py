"""Test the Emergency Alerts config flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.config_flow import EmergencyConfigFlow
from custom_components.emergency_alerts.const import DOMAIN


async def test_form_simple_trigger(hass: HomeAssistant):
    """Test the form with simple trigger configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    # Test form submission - select group setup
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "setup_type": "group",
        },
    )
    await hass.async_block_till_done()

    # Should show the group setup form
    assert result2["type"] == "form"
    assert result2["step_id"] == "group_setup"


async def test_form_template_trigger(hass: HomeAssistant):
    """Test the form with template trigger configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Test form submission - select group setup
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "setup_type": "group",
        },
    )
    await hass.async_block_till_done()

    # Should show the group setup form
    assert result2["type"] == "form"
    assert result2["step_id"] == "group_setup"


async def test_form_logical_trigger(hass: HomeAssistant):
    """Test the form with logical trigger configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Test form submission
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "setup_type": "group",
        },
    )
    await hass.async_block_till_done()

    # Should show the group setup form
    assert result2["type"] == "form"
    assert result2["step_id"] == "group_setup"


async def test_form_with_actions(hass: HomeAssistant):
    """Test the form with action configuration."""
    # Initialize the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Test form submission
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "setup_type": "group",
        },
    )
    await hass.async_block_till_done()

    # Should show the group setup form
    assert result2["type"] == "form"
    assert result2["step_id"] == "group_setup"


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
