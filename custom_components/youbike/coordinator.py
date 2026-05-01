"""YouBike coordinator — periodic polling for a single station."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import YouBikeApiError, YouBikeWebsiteApiClient
from .const import DOMAIN, EVENT_UPDATED, UID_PREFIX_TO_AREA_CODE

_LOGGER = logging.getLogger(__name__)


@dataclass
class StationData:
    uid: str
    name: str
    available_rent_general: int
    available_rent_electric: int
    available_return: int
    service_status: int        # 1 = in service, 0 = suspended
    src_update_time: datetime | None
    latitude: float | None = None
    longitude: float | None = None


class YouBikeCoordinator(DataUpdateCoordinator[dict[str, StationData]]):
    """Coordinator that fetches YouBike data for a single station."""

    # Tolerate this many consecutive failures by returning the previous data
    # so a brief upstream blip doesn't make every entity flip to unavailable.
    # The Official Website API is unofficial and known to hiccup occasionally.
    _MAX_CONSECUTIVE_FAILURES = 2

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        entry_id: str,
        scan_interval: int,
        website_api: YouBikeWebsiteApiClient,
        station_name: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            # Unique per entry so multi-entry logs don't all collide under one logger.
            name=f"{DOMAIN}_{entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._station_ids = [station_id]
        self._entry_id = entry_id
        self._website_api = website_api
        self._station_name = station_name
        self._consecutive_failures = 0

    @property
    def station_ids(self) -> tuple[str, ...]:
        """Station IDs handled by this coordinator."""
        return tuple(self._station_ids)

    @property
    def station_name(self) -> str:
        """Display name for this station when fresh data is not available yet."""
        return self._station_name

    def _uid_prefix(self, uid: str) -> str | None:
        for prefix in UID_PREFIX_TO_AREA_CODE:
            if uid.startswith(prefix):
                return prefix
        return None

    async def _async_update_data(self) -> dict[str, StationData]:
        uid = self._station_ids[0]
        _LOGGER.debug("Updating YouBike data for station: %s", uid)
        try:
            result = await self._async_update_website()
        except YouBikeApiError as exc:
            self._consecutive_failures += 1
            if (
                self._consecutive_failures < self._MAX_CONSECUTIVE_FAILURES
                and self.data is not None
            ):
                _LOGGER.warning(
                    "YouBike: transient failure %d/%d, keeping last known data for %s: %s",
                    self._consecutive_failures,
                    self._MAX_CONSECUTIVE_FAILURES,
                    uid,
                    exc,
                )
                return self.data
            _LOGGER.error("Failed to fetch website availability for %s: %s", uid, exc)
            raise UpdateFailed(f"Error fetching availability: {exc}") from exc

        self._consecutive_failures = 0
        self.hass.bus.async_fire(
            EVENT_UPDATED,
            {
                "entry_id": self._entry_id,
                "stations": {
                    uid: {
                        "name": s.name,
                        "available_rent_general": s.available_rent_general,
                        "available_rent_electric": s.available_rent_electric,
                        "available_return": s.available_return,
                    }
                    for uid, s in result.items()
                },
            },
        )
        return result

    async def _async_update_website(self) -> dict[str, StationData]:
        fetch_time = dt_util.now()
        uid = self._station_ids[0]

        uid_prefix = self._uid_prefix(uid)
        if uid_prefix is None:
            raise UpdateFailed(f"Unknown UID prefix for station {uid}")

        station_no = uid[len(uid_prefix):]

        avail = await self._website_api.async_fetch_availability([station_no])

        # Read name and location from integration-level cache
        cache = self.hass.data.get(DOMAIN, {}).get("station_cache", {})
        station_info = cache.get(uid, {})
        name = station_info.get("name", uid)
        lat = station_info.get("lat")
        lng = station_info.get("lng")

        result: dict[str, StationData] = {}
        for item in avail:
            if str(item.get("station_no", "")) != station_no:
                continue
            detail = item.get("available_spaces_detail") or {}
            general = int(detail.get("yb2") or 0)
            electric = int(detail.get("eyb") or 0)
            ret = int(item.get("empty_spaces") or 0)
            status = int(item.get("status", 1))
            result[uid] = StationData(
                uid, name, general, electric, ret, status,
                fetch_time, lat, lng,
            )

        _LOGGER.debug("Website update complete for station %s: %s", uid, "matched" if result else "no match")
        return result
