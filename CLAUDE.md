# YouBike Home Assistant Integration — Project Guide

## Overview

HA custom component (`custom_components/youbike/`) for monitoring YouBike 2.0 station availability. Each station is a separate config entry with its own coordinator and update interval.

## Architecture

### Data Source

Only the Official Website API (`website`) is used. Unofficial endpoint — may break without warning.

- Station list: `GET https://apis.youbike.com.tw/json/station-min-yb2.json` — ~9000 stations, filter by `area_code` (hex)
- Availability: `POST https://apis.youbike.com.tw/tw2/parkingInfo` — body `{"station_no": [...]}`, batched (default 20)
- Response: `retVal.data[].{station_no, available_spaces_detail.{yb2, eyb}, empty_spaces, status}`
- No auth headers needed. No per-station timestamp → `src_update_time` = coordinator fetch time (`dt_util.now()`)

### UID Format

Format: `{CITY_PREFIX}{station_no}` — no suffix, no underscore between prefix and number.

Example: `TPE500101001`

City prefixes defined in `CITY_TO_WEBSITE_UID_PREFIX` (const.py). Reverse map `UID_PREFIX_TO_AREA_CODE` also defined there.

### Station Cache

Integration-level cache in `hass.data[DOMAIN]`:
- `station_cache`: `{uid: {"name": str, "lat": float|None, "lng": float|None}}`
- `station_cache_time`: `{area_code: datetime}` — TTL 24h (`STATION_CACHE_TTL`)

`async_ensure_area_cached(hass, area_code, uid_prefix)` in `__init__.py` populates and refreshes the cache. Used by both config flow (for station browsing) and `async_setup_entry` (so coordinator can read names). Creates its own temporary session.

Cache is cleared from `hass.data` when the last entry is unloaded.

### One Entry = One Station

Each config entry monitors exactly one station. `CONF_STATION_ID` stores the single UID string.

### Coordinator

`YouBikeCoordinator` receives a single `station_id`. It:
1. Derives `uid_prefix` from `UID_PREFIX_TO_AREA_CODE`
2. Extracts `station_no = uid[len(uid_prefix):]`
3. Calls `async_fetch_availability([station_no])`
4. Reads name/location from `hass.data[DOMAIN]["station_cache"]`

### Sensor unique_id

Format: `youbike_{uid.lower()}_{sensor_type}`
Example: `youbike_tpe500101001_general_bikes`

### Sensors (4 per station) + Binary Sensor (1 per station)

| Translation key | Type | Description |
|----------------|------|-------------|
| `general_bikes` | sensor | Available general bikes to rent |
| `electric_bikes` | sensor | Available electric-assist bikes to rent |
| `available_docks` | sensor | Available docks to return bikes |
| `last_update` | sensor (timestamp) | Coordinator fetch time |
| `service_status` | binary_sensor | Station in service (True/False) |

### Device Info

- `name` = UID (e.g. `TPE500101001`) → generates clean entity_id like `sensor.tpe500101001_general_bikes`
- `model` = Chinese station name (shown in device details)
- `manufacturer` = `YouBike`

### Config Flow Steps

city → station (single select) → settings (scan_interval)

Entry unique_id = station UID (prevents duplicate entries for same station).
Entry title = Chinese station name (from cache).

### OptionsFlow

Only `scan_interval` can be changed. To change station, delete and re-add.

## Key Files

| File | Purpose |
|------|---------|
| `const.py` | Constants: WEBSITE_AVAILABLE_CITIES, CITY_TO_WEBSITE_AREA_CODE, CITY_TO_WEBSITE_UID_PREFIX, UID_PREFIX_TO_AREA_CODE, API URLs |
| `api.py` | YouBikeWebsiteApiClient only |
| `coordinator.py` | YouBikeCoordinator, StationData dataclass, single-station website update |
| `__init__.py` | async_setup_entry, async_ensure_area_cached, service registration |
| `config_flow.py` | YouBikeConfigFlow (city→station→settings) + YouBikeOptionsFlow |
| `sensor.py` | 4 sensor types; latitude/longitude in extra_state_attributes |
| `binary_sensor.py` | service_status binary sensor |
| `strings.json` | English strings + selector options |
| `translations/zh-Hant.json` | Traditional Chinese strings |
| `services.yaml` | Service schema documentation |
| `manifest.json` | HA integration manifest |
| `icon.svg` | YouBike official logo |

## Session / Cleanup

Each config entry owns one `aiohttp.ClientSession`. Closed in `async_unload_entry` via `coordinator._website_api._session`. `async_ensure_area_cached` uses its own temporary session (not stored).

## Deployment

rsync to `keelunghome.netbird.cloud` + `ha core restart`
