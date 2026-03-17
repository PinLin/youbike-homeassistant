"""YouBike Home Assistant integration."""
from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .api import YouBikeWebsiteApiClient
from .const import (
    CITY_TO_WEBSITE_AREA_CODE,
    CITY_TO_WEBSITE_UID_PREFIX,
    CONF_SCAN_INTERVAL,
    CONF_STATION_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_UPDATE,
    STATION_CACHE_TTL,
    UID_PREFIX_TO_AREA_CODE,
)
from .coordinator import YouBikeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]


async def async_ensure_area_cached(
    hass: HomeAssistant, area_code: str, uid_prefix: str
) -> None:
    """Populate integration-level station cache for an area, with 24h TTL.

    Uses its own temporary aiohttp session. Silently ignores fetch errors.
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("station_cache", {})
    hass.data[DOMAIN].setdefault("station_cache_time", {})

    last_fetch = hass.data[DOMAIN]["station_cache_time"].get(area_code)
    if last_fetch is not None:
        age = (dt_util.now() - last_fetch).total_seconds()
        if age < STATION_CACHE_TTL:
            return

    try:
        async with aiohttp.ClientSession() as session:
            client = YouBikeWebsiteApiClient(session)
            stations = await client.async_fetch_stations_for_area(area_code, uid_prefix)
        cache = hass.data[DOMAIN]["station_cache"]
        for s in stations:
            cache[s["uid"]] = {
                "name": s["name"],
                "lat": s.get("lat"),
                "lng": s.get("lng"),
            }
        hass.data[DOMAIN]["station_cache_time"][area_code] = dt_util.now()
        _LOGGER.debug(
            "Station cache populated for area_code=%s: %d stations", area_code, len(stations)
        )
    except Exception as exc:
        _LOGGER.warning("Failed to cache stations for area %s: %s", area_code, exc)


def _uid_to_prefix_and_area(uid: str) -> tuple[str, str] | None:
    """Return (uid_prefix, area_code) for a station UID, or None if unknown."""
    for prefix, area_code in UID_PREFIX_TO_AREA_CODE.items():
        if uid.startswith(prefix):
            return prefix, area_code
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up YouBike from a config entry."""
    config = {**entry.data, **entry.options}

    station_uid = config[CONF_STATION_ID].strip()
    scan_interval = int(config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    # Populate area cache so coordinator can read station name/location
    pair = _uid_to_prefix_and_area(station_uid)
    if pair:
        uid_prefix, area_code = pair
        await async_ensure_area_cached(hass, area_code, uid_prefix)
    else:
        _LOGGER.warning("Unknown UID prefix for station %s; name cache skipped", station_uid)

    session = aiohttp.ClientSession()
    website_client = YouBikeWebsiteApiClient(session)

    coordinator = YouBikeCoordinator(
        hass=hass,
        station_id=station_uid,
        entry_id=entry.entry_id,
        scan_interval=scan_interval,
        website_api=website_client,
    )

    _LOGGER.info(
        "Setting up YouBike entry: station=%s interval=%ds",
        station_uid, scan_interval,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        _LOGGER.error("First refresh failed for YouBike entry %s: %s", entry.entry_id, exc)
        await session.close()
        raise ConfigEntryNotReady from exc

    entry.runtime_data = coordinator
    _LOGGER.info("YouBike entry %s ready (station=%s)", entry.entry_id, station_uid)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    # Register services once (guard against multiple entries)
    if not hass.services.has_service(DOMAIN, SERVICE_UPDATE):
        async def handle_update(call: ServiceCall) -> None:
            """Refresh YouBike coordinators, optionally filtered by station IDs."""
            target_ids: set[str] = set(call.data.get("station_ids", []))
            for config_entry in hass.config_entries.async_entries(DOMAIN):
                if not hasattr(config_entry, "runtime_data"):
                    continue
                c = config_entry.runtime_data
                if target_ids and not target_ids.intersection(c._station_ids):
                    continue
                await c.async_refresh()

        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE,
            handle_update,
            schema=vol.Schema({
                vol.Optional("station_ids", default=[]): vol.All(cv.ensure_list, [cv.string]),
            }),
        )

    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading YouBike entry %s", entry.entry_id)
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if hasattr(entry, "runtime_data"):
        coordinator: YouBikeCoordinator = entry.runtime_data
        await coordinator._website_api._session.close()

    remaining = [
        e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id != entry.entry_id
    ]
    if not remaining:
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE)
        hass.data.pop(DOMAIN, None)

    return unloaded
