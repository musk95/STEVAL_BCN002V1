"""Support for STEVAL BCN002V1 sensor."""
import logging

import btlewrap
from btlewrap.base import BluetoothInterface, BluetoothBackendException
import voluptuous as vol
from datetime import datetime, timedelta
from threading import Lock
from custom_components import BCN002V1

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_MEDIAN = "median"

DEFAULT_MEDIAN = 1
DEFAULT_NAME = "BCN-002"

DEVICE_CLASS_PROXIMITY = "proximity"

# Sensor types are defined like: Name, units
SENSOR_TYPES = {
    "pressure":[DEVICE_CLASS_PRESSURE, "Pressure","mBar"],
    "temperature": [DEVICE_CLASS_TEMPERATURE, "Temperature", "°C"],
    "humidity": [DEVICE_CLASS_HUMIDITY, "Humidity", "%"],
    "battery": [DEVICE_CLASS_BATTERY, "Battery", "%"],
    "proximity": [DEVICE_CLASS_PROXIMITY, "Proximity", "cm"],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MEDIAN, default=DEFAULT_MEDIAN): cv.positive_int,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the BCN002V1 sensor."""
    poller = BCN002V1.BlueNRGTilePoller
    median = config.get(CONF_MEDIAN)

    devs = []

    for parameter in config[CONF_MONITORED_CONDITIONS]:
        device = SENSOR_TYPES[parameter][0]
        name = SENSOR_TYPES[parameter][1]
        unit = SENSOR_TYPES[parameter][2]

        prefix = config.get(CONF_NAME)
        if prefix:
            name = f"{prefix} {name}"

        devs.append(
            BlueTileBtSensor(poller, parameter, device, name, unit, median)
        )
    
    add_entities(devs)

class BlueTileBtSensor(Entity):
    """Implementing the BCN002V1 sensor."""

    def __init__(self, poller, parameter, device, name, unit, median):
        """Initialize the sensor."""
        self.poller = poller
        self.parameter = parameter
        self._device = device
        self._unit = unit
        self._name = name
        self._state = None
        self.data = []
        # Median is used to filter out outliers. median of 3 will filter
        # single outliers, while  median of 5 will filter double outliers
        # Use median_count = 1 if no filtering is required.
        self.median_count = median

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Device class of this entity."""
        return self._device

    def update(self):
        """
        Update current conditions.

        This uses a rolling median over 3 values to filter out outliers.
        """
#        try:
#            _LOGGER.debug("Polling data for %s", self.name)
#            data = self.poller.parameter_value(self.parameter)
#        except OSError as ioerr:
#            _LOGGER.warning("Polling error %s", ioerr)
#            return
#        except BluetoothBackendException as bterror:
#            _LOGGER.warning("Polling error %s", bterror)
#            return
        _LOGGER.debug("Polling data for %s", self.name)
        data = self.poller.parameter_value(self.parameter)

        if data is not None:
            _LOGGER.debug("%s = %s", self.name, data)
            self.data.append(data)
        else:
            _LOGGER.warning(
                "Did not receive any data from BlueTile sensor %s", self.name
            )
            # Remove old data from median list or set sensor value to None
            # if no data is available anymore
            if self.data:
                self.data = self.data[1:]
            else:
                self._state = None
            return

        if len(self.data) > self.median_count:
            self.data = self.data[1:]

        if len(self.data) == self.median_count:
            median = sorted(self.data)[int((self.median_count - 1) / 2)]
            _LOGGER.debug("Median is: %s", median)
            self._state = median
        else:
            _LOGGER.debug("Not yet enough data for median calculation")
