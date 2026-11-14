"""Review addition: downloadable diagnostics never contain tokens or personal names."""

import json

from custom_components.water_leak_detection.const import (
    CONF_NOTIFICATION_RECIPIENTS,
    DOMAIN,
)
from custom_components.water_leak_detection.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.water_leak_detection.manager import WaterLeakManager

SECRET = "recipient-secret-token"


def _with_recipient(hass, entry):
    hass.config_entries.async_update_entry(
        entry,
        options={
            CONF_NOTIFICATION_RECIPIENTS: [
                {
                    "id": "r1",
                    "name": "Private Name",
                    "notify_service": "notify.mobile_app_private_phone",
                    "tracker_entity": "device_tracker.private_phone",
                    "token": SECRET,
                    "session_user_id": "private-user-id",
                }
            ]
        },
    )


async def test_diagnostics_of_a_loaded_entry_are_redacted_and_serializable(
    runtime_hass, runtime_entry, measurement_clock
):
    _with_recipient(runtime_hass, runtime_entry)
    runtime_hass.states.async_set("sensor.flow", "10", {"unit_of_measurement": "L/h"})
    manager = WaterLeakManager(runtime_hass, runtime_entry)
    runtime_hass.data.setdefault(DOMAIN, {})[runtime_entry.entry_id] = manager
    await manager.async_setup()

    data = await async_get_config_entry_diagnostics(runtime_hass, runtime_entry)
    text = json.dumps(data, default=str)

    assert data["loaded"] is True
    assert data["measurement"]["flow_source"] == "sensor.flow"
    assert data["status"]["hydraulic_monitoring_status"] == "active"
    assert data["detector_settings"]["burst_threshold_lph"] > 0
    recipient = data["entry"]["options"][CONF_NOTIFICATION_RECIPIENTS][0]
    assert recipient["id"] == "r1" and recipient["token"] == "**REDACTED**"
    for private in (SECRET, "Private Name", "private_phone", "private-user-id"):
        assert private not in text


async def test_diagnostics_of_an_unloaded_entry_only_show_redacted_configuration(
    runtime_hass, runtime_entry
):
    _with_recipient(runtime_hass, runtime_entry)
    data = await async_get_config_entry_diagnostics(runtime_hass, runtime_entry)
    assert data["loaded"] is False and "measurement" not in data
    assert SECRET not in json.dumps(data)
