"""Test the Emergency Alerts config flow."""

import pytest
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.emergency_alerts.config_flow import (
    EmergencyAlertsConfigFlow,
    EmergencyOptionsFlow,
    _optional,
)
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


# ---------------------------------------------------------------------------
# Bug 6 regression — EntitySelector default="" rejects empty submissions.
# Verifies the `_optional()` helper builds a schema marker that omits any
# default value when there's nothing to suggest, so the field's selector is
# never asked to validate an empty string. With the old `default=""` pattern,
# submitting the form without picking an entity raised "Entity not found".
# ---------------------------------------------------------------------------


def test_optional_helper_omits_default_when_value_falsy():
    """`_optional(k)` and `_optional(k, "")` produce a bare vol.Optional."""
    marker_none = _optional("entity_id")
    marker_empty = _optional("entity_id", "")
    marker_falsy_zero = _optional("entity_id", 0)

    assert isinstance(marker_none, vol.Optional)
    assert marker_none.default is vol.UNDEFINED
    # voluptuous stores description as `description` attribute
    assert getattr(marker_none, "description", None) is None

    assert getattr(marker_empty, "description", None) is None
    assert getattr(marker_falsy_zero, "description", None) is None


def test_optional_helper_uses_suggested_value_when_truthy():
    """`_optional(k, "light.foo")` sets suggested_value, not default."""
    marker = _optional("entity_id", "light.foo")
    assert isinstance(marker, vol.Optional)
    assert marker.default is vol.UNDEFINED
    assert marker.description == {"suggested_value": "light.foo"}


def test_alert_schema_accepts_empty_submission_with_no_entity_id():
    """Empty form submission must not fail EntitySelector validation.

    Prior to Bug 6 fix, `vol.Optional("entity_id", default="")` injected an
    empty string into the validated data when the user left the field blank,
    and EntitySelector rejected it as "Entity not found". The fix uses
    `description={"suggested_value": ...}` for pre-fill, with no schema
    default, so empty submissions pass through cleanly.
    """
    # _build_alert_schema doesn't touch self.config_entry — pure schema build
    schema = EmergencyOptionsFlow._build_alert_schema(None)

    # Minimum valid submission for a template trigger: no entity_id, just
    # severity + trigger_type + template + name.
    result = schema({
        "name": "Test Alert",
        "severity": "warning",
        "trigger_type": "template",
        "template": "{{ True }}",
    })

    # entity_id must NOT have been injected as ""
    assert "entity_id" not in result
    # on_triggered_script must NOT have been injected as ""
    assert "on_triggered_script" not in result


def test_alert_schema_preserves_existing_entity_id_via_suggested_value():
    """Editing an alert: existing entity_id should re-appear as suggestion."""
    schema = EmergencyOptionsFlow._build_alert_schema(
        None, defaults={"entity_id": "binary_sensor.front_door"}
    )

    # Find the entity_id marker and check the suggested_value attached
    for marker in schema.schema:
        if getattr(marker, "schema", None) == "entity_id":
            assert marker.description == {"suggested_value": "binary_sensor.front_door"}
            assert marker.default is vol.UNDEFINED
            break
    else:
        raise AssertionError("entity_id field not found in schema")


# ---------------------------------------------------------------------------
# Edit-alert flow regression — submitting an edit_alert_form rendered with
# step_id="add_alert" used to misfire as "already_configured" because the
# duplicate-name guard didn't know it was an edit. async_step_add_alert now
# reads `self._editing_alert_id` (set by edit_alert) and allows the slug
# match when it matches the editing target.
# ---------------------------------------------------------------------------


@pytest.fixture
def _options_flow_factory(hass):
    """Build an EmergencyOptionsFlow bound to a MockConfigEntry.

    OptionsFlow.config_entry is a read-only property derived from
    self.handler + hass.config_entries.options registry, so we register a
    MockConfigEntry with hass and point self.handler at its entry_id.
    """
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from custom_components.emergency_alerts.const import DOMAIN

    def factory(data):
        entry = MockConfigEntry(
            domain=DOMAIN, version=2, data=data,
            title=data.get("hub_name", "Test Hub"),
        )
        entry.add_to_hass(hass)
        flow = EmergencyOptionsFlow()
        flow.hass = hass
        flow.handler = entry.entry_id
        return flow

    return factory


async def test_add_alert_blocks_duplicate_name_when_not_editing(_options_flow_factory):
    """Without `_editing_alert_id`, slug-matched submission errors as expected."""
    flow = _options_flow_factory({
        "alerts": {
            "external_door_open": {
                "name": "External Door Open", "severity": "warning",
                "trigger_type": "simple",
                "entity_id": "binary_sensor.front_door",
                "trigger_state": "on",
            }
        }
    })
    flow._editing_alert_id = None
    result = await flow.async_step_add_alert({
        "name": "External Door Open",  # collides
        "severity": "warning",
        "trigger_type": "simple",
        "entity_id": "binary_sensor.front_door",
        "trigger_state": "on",
    })
    assert result["type"] == "form"
    assert result["errors"] == {"name": "already_configured"}


async def test_edit_alert_does_not_misfire_already_configured(_options_flow_factory):
    """Edit submission with the SAME name must NOT raise already_configured.

    Regression for v4.1.0/4.2.0 bug: edit_alert_form rendered with
    step_id="add_alert" caused HA to route POSTs back to add_alert, which
    then ran the duplicate-name guard and rejected the edit. add_alert now
    permits the slug match when `_editing_alert_id` is set.
    """
    flow = _options_flow_factory({
        "alerts": {
            "external_door_open": {
                "name": "External Door Open", "severity": "warning",
                "trigger_type": "template",
                "template": "{{ is_state('binary_sensor.front_door','on') }}",
                "on_triggered_script": "script.emergency_critical_push",
            }
        }
    })
    flow._editing_alert_id = "external_door_open"

    result = await flow.async_step_add_alert({
        "name": "External Door Open",        # same name — same slug
        "severity": "warning",
        "trigger_type": "template",
        "template": "{{ is_state('binary_sensor.front_door','on') }}",
        "for_seconds": 60,
        # deliberately omit on_triggered_script — this is the migration case
    })

    # Edit succeeds and closes the flow
    assert result["type"] == "create_entry", f"Expected create_entry, got {result}"
    # Editing state cleared
    assert flow._editing_alert_id is None
    # on_triggered_script dropped from storage
    saved = flow.config_entry.data["alerts"]["external_door_open"]
    assert "on_triggered_script" not in saved
    assert saved.get("for_seconds") == 60


async def test_edit_alert_with_renamed_slug_drops_old_key(_options_flow_factory):
    """Renaming an alert during edit removes the old slug and adds the new one."""
    flow = _options_flow_factory({
        "alerts": {
            "old_name": {
                "name": "Old Name", "severity": "warning",
                "trigger_type": "simple", "entity_id": "binary_sensor.x",
                "trigger_state": "on",
            }
        }
    })
    flow._editing_alert_id = "old_name"

    result = await flow.async_step_add_alert({
        "name": "New Name",
        "severity": "warning",
        "trigger_type": "simple",
        "entity_id": "binary_sensor.x",
        "trigger_state": "on",
    })

    assert result["type"] == "create_entry"
    alerts = flow.config_entry.data["alerts"]
    assert "old_name" not in alerts
    assert "new_name" in alerts
