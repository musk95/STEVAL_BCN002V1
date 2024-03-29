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

       bcn002v1:
         mac: 'f5:ce:8c:51:00:95'

       sensor:
         - platform: BCN002V1
           scan_interval: 15
           monitored_conditions:
             - pressure
             - temperature
             - humidity
             - battery
             - proximity
        
       light:
         - platform: BCN002V1

![image2](https://user-images.githubusercontent.com/11463289/69224236-88ccbe80-0bbf-11ea-85cb-607900e624c1.png)

## CONFIGURATION VARIABLES
### mac
>*(string)(Required)*<br>
The MAC address of your sensor.

### monitored_conditions
>*(list)(Optional)*<br>
The parameters that should be monitored.<br><br>
>*Default value:*<br>
[“pressure”, “temperature”, “humidity”, “battery”, “proximity”]<br>
>>**pressure**<br>
Pressure in mBar at the sensor’s location.<br><br>
>**temperature**<br>
Temperature in C at the sensor’s location.<br><br>
>**humidity**<br>
Humidity level in % at the sensor’s location.<br><br>
>**proximity**<br>
Proximity distance in cm at the sensor’s location.<br><br>
>**battery**<br>
Battery details (in %).<br>

### name
>*(string)(Optional)*<br>
The name displayed in the frontend.

### force_update
>*(boolean)(Optional)*<br>
Sends update events even if the value hasn’t changed.<br><br>
>*Default value:*<br>
false

### median
>*(integer)(Optional)*<br>
Sometimes the sensor measurements show spikes. Using this parameter, the poller will report the median of the last 3 (you can also use larger values) measurements. This filters out single spikes. Median: 5 will also filter double spikes. If you never have problems with spikes, median: 1 will work fine.<br><br>
>*Default value:*<br>
1

### timeout
>*(integer)(Optional)*<br>
Define the timeout value in seconds when polling.<br><br>
>*Default value:*<br>
10

### retries
>*(integer)(Optional)*<br>
Define the number of retries when polling.<br><br>
>*Default value:*<br>
2

### cache_value
>*(integer)(Optional)*<br>
Define cache expiration value in seconds.<br><br>
>*Default value:*<br>
3

### adapter
>*(string)(Optional)*<br>
Define the Bluetooth adapter to use. Run hciconfig to get a list of available adapters.<br><br>
>*Default value:*<br>
hci0

[hass]: https://home-assistant.io
