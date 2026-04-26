"""YouBike sensor entities."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import YouBikeCoordinator
from .entity import YouBikeEntityBase


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


class YouBikeBaseSensor(YouBikeEntityBase, SensorEntity):
    """Sensor base — adds platform-specific defaults and entity_id."""

    _attr_native_unit_of_measurement = "bikes"
    _attr_icon = "mdi:bicycle"

    def __init__(self, coordinator: YouBikeCoordinator, uid: str) -> None:
        super().__init__(coordinator, uid)
        # Entity_id is UID-based and stable, independent of translation timing.
        self.entity_id = f"sensor.youbike_{uid.lower()}_{self._sensor_type}"

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


class YouBikeGeneralBikeSensor(YouBikeBaseSensor):
    """Sensor for available general (non-electric) bikes to rent."""

    _sensor_type = "general_bikes"
    _attr_icon = "mdi:bicycle"
    _attr_translation_key = "general_bikes"

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
    def native_value(self) -> int | None:
        station = self._station
        return station.available_rent_electric if station else None


class YouBikeReturnSensor(YouBikeBaseSensor):
    """Sensor for available docks to return bikes."""

    _sensor_type = "available_docks"
    _attr_icon = "mdi:bicycle-basket"
    _attr_translation_key = "available_docks"

    @property
    def native_value(self) -> int | None:
        station = self._station
        return station.available_return if station else None


class YouBikeLastUpdateSensor(YouBikeBaseSensor):
    """Sensor showing when coordinator last fetched data for this station."""

    _sensor_type = "last_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:clock-outline"
    _attr_translation_key = "last_update"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> datetime | None:
        station = self._station
        return station.src_update_time if station else None
