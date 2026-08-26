"""Calendar platform for RCE integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=30)

PSE_API_URL_TODAY = "https://api.raporty.pse.pl/api/rce-pln"
PSE_API_URL_TOMORROW = "https://apimpdv2-bmgdhhajexe8aade.a01.azurefd.net/api/rce-pln"
PSE_INFO_URL = (
    "https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z-funkcjonowania-rb/"
    "podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena-energii-elektrycznej-rce"
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RCE calendar platform."""
    async_add_entities([RCECalendar(hass)], update_before_add=True)


class RCECalendar(CalendarEntity):
    """Representation of the RCE Calendar entity."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the RCE calendar."""
        _LOGGER.info("Initializing RCE calendar")
        super().__init__()
        self.hass = hass
        self.events: list[CalendarEvent] = []
        self.cloud_response = None
        self.last_network_pull = datetime(
            year=2000, month=1, day=1, tzinfo=timezone.utc
        )
        self._attr_unique_id = "rce_calendar"
        self._attr_name = "RCE Calendar"

    def _get_now(self) -> datetime:
        """Get current time in the configured timezone."""
        tz = ZoneInfo(self.hass.config.time_zone)
        return datetime.now(tz)

    def _fetch_data(self, url: str, query_date: datetime) -> dict | None:
        """Fetch data from PSE API."""
        try:
            formatted_date = query_date.strftime("%Y-%m-%d")
            full_url = f"{url}?$filter=business_date+eq+'{formatted_date}'"
            response = requests.get(full_url, timeout=10)
            response.encoding = "ISO-8859-2"

            if response.status_code == 200:
                return response.json()
            _LOGGER.warning(
                "API returned status code %d for date %s",
                response.status_code,
                formatted_date,
            )
        except requests.exceptions.Timeout:
            _LOGGER.error("Timeout fetching data for date %s", query_date.strftime("%Y-%m-%d"))
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error fetching data: %s", err)
        except ValueError as err:
            _LOGGER.error("Invalid JSON response: %s", err)

        return None

    def _json_to_events(self, data: dict | None, day: datetime) -> None:
        """Transform JSON data to calendar events."""
        if not data or "value" not in data:
            _LOGGER.debug("No data to process for date %s", day.date())
            return

        try:
            curr_price = None
            start_time = None
            end_time = None

            for item in data["value"]:
                if "period" not in item or "rce_pln" not in item:
                    continue

                period_str = item["period"]
                times = period_str.split("-")

                if len(times) != 2:
                    _LOGGER.debug("Invalid period format: %s", period_str)
                    continue

                try:
                    ts = datetime.strptime(times[0].strip(), "%H:%M")
                    ts = day.replace(hour=ts.hour, minute=ts.minute, second=0)

                    if times[1].strip() == "24:00":
                        te = day.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                    else:
                        te = datetime.strptime(times[1].strip(), "%H:%M")
                        te = day.replace(hour=te.hour, minute=te.minute, second=0)

                    price = item["rce_pln"]

                    if price != curr_price:
                        if curr_price is not None and start_time is not None and end_time is not None:
                            event = CalendarEvent(
                                start=start_time,
                                end=end_time,
                                title=f"RCE: {curr_price} PLN/MWh",
                                description=PSE_INFO_URL,
                            )
                            self.events.append(event)

                        curr_price = price
                        start_time = ts

                    end_time = te

                except ValueError as err:
                    _LOGGER.debug("Error parsing period %s: %s", period_str, err)
                    continue

            # Add the last event
            if curr_price is not None and start_time is not None and end_time is not None:
                event = CalendarEvent(
                    start=start_time,
                    end=end_time,
                    title=f"RCE: {curr_price} PLN/MWh",
                    description=PSE_INFO_URL,
                )
                self.events.append(event)

        except (KeyError, TypeError) as err:
            _LOGGER.error("Error processing JSON data: %s", err)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        ret = []
        for event in self.events:
            if start_date <= event.start < end_date or start_date < event.end <= end_date:
                ret.append(event)
        return ret

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        now = self._get_now()
        for event in self.events:
            if now < event.end:
                return event
        return None

    async def async_update(self) -> None:
        """Retrieve latest state from the API."""
        now = self._get_now()

        # Check if we should update (throttle to 30 minutes)
        if now < self.last_network_pull + timedelta(minutes=30):
            return

        self.last_network_pull = now
        self.events.clear()

        # Fetch today's data
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_data = await self.hass.async_add_executor_job(
            self._fetch_data, PSE_API_URL_TODAY, today
        )
        self._json_to_events(today_data, today)

        # Fetch tomorrow's data
        tomorrow = today + timedelta(days=1)
        tomorrow_data = await self.hass.async_add_executor_job(
            self._fetch_data, PSE_API_URL_TOMORROW, tomorrow
        )
        self._json_to_events(tomorrow_data, tomorrow)

        _LOGGER.debug("RCE calendar updated with %d events", len(self.events))
