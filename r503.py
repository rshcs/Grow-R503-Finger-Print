import serial
from time import sleep
from ctypes import c_uint8, c_uint16, c_uint32, sizeof
from read_conf import conf_codes
from struct import unpack


class R503:
    HEADER = c_uint16(0xEF01)
    PID_COMMAND = 0x01  # Command packet
    PID_DATA = c_uint8(0x02)  # Data packet, data packet must follow command packet or ack packet
    PID_ACK = c_uint8(0x07)  # Acknowledge packet
    PID_END = c_uint8(0x08)  # End of data packet
    
    def __init__(self, port=8, baud=57600, pw=0, addr=0xFFFFFFFF):
        # self.port = port
        # self.baud = baud
        self.pw = c_uint32(pw)
        self.addr = c_uint32(addr)
        self.ser = serial.Serial(f'COM{port}', baud, timeout=1)

    def ser_close(self):
        self.ser.close()

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
        hdr_rd, adr_rd, pkg_id_rd, pkg_len_rd = unpack('>HIBH', data_stream[:9])
        conf_code_rd = data_stream[9:len(data_stream)-2]
        chksum_rd = int.from_bytes(data_stream[-2:], 'big')  # Checksum
        return hdr_rd, adr_rd, pkg_id_rd, pkg_len_rd, conf_code_rd, chksum_rd

    def led_control(self, ctrl=0x03, speed=0, color=0x01, cycles=0):
        """
        ctrl: (int) 1 to 6
        1: brathing light, 2: flashing light, 3: always on, 4: always off, 5: gradually on, 6: gradually off
        speed: (int) 0 to 255
        color: (int) 0 to 7
        cycles: (int) 0 to 255
        returns confirmation code
        """
        cmd = ctrl << 24 | speed << 16 | color << 8 | cycles
        rd = self.ser_send(pid=self.PID_COMMAND, pkg_len=0x07, instr_code=0x35, pkg=cmd)
        return rd[4][0]

    def read_sys_para(self):
        # status reg and other details
        ds = self.ser_send(pid=self.PID_COMMAND, pkg_len=0x03, instr_code=0x0F)[4]
        return unpack('>HHHHIHH', ds[1:])

    def check_pw(self, pw=0x00):
        return self.ser_send(pid=self.PID_COMMAND, pkg_len=0x07, instr_code=0x13, pkg=pw)[4][0]

    def handshake(self):
        return self.ser_send(pid=self.PID_COMMAND, pkg_len=0x03, instr_code=0x40)[4][0]

    def check_sensor(self):
        return self.ser_send(pid=self.PID_COMMAND, pkg_len=0x03, instr_code=0x36)[4][0]



    def confirmation_decode(self, msg):
        confirmation_codes = conf_codes()
        return confirmation_codes[msg]

    def ser_send(self, demo_mode=False, **kwargs):
        """
        pid, pkg_len, instr_code, pkg
        """
        kwargs['pid'] = c_uint8(kwargs['pid'])
        kwargs['pkg_len'] = c_uint16(kwargs['pkg_len'])
        kwargs['instr_code'] = c_uint8(kwargs['instr_code'])
        if 'pkg' in kwargs:
            kwargs['pkg'] = c_uint32(kwargs['pkg'])

        send_values = self.send_msg(*list(kwargs.values()))
        print(send_values)
        if not demo_mode:
            self.ser.write(send_values)
            read_val = self.ser.read(256)
            print(read_val)
            if read_val != b'':
                # hdrrd, adrrd, pidrd, p_len_rd, pkgrd, chksumrd = self.read_msg(read_val)
                # print(hex(hdrrd), hex(adrrd), hex(pidrd), hex(p_len_rd), pkgrd, hex(chksumrd))
                return self.read_msg(read_val)


if __name__ == '__main__':
    fp = R503(port=5)

    # led control
    # pid = 0x01
    # pkg_len = 0x07
    # instruction_code = 0x35
    # led_cont = fp.led_control(ctrl=0x04, color=0x06)
    

    #pid, pkg_len, instruction_code, pkg
    demo = False
    # fp.ser_send(pid=pid, pkg_len=pkg_len, instr_code=instruction_code, demo_mode=demo)
    msg = fp.led_control(ctrl=2, color=7, speed=255, cycles=3)
    print(fp.confirmation_decode(msg))
    fp.ser_close()
    