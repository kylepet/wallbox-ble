from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import WallboxBLEApiClient, WallboxBLEApiConst
from .const import DOMAIN, LOGGER


class WallboxBLEDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.hass = hass
        self.locked = False
        self.charge_current = 0
        self.max_charge_current = 0
        self.status = ""
        self.status_code = 0
        self.available = False
        # Power meter data from GET_POWER_BOOST_STATUS
        self.grid_power_l1 = 0
        self.grid_power_l2 = 0
        self.grid_power_l3 = 0
        self.grid_voltage_l1 = 0
        self.grid_voltage_l2 = 0
        self.grid_voltage_l3 = 0
        self.grid_current_l1 = 0.0
        self.grid_current_l2 = 0.0
        self.grid_current_l3 = 0.0
        self.grid_energy = 0.0

    @classmethod
    async def create(cls, hass, address):
        self = WallboxBLEDataUpdateCoordinator(hass)
        self.wb = await WallboxBLEApiClient.create(hass, address)
        return self

    async def async_refresh_later(self, delay):
        async def wrap(*_):
            await self.async_refresh()

        async_call_later(self.hass, delay, wrap)

    async def _async_update_data(self):
        if not self.wb.ready:
            return {}

        if self.max_charge_current == 0:
            ok, data = await self.wb.async_get_max_charge_current()
            if ok:
                self.max_charge_current = data
                LOGGER.debug(f"SET {self.max_charge_current=}")

        ok, data = await self.wb.async_get_data()
        if ok:
            LOGGER.debug("Update done")
            self.status_code = data.get("st", 0)
            self.locked = self.status_code == 6
            self.charge_current = data.get("cur", 6)
            self.status = WallboxBLEApiConst.STATUS_CODES[self.status_code]
            self.available = True
        else:
            self.available = False
            return {}

        ok_pbs, pbs = await self.wb.async_get_power_boost_status()
        if ok_pbs and pbs:
            LOGGER.debug(f"Power boost status: {pbs}")
            self.grid_power_l1 = pbs.get("p1", 0)
            self.grid_power_l2 = pbs.get("p2", 0)
            self.grid_power_l3 = pbs.get("p3", 0)
            self.grid_voltage_l1 = pbs.get("v1", 0)
            self.grid_voltage_l2 = pbs.get("v2", 0)
            self.grid_voltage_l3 = pbs.get("v3", 0)
            self.grid_current_l1 = pbs.get("c1", 0) / 10.0
            self.grid_current_l2 = pbs.get("c2", 0) / 10.0
            self.grid_current_l3 = pbs.get("c3", 0) / 10.0
            self.grid_energy = pbs.get("e", 0) / 1000.0

        return data

    async def async_set_parameter(self, parameter, value):
        ok, _ = await self.wb.request(parameter, value)
        return ok
