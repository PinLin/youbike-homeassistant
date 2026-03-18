"""Config flow for YouBike."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

_LOGGER = logging.getLogger(__name__)

from .const import (
    CITY_TO_WEBSITE_AREA_CODE,
    CITY_TO_WEBSITE_UID_PREFIX,
    CONF_SCAN_INTERVAL,
    CONF_STATION_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    WEBSITE_AVAILABLE_CITIES,
)

_CITY_OPTIONS = [
    selector.SelectOptionDict(value=k, label=k)
    for k in WEBSITE_AVAILABLE_CITIES
]


class YouBikeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for YouBike."""

    VERSION = 1

    def __init__(self) -> None:
        self._city: str = ""
        self._area_code: str = ""
        self._uid_prefix: str = ""
        self._keyword: str = ""
        self._station_uid: str = ""

    # ------------------------------------------------------------------
    # Step 1: city selection
    # ------------------------------------------------------------------
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        return await self.async_step_city(user_input)

    async def async_step_city(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._city = user_input["city"]
            self._area_code = CITY_TO_WEBSITE_AREA_CODE.get(self._city, "")
            self._uid_prefix = CITY_TO_WEBSITE_UID_PREFIX.get(self._city, self._city[:3].upper())
            self._keyword = ""
            return await self.async_step_search()

        schema = vol.Schema({
            vol.Required("city", default="Taipei"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_CITY_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="city",
                )
            ),
        })
        return self.async_show_form(step_id="city", data_schema=schema)

    # ------------------------------------------------------------------
    # Step 2: keyword search
    # ------------------------------------------------------------------
    async def async_step_search(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._keyword = user_input.get("keyword", "").strip()
            return await self.async_step_results()

        return self.async_show_form(
            step_id="search",
            data_schema=vol.Schema({
                vol.Optional("keyword", default=self._keyword): selector.TextSelector(),
            }),
        )

    # ------------------------------------------------------------------
    # Step 3: station selection from filtered results
    # ------------------------------------------------------------------
    async def async_step_results(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        # Ensure cache is populated
        from . import async_ensure_area_cached
        await async_ensure_area_cached(self.hass, self._area_code, self._uid_prefix)

        all_stations = _stations_for_area(self.hass, self._area_code, self._uid_prefix)

        if user_input is not None:
            if user_input.get("back"):
                return await self.async_step_search()
            uid = user_input.get(CONF_STATION_ID)
            if uid:
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()
                self._station_uid = uid
                return await self.async_step_settings()
            errors["base"] = "no_station_selected"

        keyword_lower = self._keyword.lower()
        if keyword_lower:
            stations = [(uid, name) for uid, name in all_stations if keyword_lower in name.lower()]
        else:
            stations = all_stations

        if not all_stations:
            errors["base"] = "cannot_connect"

        station_options = [
            selector.SelectOptionDict(value=uid, label=name)
            for uid, name in stations
        ]

        return self.async_show_form(
            step_id="results",
            data_schema=vol.Schema({
                vol.Optional(CONF_STATION_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=station_options,
                        multiple=False,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional("back", default=False): selector.BooleanSelector(),
            }),
            description_placeholders={
                "count": str(len(stations)),
                "keyword": self._keyword or "（全部）",
            },
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Step 4: scan interval
    # ------------------------------------------------------------------
    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            scan_interval = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
            cache = self.hass.data.get(DOMAIN, {}).get("station_cache", {})
            station_name = cache.get(self._station_uid, {}).get("name", self._station_uid)
            city_label = WEBSITE_AVAILABLE_CITIES.get(self._city, self._city)
            title = f"{city_label} {station_name}"
            return self.async_create_entry(
                title=title,
                data={
                    CONF_STATION_ID: self._station_uid,
                    CONF_SCAN_INTERVAL: scan_interval,
                },
            )

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema({
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> YouBikeOptionsFlow:
        return YouBikeOptionsFlow(config_entry)


class YouBikeOptionsFlow(config_entries.OptionsFlow):
    """Options flow — update scan interval only."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        cfg = {**self._config_entry.data, **self._config_entry.options}
        current_interval = int(cfg.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_SCAN_INTERVAL: int(user_input.get(CONF_SCAN_INTERVAL, current_interval))},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }),
        )


def _stations_for_area(hass, area_code: str, uid_prefix: str) -> list[tuple[str, str]]:
    """Return list of (uid, name) for an area from the integration cache."""
    cache = hass.data.get(DOMAIN, {}).get("station_cache", {})
    return [
        (uid, info["name"])
        for uid, info in cache.items()
        if uid.startswith(uid_prefix)
    ]
