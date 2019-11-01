# Home Assistant: STEVAL_BCN002V1
This component allows to get the data of sensors of STEVAL_BCN002V1 on [Home Assistant][hass].

![image](https://user-images.githubusercontent.com/11463289/68007850-4438bc00-fcc0-11e9-9695-32c8a53a86ee.png)

## Installation

* All files of this repository should be placed on `custom_components\BCN002V1` inside of `~/.homeassistant` or `~/config` folder. 

       $ cd ~/.homeassistant
       $ mkdir custom_components
       $ cd custom_components
       $ git clone https://github.com/musk95/STEVAL_BCN002V1.git BCN002V1

# Configuration
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


[hass]: https://home-assistant.io
