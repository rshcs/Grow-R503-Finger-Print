import serial
from time import sleep
from ctypes import c_uint8, c_uint16, c_uint32, sizeof

port_number = 8
baud_rate = 57600

header = c_uint16(0xEF01)
addr = c_uint32(0xFFFFFFFF)
pid = c_uint8(0x01)
pkg_len = c_uint16(0x07)
instruction_code = c_uint8(0x13)
passwd = c_uint32(0x00)

def send_msg(hdr, adr, pkgid, pkglen, instcode, pswd):
    return b_array(hdr, adr, pkgid, pkglen, instcode, pswd) + calc_checksum(pkgid, pkglen, instcode, pswd).value.to_bytes(2, 'big')

def b_array(*args):
    array_of_bytes = b''
    for arg in args:
        array_of_bytes += arg.value.to_bytes(sizeof(arg), 'big')
    return array_of_bytes

def calc_checksum(pkg_id, pkglen, instr_code, pkg):
    whole_pkg = b_array(pkg_id, instr_code, pkglen, pkg)
    chksum = sum(whole_pkg)
    return c_uint16(chksum)

# print(calc_checksum(pid, instruction_code, pkg_len, passwd))
# print(send_msg(header, addr, pid, pkg_len, instruction_code, passwd))

sleep(1)
with serial.Serial(f'COM{port_number}', baud_rate, timeout=1) as ser:
    send_values = send_msg(header, addr, pid, pkg_len, instruction_code, passwd)
    print(send_values)
    ser.write(send_values)
    read_val = ser.read(100)
    print(read_val)
