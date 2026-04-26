"""Diagnostics support for YouBike."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# Station coordinates and IDs are public information for YouBike, so we keep
# the redaction set conservative — only common credential keys we'd want
# stripped if any future config flow stores them.
REDACT_KEYS = {
    "access_token",
    "refresh_token",
    "password",
    "api_key",
}


def _serialize(obj: Any) -> Any:
    """Convert nested dataclasses to plain dicts so async_redact_data can walk them."""
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostic info for one config entry."""
    coordinator = entry.runtime_data
    raw_data = coordinator.data if coordinator is not None else None

    return {
        "entry": async_redact_data(entry.as_dict(), REDACT_KEYS),
        "coordinator": {
            "last_update_success": (
                coordinator.last_update_success if coordinator is not None else None
            ),
        },
        "data": async_redact_data(_serialize(raw_data), REDACT_KEYS),
    }
