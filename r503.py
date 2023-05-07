import serial
from time import sleep
from ctypes import c_uint8, c_uint16, c_uint32, sizeof
from read_conf import conf_codes


class R503:
    HEADER = c_uint16(0xEF01)
    PID_COMMAND = c_uint8(0x01) # Command packet
    PID_DATA = c_uint8(0x02) # Data packet, data packet must follow command packet or ack packet
    PID_ACK = c_uint8(0x07) # Acknowledge packet
    PID_END = c_uint8(0x08) # End of data packet
    confirmation_codes = conf_codes()
    
    def __init__(self, port=8, baud=57600, pw=0) -> None:
        self.port = port
        self.baud = baud
        self.pw = c_uint32(pw)



