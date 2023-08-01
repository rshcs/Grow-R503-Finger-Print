![python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=Python&logoColor=white)

![licence_mit](https://img.shields.io/badge/python-3.6+-blue)
![licence_mit](https://img.shields.io/badge/licence-MIT-orange)
![commits](https://img.shields.io/github/last-commit/rshcs/Grow-R503-Finger-Print)


# GROW R503 Fingerprint 

![Fingerprint_sensor](https://i.ibb.co/2vWR4jH/seonsor.jpg)

---

### Features

* Written in pure python with only using build in modules except *pyserial*.
* Provides all the manufacturer specified operations of the module.
* Can be connected with a computer directly with a USB to TTL converter. (Do not need a microcontroller)
* Can be used for testing or direct applications.

---

### Interfacing
#### Wiring connections:

|Sensor Side|RS232 Converter|
|---|---|
|Red <br>(power)|3.3v Power|
|White <br>(touch induction power)|3.3v power|
|Black <br>(Ground)|Ground (0v)|
|Maroon or Green or Brown <br> (Rx)|Tx|
|Yellow <br> (Tx)|Rx|
|Blue <br> (Wakeup)|Not connected|

![Connections](https://i.ibb.co/SyXvZ2G/connections.png)
(Ref: Datasheet)

* **Make sure to use 3.3v power supply unless you have the 5v version of the sensor.**

* If you use a separate 3.3v power supply other than the RS232 converters power then make sure to connect grounds together (common ground).

* The line order is according to the colors, even though the note says it's not.

--- 

#### Tip
![rs232_usb](https://i.ibb.co/MndQz7M/usb-to-rs232.png)
* This module can be used to interface with the module since it provides 5v to 3.3v conversion for both logic level and power.
* However make sure to switch jumper position to the 3.3v and connect 3.3v power pin of the converter.

### Installation


* Run `pip install pyserial` on terminal.

* Download **r503.py** file.

