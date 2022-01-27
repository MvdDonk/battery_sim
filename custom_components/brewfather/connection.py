from __future__ import annotations
import logging
from typing import List
import aiohttp
import json
from homeassistant import exceptions
from .models.batches_item import BatchesItemElement, batches_item_from_dict
from .models.batch_item import BatchItem, batch_item_from_dict
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from .const import *
from .testdata import *

_LOGGER = logging.getLogger(__name__)


class Connection:
    def __init__(self, hass: HomeAssistant, username: str, apikey: str):
        # self.username = username
        # self.password = apikey
        self.auth = aiohttp.BasicAuth(username, apikey)

    async def test_connection(self) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.get(TEST_URI, auth=self.auth) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:  # invalid credentials
                    raise InvalidCredentials()
                elif response.status == 403:  # scope issue
                    raise InvalidScope()
                else:
                    raise CannotConnect()

        return False

    async def get_batches(self, dryRun: bool) -> List[BatchesItemElement]:
        _LOGGER.debug("get_batches %s!", BATCHES_URI)
        if dryRun:
            # testJson = """[
            #     {'_id': 'MdygaYwzcjEGmDTwQXJ4Wfhjbm0O8s', 'name': 'Batch', 'batchNo': 30, 'status': 'Fermenting', 'brewer': '', 'brewDate': 1642806000000, 'recipe': {'name': 'Ryerish Red Ale'} },
            #     {'_id': 'aIJH9A6NeUApZcrN93oXoZm4HcanrB', 'name': 'Batch', 'batchNo': 29, 'status': 'Completed', 'brewer': '', 'brewDate': 1638486000000, 'recipe': {'name': 'Even Sharks Need Water - Donky'} },
            #     {'_id': 'PqADx67L8peat5TbjXI4L6Lh56iyNz', 'name': 'Batch', 'batchNo': 28, 'status': 'Conditioning', 'brewer': '', 'brewDate': 1631867216513, 'recipe': {'name': 'MG - American Amber Ale - Short'} },
            #     {'_id': '2KDjsjUr3iGksIBk9vFgeet1ZBh9lw', 'name': 'Batch', 'batchNo': 27, 'status': 'Conditioning', 'brewer': 'Maarten', 'brewDate': 1630133999772, 'recipe': {'name': 'Donkel Weizen'} },
            #     {'_id': 'wKBJXsJmMES0VesusqKg2uZpbnuBpi', 'name': 'Batch', 'batchNo': 26, 'status': 'Completed', 'brewer': '', 'brewDate': 1621838995222, 'recipe': {'name': 'CAS NEIPA'} },
            #     {'_id': 'YjD1G1pi8mC5miGX6bqoynRVsx2BYZ', 'name': 'Batch', 'batchNo': 25, 'status': 'Archived', 'brewer': '', 'brewDate': 1615636120457, 'recipe': {'name': 'Saison Greeg en Donk'} },
            #     {'_id': 'yCtZiqTaQL07UldKx0CtVVa8fwq4ki', 'name': 'Batch', 'batchNo': 24, 'status': 'Archived', 'brewer': '', 'brewDate': 1611906119965, 'recipe': {'name': 'NEIPA Milkshake'} },
            #     {'_id': 'NRZfJRMl8zsQEelk4dzhexbMPlZz7a', 'name': 'Batch', 'batchNo': 23, 'status': 'Archived', 'brewer': '', 'brewDate': 1608455980274, 'recipe': {'name': 'Homebrew Challenge - Belgian IPA'} },
            #     {'_id': '5pcAXwZDsmxh25XSSffZ81UFpraJgP', 'name': 'Batch', 'batchNo': 22, 'status': 'Archived', 'brewer': '', 'brewDate': 1605250827018, 'recipe': {'name': 'Gingerbread christmas'} },
            #     {'_id': 'dh7ulzII0WICzBlFuYtpYGu2so57De', 'name': 'Batch', 'batchNo': 21, 'status': 'Archived', 'brewer': '', 'brewDate': 1603443822289, 'recipe': {'name': 'Restjes stout'} }]"""
            # testJson = testJson.replace("'", '"')
            return batches_item_from_dict(json.loads(TESTDATA_BATCHES))
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(BATCHES_URI, auth=self.auth) as response:
                    if response.status == 200:
                        jsonText = await response.text()
                        _LOGGER.debug(jsonText)
                        return batches_item_from_dict(json.loads(jsonText))
                    else:
                        raise UpdateFailed(
                            f"Error communicating with API: {response.status}"
                        )

    async def get_batch(self, batchId: str, dryRun: bool) -> BatchItem:
        _LOGGER.debug("get_batch %s!", BATCHES_URI)

        if dryRun:
            return batch_item_from_dict(json.loads(TESTDATA_BATCH))
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    BATCH_URI.format(batchId), auth=self.auth
                ) as response:
                    if response.status == 200:
                        jsonText = await response.text()
                        _LOGGER.debug(jsonText)
                        return batch_item_from_dict(json.loads(jsonText))
                    else:
                        raise UpdateFailed(
                            f"Error communicating with API: {response.status}"
                        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidCredentials(exceptions.HomeAssistantError):
    """Error to indicate we do not have the correct credentials, 401."""


class InvalidScope(exceptions.HomeAssistantError):
    """Error to indicate api key doesn't have the correct scope, 403."""
