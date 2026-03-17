"""YouBike coordinator — periodic polling for a single station."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import YouBikeWebsiteApiClient
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

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        entry_id: str,
        scan_interval: int,
        website_api: YouBikeWebsiteApiClient,
    ) -> None:
        update_interval = timedelta(seconds=scan_interval) if scan_interval > 0 else None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._station_ids = [station_id]
        self._entry_id = entry_id
        self._website_api = website_api

    def _uid_prefix(self, uid: str) -> str | None:
        for prefix in UID_PREFIX_TO_AREA_CODE:
            if uid.startswith(prefix):
                return prefix
        return None

    async def async_refresh(self) -> None:
        """Refresh data and fire youbike_updated event when done."""
        await super().async_refresh()
        event_data: dict = {
            "entry_id": self._entry_id,
            "success": self.last_update_success,
        }
        if self.last_update_success and self.data:
            event_data["stations"] = {
                uid: {
                    "name": s.name,
                    "available_rent_general": s.available_rent_general,
                    "available_rent_electric": s.available_rent_electric,
                    "available_return": s.available_return,
                }
                for uid, s in self.data.items()
            }
        self.hass.bus.async_fire(EVENT_UPDATED, event_data)

    async def _async_update_data(self) -> dict[str, StationData]:
        _LOGGER.debug("Updating YouBike data for station: %s", self._station_ids[0])
        return await self._async_update_website()

    async def _async_update_website(self) -> dict[str, StationData]:
        fetch_time = dt_util.now()
        uid = self._station_ids[0]

        uid_prefix = self._uid_prefix(uid)
        if uid_prefix is None:
            raise UpdateFailed(f"Unknown UID prefix for station {uid}")

        station_no = uid[len(uid_prefix):]

        try:
            avail = await self._website_api.async_fetch_availability([station_no])
        except Exception as exc:
            _LOGGER.error("Failed to fetch website availability for %s: %s", uid, exc)
            raise UpdateFailed(f"Error fetching availability: {exc}") from exc

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
            status = int(item.get("status") or 1)
            result[uid] = StationData(
                uid, name, general, electric, ret, status,
                fetch_time, lat, lng,
            )

        _LOGGER.debug("Website update complete for station %s: %s", uid, "matched" if result else "no match")
        return result
