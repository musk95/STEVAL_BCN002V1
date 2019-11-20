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

#    def get_environment_sensor_data(self):
#        """Fill the cache with new data from the sensor."""
#        _LOGGER.debug("Filling cache with new sensor data.")
#        try:
#            self._device = Peripheral()
#            self._device.connect(self._mac, addrType=self._address_type, iface=self._iface)
#        except BTLEException as ex:
#            _LOGGER.warning("%s", ex)
#            return
#
#        try:
#            self._device.writeCharacteristic(_HANDLE_READ_ENVIRONMENTAL_SENSORS + 2, self._DATA_MODE_LISTEN, True)
#            self._device.withDelegate(self)
#            self._device.waitForNotifications(self.ble_timeout)
#            self._device.writeCharacteristic(_HANDLE_READ_ENVIRONMENTAL_SENSORS + 2, self._DATA_MODE_LISTEN_CANCEL, True)
#        except BTLEException:
#            self._cache = None
#            _LOGGER.warning("Unable to read the data of sensors!!")
#            self._last_read = datetime.now() - self._cache_timeout + \
#                    timedelta(seconds=300)
#
#        self._device.disconnect()

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

'''
class BlueTilePoller(object):
    def __init__(self, mac, backend, cache_timeout=600, retries=3, adapter='hci0'):
        """
        Initialize a BlueTile Poller for the given MAC address.
        """

        self._mac = mac
        self._bt_interface = BluetoothInterface(backend, adapter=adapter, address_type="random")
        self._cache = None
        self._cache_timeout = timedelta(seconds=cache_timeout)
        self._last_read = None
        self._fw_last_read = None
        self.retries = retries
        self.ble_timeout = 10
        self.lock = Lock()
        self.battery = None

    def name(self):
        """Return the name of the sensor."""
        with self._bt_interface.connect(self._mac) as connection:
            name = connection.read_handle(_HANDLE_READ_NAME)  # pylint: disable=no-member
            print('Received result for handle {}: {}'.format(_HANDLE_READ_NAME, name))

        if not name:
            raise BluetoothBackendException("Could not read NAME using handle %s"
                                            " from Mi Temp sensor %s" % (hex(_HANDLE_READ_NAME), self._mac))
        return ''.join(chr(n) for n in name)

    def fill_cache(self):
        """Fill the cache with new data from the sensor."""
        print('Filling cache with new sensor data.')

        with self._bt_interface.connect(self._mac) as connection:
            try:
                connection.wait_for_notification(_HANDLE_READ_ENVIRONMENTAL_SENSORS + 2, self,
                                                 self.ble_timeout)  # pylint: disable=no-member
                # If a sensor doesn't work, wait 5 minutes before retrying
            except BluetoothBackendException:
                self._last_read = datetime.now() - self._cache_timeout + \
                    timedelta(seconds=300)
                return

    def battery_level(self):
        with self._bt_interface.connect(self._mac) as connection:
            try:
                connection.wait_for_notification(_HANDLE_READ_BATTERY_LEVEL + 2, self,
                                                 self.ble_timeout)  # pylint: disable=no-member
                # If a sensor doesn't work, wait 5 minutes before retrying
            except BluetoothBackendException:
                self._last_read = datetime.now() - self._cache_timeout + \
                    timedelta(seconds=300)
                return
        return self.battery
		
    def parameter_value(self, parameter, read_cached=True):
        """Return a value of one of the monitored paramaters.

        This method will try to retrieve the data from cache and only
        request it by bluetooth if no cached value is stored or the cache is
        expired.
        This behaviour can be overwritten by the "read_cached" parameter.
        """
        # Special handling for battery attribute
        if parameter == ST_BATTERY:
            return self.battery_level()

        # Use the lock to make sure the cache isn't updated multiple times
        with self.lock:
            if (read_cached is False) or \
                    (self._last_read is None) or \
                    (datetime.now() - self._cache_timeout > self._last_read):
                self.fill_cache()
            else:
                print("Using cache ({} < {})".format(
                              datetime.now() - self._last_read,
                              self._cache_timeout))

        if self.cache_available():
            return self._parse_data()[parameter]
        else:
            raise BluetoothBackendException("Could not read data from BlueTile sensor %s" % self._mac)

    def clear_cache(self):
        """Manually force the cache to be cleared."""
        self._cache = None
        self._last_read = None

    def cache_available(self):
        """Check if there is data in the cache."""
        return self._cache is not None

    def _check_data(self):
        """Ensure that the data in the cache is valid.

        If it's invalid, the cache is wiped.
        """
        if not self.cache_available():
            return

        parsed = self._parse_data()
        print('Received new data from sensor: Press= {}, Temp={}, Humidity={}'.format(parsed[ST_PRESSURE], parsed[ST_TEMPERATURE], parsed[ST_HUMIDITY]))

        if parsed[ST_HUMIDITY] > 100:  # humidity over 100 procent
            self.clear_cache()
            return

    def _parse_data(self):
        """Parses the byte array returned by the sensor."""
        data = self._cache

        res = dict()
        res[ST_PRESSURE] = float((data[2]+(data[3]<<8)+(data[4]<<16)+(data[5]<<24))/100)
        res[ST_HUMIDITY] = float((data[6]+(data[7]<<8))/10)
        res[ST_TEMPERATURE] = float((data[8]+(data[9]<<8))/10)
        return res

    def handleNotification(self, handle, raw_data):  # pylint: disable=unused-argument,invalid-name
        print(handle)
        if handle==(_HANDLE_READ_BATTERY_LEVEL + 1):
            self.battery = (raw_data[2]+(raw_data[3]<<8))/10

        if handle==(_HANDLE_READ_ENVIRONMENTAL_SENSORS + 1):
            self._cache = raw_data
            self._check_data()
            if self.cache_available():
                self._last_read = datetime.now()
            else:
                # If a sensor doesn't work, wait 5 minutes before retrying
                self._last_read = datetime.now() - self._cache_timeout + \
                    timedelta(seconds=300)
'''