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

    def send_msg(self, *args): # pkgid, pkglen, instcode, pkg
        return self.b_array(self.HEADER, self.addr, *args) + self.calc_checksum(*args).value.to_bytes(2, 'big')

    @staticmethod
    def b_array(*args):
        array_of_bytes = b''
        for arg in args:
            array_of_bytes += arg.value.to_bytes(sizeof(arg), 'big')
        return array_of_bytes

    def calc_checksum(self, *args):
        whole_pkg = self.b_array(*args)
        chksum = sum(whole_pkg)
        return c_uint16(chksum)
    
    def read_msg(self, data_stream):
        hdr_rd = int.from_bytes(data_stream[:2], 'big') # Header
        adr_rd = int.from_bytes(data_stream[2:6], 'big') # Address
        pkg_id_rd = data_stream[6] # Package ID
        pkg_len_rd = int.from_bytes(data_stream[7:9], 'big') # Length
        conf_code_rd = int.from_bytes(data_stream[9:7+pkg_len_rd], 'big') # Actual package
        chksum_rd = int.from_bytes(data_stream[-2:], 'big') # Checksum
        return hdr_rd, adr_rd, pkg_id_rd, pkg_len_rd, conf_code_rd, chksum_rd

    def led_control(self, ctrl=0x03, speed=0, color=0x01, cycles=0):
        return ctrl << 24 | speed << 16 | color << 8 | cycles

    def ser_send(self, demo_mode=True, **kwargs): 
        """
        pid, pkg_len, instr_code, pkg
        """
        kwargs['pid'] = c_uint8(kwargs['pid'])
        kwargs['pkg_len'] = c_uint16(kwargs['pkg_len'])
        kwargs['instr_code'] = c_uint8(kwargs['instr_code'])
        if 'pkg' in kwargs:
            kwargs['pkg'] = c_uint32(kwargs['pkg'])
        with serial.Serial(f'COM{self.port}', self.baud, timeout=1) as ser:
            send_values = self.send_msg(*list(kwargs.values()))
            print(send_values)
            if demo_mode == False:
                ser.write(send_values)
                read_val = ser.read(256)
                print(read_val)
                hdrrd, adrrd, pidrd, p_len_rd, pkgrd, chksumrd = self.read_msg(read_val)
                print(hex(hdrrd), hex(adrrd), hex(pidrd), hex(p_len_rd), hex(pkgrd), hex(chksumrd))
            # print('done.')


if __name__ == '__main__':
    fp = R503()

    #status reg and other details
    # pid = 0x01
    # pkg_len = 0x03
    # instruction_code = 0x0F

    # Check pw
    # pid = 0x01
    # pkg_len = 0x07
    # instruction_code = 0x13
    # pkg = 0x00

    # Hand shake 
    # pid = 0x01
    # pkg_len = 0x03
    # instruction_code = 0x40

    # Check sensor
    # pid = 0x01
    # pkg_len = 0x03
    # instruction_code = 0x36

    # led control
    pid = 0x01
    pkg_len = 0x07
    instruction_code = 0x35
    led_cont = fp.led_control(ctrl=0x04, color=0x06)
    

    #pid, pkg_len, instruction_code, pkg
    demo = False
    fp.ser_send(pid=pid, pkg_len=pkg_len, instr_code=instruction_code, pkg=led_cont, demo_mode=demo)

    