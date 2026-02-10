"""Test numeric comparisons in template triggers."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.emergency_alerts.binary_sensor import EmergencyBinarySensor
from custom_components.emergency_alerts.const import DOMAIN


@pytest.fixture
def mock_numeric_config_entry():
    """Return a mock config entry with numeric template trigger."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Test Numeric Alert",
        data={
            "hub_type": "group",
            "group": "temperature",
            "hub_name": "test_hub_temp",
            "alerts": {
                "temp_below_20": {
                    "name": "Temperature Below 20",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.test_temperature') | float < 20 }}",
                    "severity": "warning",
                }
            },
        },
    )


async def test_template_less_than_trigger(
    hass: HomeAssistant, mock_numeric_config_entry
):
    """Test template trigger with < operator."""
    alert_data = mock_numeric_config_entry.data["alerts"]["temp_below_20"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=mock_numeric_config_entry,
        alert_id="temp_below_20",
        alert_data=alert_data,
        group="temperature",
        hub_name="test_hub_temp",
    )

    sensor.entity_id = "binary_sensor.emergency_temperature_below_20"
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    # Mock template to return True (16 < 20)
    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value
        mock_tpl.async_render.return_value = True

        sensor._evaluate_trigger()
        assert sensor.is_on is True
        assert sensor._already_triggered is True

        await hass.async_block_till_done()

        # Mock template to return False (25 < 20)
        mock_tpl.async_render.return_value = False
        sensor._evaluate_trigger()
        assert sensor.is_on is False

    await hass.async_block_till_done()
    sensor._cleanup_timers()


async def test_template_greater_than_trigger(hass: HomeAssistant):
    """Test template trigger with > operator."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "hub_type": "group",
            "group": "temperature",
            "hub_name": "test_hub_temp",
            "alerts": {
                "temp_above_30": {
                    "name": "Temperature Above 30",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.test_temperature') | float > 30 }}",
                    "severity": "critical",
                }
            },
        },
    )

    alert_data = config_entry.data["alerts"]["temp_above_30"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=config_entry,
        alert_id="temp_above_30",
        alert_data=alert_data,
        group="temperature",
        hub_name="test_hub_temp",
    )

    sensor.entity_id = "binary_sensor.emergency_temperature_above_30"
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value

        # Test 35 > 30 (should trigger)
        mock_tpl.async_render.return_value = True
        sensor._evaluate_trigger()
        assert sensor.is_on is True

        await hass.async_block_till_done()

        # Test 25 > 30 (should not trigger)
        mock_tpl.async_render.return_value = False
        sensor._evaluate_trigger()
        assert sensor.is_on is False

    await hass.async_block_till_done()
    sensor._cleanup_timers()


async def test_template_equals_trigger(hass: HomeAssistant):
    """Test template trigger with == operator."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "hub_type": "group",
            "group": "temperature",
            "hub_name": "test_hub_temp",
            "alerts": {
                "temp_equals_16": {
                    "name": "Temperature Equals 16",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.test_temperature') | float == 16 }}",
                    "severity": "info",
                }
            },
        },
    )

    alert_data = config_entry.data["alerts"]["temp_equals_16"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=config_entry,
        alert_id="temp_equals_16",
        alert_data=alert_data,
        group="temperature",
        hub_name="test_hub_temp",
    )

    sensor.entity_id = "binary_sensor.emergency_temperature_equals_16"
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value

        # Test 16 == 16 (should trigger)
        mock_tpl.async_render.return_value = True
        sensor._evaluate_trigger()
        assert sensor.is_on is True

        await hass.async_block_till_done()

        # Test 17 == 16 (should not trigger)
        mock_tpl.async_render.return_value = False
        sensor._evaluate_trigger()
        assert sensor.is_on is False

    await hass.async_block_till_done()
    sensor._cleanup_timers()


async def test_template_with_default_value(hass: HomeAssistant):
    """Test template with float default value for unknown states."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "hub_type": "group",
            "group": "temperature",
            "hub_name": "test_hub_temp",
            "alerts": {
                "temp_with_default": {
                    "name": "Temperature With Default",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.test_temperature') | float(0) < 20 }}",
                    "severity": "warning",
                }
            },
        },
    )

    alert_data = config_entry.data["alerts"]["temp_with_default"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=config_entry,
        alert_id="temp_with_default",
        alert_data=alert_data,
        group="temperature",
        hub_name="test_hub_temp",
    )

    sensor.entity_id = "binary_sensor.emergency_temperature_with_default"
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value

        # Sensor returns 'unknown', default to 0, 0 < 20 = True
        mock_tpl.async_render.return_value = True
        sensor._evaluate_trigger()
        assert sensor.is_on is True

        await hass.async_block_till_done()
        sensor._cleanup_timers()


async def test_template_error_handling(hass: HomeAssistant):
    """Test that template errors are handled gracefully."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "hub_type": "group",
            "group": "temperature",
            "hub_name": "test_hub_temp",
            "alerts": {
                "temp_error": {
                    "name": "Temperature Error Test",
                    "trigger_type": "template",
                    "template": "{{ states('sensor.test_temperature') | float < 20 }}",
                    "severity": "warning",
                }
            },
        },
    )

    alert_data = config_entry.data["alerts"]["temp_error"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=config_entry,
        alert_id="temp_error",
        alert_data=alert_data,
        group="temperature",
        hub_name="test_hub_temp",
    )

    sensor.entity_id = "binary_sensor.emergency_temperature_error"
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value

        # Simulate template error
        mock_tpl.async_render.side_effect = ValueError(
            "Template error: float got invalid input 'unknown'"
        )

        sensor._evaluate_trigger()
        # Should not trigger on error
        assert sensor.is_on is False

        await hass.async_block_till_done()
        sensor._cleanup_timers()


async def test_template_multiple_comparisons(hass: HomeAssistant):
    """Test template with numeric range checks."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "hub_type": "group",
            "group": "temperature",
            "hub_name": "test_hub_temp",
            "alerts": {
                "temp_in_range": {
                    "name": "Temperature In Range",
                    "trigger_type": "template",
                    "template": (
                        "{{ 15 <= (states('sensor.test_temperature') "
                        "| float(0)) <= 25 }}"
                    ),
                    "severity": "info",
                }
            },
        },
    )

    alert_data = config_entry.data["alerts"]["temp_in_range"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=config_entry,
        alert_id="temp_in_range",
        alert_data=alert_data,
        group="temperature",
        hub_name="test_hub_temp",
    )

    sensor.entity_id = "binary_sensor.emergency_temperature_in_range"
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value

        # Test 20 in range [15, 25] (should trigger)
        mock_tpl.async_render.return_value = True
        sensor._evaluate_trigger()
        assert sensor.is_on is True

        await hass.async_block_till_done()

        # Test 10 not in range [15, 25] (should not trigger)
        mock_tpl.async_render.return_value = False
        sensor._evaluate_trigger()
        assert sensor.is_on is False

    await hass.async_block_till_done()
    sensor._cleanup_timers()


async def test_template_result_types(hass: HomeAssistant):
    """Test that various truthy return values are handled correctly."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "hub_type": "group",
            "group": "test",
            "hub_name": "test_hub",
            "alerts": {
                "test_alert": {
                    "name": "Test Alert",
                    "trigger_type": "template",
                    "template": "{{ true }}",
                    "severity": "info",
                }
            },
        },
    )

    alert_data = config_entry.data["alerts"]["test_alert"]
    sensor = EmergencyBinarySensor(
        hass=hass,
        entry=config_entry,
        alert_id="test_alert",
        alert_data=alert_data,
        group="test",
        hub_name="test_hub",
    )

    sensor.entity_id = "binary_sensor.emergency_test_alert"
    sensor.hass = hass
    sensor.async_on_remove(sensor._cleanup_timers)

    with patch(
        "custom_components.emergency_alerts.binary_sensor.Template"
    ) as MockTemplate:
        mock_tpl = MockTemplate.return_value

        # Test various truthy values per binary_sensor.py:419
        truthy_values = [True, "True", "true", 1, "1"]

        for value in truthy_values:
            mock_tpl.async_render.return_value = value
            sensor._evaluate_trigger()
            assert (
                sensor.is_on is True
            ), f"Expected {value} to be truthy but got {sensor.is_on}"

            # Reset state
            sensor._is_on = False
            sensor._already_triggered = False

        await hass.async_block_till_done()

        # Test falsy values
        falsy_values = [False, "False", "false", 0, "0", None, ""]

        for value in falsy_values:
            mock_tpl.async_render.return_value = value
            sensor._evaluate_trigger()
            assert (
                sensor.is_on is False
            ), f"Expected {value} to be falsy but got {sensor.is_on}"

        await hass.async_block_till_done()
        sensor._cleanup_timers()
