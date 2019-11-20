"""Support for STEVAL BCN002V1 led light."""
import logging
import voluptuous as vol
import btlewrap
import homeassistant.helpers.config_validation as cv
from .bluetile import BlueTilePoller
from homeassistant.components.light  import (
    PLATFORM_SCHEMA, Light)
#from .bluetile import BlueTilePoller
from custom_components import BCN002V1

_LOGGER = logging.getLogger(__name__)

CONF_ADAPTER = "adapter"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {

    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("BCN002V1 Light is setup")

    poller = BCN002V1.BlueNRGTilePoller

    devs = []
    devs.append(
        BlueTileBtLight(poller)
    )
    add_entities(devs)

class BlueTileBtLight(Light):
    def __init__(self, poller):
        self.poller = poller
        self._is_on = None
        _LOGGER.debug("BCN002V1 is init for the switch.")

    @property
    def name(self):
        """Name of the device."""
        return 'Red LED'

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self.poller.light_control(True)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self.poller.light_control(False)

    def update(self):
        _LOGGER.debug("Called update of BlueTileBtLight")
        __result = self.poller.light_status()
        if __result!=None:
            self._is_on = __result
