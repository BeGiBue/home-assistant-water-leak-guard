"""Review fix: options the manager changes itself are applied exactly once."""

from custom_components.water_leak_detection import _async_options_updated
from custom_components.water_leak_detection.const import (
    CONF_HIGH_THRESHOLD_LPH,
    CONF_SLOW_ENABLED,
    DOMAIN,
)
from custom_components.water_leak_detection.manager import WaterLeakManager


async def _manager_with_listener(hass, entry):
    hass.states.async_set("sensor.flow", "10", {"unit_of_measurement": "L/h"})
    manager = WaterLeakManager(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    await manager.async_setup()
    entry.add_update_listener(_async_options_updated)
    applied = []
    apply = manager.async_apply_options

    async def counting_apply():
        applied.append(dict(entry.options))
        await apply()

    manager.async_apply_options = counting_apply
    return manager, applied


async def test_own_option_change_is_not_applied_a_second_time(
    runtime_hass, runtime_entry, measurement_clock
):
    manager, applied = await _manager_with_listener(runtime_hass, runtime_entry)

    await manager.async_set_detector_enabled("slow", False)
    await runtime_hass.async_block_till_done()
    assert runtime_entry.options[CONF_SLOW_ENABLED] is False
    assert manager.engine.settings.slow_enabled is False
    assert applied == []

    await manager.async_update_options({**runtime_entry.options, CONF_HIGH_THRESHOLD_LPH: 700})
    await runtime_hass.async_block_till_done()
    assert manager.engine.settings.high_threshold_lph == 700
    assert applied == []


async def test_foreign_option_change_is_still_applied_live(
    runtime_hass, runtime_entry, measurement_clock
):
    manager, applied = await _manager_with_listener(runtime_hass, runtime_entry)

    runtime_hass.config_entries.async_update_entry(
        runtime_entry, options={**runtime_entry.options, CONF_HIGH_THRESHOLD_LPH: 800}
    )
    await runtime_hass.async_block_till_done()
    assert len(applied) == 1
    assert manager.engine.settings.high_threshold_lph == 800
