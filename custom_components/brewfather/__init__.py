"""The Candy integration."""
from __future__ import annotations

# https://github.com/robinostlund/homeassistant-volkswagencarnet/blob/master/custom_components/volkswagencarnet/__init__.py
import logging
from datetime import timedelta
from typing import Union

# ontwikkelogmvign: https://developers.home-assistant.io/docs/development_environment/

# voorbeeld https://github.com/black-roland/homeassistant-microsoft-todo/tree/master/custom_components/microsoft_todo
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryNotReady

# from .client import CandyClient, WashingMachineStatus

from .const import *

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Setup our skeleton component."""
    # States are in the format DOMAIN.OBJECT_ID.
    _LOGGER.debug("username %s", config_entry.data[CONF_USERNAME])
    _LOGGER.debug("password %s", config_entry.data[CONF_PASSWORD])
    _LOGGER.debug("config_entry.entry_id %s", config_entry.entry_id)
    hass.states.async_set("brewfather.Hello_World", "Works!2")

    update_interval = timedelta(seconds=5)
    coordinator = BrewfatherCoordinator(hass, config_entry, update_interval)

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {COORDINATOR: coordinator}
    _LOGGER.debug("Done %s", hass.data[DOMAIN])

    for component in PLATFORMS:
        _LOGGER.info("Setting up platform: %s", component)
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    # Return boolean to indicate that initialization was successfully.
    return True


def update_callback(hass, coordinator):
    _LOGGER.debug("CALLBACK!")
    hass.async_create_task(coordinator.async_request_refresh())


class BrewfatherCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, entry, update_interval: timedelta):
        self.entry = entry
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("BrewfatherCoordinator._async_update_data!")
        # https://github.com/djtimca/HASpaceX/blob/master/custom_components/spacex/__init__.py
        return {"status": "ok"}
        # vehicle = await self.update()

    # if not vehicle:
    #     raise UpdateFailed(
    #         "Failed to update WeConnect. Need to accept EULA? Try logging in to the portal: https://www.portal.volkswagen-we.com/"
    #     )

    # if self.entry.options.get(CONF_REPORT_REQUEST, False):
    #     await self.report_request(vehicle)

    # # Backward compatibility
    # default_convert_conf = get_convert_conf(self.entry)

    # convert_conf = self.entry.options.get(
    #     CONF_CONVERT, self.entry.data.get(CONF_CONVERT, default_convert_conf)
    # )

    # dashboard = vehicle.dashboard(
    #     mutable=self.entry.data.get(CONF_MUTABLE),
    #     spin=self.entry.data.get(CONF_SPIN),
    #     miles=convert_conf == CONF_IMPERIAL_UNITS,
    #     scandinavian_miles=convert_conf == CONF_SCANDINAVIAN_MILES,
    # )

    # return dashboard.instruments

    async def update(self) -> bool:  # Union[bool, Vehicle]:
        """Update status from Volkswagen WeConnect"""
        _LOGGER.debug("BrewfatherCoordinator.update!")

        return True
        # # update vehicles
        # if not await self.connection.update():
        #     _LOGGER.warning("Could not query update from volkswagen WeConnect")
        #     return False

        # _LOGGER.debug("Updating data from volkswagen WeConnect")
        # for vehicle in self.connection.vehicles:
        #     if vehicle.vin.upper() == self.vin:
        #         return vehicle

        # return False
