"""Data coordinator for RCE integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    PSE_API_URL_TODAY,
    PSE_API_URL_TOMORROW,
    SCAN_INTERVAL,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class RCEDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching RCE data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.hass = hass
        self.last_successful_update: datetime | None = None

    def _get_now(self) -> datetime:
        """Get current time in configured timezone."""
        tz = ZoneInfo(self.hass.config.time_zone)
        return datetime.now(tz)

    def _fetch_api(self, url: str, date: datetime) -> dict | None:
        """Fetch data from PSE API with error handling."""
        try:
            formatted_date = date.strftime("%Y-%m-%d")
            query_url = f"{url}?$filter=business_date+eq+'{formatted_date}'"

            _LOGGER.debug("Fetching RCE data from %s for %s", url, formatted_date)

            response = requests.get(query_url, timeout=REQUEST_TIMEOUT)
            response.encoding = "ISO-8859-2"
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout as err:
            _LOGGER.warning("Timeout fetching RCE data for %s: %s", date.date(), err)
        except requests.exceptions.HTTPError as err:
            _LOGGER.warning("HTTP error fetching RCE data: %s", err)
        except requests.exceptions.RequestException as err:
            _LOGGER.warning("Request error fetching RCE data: %s", err)
        except ValueError as err:
            _LOGGER.error("Invalid JSON response from RCE API: %s", err)

        return None

    def _parse_events(self, data: dict | None, day: datetime) -> list[dict]:
        """Parse API response into event list."""
        events = []

        if not data or "value" not in data:
            return events

        try:
            current_price = None
            start_time = None

            for item in data["value"]:
                if "period" not in item or "rce_pln" not in item:
                    continue

                times = item["period"].split("-")
                if len(times) != 2:
                    continue

                try:
                    start = datetime.strptime(times[0].strip(), "%H:%M")
                    start = day.replace(hour=start.hour, minute=start.minute, second=0)

                    if times[1].strip() == "24:00":
                        end = day.replace(hour=0, minute=0, second=0) + timedelta(
                            days=1
                        )
                    else:
                        end = datetime.strptime(times[1].strip(), "%H:%M")
                        end = day.replace(hour=end.hour, minute=end.minute, second=0)

                    price = item["rce_pln"]

                    # Create event when price changes
                    if price != current_price:
                        if current_price is not None and start_time is not None:
                            events.append(
                                {
                                    "start": start_time,
                                    "end": start,
                                    "price": current_price,
                                }
                            )
                        current_price = price
                        start_time = start

                except ValueError as err:
                    _LOGGER.debug(
                        "Error parsing period %s: %s", item.get("period"), err
                    )
                    continue

            # Add final event
            if current_price is not None and start_time is not None:
                end_of_day = day.replace(hour=23, minute=59, second=59) + timedelta(
                    seconds=1
                )
                events.append(
                    {
                        "start": start_time,
                        "end": end_of_day,
                        "price": current_price,
                    }
                )

        except (KeyError, TypeError) as err:
            _LOGGER.error("Error processing RCE data: %s", err)

        return events

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from PSE API."""
        try:
            now = self._get_now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)

            # Fetch both days
            today_data = await self.hass.async_add_executor_job(
                self._fetch_api, PSE_API_URL_TODAY, today
            )
            tomorrow_data = await self.hass.async_add_executor_job(
                self._fetch_api, PSE_API_URL_TOMORROW, tomorrow
            )

            # Parse events
            today_events = self._parse_events(today_data, today)
            tomorrow_events = self._parse_events(tomorrow_data, tomorrow)

            if not today_events:
                raise UpdateFailed("No data received from PSE API")

            self.last_successful_update = now

            return {
                "today": today_events,
                "tomorrow": tomorrow_events,
                "timestamp": now,
            }

        except Exception as err:
            _LOGGER.error("Error updating RCE data: %s", err)
            raise UpdateFailed(f"Error fetching RCE data: {err}") from err
