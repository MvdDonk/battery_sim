"""The Candy integration."""
from __future__ import annotations
import datetime

# https://github.com/robinostlund/homeassistant-volkswagencarnet/blob/master/custom_components/volkswagencarnet/__init__.py
import logging
from datetime import datetime, timezone, timedelta
from typing import TypedDict, Optional

from dataclasses import dataclass
from typing import Any, List, TypeVar, Type, cast, Callable

import aiohttp
from black import json


# from models.batches_item import BatchesItemElement
from .models.batches_item import BatchesItemElement, batches_item_from_dict
from .models.batch_item import BatchItem, batch_item_from_dict, FermentationStep

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
UPDATE_INTERVAL = 3600
MS_IN_DAY = 86400000
BATCHES_URI = "https://api.brewfather.app/v1/batches/"
BATCH_URI = "https://api.brewfather.app/v1/batches/{}"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Setup our skeleton component."""
    # States are in the format DOMAIN.OBJECT_ID.
    # hass.states.async_set("brewfather.Hello_World", "Works!2")

    update_interval = timedelta(seconds=UPDATE_INTERVAL)
    coordinator = BrewfatherCoordinator(hass, config_entry, update_interval)

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {COORDINATOR: coordinator}

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


def sort_by_actual_time(entity: FermentationStep):
    return entity.actual_time


class BrewfatherCoordinatorData:
    fermenting_name: str
    fermenting_current_temperature: Optional[float]
    fermenting_next_date: Optional[datetime.datetime]
    fermenting_next_temperature: Optional[float]

    def __init__(self):
        # set defaults to None
        self.fermenting_current_temperature = None
        self.fermenting_next_date = None
        self.fermenting_next_temperature = None


class BrewfatherCoordinator(DataUpdateCoordinator[BrewfatherCoordinatorData]):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, entry, update_interval: timedelta):
        self.entry = entry
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> BrewfatherCoordinatorData:
        """Update data via library."""
        _LOGGER.debug("BrewfatherCoordinator._async_update_data!")
        # https://github.com/djtimca/HASpaceX/blob/master/custom_components/spacex/__init__.py
        batches = await self.update()

        data = BrewfatherCoordinatorData()

        currentBatch = batches[0]
        data.fermenting_name = currentBatch.recipe.name

        currentTimeInMs = datetime.utcnow().timestamp() * 1000

        # cur: 18   1642806000000,  next: 20    1643151600000
        # currentTimeInMs = 1642944926000

        # cur: 20   1643151600000,  next: 22    1643324400000
        # currentTimeInMs = 1643244926000

        # cur: 2    1643497200000,  next: NONE
        # currentTimeInMs = 1643546716000

        # cur: NONE              ,  next: NONE
        # currentTimeInMs = 1643899443000

        # sort steps from first to latest
        currentBatch.recipe.fermentation.steps.sort(key=sort_by_actual_time)

        currentStep: FermentationStep | None = None
        nextStep: FermentationStep | None = None

        # _LOGGER.debug("current time %s", currentTimeInMs)

        for index, obj in enumerate(currentBatch.recipe.fermentation.steps):
            # _LOGGER.debug("----")
            # _LOGGER.debug("actual_time %s", obj.actual_time)
            # _LOGGER.debug("end time %s", obj.actual_time + obj.step_time * MS_IN_DAY)
            # _LOGGER.debug("step_temp %s", obj.step_time)
            next_ = None
            # check if start date is in past, also check if end date (start date + step_time * MS_IN_DAY) is in future
            if (
                obj.actual_time < currentTimeInMs
                and obj.actual_time + obj.step_time * MS_IN_DAY > currentTimeInMs
            ):
                # _LOGGER.debug("set current %s", obj.display_step_temp)
                currentStep = obj
            # check if start date is in future
            elif obj.actual_time > currentTimeInMs:
                # _LOGGER.debug("set next %s", obj.display_step_temp)
                nextStep = obj
                break

        if currentStep is not None:
            data.fermenting_current_temperature = currentStep.display_step_temp
            _LOGGER.debug("Current step: %s", currentStep.display_step_temp)
        else:
            _LOGGER.debug("No current step")

        if nextStep is not None:
            data.fermenting_next_temperature = nextStep.display_step_temp
            data.fermenting_next_date = datetime.fromtimestamp(
                nextStep.actual_time / 1000, timezone.utc
            )
            _LOGGER.debug("Next step: %s", nextStep.display_step_temp)
        else:
            _LOGGER.debug("No next step")

        return data

    async def update(self) -> List[BatchItem]:
        """Update status from Volkswagen WeConnect"""
        _LOGGER.debug("BrewfatherCoordinator.update!")
        dry_run = True

        activeBatches = await self.get_active_batches(dry_run)

        activeBatchesData = []
        for batch in activeBatches:
            batch = await self.get_batch(batch.id, dry_run)
            activeBatchesData.append(batch)

        return activeBatchesData

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
