"""The Candy integration."""
from __future__ import annotations

# https://github.com/robinostlund/homeassistant-volkswagencarnet/blob/master/custom_components/volkswagencarnet/__init__.py
import logging
from datetime import timedelta
from typing import TypedDict

from dataclasses import dataclass
from typing import Any, List, TypeVar, Type, cast, Callable

import aiohttp
from black import json


# from models.batches_item import BatchesItemElement
from .models.batches_item import BatchesItemElement, batches_item_from_dict
from .models.batch_item import BatchItem, batch_item_from_dict

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
from .testdata import TESTDATA_BATCH

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]
REQUEST_TIMEOUT = 10
UPDATE_INTERVAL = 120
BATCHES_URI = "https://api.brewfather.app/v1/batches/"
BATCH_URI = "https://api.brewfather.app/v1/batches/{}"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Setup our skeleton component."""
    # States are in the format DOMAIN.OBJECT_ID.
    _LOGGER.debug("username %s", config_entry.data[CONF_USERNAME])
    _LOGGER.debug("password %s", config_entry.data[CONF_PASSWORD])
    _LOGGER.debug("config_entry.entry_id %s", config_entry.entry_id)
    hass.states.async_set("brewfather.Hello_World", "Works!2")

    update_interval = timedelta(seconds=UPDATE_INTERVAL)
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
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("BrewfatherCoordinator._async_update_data! %s", self.username)
        # https://github.com/djtimca/HASpaceX/blob/master/custom_components/spacex/__init__.py
        vehicle = await self.update()
        return {"status": "ok"}

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
        _LOGGER.debug("BrewfatherCoordinator.update! %s", self.password)
        dry_run = True

        activeBatches = await self.get_active_batches(dry_run)

        batch = await self.get_batch(activeBatches[0].id, dry_run)

        return True

    async def get_active_batches(self, dry_run: bool) -> List[BatchesItemElement]:
        """Update status from Volkswagen WeConnect"""
        _LOGGER.debug("get_active_batches!")

        # 'Hello, {}'.format(name)
        if dry_run:
            testJson = """[
                {'_id': 'MdygaYwzcjEGmDTwQXJ4Wfhjbm0O8s', 'name': 'Batch', 'batchNo': 30, 'status': 'Fermenting', 'brewer': '', 'brewDate': 1642806000000, 'recipe': {'name': 'Ryerish Red Ale'} },
                {'_id': 'aIJH9A6NeUApZcrN93oXoZm4HcanrB', 'name': 'Batch', 'batchNo': 29, 'status': 'Completed', 'brewer': '', 'brewDate': 1638486000000, 'recipe': {'name': 'Even Sharks Need Water - Donky'} },
                {'_id': 'PqADx67L8peat5TbjXI4L6Lh56iyNz', 'name': 'Batch', 'batchNo': 28, 'status': 'Conditioning', 'brewer': '', 'brewDate': 1631867216513, 'recipe': {'name': 'MG - American Amber Ale - Short'} },
                {'_id': '2KDjsjUr3iGksIBk9vFgeet1ZBh9lw', 'name': 'Batch', 'batchNo': 27, 'status': 'Conditioning', 'brewer': 'Maarten', 'brewDate': 1630133999772, 'recipe': {'name': 'Donkel Weizen'} },
                {'_id': 'wKBJXsJmMES0VesusqKg2uZpbnuBpi', 'name': 'Batch', 'batchNo': 26, 'status': 'Completed', 'brewer': '', 'brewDate': 1621838995222, 'recipe': {'name': 'CAS NEIPA'} },
                {'_id': 'YjD1G1pi8mC5miGX6bqoynRVsx2BYZ', 'name': 'Batch', 'batchNo': 25, 'status': 'Archived', 'brewer': '', 'brewDate': 1615636120457, 'recipe': {'name': 'Saison Greeg en Donk'} },
                {'_id': 'yCtZiqTaQL07UldKx0CtVVa8fwq4ki', 'name': 'Batch', 'batchNo': 24, 'status': 'Archived', 'brewer': '', 'brewDate': 1611906119965, 'recipe': {'name': 'NEIPA Milkshake'} },
                {'_id': 'NRZfJRMl8zsQEelk4dzhexbMPlZz7a', 'name': 'Batch', 'batchNo': 23, 'status': 'Archived', 'brewer': '', 'brewDate': 1608455980274, 'recipe': {'name': 'Homebrew Challenge - Belgian IPA'} },
                {'_id': '5pcAXwZDsmxh25XSSffZ81UFpraJgP', 'name': 'Batch', 'batchNo': 22, 'status': 'Archived', 'brewer': '', 'brewDate': 1605250827018, 'recipe': {'name': 'Gingerbread christmas'} },
                {'_id': 'dh7ulzII0WICzBlFuYtpYGu2so57De', 'name': 'Batch', 'batchNo': 21, 'status': 'Archived', 'brewer': '', 'brewDate': 1603443822289, 'recipe': {'name': 'Restjes stout'} }]"""
            testJson = testJson.replace("'", '"')
            allBatches = batches_item_from_dict(json.loads(testJson))
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    BATCHES_URI, auth=aiohttp.BasicAuth(self.username, self.password)
                ) as response:

                    if response.status == 200:
                        allBatches = batches_item_from_dict(
                            json.loads(await response.json())
                        )
                    else:
                        raise UpdateFailed(
                            f"Error communicating with API: {response.status}"
                        )

        activeBatches = []
        for batch in allBatches:
            if batch.status == "Fermenting":
                activeBatches.append(batch)

        return activeBatches

    async def get_batch(self, batch_id: str, dry_run: bool) -> BatchItem:
        """Update status from Volkswagen WeConnect"""
        _LOGGER.debug("get_batch! %s", batch_id)

        if dry_run:
            batch = batch_item_from_dict(json.loads(TESTDATA_BATCH))
        else:
            async with aiohttp.ClientSession() as session:
                url = BATCH_URI.format(batch_id)
                async with session.get(
                    url, auth=aiohttp.BasicAuth(self.username, self.password)
                ) as response:

                    if response.status == 200:
                        batch = batch_item_from_dict(json.loads(await response.json()))
                    else:
                        raise UpdateFailed(
                            f"Error communicating with API: {response.status}"
                        )

        return batch


# class BatchesItem:
#      def __init__(self, label, x, y, width, height):
#         self.label = label
#         self.x = x
#         self.y = y
#         self.width = width
#         self.height = height

#     @staticmethod
#     def from_json(json_dct):
#       return Label(json_dct['label'],
#                    json_dct['x'], json_dct['y'],
#                    json_dct['width'], json_dct['height'])


# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = batches_item_from_dict(json.loads(json_string))

# from dataclasses import dataclass
# from typing import Any, List, TypeVar, Type, cast, Callable


T = TypeVar("T")


# def from_str(x: Any) -> str:
#     assert isinstance(x, str)
#     return x


# def from_int(x: Any) -> int:
#     assert isinstance(x, int) and not isinstance(x, bool)
#     return x


# def from_none(x: Any) -> Any:
#     assert x is None
#     return x


# def to_class(c: Type[T], x: Any) -> dict:
#     assert isinstance(x, c)
#     return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


# @dataclass
# class Recipe:
#     name: str

#     @staticmethod
#     def from_dict(obj: Any) -> "Recipe":
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         return Recipe(name)

#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         return result


# @dataclass
# class BatchesItemElement:
#     id: str
#     name: str
#     batch_no: int
#     status: str
#     brewer: None
#     brew_date: int
#     recipe: Recipe

#     @staticmethod
#     def from_dict(obj: Any) -> "BatchesItemElement":
#         assert isinstance(obj, dict)
#         id = from_str(obj.get("_id"))
#         name = from_str(obj.get("name"))
#         batch_no = from_int(obj.get("batchNo"))
#         status = from_str(obj.get("status"))
#         brewer = from_str(obj.get("brewer"))
#         brew_date = from_int(obj.get("brewDate"))
#         recipe = Recipe.from_dict(obj.get("recipe"))
#         return BatchesItemElement(id, name, batch_no, status, brewer, brew_date, recipe)

#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["_id"] = from_str(self.id)
#         result["name"] = from_str(self.name)
#         result["batchNo"] = from_int(self.batch_no)
#         result["status"] = from_str(self.status)
#         result["brewer"] = from_str(self.brewer)
#         result["brewDate"] = from_int(self.brew_date)
#         result["recipe"] = to_class(Recipe, self.recipe)
#         return result


# def batches_item_from_dict(s: Any) -> List[BatchesItemElement]:
#     return from_list(BatchesItemElement.from_dict, s)


# def batches_item_to_dict(x: List[BatchesItemElement]) -> Any:
#     return from_list(lambda x: to_class(BatchesItemElement, x), x)
