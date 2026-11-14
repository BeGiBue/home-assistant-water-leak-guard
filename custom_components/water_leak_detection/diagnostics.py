"""Downloadable diagnostics for one Water Leak Guard entry.

The download is meant to be attached to an issue. Recipient tokens authorize
alarm actions and never leave the server; names of people, their devices and
HA logins are personal. Both are redacted. Reset nonces are not part of any
public payload used here.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    RECIPIENT_NAME,
    RECIPIENT_NOTIFY_SERVICE,
    RECIPIENT_SESSION_TOKEN_ID,
    RECIPIENT_SESSION_USER_ID,
    RECIPIENT_TOKEN,
    RECIPIENT_TRACKER_ENTITY,
)

TO_REDACT = {
    RECIPIENT_TOKEN,
    RECIPIENT_NAME,
    RECIPIENT_NOTIFY_SERVICE,
    RECIPIENT_TRACKER_ENTITY,
    RECIPIENT_SESSION_TOKEN_ID,
    RECIPIENT_SESSION_USER_ID,
    "reset_nonce",
    "recipient_token",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the configuration and the live runtime view of one entry."""
    result: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "loaded": False,
    }
    manager = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if manager is None:
        return result

    now = dt_util.utcnow()
    thresholds = manager.adaptive_thresholds(now)
    learning = manager.learning_snapshot
    long_term = manager.long_term_learner
    result.update(
        {
            "loaded": True,
            "status": {
                "alarm_active": manager.alarm_active,
                "shutoff_request": manager.shutoff_request,
                "hydraulic_monitoring_status": manager.hydraulic_monitoring_status,
                "hydraulic_monitoring_reason": manager.hydraulic_monitoring_reason,
                "high_flow_bypass_active": manager.high_flow_bypass_active,
                "learning_storage_ready": manager.learning_storage_ready,
                "storage_recovery_required": manager.storage_recovery_required,
                "active_event_ids": sorted(manager.active_events()),
            },
            "measurement": manager.source_diagnostics(),
            "detectors": manager.hydraulic_diagnostics(),
            "detector_settings": asdict(manager.engine.settings),
            "thresholds": asdict(thresholds),
            "learning": {**asdict(learning), "confidence": learning.confidence.value},
            "long_term_learning": {
                "confirmed_long_term_normal_max_lph": (
                    long_term.confirmed_long_term_normal_max_lph
                ),
                "pending_count": len(long_term.pending_high_candidates),
                "confirmed_history_count": len(long_term.confirmed_high_history),
                "startup_guard_blocked": long_term.high_blocked,
            },
            "external_sources": async_redact_data(manager.external_diagnostics(), TO_REDACT),
            "notification_events": {
                event_id: {
                    "globally_acknowledged": state.globally_acknowledged,
                    "muted_recipient_count": len(state.muted_recipients),
                    "dispatch_states": sorted(set(state.dispatch_states.values())),
                }
                for event_id, state in manager.notifications.acknowledgements.items()
            },
        }
    )
    return result
