"""Platform for sensor integration."""
from __future__ import annotations
import csv
from zoneinfo import ZoneInfo

import requests
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from datetime import datetime, timedelta, timezone

SCAN_INTERVAL = timedelta(seconds=20)
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Konfiguracja za pomcą przepływu konfiguracji."""

    """This one is in use"""
    async_add_entities([RCECalendar()])


class RCECalendar(CalendarEntity):
    """Representation of a Sensor."""

    def __init__(self) -> None:
        _LOGGER.info("RCE calendar")
        super().__init__()
        self.ev = []
        self.cr_time = None
        self.last_update = None
        self.cloud_response = None
        self.last_network_pull = datetime(
            year=2000, month=1, day=1, tzinfo=timezone.utc
        )
        self._attr_unique_id = "rce_calendar"
        self._attr_name = "RCE calendar"


    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        ret = []
        ev: CalendarEvent
        for ev in self.ev:
            if (
                start_date < ev.start
                and ev.start < end_date
                or start_date < ev.start
                and ev.end < end_date
                or start_date < ev.end
                and ev.end < end_date
            ):
                ret.append(ev)
        return ret

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""

        ev: CalendarEvent
        for ev in self.ev:
            if datetime.now(ZoneInfo(self.hass.config.time_zone)) < ev.end:
                return ev

    def fetch_cloud_data(self):
        """fetch today data"""
        now = datetime.now(ZoneInfo(self.hass.config.time_zone))
        url = f"https://api.raporty.pse.pl/api/rce-pln?$filter=doba eq '{now.strftime('%Y-%m-%d')}'"
        try:
            self.cloud_response = requests.get(url, timeout=10)
            self.cloud_response.encoding = 'ISO-8859-2'

        except ReadTimeout:
            self.cloud_response = ""

    def fetch_cloud_data_1(self):
        """fetch tomorrow data"""
        now = datetime.now(ZoneInfo(self.hass.config.time_zone)) + timedelta(days=1)
        url = f"https://api.raporty.pse.pl/api/rce-pln?$filter=doba eq '{now.strftime('%Y-%m-%d')}'"
        try:
            self.cloud_response = requests.get(url, timeout=10)
            self.cloud_response.encoding = 'ISO-8859-2'
        except requests.exceptions.ReadTimeout:
            self.cloud_response = ""

    def csv_to_events(self, csv_reader: csv, day: datetime):
        """Transform csv to events"""

        for row in csv_reader:
            if not row[1].isnumeric():
                continue
            self.ev.append(
                CalendarEvent(
                    day.replace(hour=int(row[1])-1),
                    day.replace(hour=int(row[1])-1,minute=59,second=59),
                    row[2],
                    description="https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z-funkcjonowania-rb/podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena-energii-elektrycznej-rce",
                )
            )
            event_start = int(row[1])


    def json_to_events(self, json, day: datetime):
        curr_price = None
        start_time = None
        end_time = None
        for i in json['value']:
            times =  i['udtczas_oreb'].split("-")
            ts = datetime.strptime(times[0].strip(),"%H:%M")
            ts = day.replace(hour=ts.hour, minute=ts.minute, second=0)
            if times[1].strip()=="24:00":
                te = day.replace(hour=0, minute=0, second=0) + timedelta(days=1)
            else:
                te = datetime.strptime(times[1].strip(),"%H:%M")
                te = day.replace(hour=te.hour, minute=te.minute, second=0)
            if(i['rce_pln']!=curr_price):
                if(curr_price):
                    #if ts==end_time:
                    #    end_time = end_time - timedelta(seconds=1)
                    self.ev.append(
                        CalendarEvent( start_time, end_time,curr_price,
                            description="https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z-funkcjonowania-rb/podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena-energii-elektrycznej-rce",
                        )
                    )
                curr_price = i['rce_pln']
                start_time = ts
            end_time = te
        if end_time is not None:
            self.ev.append(
                CalendarEvent( start_time, end_time,curr_price, 
                            description="https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z-funkcjonowania-rb/podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena-energii-elektrycznej-rce",
                        )
            )


    async def async_update(self):
        """Retrieve latest state."""
        now = datetime.now(ZoneInfo(self.hass.config.time_zone))
        if now < self.last_network_pull + timedelta(minutes=30):
            return
        self.last_network_pull = now
        self.cloud_response = None
        await self.hass.async_add_executor_job(self.fetch_cloud_data)

        if self.cloud_response is None or self.cloud_response.status_code != 200:
            return False
        self.ev.clear()

        now = now.replace(minute=0).replace(second=0)
        self.json_to_events(self.cloud_response.json(), now)
        #CalendarEvent( now, now, now, description=self.cloud_response)

        self.cloud_response = None
        await self.hass.async_add_executor_job(self.fetch_cloud_data_1)

        if self.cloud_response is None or self.cloud_response.status_code != 200:
            return False

        now = now.replace(minute=0).replace(second=0) + timedelta(days=1)
        self.json_to_events(self.cloud_response.json(), now)
        #CalendarEvent( now, now, now, description=self.cloud_response)

