import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from .bluetile import BlueTilePoller

from homeassistant.const import (
    CONF_MAC,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bcn002v1"

CONF_ADAPTER = "adapter"
CONF_CACHE = "cache_value"
CONF_RETRIES = "retries"
CONF_TIMEOUT = "timeout"

DEFAULT_ADAPTER = "hci0"
DEFAULT_UPDATE_INTERVAL = 3
DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 10

BlueNRGTilePoller = None

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_MAC): cv.string, \
        vol.Optional(CONF_CACHE, default=DEFAULT_UPDATE_INTERVAL): cv.positive_int, \
        vol.Optional(CONF_ADAPTER, default=DEFAULT_ADAPTER): cv.string, \
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int, \
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,})}, extra=vol.ALLOW_EXTRA
)

def setup(hass, config):
    """Set up the bcn002v1 component."""
    global BlueNRGTilePoller

    BlueNRGTilePoller = BlueTilePoller(
        config[DOMAIN][CONF_MAC],
        cache_timeout=config[DOMAIN][CONF_CACHE],
        adapter=config[DOMAIN][CONF_ADAPTER],
    )
    BlueNRGTilePoller.ble_timeout = config[DOMAIN][CONF_TIMEOUT]
    BlueNRGTilePoller.retries = config[DOMAIN][CONF_RETRIES]
    return True