"""YouBike sensor entities."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StationData, YouBikeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up YouBike sensors for a config entry."""
    coordinator: YouBikeCoordinator = entry.runtime_data

    entities: list[SensorEntity] = []
    for uid in coordinator._station_ids:
        entities.append(YouBikeGeneralBikeSensor(coordinator, uid))
        entities.append(YouBikeElectricBikeSensor(coordinator, uid))
        entities.append(YouBikeReturnSensor(coordinator, uid))
        entities.append(YouBikeLastUpdateSensor(coordinator, uid))

    async_add_entities(entities)


class YouBikeBaseSensor(CoordinatorEntity[YouBikeCoordinator], SensorEntity):
    """Base class for YouBike sensors."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "bikes"
    _attr_icon = "mdi:bicycle"
    _sensor_type: str  # defined in each subclass; used for entity_id suffix

    def __init__(self, coordinator: YouBikeCoordinator, uid: str) -> None:
        super().__init__(coordinator)
        self._uid = uid
        # Set entity_id explicitly so it is always UID-based and stable,
        # independent of translation-loading timing.
        self.entity_id = f"sensor.{uid.lower()}_{self._sensor_type}"

    @property
    def _station(self) -> StationData | None:
        if self.coordinator.data:
            return self.coordinator.data.get(self._uid)
        return None

    @property
    def available(self) -> bool:
        station = self._station
        return (
            self.coordinator.last_update_success
            and station is not None
            and station.service_status == 1
        )

    @property
    def extra_state_attributes(self) -> dict | None:
        station = self._station
        if station and station.latitude is not None:
            return {"latitude": station.latitude, "longitude": station.longitude}
        return None

    @property
    def device_info(self) -> DeviceInfo:
        station = self._station
        return DeviceInfo(
            identifiers={(DOMAIN, self._uid)},
            name=station.name if station else self._uid,
            model=self._uid,
            manufacturer="YouBike",
        )


class YouBikeGeneralBikeSensor(YouBikeBaseSensor):
    """Sensor for available general (non-electric) bikes to rent."""

    _sensor_type = "general_bikes"
    _attr_icon = "mdi:bicycle"
    _attr_translation_key = "general_bikes"

    @property
    def unique_id(self) -> str:
        return f"youbike_{self._uid.lower()}_general_bikes"

    @property
    def native_value(self) -> int | None:
        station = self._station
        return station.available_rent_general if station else None


class YouBikeElectricBikeSensor(YouBikeBaseSensor):
    """Sensor for available electric-assist bikes to rent."""

    _sensor_type = "electric_bikes"
    _attr_icon = "mdi:bicycle-electric"
    _attr_translation_key = "electric_bikes"

    @property
    def unique_id(self) -> str:
        return f"youbike_{self._uid.lower()}_electric_bikes"

    @property
    def native_value(self) -> int | None:
        station = self._station
        return station.available_rent_electric if station else None


class YouBikeReturnSensor(YouBikeBaseSensor):
    """Sensor for available docks to return bikes."""

    _sensor_type = "available_docks"
    _attr_icon = "mdi:bicycle-basket"
    _attr_translation_key = "available_docks"

    @property
    def unique_id(self) -> str:
        return f"youbike_{self._uid.lower()}_available_docks"

    @property
    def native_value(self) -> int | None:
        station = self._station
        return station.available_return if station else None


class YouBikeLastUpdateSensor(YouBikeBaseSensor):
    """Sensor showing when coordinator last fetched data for this station."""

    _sensor_type = "last_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_state_class = None
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:clock-outline"
    _attr_translation_key = "last_update"

    @property
    def unique_id(self) -> str:
        return f"youbike_{self._uid.lower()}_last_update"

    @property
    def native_value(self) -> datetime | None:
        station = self._station
        return station.src_update_time if station else None
