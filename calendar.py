"""Calendar platform for RCE integration."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PSE_INFO_URL
from .coordinator import RCEDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calendar platform."""
    coordinator: RCEDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([RCECalendar(coordinator)])


class RCECalendar(CoordinatorEntity, CalendarEntity):
    """RCE Calendar entity using coordinator."""

    def __init__(self, coordinator: RCEDataUpdateCoordinator) -> None:
        """Initialize calendar."""
        super().__init__(coordinator)
        self._attr_unique_id = "rce_calendar"
        self._attr_name = "RCE Calendar"
        self._attr_has_entity_name = False

    @property
    def event(self) -> CalendarEvent | None:
        """Return next upcoming event."""
        if not self.coordinator.data:
            return None

        events = self._get_all_events()
        if not events:
            return None

        return events[0]

    def _get_all_events(self) -> list[CalendarEvent]:
        """Get all parsed events."""
        if not self.coordinator.data:
            return []

        all_events = []

        for day_key in ["today", "tomorrow"]:
            for event_data in self.coordinator.data.get(day_key, []):
                all_events.append(
                    CalendarEvent(
                        start=event_data["start"],
                        end=event_data["end"],
                        summary=f"RCE: {event_data['price']} PLN/MWh",
                        description=PSE_INFO_URL,
                    )
                )

        # Sort by start time
        return sorted(all_events, key=lambda e: e.start)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events in date range."""
        all_events = self._get_all_events()

        return [
            event
            for event in all_events
            if start_date <= event.start < end_date or start_date < event.end <= end_date
        ]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update."""
        self.async_write_ha_state()
