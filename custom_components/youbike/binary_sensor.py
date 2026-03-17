"""YouBike binary sensor — station service status."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up YouBike binary sensors for a config entry."""
    coordinator: YouBikeCoordinator = entry.runtime_data
    async_add_entities(
        YouBikeServiceStatusSensor(coordinator, uid)
        for uid in coordinator._station_ids
    )


class YouBikeServiceStatusSensor(CoordinatorEntity[YouBikeCoordinator], BinarySensorEntity):
    """Binary sensor: True = station in service, False = suspended."""

    _attr_has_entity_name = True
    _attr_translation_key = "service_status"

    def __init__(self, coordinator: YouBikeCoordinator, uid: str) -> None:
        super().__init__(coordinator)
        self._uid = uid
        self.entity_id = f"binary_sensor.{uid.lower()}_service_status"

    @property
    def unique_id(self) -> str:
        return f"youbike_{self._uid.lower()}_service_status"

    @property
    def _station(self) -> StationData | None:
        if self.coordinator.data:
            return self.coordinator.data.get(self._uid)
        return None

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self._station is not None

    @property
    def is_on(self) -> bool | None:
        station = self._station
        return station.service_status == 1 if station else None

    @property
    def device_info(self) -> DeviceInfo:
        station = self._station
        return DeviceInfo(
            identifiers={(DOMAIN, self._uid)},
            name=station.name if station else self._uid,
            model=self._uid,
            manufacturer="YouBike",
        )
