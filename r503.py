import serial
from time import sleep
from ctypes import c_uint8, c_uint16, c_uint32, sizeof
from struct import pack, unpack
import sys
import json


class R503:
    header = c_uint16(0xEF01)
    pid_command = 0x01  # pid_command packet
    
    def __init__(self, port=8, baud=57600, pw=0, addr=0xFFFFFFFF):
        self.pw = c_uint32(pw)
        self.addr = c_uint32(addr)
        try:
            self.ser = serial.Serial(f'COM{port}', baud, timeout=1)
        except serial.serialutil.SerialException:
            sys.exit('Serial port not found !')

    def conf_codes(self):
        with open('confirmation_codes.json', 'r') as jf:
            jsob = json.load(jf)
        return jsob

    def ser_close(self):
        self.ser.close()

    def send_msg(self, *args):  # pkgid, pkglen, instcode, pkg
        return self.b_array(self.header, self.addr, *args) + self.calc_checksum(*args).value.to_bytes(2, 'big')

    @staticmethod
    def b_array(*args):
        array_of_bytes = b''
        for arg in args:
            if isinstance(arg, bytes):
                array_of_bytes += arg
            else:
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
        1: breathing light, 2: flashing light, 3: always on, 4: always off, 5: gradually on, 6: gradually off
        speed: (int) 0 to 255
        color: (int) 0 to 7
        cycles: (int) 0 to 255
        returns: confirmation code
        """
        # cmd = ctrl << 24 | speed << 16 | color << 8 | cycles
        cmd = pack('>BBBB', ctrl, speed, color, cycles)
        rd = self.ser_send(pid=self.pid_command, pkg_len=0x07, instr_code=0x35, pkg=cmd)
        print(rd[4])
        return rd[4][0]

    def read_sys_para(self):
        """
        Returns status register and other basic configuration parameters

        returns: (list) status_reg, sys_id_code, finger_lib_size, security_lvl, device_addr, data_packet_size, baud_rate
        """
        # status reg and other details
        ds = self.ser_send(pid=self.pid_command, pkg_len=0x03, instr_code=0x0F)[4]
        return unpack('>HHHHIHH', ds[1:])

    def read_sys_para_decode(self):
        """
        Return decoded system parameters in more human-readable way
        returns: (dictionary) system parameters
        """
        rsp = self.read_sys_para()
        pkg_length = {0: 32, 1: 64, 2: 128, 3: 256}
        sys_parameters = {
            'system_busy': bool(rsp[0] & 8),
            'matching_finger_found': bool(rsp[0] & 4),
            'pw_verified': bool(rsp[0] & 2),
            'valid_image_in_buffer': bool(rsp[0] & 1),
            'system_id_code': rsp[1],
            'finger_library_size': rsp[2],
            'security_level': rsp[3],
            'device_address': hex(rsp[4]),
            'data_packet_size': pkg_length[rsp[5]],
            'baud_rate': rsp[6]*9600}
        return sys_parameters

    def check_pw(self, pw=0x00):
        return self.ser_send(pid=self.pid_command, pkg_len=0x07, instr_code=0x13, pkg=pw)[4][0]

    def handshake(self):
        return self.ser_send(pid=self.pid_command, pkg_len=0x03, instr_code=0x40)[4][0]

    def check_sensor(self):
        return self.ser_send(pid=self.pid_command, pkg_len=0x03, instr_code=0x36)[4][0]

    def confirmation_decode(self, msg):
        confirmation_codes = self.conf_codes()
        return confirmation_codes[str(msg)]

    def get_img(self):
        """
        Detect a finger and store it in image_buffer
        """
        return self.ser_send(pid=self.pid_command, pkg_len=0x03, instr_code=0x01)[4][0]

    def get_img_ex(self):
        """
        Detect a finger and store it in image_buffer return 0x07 if image poor quality
        """
        return self.ser_send(pid=self.pid_command, pkg_len=0x03, instr_code=0x28)[4][0]

    def img2tz(self, buffer_id=1):
        """
        Generate character file from the original image in Image Buffer and store the file in CharBuffer 1 or 2
        parameter: (int) buffer_id, 1 or 2
        returns: (int) confirmation code
        """
        return self.ser_send(pid=self.pid_command, pkg_len=0x04, instr_code=0x02, pkg=buffer_id)[4][0]

    def reg_model(self):
        """
        Combine info of character files in CharBuffer 1 and 2 and generate a template which is stored back in both
        CharBuffer 1 and 2
        input parameters: None
        returns: (int) confirmation code
        """
        return self.ser_send(pid=self.pid_command, pkg_len=0x03, instr_code=0x05)[4][0]

    def store(self, buffer_id, page_id):
        """
        Store the template of buffer1 or buffer2 on the flash library
        """
        package = pack('>BH', buffer_id, page_id)
        return self.ser_send(pid=self.pid_command, pkg_len=0x06, instr_code=0x06, pkg=package, demo_mode=True)[4][0]

    def ser_send(self, demo_mode=False, **kwargs):
        """
        pid, pkg_len, instr_code, pkg
        """
        kwargs['pid'] = c_uint8(kwargs['pid'])
        kwargs['pkg_len'] = c_uint16(kwargs['pkg_len'])
        kwargs['instr_code'] = c_uint8(kwargs['instr_code'])
        # if 'pkg' in kwargs:
        #     kwargs['pkg'] = c_uint32(kwargs['pkg'])

        send_values = self.send_msg(*list(kwargs.values()))
        print(send_values)
        if not demo_mode:
            self.ser.write(send_values)
            read_val = self.ser.read(128)
            print(read_val)
            if read_val == b'':
                sys.exit('Respond not received from the module')
            else:
                return self.read_msg(read_val)


if __name__ == '__main__':
    fp = R503()

    #pid, pkg_len, instruction_code, pkg
    # demo = False
    # # fp.ser_send(pid=pid, pkg_len=pkg_len, instr_code=instruction_code, demo_mode=demo)
    # msg = fp.led_control(ctrl=2, color=3, speed=255, cycles=3)
    # msg = fp.read_sys_para_decode()
    # for k, v in msg.items():
    #     print(k, ": ", v)

    fp.store(buffer_id=1, page_id=1)
    # print(fp.conf_codes())

    # print(fp.gen_img())
    fp.ser_close()
