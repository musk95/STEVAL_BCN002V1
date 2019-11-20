from datetime import datetime, timedelta
import logging
import re
import time
from bluepy.btle import BTLEException
from threading import Lock
#from btlewrap.base import BluetoothInterface, BluetoothBackendException
from bluepy.btle import Peripheral
import threading

_HANDLE_READ_NAME = 0x0006
_HANDLE_READ_PROXIMITY = 0x0016
_HANDLE_READ_LIGHT = 0x0019
_HANDLE_READ_BATTERY_LEVEL = 0x001C
_HANDLE_READ_ENVIRONMENTAL_SENSORS = 0x000d
_HANDLE_WRITE_CONFIG = 0x002c

ST_PRESSURE = "pressure"
ST_TEMPERATURE = "temperature"
ST_HUMIDITY = "humidity"
ST_BATTERY = "battery"
ST_PROXIMITY = "proximity"

_LOGGER = logging.getLogger(__name__)

class BlueTilePoller(object):
    _DATA_MODE_LISTEN = bytes([0x01, 0x00])
    _DATA_MODE_LISTEN_CANCEL = bytes([0x00, 0x00])

    def __init__(self, mac, cache_timeout=600, retries=3, adapter='hci0'):
        """
        Initialize a BlueTile Poller for the given MAC address.
        """
        _LOGGER.debug("Create BlueTilePoller %s [%s]", mac, adapter)
        self._mac = mac
        self._address_type = "random"
        match_result = re.search(r'hci([\d]+)', adapter)
        if match_result is None:
            _LOGGER.debug(
                "Invalid pattern %s for BLuetooth adpater. \
                Expetected something like hci0", adapter)
        self._iface = int(match_result.group(1))
        self._cache = None
        self._cache_timeout = timedelta(seconds=cache_timeout)
        self._last_read = None
        self._fw_last_read = None
        self._max_retries = retries
        self.ble_timeout = 10
        self.lock = threading.Lock()
        self.battery = None
        self._data = dict()
        self._data[ST_BATTERY] = None
        self._data[ST_PRESSURE] = None
        self._data[ST_TEMPERATURE] = None
        self._data[ST_HUMIDITY] = None
        self._data[ST_PROXIMITY] = None

    def get_sensor_data_notify(self, handle, parameter):
        self._data[parameter] = None
        _LOGGER.debug("Waiting for notification of %s.", parameter)
        with self.lock:
            try:
                self._device = Peripheral()
                self._device.connect(self._mac, addrType=self._address_type, iface=self._iface)
            except BTLEException as ex:
                _LOGGER.warning("%s", ex)
                return

            try:
                self._device.writeCharacteristic(handle, self._DATA_MODE_LISTEN, True)
                self._device.withDelegate(self)
                self._device.waitForNotifications(self.ble_timeout)
                self._device.writeCharacteristic(handle, self._DATA_MODE_LISTEN_CANCEL, True)
            except BTLEException:
                _LOGGER.warning("Unable to read the data via bluetooth!!")

            self._device.disconnect()

    def parameter_value(self, parameter, read_cached=True):
        # Special handling for battery attribute
        if parameter == ST_BATTERY:
            self.get_sensor_data_notify(_HANDLE_READ_BATTERY_LEVEL + 2, parameter)
            return self._data[ST_BATTERY]
        if parameter == ST_PROXIMITY:
            self.get_sensor_data_notify(_HANDLE_READ_PROXIMITY + 2, parameter)
            return self._data[ST_PROXIMITY]

        if self._data[parameter]==None:
            self.get_sensor_data_notify(_HANDLE_READ_ENVIRONMENTAL_SENSORS + 2, parameter)

        __return = self._data[parameter]
        self._data[parameter] = None
        return __return

    def handleNotification(self, handle, raw_data):
        _LOGGER.debug("handleNotification 0x%x", handle)
        if handle==(_HANDLE_READ_BATTERY_LEVEL + 1):
            self._data[ST_BATTERY] = (raw_data[2]+(raw_data[3]<<8))/10
        if handle==(_HANDLE_READ_PROXIMITY + 1):
            self._data[ST_PROXIMITY] = (raw_data[2]+((raw_data[3] & 0x7f)<<8))/10
        if handle==(_HANDLE_READ_ENVIRONMENTAL_SENSORS + 1):
            self._data[ST_PRESSURE] = float((raw_data[2]+(raw_data[3]<<8)+(raw_data[4]<<16)+(raw_data[5]<<24))/100)
            self._data[ST_HUMIDITY] = float((raw_data[6]+(raw_data[7]<<8))/10)
            self._data[ST_TEMPERATURE] = float((raw_data[8]+(raw_data[9]<<8))/10)

############################################################################################
# Switch Function
############################################################################################
    def light_status(self):
        _result = None
        with self.lock:
            try:
                self._device = Peripheral()
                self._device.connect(self._mac, addrType=self._address_type, iface=self._iface)
            except BTLEException as ex:
                _LOGGER.warning("%s", ex)
                return _result

            try:
                status = self._device.readCharacteristic(_HANDLE_READ_LIGHT+1);
                _LOGGER.debug("Light status update %02x", status[2])
                _result = True if status[2]==1 else False
            except BTLEException:
                _LOGGER.warning("Unable to get the status")
        
            self._device.disconnect()

        return _result

    def light_control(self, onoff):
        connected = False
        retrycount = 0
        with self.lock:
            self._device = Peripheral()
            while not connected and retrycount < self._max_retries:
                try:
                    self._device.connect(self._mac, addrType=self._address_type, iface=self._iface)
                    connected = True
                except BTLEException as ex:
                    _LOGGER.debug("%s", ex)
                    time.sleep(1)
                    retrycount += 1
            if not connected:
                _LOGGER.warning("Unable to connect to the device %s, retrying: %d", self._mac, retrycount)
                return

            try:
                self._device.writeCharacteristic(_HANDLE_READ_LIGHT + 2, b'\x01', False)
                self._device.writeCharacteristic(_HANDLE_WRITE_CONFIG + 1, \
                    b'\x20\x00\x00\x00\x01\x00' \
                    if onoff else b'\x20\x00\x00\x00\x00\x00', \
                    False)

                _LOGGER.debug("Sent config data to control LED!!")
                self._device.writeCharacteristic(_HANDLE_READ_LIGHT + 2, b'\x00', False)
            except BTLEException:
                _LOGGER.warning("Unable to control the device")

            self._device.disconnect()
