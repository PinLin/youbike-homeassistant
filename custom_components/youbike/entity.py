"""Shared entity base for YouBike sensors and binary sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.core import callback
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

    # Subclasses list the entity property names that, when changed, require
    # broadcasting a new state to HA. Each coordinator refresh fans out to
    # every entity's _handle_coordinator_update; this guard suppresses
    # async_write_ha_state when the snapshot of those properties is
    # unchanged. An empty tuple keeps the default CoordinatorEntity
    # behaviour (broadcast on every refresh).
    _state_attrs: tuple[str, ...] = ()

    def __init__(self, coordinator: YouBikeCoordinator, uid: str) -> None:
        super().__init__(coordinator)
        self._uid = uid
        self._attr_unique_id = f"youbike_{uid.lower()}_{self._sensor_type}"
        self._last_broadcast_state: tuple[Any, ...] | None = None

    async def async_added_to_hass(self) -> None:
        """Seed the last-broadcast snapshot so the first real update is honest."""
        await super().async_added_to_hass()
        self._refresh_last_broadcast()

    def _refresh_last_broadcast(self) -> bool:
        """Recompute the snapshot. Return True if it differs from the prior one."""
        if not self._state_attrs:
            return True
        snapshot = tuple(getattr(self, attr, None) for attr in self._state_attrs)
        if snapshot != self._last_broadcast_state:
            self._last_broadcast_state = snapshot
            return True
        return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Only broadcast when the entity's tracked state actually changed."""
        if self._refresh_last_broadcast():
            self.async_write_ha_state()

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
