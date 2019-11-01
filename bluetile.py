from datetime import datetime, timedelta
import logging
from threading import Lock
from btlewrap.base import BluetoothInterface, BluetoothBackendException

_HANDLE_READ_NAME = 0x0006
_HANDLE_READ_BATTERY_LEVEL = 0x001C
_HANDLE_READ_ENVIRONMENTAL_SENSORS = 0x000d

ST_PRESSURE = "pressure"
ST_TEMPERATURE = "temperature"
ST_HUMIDITY = "humidity"
ST_BATTERY = "battery"

_LOGGER = logging.getLogger(__name__)

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