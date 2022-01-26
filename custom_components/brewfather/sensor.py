"""Platform for sensor integration."""
from __future__ import annotations
import logging
import sys
import aiohttp
import async_timeout
from datetime import timedelta
from config.custom_components.brewfather import BrewfatherCoordinator

from homeassistant.config_entries import ConfigEntry
from .const import *

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10
BKK_URI = "https://api.brewfather.app/v1/batches/MdygaYwzcjEGmDTwQXJ4Wfhjbm0O8s/"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platforms."""
    _LOGGER.debug("async_setup_entry")
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    sensors = []

    sensors.append(
        SpaceXSensor(
            coordinator,
            "Starman Speed",
            "spacex_starman_speed",
            "mdi:account-star",
            "spacexstarman",
        )
    )
    async_add_entities(sensors)


class SpaceXSensor(CoordinatorEntity):
    """Defines a SpaceX Binary sensor."""

    def __init__(
        self,
        coordinator: BrewfatherCoordinator,
        name: str,
        entity_id: str,
        icon: str,
        device_identifier: str,
    ):
        """Initialize Entities."""

        super().__init__(coordinator=coordinator)

        self._name = name
        self._unique_id = f"spacex_{entity_id}"
        self._state = None
        self._icon = icon
        self._kind = entity_id
        self._device_identifier = device_identifier
        self._unit_of_measure = None
        self.attrs = {}

        # if self._kind == "spacex_starman_speed":
        #     self._unit_of_measure = SPEED_KILOMETERS_PER_HOUR

        # elif self._kind == "spacex_starman_distance":
        #     self._unit_of_measure = LENGTH_KILOMETERS

    @property
    def unique_id(self):
        """Return the unique Home Assistant friendly identifier for this entity."""
        return self._unique_id

    @property
    def name(self):
        """Return the friendly name of this entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon for this entity."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for this entity."""
        return self._unit_of_measure

    # @property
    # def device_info(self):
    #     """Define the device based on device_identifier."""

    #     device_name = "SpaceX Launches"
    #     device_model = "Launch"

    #     if self._device_identifier != "spacexlaunch":
    #         device_name = "SpaceX Starman"
    #         device_model = "Starman"

    #     return {
    #         ATTR_IDENTIFIERS: {(DOMAIN, self._device_identifier)},
    #         ATTR_NAME: device_name,
    #         ATTR_MANUFACTURER: "SpaceX",
    #         ATTR_MODEL: device_model,
    #     }

    @property
    def state(self):
        """Return the state."""
        coordinator_data = self.coordinator.data
        # starman_data = coordinator_data["starman"]
        # launch_data = coordinator_data["next_launch"]
        # latest_launch_data = coordinator_data["latest_launch"]

        self._state = "donky"

        return self._state

    async def async_update(self):
        """Update SpaceX Binary Sensor Entity."""
        await self.coordinator.async_request_refresh()
        _LOGGER.debug("Updating state of the sensors.")

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


# # https://developers.home-assistant.io/docs/integration_fetching_data/#separate-polling-for-each-individual-entity
# async def async_setup_platform(
#     hass: HomeAssistant,
#     config: ConfigType,
#     async_add_entities: AddEntitiesCallback,
#     discovery_info: DiscoveryInfoType | None = None,
# ) -> None:
#     """Set up the sensor platform."""

#     # host = config[CONF_HOST]

#     async def async_update_data():
#         _LOGGER.info("update data")
#         user = "v50ynXGwmlYgoysyyGqpRoKFJbS2"
#         password = "SAc0UHYsAn1BTIsDUyzMXH54UsjTEi8UMqwvlUEOCCP1HQMP7x6Ve0WIGEHliNFr"

#         async with aiohttp.ClientSession() as session:
#             async with session.get(
#                 BKK_URI, auth=aiohttp.BasicAuth(user, password)
#             ) as response:

#                 if response.status == 200:
#                     return await response.json()
#                 else:
#                     raise UpdateFailed(
#                         f"Error communicating with API: {response.status}"
#                     )

#         # websession = async_get_clientsession(self.hass)

#         # with async_timeout.timeout(REQUEST_TIMEOUT):
#         #     response = await websession.get(
#         #         BKK_URI, auth=aiohttp.BasicAuth(user, password)
#         #     )
#         # if response.status == 200:
#         #     return await response.json()
#         # else:
#         #     raise UpdateFailed(f"Error communicating with API: {response.status}")

#         # json_response = await resp.json()

#         # async with aiohttp.ClientSession() as session:
#         #     async with session.get(BKK_URI) as response:

#         #         if response.status == 200:
#         #             return await response.json()
#         #         else:
#         #             raise UpdateFailed(
#         #                 f"Error communicating with API: {response.status}"
#         #             )

#     # async def async_update_data():
#     #     """Fetch data from API endpoint.

#     #     This is the place to pre-process the data to lookup tables
#     #     so entities can quickly look up their data.
#     #     """
#     #     _LOGGER.info("brewie async_update_data .")

#     #     # try:
#     #     #     # Note: asyncio.TimeoutError and aiohttp.ClientError are already
#     #     #     # handled by the data update coordinator.
#     #     #     async with async_timeout.timeout(10):
#     #     #         return await api.fetch_data()
#     #     # except ApiAuthError as err:
#     #     #     # Raising ConfigEntryAuthFailed will cancel future updates
#     #     #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
#     #     #     raise ConfigEntryAuthFailed from err
#     #     # except ApiError as err:
#     #     #     raise UpdateFailed(f"Error communicating with API: {err}")

#     # https://github.com/robinostlund/homeassistant-volkswagencarnet/blob/master/custom_components/volkswagencarnet/__init__.py
#     coordinator = DataUpdateCoordinator(
#         hass,
#         _LOGGER,
#         # Name of the data. For logging purposes.
#         name="sensor",
#         update_method=async_update_data,
#         # Polling interval. Will only be polled if there are subscribers.
#         update_interval=timedelta(seconds=10),
#     )

#     #  await coordinator.async_config_entry_first_refresh()
#     await coordinator.async_refresh()

#     async_add_entities(
#         [
#             BrewfatherSensor(coordinator)
#         ]  # , idx) for idx, ent in enumerate(coordinator.data)
#     )
#     # add_entities([BrewfatherSensor(coordinator)])


# # run: hass -c ./config
# class BrewfatherSensor(CoordinatorEntity, SensorEntity):
#     """Representation of a Sensor."""

#     def __init__(self, coordinator):  # , idx):
#         """Pass coordinator to CoordinatorEntity."""
#         super().__init__(coordinator)
#         # self.idx = idx

#     _attr_name = "BrewfatherSensor Temperature"
#     _attr_native_unit_of_measurement = TEMP_CELSIUS
#     _attr_device_class = SensorDeviceClass.TEMPERATURE
#     _attr_state_class = SensorStateClass.MEASUREMENT

#     async def async_added_to_hass(self):
#         _LOGGER.info("Migrating dsadsa2 test brewfather .")

#     async def async_update(self) -> None:
#         """Fetch new state data for the sensor.
#         This is the only method that should fetch new data for Home Assistant.
#         """
#         _LOGGER.info("Migrating maarten test brewfather .")
#         # self._attr_native_value = 23
#         # try:
#         #     websession = async_get_clientsession(self.hass)
#         #     user = "v50ynXGwmlYgoysyyGqpRoKFJbS2"
#         #     password = (
#         #         "SAc0UHYsAn1BTIsDUyzMXH54UsjTEi8UMqwvlUEOCCP1HQMP7x6Ve0WIGEHliNFr"
#         #     )
#         #     with async_timeout.timeout(REQUEST_TIMEOUT):
#         #         resp = await websession.get(
#         #             BKK_URI, auth=aiohttp.BasicAuth(user, password)
#         #         )
#         #     if resp.status != 200:
#         #         _LOGGER.error(f"{resp.url} returned {resp.status}")
#         #         return

#         #     json_response = await resp.json()
#         #     _LOGGER.debug("async_update: %s", json_response)
#         #     # _LOGGER.debug("async_update: %s", resp.text().encode("utf-8"))
#         #     return json_response

#         # except Exception as e:
#         #     _LOGGER.error(
#         #         "[" + sys._getframe().f_code.co_name + "] Exception: " + str(e)
#         #     )
