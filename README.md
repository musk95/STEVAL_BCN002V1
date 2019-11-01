# Home Assistant: STEVAL_BCN002V1
This component allows to get the data of sensors of STEVAL_BCN002V1 on [Home Assistant][hass].

![image](https://user-images.githubusercontent.com/11463289/68007850-4438bc00-fcc0-11e9-9695-32c8a53a86ee.png)

## Installation

* All files of this repository should be placed on `custom_components\BCN002V1` inside of `~/.homeassistant` or `~/config` folder. 

       $ cd ~/.homeassistant
       $ mkdir custom_components
       $ cd custom_components
       $ git clone https://github.com/musk95/STEVAL_BCN002V1.git BCN002V1

## Configuration
1. Start a scan to determine the MAC addresses of the sensor:

       $ sudo hcitool lescan
       LE Scan ...
       4C:65:A8:D2:31:7F BCN-002
       [...]

   Or if your distribution is using bluetoothctl:
  
       $ bluetoothctl
       [bluetooth]# scan on
       Discovery started
       [CHG] Controller XX:XX:XX:XX:XX:XX Discovering: yes
       [NEW] Device E0:F5:F4:FE:DE:AD BCN-002
  
2. Check for BCN-002 or similar entries, those are your sensor.

3. To use sensors in your installation, add the following on `confidureation.yaml` which is located on `~/.homeassistant` or `~/config` folder.

       sensor:
         - platform: BCN002V1
           mac: 'E0:F5:F4:FE:DE:AD'
           scan_interval: 5
           monitored_conditions:
             - pressure
             - temperature
             - humidity
             - battery

## CONFIGURATION VARIABLES
### mac
>*(string)(Required)*<br>
The MAC address of your sensor.

### monitored_conditions
>*(list)(Optional)*<br>
The parameters that should be monitored.

>*Default value:*<br>
[“pressure”, “temperature”, “humidity”, “battery”]

>**pressure**<br>
Pressure in mBar at the sensor’s location.

>**temperature**<br>
Temperature in C at the sensor’s location.

>**humidity**<br>
Humidity level in % at the sensor’s location.

>**battery**<br>
Battery details (in %).

### name
>*(string)(Optional)*<br>
The name displayed in the frontend.

### force_update
>*(boolean)(Optional)*<br>
Sends update events even if the value hasn’t changed.

>*Default value:*<br>
false

### median
>*(integer)(Optional)*<br>
Sometimes the sensor measurements show spikes. Using this parameter, the poller will report the median of the last 3 (you can also use larger values) measurements. This filters out single spikes. Median: 5 will also filter double spikes. If you never have problems with spikes, median: 1 will work fine.

>*Default value:*<br>
1

### timeout
>*(integer)(Optional)*<br>
Define the timeout value in seconds when polling.

>*Default value:*<br>
10

### retries
>*(integer)(Optional)*<br>
Define the number of retries when polling.

>*Default value:*<br>
2

### cache_value
>*(integer)(Optional)*<br>
Define cache expiration value in seconds.

>*Default value:*<br>
3

### adapter
>*(string)(Optional)*<br>
Define the Bluetooth adapter to use. Run hciconfig to get a list of available adapters.

>*Default value:*<br>
hci0

![image](https://user-images.githubusercontent.com/11463289/68009223-bb704f00-fcc4-11e9-86a1-c4d637333635.png)

[hass]: https://home-assistant.io
