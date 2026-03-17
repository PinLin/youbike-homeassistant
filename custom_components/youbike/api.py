"""YouBike API client — Official Website (unofficial, no auth required)."""
from __future__ import annotations

import logging

import aiohttp

from .const import (
    YOUBIKE_WEBSITE_PARKING_URL,
    YOUBIKE_WEBSITE_STATION_URL,
)

_LOGGER = logging.getLogger(__name__)


class YouBikeWebsiteApiClient:
    """Client for YouBike Official Website API (no auth required).

    ⚠️ This is an unofficial API endpoint and may stop working without warning.
    """

    _BATCH_SIZE = 20

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_fetch_stations_for_area(
        self, area_code: str, uid_prefix: str, keyword: str = ""
    ) -> list[dict]:
        """GET station-min-yb2.json (~9000 stations, single file).

        Filter by area_code (hex, e.g. "00" for Taipei) client-side.
        Apply keyword filter on name_tw.
        Returns list of {uid, name, lat, lng}.
        """
        _LOGGER.debug(
            "Fetching YouBike website station list for area_code=%s", area_code
        )
        async with self._session.get(YOUBIKE_WEBSITE_STATION_URL) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

        if not isinstance(data, list):
            _LOGGER.warning("Unexpected station list format from website API")
            return []

        keyword_lower = keyword.strip().lower()
        results: list[dict] = []
        for item in data:
            if item.get("area_code") != area_code:
                continue
            station_no = str(item.get("station_no", ""))
            if not station_no:
                continue
            name = str(item.get("name_tw", station_no))
            if keyword_lower and keyword_lower not in name.lower():
                continue
            uid = f"{uid_prefix}{station_no}"
            try:
                lat = float(item.get("lat") or 0) or None
                lng = float(item.get("lng") or 0) or None
            except (ValueError, TypeError):
                lat, lng = None, None
            results.append({"uid": uid, "name": name, "lat": lat, "lng": lng})

        _LOGGER.debug(
            "Website station filter: %d stations in area_code=%s", len(results), area_code
        )
        return results

    async def async_fetch_availability(
        self, station_nos: list[str]
    ) -> list[dict]:
        """POST tw2/parkingInfo in batches of 20.

        Body: {"station_no": [...]}.
        Response: retVal.data → list of {station_no, available_spaces_detail.yb2,
        .eyb, empty_spaces, status}. No timestamp in response.
        """
        results: list[dict] = []
        for i in range(0, len(station_nos), self._BATCH_SIZE):
            batch = station_nos[i : i + self._BATCH_SIZE]
            _LOGGER.debug(
                "Fetching website availability for %d stations (batch %d)",
                len(batch), i // self._BATCH_SIZE + 1,
            )
            async with self._session.post(
                YOUBIKE_WEBSITE_PARKING_URL,
                json={"station_no": batch},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)

            ret_val = data.get("retVal", {})
            stations_data = ret_val.get("data", []) if isinstance(ret_val, dict) else []
            results.extend(stations_data)

        _LOGGER.debug("Website availability fetched: %d records", len(results))
        return results
