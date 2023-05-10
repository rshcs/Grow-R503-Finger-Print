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
    
    def __init__(self, port=8, baud=57600, pw=0, addr=0xFFFFFFFF):
        self.port = port
        self.baud = baud
        self.pw = c_uint32(pw)
        self.addr = c_uint32(addr)


    def send_msg(self, pkgid, pkglen, instcode, pkg):
        return self.b_array(self.HEADER, self.addr, pkgid, pkglen, instcode, pkg) + self.calc_checksum(pkgid, pkglen, instcode, pkg).value.to_bytes(2, 'big')

    @staticmethod
    def b_array(*args):
        array_of_bytes = b''
        for arg in args:
            array_of_bytes += arg.value.to_bytes(sizeof(arg), 'big')
        return array_of_bytes

    def calc_checksum(self, pkg_id, pkglen, instr_code, pkg):
        whole_pkg = self.b_array(pkg_id, instr_code, pkglen, pkg)
        chksum = sum(whole_pkg)
        return c_uint16(chksum)
    
    def read_msg(self, data_stream):
        hdr_rd = data_stream[:2]
        adr_rd = data_stream[2:6]
        instr_code_rd = data_stream[6]
        pkg_len_rd = data_stream[7:9]
        return hdr_rd, adr_rd, instr_code_rd, pkg_len_rd


    def ser_send(self, pid, pkg_len, instruction_code, pkg):
        pid = c_uint8(pid)
        pkg_len = c_uint16(pkg_len)
        instruction_code = c_uint8(instruction_code)
        pkg = c_uint32(pkg)
        with serial.Serial(f'COM{self.port}', self.baud, timeout=1) as ser:
            send_values = self.send_msg(pid, pkg_len, instruction_code, pkg)
            print(send_values)
            ser.write(send_values)
            read_val = ser.read(128)
            print(read_val)
            print(self.read_msg(read_val))
            print('done.')

if __name__ == '__main__':
    pid = 0x01
    pkg_len = 0x07
    instruction_code = 0x13
    pkg = 0x00

    fp = R503()
    fp.ser_send(pid, pkg_len, instruction_code, pkg)