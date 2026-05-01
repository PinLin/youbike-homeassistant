"""Shared entity base for YouBike sensors and binary sensors."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StationData, YouBikeCoordinator


class YouBikeEntityBase(CoordinatorEntity[YouBikeCoordinator]):
    """Common state-access and device_info helpers.

    Each subclass defines `_sensor_type` (used for unique_id and entity_id)
    and inherits the appropriate platform mix-in (SensorEntity / BinarySensorEntity)
    alongside this base.
    """

    _attr_has_entity_name = True
    _sensor_type: str  # set per subclass

    def __init__(self, coordinator: YouBikeCoordinator, uid: str) -> None:
        super().__init__(coordinator)
        self._uid = uid
        self._attr_unique_id = f"youbike_{uid.lower()}_{self._sensor_type}"

    @property
    def _station(self) -> StationData | None:
        if self.coordinator.data:
            return self.coordinator.data.get(self._uid)
        return None

    @property
    def device_info(self) -> DeviceInfo:
        station = self._station
        station_name = (
            station.name
            if station is not None and station.name and station.name != self._uid
            else self.coordinator.station_name
        )
        return DeviceInfo(
            identifiers={(DOMAIN, self._uid)},
            name=station_name,
            model=self._uid,
            manufacturer="YouBike",
        )
