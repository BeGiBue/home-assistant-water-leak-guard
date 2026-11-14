"""Review fixes: tick/measurement race and the invalid-flow log message."""

import asyncio
import logging

from homeassistant.helpers import entity_registry as er
from test_hydrus_mqtt_diagnostics import HydrusTransport

from custom_components.water_leak_detection import manager as manager_module
from custom_components.water_leak_detection.const import DOMAIN
from custom_components.water_leak_detection.manager import WaterLeakManager

MANAGER_LOGGER = "custom_components.water_leak_detection.manager"


async def test_tick_during_provenance_write_keeps_the_report_credit(
    runtime_hass, runtime_entry, measurement_clock
):
    """A tick that fires while the MQTT provenance is persisted is not an evidence gap."""
    transport = HydrusTransport(runtime_hass, runtime_entry, measurement_clock, True)
    await transport.telegram(0.250, 0)
    manager = WaterLeakManager(runtime_hass, runtime_entry)
    runtime_hass.data.setdefault(DOMAIN, {})[runtime_entry.entry_id] = manager
    await manager.async_setup()
    await transport.telegram(0.250)
    await transport.telegram(0.250)
    assert manager.engine.last_evidence_gap is False

    save = manager._store.async_save
    ticks = []

    async def save_while_tick_fires(data):
        # The periodic tick is not serialized up to its refresh: let it run now.
        ticks.append(asyncio.ensure_future(manager._async_tick(None)))
        await asyncio.sleep(0)
        await save(data)

    manager._store.async_save = save_while_tick_fires
    await transport.telegram(0.250)
    manager._store.async_save = save
    await asyncio.gather(*ticks)

    assert ticks, "the measurement must have persisted its provenance"
    assert manager.source_available
    assert manager.engine.last_evidence_gap is False


async def _invalid_then_valid(hass, manager, value):
    hass.states.async_set("sensor.flow", value, {"unit_of_measurement": "L/h"})
    await hass.async_block_till_done()
    assert manager.hydraulic_monitoring_reason == "invalid_flow_measurement"
    hass.states.async_set("sensor.flow", "10", {"unit_of_measurement": "L/h"})
    await hass.async_block_till_done()
    assert manager.hydraulic_monitoring_reason == "verified_measurement"


async def test_invalid_flow_names_the_value_and_warns_once_per_interval(
    runtime_hass, runtime_entry, measurement_clock, caplog
):
    assert er.async_get(runtime_hass).async_get("sensor.flow").platform == "test"
    runtime_hass.states.async_set("sensor.flow", "10", {"unit_of_measurement": "L/h"})
    manager = WaterLeakManager(runtime_hass, runtime_entry)
    runtime_hass.data.setdefault(DOMAIN, {})[runtime_entry.entry_id] = manager
    await manager.async_setup()

    def warnings():
        return [
            record
            for record in caplog.records
            if record.name == MANAGER_LOGGER
            and record.levelno == logging.WARNING
            and "Unable to normalize flow source" in record.getMessage()
        ]

    with caplog.at_level(logging.DEBUG, logger=MANAGER_LOGGER):
        for _ in range(3):
            measurement_clock.advance(60)
            await _invalid_then_valid(runtime_hass, manager, "-0.4")
        assert len(warnings()) == 1
        message = warnings()[0].getMessage()
        assert "sensor.flow" in message and "'-0.4'" in message and "'L/h'" in message

        measurement_clock.advance(manager_module.INVALID_FLOW_WARNING_INTERVAL_SECONDS)
        await _invalid_then_valid(runtime_hass, manager, "nan")
        assert len(warnings()) == 2
        # Two repeats were logged at debug level only; this warning accounts for them.
        assert "3 invalid report(s) since the last warning, 4 since start" in (
            warnings()[1].getMessage()
        )

    diagnostics = manager.source_diagnostics()
    assert diagnostics["invalid_flow_report_count"] == 4
    assert diagnostics["last_invalid_flow_state"] == "nan"
    assert diagnostics["last_invalid_flow_at"] is not None
