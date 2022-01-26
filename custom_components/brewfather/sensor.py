"""Platform for sensor integration."""
from __future__ import annotations
import enum
import logging
import sys
import aiohttp
import async_timeout
from datetime import timedelta
from .models.batch_item import BatchItem
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
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType
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
        BrewfatherSensor(
            coordinator,
            "Brew name",
            SensorKinds.fermenting_name,
            "mdi:glass-mug",
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            "Current fermenting temperature",
            SensorKinds.fermenting_current_temperature,
            "mdi:thermometer",
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            "Upcoming fermenting temperature",
            SensorKinds.fermenting_next_temperature,
            "mdi:thermometer-chevron-up",
        )
    )

    sensors.append(
        BrewfatherSensor(
            coordinator,
            "Upcoming fermenting temperature change",
            SensorKinds.fermenting_next_date,
            "mdi:clock",
        )
    )
    async_add_entities(sensors)


class BrewfatherSensor(CoordinatorEntity):
    """Defines a sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        name: str,
        sensorKind: SensorKinds,
        icon: str,
    ):
        """Initialize Entities."""

        super().__init__(coordinator=coordinator)

        self._name = name
        self._unique_id = f"{DOMAIN}_{sensorKind}"
        self._state = None
        self._icon = icon
        self._kind = sensorKind
        self._unit_of_measure = None

        self.attrs = {}

        if "temperature" in str(self._kind):
            self._unit_of_measure = TEMP_CELSIUS
            self._attr_device_class = "temperature"
        elif "date" in str(self._kind):
            self._attr_device_class = "timestamp"

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
    def state(self) -> StateType:
        """Return the state."""
        # brewfatherCoordinator: BrewfatherCoordinator = self.coordinator
        brewfatherCoordinator = self.coordinator

        if self._kind == SensorKinds.fermenting_name:
            self._state = brewfatherCoordinator.data.fermenting_name
        elif self._kind == SensorKinds.fermenting_current_temperature:
            self._state = brewfatherCoordinator.data.fermenting_current_temperature
        elif self._kind == SensorKinds.fermenting_next_date:
            self._state = brewfatherCoordinator.data.fermenting_next_date
        elif self._kind == SensorKinds.fermenting_next_temperature:
            self._state = brewfatherCoordinator.data.fermenting_next_temperature

        return self._state

    async def async_update(self):
        """Update Sensor Entity."""
        await self.coordinator.async_request_refresh()
        _LOGGER.debug("Updating state of the sensors.")

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class SensorKinds(enum.Enum):
    fermenting_name = 1
    fermenting_current_temperature = 2
    fermenting_next_temperature = 3
    fermenting_next_date = 4
