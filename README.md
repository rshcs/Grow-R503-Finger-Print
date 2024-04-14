![python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=Python&logoColor=white)

![licence_mit](https://img.shields.io/badge/python-3.6+-blue)
![licence_mit](https://img.shields.io/badge/licence-MIT-orange)
![commits](https://img.shields.io/github/last-commit/rshcs/Grow-R503-Finger-Print)


# GROW R503 Fingerprint 

![Fingerprint_sensor](https://i.ibb.co/Z2rnD0K/seonsor.jpg)

---

### Features

* Written in pure python.
* Provides all the manufacturer specified operations of the module.
* Can be connected with a computer directly with a USB to TTL converter. (Do not need a microcontroller)
* Can be used for testing the functionality of the module or creating direct applications without involving a microcontroller.

---

### Interfacing
#### Wiring connections:

|Sensor Side|RS232 Converter|
|---|---|
|Red (power)|3.3v Power|
|White (touch induction power)|3.3v power|
|Black (Ground)|Ground (0v)|
|Maroon or Green or Brown (Rx)|Tx|
|Yellow  (Tx)|Rx|
|Blue (Wakeup)|Not connected|

![Connections](https://i.ibb.co/SyXvZ2G/connections.png)
(Ref: Datasheet)

* **Make sure to use 3.3v power supply unless you have the 5v version of the sensor.**

* If you use a separate 3.3v power supply other than the RS232 converters power then make sure to connect grounds together (common ground).

* The line order is according to the colors, even though the note says it's not.

--- 

#### Usb to TTL
![rs232_usb](https://i.ibb.co/nmkbvb3/usb-to-rs232.png)
* This module can be used to interface with the module since it provides 5v to 3.3v conversion for both logic level and power.
* However, make sure to switch jumper position to the 3.3v and connect 3.3v power pin of the converter.

---

### Installation

Method 1: 
* Run `pip install r503` on terminal 

Method 2:
* Run `pip install pyserial` on terminal.
* Download **r503.py** file.
* Download **confirmation_codes.json** file.
* Place downloaded files in the project directory

### Basic usage overview

---
#### Registering a fingerprint

    from r503 import R503

    fp = R503(port=5)
    fp.manual_enroll(location=8)

* you have to place the finger 4 (changeable) times on the sensor during the process

Terminal output:

![Fingerprint registering](https://i.ibb.co/ssRx1hG/fingerprint-registering.png)

---

#### Search a Fingerprint from the stored data

    from r503 import R503
    from time import sleep
    
    fp = R503(port=5)
    
    print('Place your finger on the sensor..')
    sleep(3) # Not required to add this line
    print(fp.search())

Terminal output:

![Fingerprint matching status](https://i.ibb.co/y8z0Gdf/fp-location.png)

* first value = success if 0
* second value = stored location of the memory
* third value = match score

---

Number of fingerprints in the memory

    from r503 import R503
    
    fp = R503(port=5)
    print('Num of templates: ', fp.read_valid_template_num())

Terminal output:

![Number of templates](https://i.ibb.co/wsRSQg8/num-of-temps.png)

---
#### Read fingerprint stored locations

    from r503 import R503
    
    fp = R503(port=5)
    print(fp.read_index_table())

Terminal output:

![Fingerprint stored locations](https://i.ibb.co/drXhRRB/temp-locations.png)

---
#### Delete a fingerprint

    from r503 import R503
    
    fp = R503(port=5)
    fp.delete_char(6)

Deletes the fingerprint record at given index

---

#### Aura LED Control

    from r503 import R503
    
    fp = R503(port=5)
    fp.led_control(ctrl=3, color=5)

Output: LED keeps on with a specific color according to the number

---
#### Read Product Information

    from r503 import R503
    
    fp = R503(port=5)

    for k, v in fp.read_prod_info_decode().items():
        print(k, ': ', v)

Terminal output:

![Info](https://i.ibb.co/3WjyGnP/info.png)

---

For Linux users: if a permission error occurs while opening the serial port, run the following command:

`sudo chmod a+rw /dev/ttyUSB{your device port number}`

Etc:

`sudo chmod a+rw /dev/ttyUSB0`

References:

- [pypi.org/r503](https://pypi.org/project/r503/)
- [grow-r503-docs.readthedocs.io](https://grow-r503-docs.readthedocs.io/en/latest/r503.html)

