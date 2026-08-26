"""Sensor platform for RCE integration."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RCEDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator: RCEDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            RCECurrentPriceSensor(coordinator),
            RCEMinPriceSensor(coordinator),
            RCEMaxPriceSensor(coordinator),
        ]
    )


class RCECurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing current electricity price."""

    def __init__(self, coordinator: RCEDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "rce_current_price"
        self._attr_name = "RCE Current Price"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "PLN/MWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:flash"

    @property
    def native_value(self) -> float | None:
        """Return current price."""
        if not self.coordinator.data:
            return None

        now = self._get_now()

        # Check today's events first
        for event in self.coordinator.data.get("today", []):
            if event["start"] <= now < event["end"]:
                return event["price"]

        # Check tomorrow's events
        for event in self.coordinator.data.get("tomorrow", []):
            if event["start"] <= now < event["end"]:
                return event["price"]

        return None

    def _get_now(self) -> datetime:
        """Get current time in configured timezone."""
        tz = ZoneInfo(self.hass.config.time_zone)
        return datetime.now(tz)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update."""
        self.async_write_ha_state()


class RCEMinPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing minimum price for today."""

    def __init__(self, coordinator: RCEDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "rce_min_price"
        self._attr_name = "RCE Min Price Today"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "PLN/MWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:trending-down"

    @property
    def native_value(self) -> float | None:
        """Return minimum price for today."""
        if not self.coordinator.data:
            return None

        prices = [event["price"] for event in self.coordinator.data.get("today", [])]
        return min(prices) if prices else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update."""
        self.async_write_ha_state()


class RCEMaxPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing maximum price for today."""

    def __init__(self, coordinator: RCEDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "rce_max_price"
        self._attr_name = "RCE Max Price Today"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "PLN/MWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:trending-up"

    @property
    def native_value(self) -> float | None:
        """Return maximum price for today."""
        if not self.coordinator.data:
            return None

        prices = [event["price"] for event in self.coordinator.data.get("today", [])]
        return max(prices) if prices else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update."""
        self.async_write_ha_state()
