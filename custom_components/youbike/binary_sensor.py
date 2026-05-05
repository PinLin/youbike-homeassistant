"""YouBike binary sensor — station service status."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up YouBike binary sensors for a config entry."""
    coordinator: YouBikeCoordinator = entry.runtime_data
    async_add_entities(
        YouBikeServiceStatusSensor(coordinator, uid)
        for uid in coordinator.station_ids
    )


class YouBikeServiceStatusSensor(YouBikeEntityBase, BinarySensorEntity):
    """Binary sensor: True = station in service, False = suspended."""

    _sensor_type = "service_status"
    _attr_translation_key = "service_status"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _state_attrs = ("is_on", "available")

    def __init__(self, coordinator: YouBikeCoordinator, uid: str) -> None:
        super().__init__(coordinator, uid)
        self.entity_id = f"binary_sensor.youbike_{uid.lower()}_{self._sensor_type}"

    @property
    def available(self) -> bool:
        # Stay available even when suspended — service_status IS the value.
        return self.coordinator.last_update_success and self._station is not None

    @property
    def is_on(self) -> bool | None:
        station = self._station
        return station.service_status == 1 if station else None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {"station_id": self._uid}
