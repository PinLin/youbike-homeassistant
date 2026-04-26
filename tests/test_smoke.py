"""Smoke tests for the YouBike integration.

These tests cover pure helpers and dataclasses that don't require Home
Assistant's full test scaffolding. Run with:

    python -m pytest tests/ -v
"""
from __future__ import annotations

from datetime import datetime

from custom_components.youbike.api import YouBikeApiError
from custom_components.youbike.const import (
    CITY_TO_WEBSITE_AREA_CODE,
    CITY_TO_WEBSITE_UID_PREFIX,
    DOMAIN,
    UID_PREFIX_TO_AREA_CODE,
    WEBSITE_AVAILABLE_CITIES,
)
from custom_components.youbike.coordinator import StationData


def test_domain_constant() -> None:
    assert DOMAIN == "youbike"


def test_city_maps_align() -> None:
    """Every supported city must have an area_code AND a UID prefix."""
    for city in WEBSITE_AVAILABLE_CITIES:
        assert city in CITY_TO_WEBSITE_AREA_CODE, f"missing area_code for {city}"
        assert city in CITY_TO_WEBSITE_UID_PREFIX, f"missing uid_prefix for {city}"


def test_uid_prefix_to_area_code_inverse_consistent() -> None:
    """The UID-prefix→area_code reverse map should agree with the forward maps."""
    for city, prefix in CITY_TO_WEBSITE_UID_PREFIX.items():
        forward = CITY_TO_WEBSITE_AREA_CODE[city]
        assert UID_PREFIX_TO_AREA_CODE[prefix] == forward, (
            f"{city}: prefix {prefix!r} should map to area_code {forward!r}"
        )


def test_uid_prefixes_unique() -> None:
    """Distinct cities cannot share a UID prefix — UID parsing depends on it."""
    prefixes = list(CITY_TO_WEBSITE_UID_PREFIX.values())
    assert len(prefixes) == len(set(prefixes))


def test_station_data_holds_all_metrics() -> None:
    """StationData must accept the full set of fields the coordinator emits."""
    now = datetime(2026, 4, 26, 20, 0)
    s = StationData(
        uid="TPE500101001",
        name="台大校門口",
        available_rent_general=5,
        available_rent_electric=2,
        available_return=10,
        service_status=1,
        src_update_time=now,
        latitude=25.017,
        longitude=121.539,
    )
    assert s.uid == "TPE500101001"
    assert s.service_status == 1
    assert s.src_update_time == now


def test_station_data_optional_coordinates() -> None:
    """Coordinates are optional — coordinator skips them when cache misses."""
    s = StationData(
        uid="TPE500101001",
        name="台大校門口",
        available_rent_general=0,
        available_rent_electric=0,
        available_return=0,
        service_status=0,
        src_update_time=None,
    )
    assert s.latitude is None
    assert s.longitude is None


def test_youbike_api_error_is_exception() -> None:
    """The custom error must inherit from Exception so ``except`` catches it."""
    assert issubclass(YouBikeApiError, Exception)
    err = YouBikeApiError("boom")
    assert str(err) == "boom"
