import serial
from time import sleep, time
from struct import pack, unpack
import sys
import json


class R503:
    header = pack('>H', 0xEF01)
    pid_command = 0x01  # pid_command packet
    
    def __init__(self, port=8, baud=57600, pw=0, addr=0xFFFFFFFF):
        self.pw = pack('>I', pw)
        self.addr = pack('>I', addr)
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
    
    def read_msg(self, data_stream):
        hdr_rd, adr_rd, pkg_id_rd, pkg_len_rd, conf_code_rd = unpack('>HIBHB', data_stream[:10])
        pkg = data_stream[10:len(data_stream)-2]
        chksum_rd = unpack('>H', data_stream[-2:])
        return hdr_rd, adr_rd, pkg_id_rd, pkg_len_rd, conf_code_rd, pkg, chksum_rd

    def led_control(self, ctrl=0x03, speed=0, color=0x01, cycles=0):
        """
        ctrl: (int) 1 to 6
        1: breathing light, 2: flashing light, 3: always on, 4: always off, 5: gradually on, 6: gradually off
        speed: (int) 0 to 255
        color: (int) 0 to 7
        cycles: (int) 0 to 255
        returns: confirmation code
        """
        cmd = pack('>BBBB', ctrl, speed, color, cycles)
        rd = self.ser_send(pkg_len=0x07, instr_code=0x35, pkg=cmd)
        return -1 if rd == -1 else rd[4]

    def read_sys_para(self):
        """
        Status register and other basic configuration parameters
        returns: (list) status_reg, sys_id_code, finger_lib_size, security_lvl, device_addr, data_packet_size, baud_rate
        """
        read_pkg = self.ser_send(pkg_len=0x03, instr_code=0x0F)
        return -1 if read_pkg == -1 else unpack('>HHHHIHH', read_pkg[5])

    def read_sys_para_decode(self):
        """
        Get decoded system parameters in more human-readable way
        returns: (dictionary) system parameters
        """
        rsp = self.read_sys_para()
        if rsp == -1:
            return -1
        pkg_length = {0: 32, 1: 64, 2: 128, 3: 256}
        return {
            'system_busy': bool(rsp[0] & 1),
            'matching_finger_found': bool(rsp[0] & 2),
            'pw_verified': bool(rsp[0] & 4),
            'valid_image_in_buffer': bool(rsp[0] & 8),
            'system_id_code': rsp[1],
            'finger_library_size': rsp[2],
            'security_level': rsp[3],
            'device_address': hex(rsp[4]),
            'data_packet_size': pkg_length[rsp[5]],
            'baud_rate': rsp[6] * 9600,
        }

    def check_pw(self, pw=0x00):
        return self.ser_send(pkg_len=0x07, instr_code=0x13, pkg=pack('>I', pw))[4]

    def handshake(self):
        return self.ser_send(pkg_len=0x03, instr_code=0x40)[4]

    def check_sensor(self):
        return self.ser_send(pkg_len=0x03, instr_code=0x36)[4]

    def confirmation_decode(self, c_code):
        cc = self.conf_codes()
        return cc[str(c_code)] if c_code in cc else 'others: system reserved'

    def get_img(self):
        """
        Detect a finger and store it in image_buffer
        """
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x01, print_hex=False)
        return -1 if read_conf_code == -1 else read_conf_code[4]

    def get_image_ex(self, print_hex=True):
        """
        Detect a finger and store it in image_buffer return 0x07 if image poor quality
        """
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x28, print_hex=print_hex)
        return -1 if read_conf_code == -1 else read_conf_code[4]

    def img2tz(self, buffer_id, print_hex=True):
        """
        Generate character file from the original image in Image Buffer and store the file in CharBuffer 1 or 2
        parameter: (int) buffer_id, 1 or 2
        returns: (int) confirmation code
        """
        read_conf_code = self.ser_send(pkg_len=0x04, instr_code=0x02, pkg=pack('>B', buffer_id), print_hex=print_hex)
        return -1 if read_conf_code == -1 else read_conf_code[4]

    def reg_model(self, print_hex=True):
        """
        Combine info of character files in CharBuffer 1 and 2 and generate a template which is stored back in both
        CharBuffer 1 and 2
        input parameters: None
        returns: (int) confirmation code
        """
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x05, print_hex=print_hex)
        return -1 if read_conf_code == -1 else read_conf_code[4]

    def store(self, buffer_id, page_id, timeout=2):
        """
        Store the template of buffer1 or buffer2 on the flash library
        """
        package = pack('>BH', buffer_id, page_id)
        read_conf_code = self.ser_send(pkg_len=0x06, instr_code=0x06, pkg=package, timeout=timeout)
        return -1 if read_conf_code == -1 else read_conf_code[4]

    def manual_enroll(self, timeout=10, num_of_fps=4):
        inc = 1
        printed = False
        t1 = time()
        finger_prints = 0
        while True:
            if not printed:
                print(f'Place your finger on the sensor: {inc}')
                printed = True
            msg = self.get_image_ex(print_hex=False)
            if msg == 0:
                print('Reading the finger print')
                char_status = self.img2tz(buffer_id=inc, print_hex=False)
                if char_status == 0:
                    print('Character file generation successful.')
                    finger_prints += 1
                else:
                    print('Character file generation failed !')
                    inc -= 1
                if finger_prints >= num_of_fps:
                    print('registering a finger print')
                    rm = self.reg_model(print_hex=False)
                    if rm == 0:
                        st = self.store(buffer_id=1, page_id=5)
                        print(st)
                        print('finger print registered successfully.')
                        break
                inc += 1
                sleep(2)
                t1 = time()
                printed = False
            sleep(.3)
            if time() - t1 > timeout:
                print('Timeout')
                break

    def match(self):
        """
        Compare the recently extracted character with the templates in the ModelBuffer, providing matching result.
        returns: (tuple) status: [0: matching, 1: error, 8: not matching], match score
        """
        rec_data = self.ser_send(pid=0x01, pkg_len=0x03, instr_code=0x03)
        if rec_data == -1:
            return -1
        return rec_data[4], rec_data[5]

    def empty_finger_lib(self):
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x0d)
        return -1 if read_conf_code == -1 else read_conf_code[4]

    def read_valid_template_num(self):
        read_pkg = self.ser_send(pkg_len=0x03, instr_code=0x1d)
        return -1 if read_pkg == -1 else unpack('>H', read_pkg[5])

    def read_index_table(self, index_page=0):
        """
        Read the fingerprint template index table
        parameters: (int) index_page = 0/1/2/3
        returns: (list) index which fingerprints saved already
        """
        index_page = pack('>B', index_page)
        temp = self.ser_send(pkg_len=0x04, instr_code=0x1f, pkg=index_page, print_hex=False)
        if temp == -1:
            return -1
        temp = temp[5]
        temp_indx = []
        for n, lv in enumerate(temp):
            temp_indx.extend(8 * n + i for i in range(8) if (lv >> i) & 1)
        return temp_indx

    def auto_enroll(self, location_id, duplicate_id=1, duplicate_fp=1, ret_status=1, finger_leave=1):
        """
        Automatic registration a template
        """
        package = pack('>BBBBB', location_id, duplicate_id, duplicate_fp, ret_status, finger_leave)
        read_pkg = self.ser_send(pkg_len=0x08, instr_code=0x31, pkg=package)
        if read_pkg == -1:
            return -1
        return read_pkg[4]

    def auto_identify(self, security_lvl=3, start_pos=0, end_pos=199, ret_key_step=0, num_of_fp_errors=1):
        """
        Search and verify a fingerprint
        return: (tuple) fp store location, match score
        """
        package = pack('>BBBBB', security_lvl, start_pos, end_pos, ret_key_step, num_of_fp_errors)
        read_pkg = self.ser_send(pkg_len=0x08, instr_code=0x32, pkg=package, timeout=10)
        if read_pkg == -1:
            return -1
        _, position, match_score = unpack('>BHH', read_pkg[5])
        return position, match_score

    def read_prod_info(self):
        info = self.ser_send(pkg_len=0x03, instr_code=0x3c)
        if info == -1:
            return -1
        info = info[5]
        return info[:16], info[16:20], info[20:28], info[28:30], info[30:38], info[38:40], info[40:42], info[42:44], info[44:46]

    def read_prod_info_decode(self):
        inf = self.read_prod_info()
        if inf == -1:
            return -1
        return {
            'module type': inf[0].decode('ascii').replace('\x00', ''),
            'batch number': inf[1].decode('ascii'),
            'serial number': inf[2].decode('ascii'),
            'hw main version': inf[3][0],
            'hw sub version': inf[3][1],
            'sensor type': inf[4].decode('ascii'),
            'image width': unpack('>H', inf[5])[0],
            'image height': unpack('>H', inf[6])[0],
            'template size': unpack('>H', inf[7])[0],
            'fp database size': unpack('>H', inf[8])[0]
        }

    def get_random_code(self):
        """
        Generates a random number
        returns: (unsigned 4 bytes integer)
        """
        read_pkg = self.ser_send(pkg_len=0x03, pid=0x01, instr_code=0x14, print_hex=False)
        return -1 if read_pkg == -1 else unpack('>I', read_pkg[5])[0]

    def ser_send(self, pkg_len, instr_code, pid=pid_command, pkg=None, demo_mode=False, timeout=1, print_hex=True):
        """
        pid, pkg_len, instr_code, pkg
        """
        send_values = pack('>BHB', pid, pkg_len, instr_code)
        if pkg is not None:
            send_values += pkg
        check_sum = sum(send_values)
        send_values = self.header + self.addr + send_values + pack('>H', check_sum)
        if print_hex:
            print(send_values.hex(sep=' '))
        if not demo_mode:
            self.ser.timeout = timeout
            self.ser.write(send_values)
            read_val = self.ser.read(128)
            if print_hex:
                print(read_val.hex(sep=' '))
            return -1 if read_val == b'' else self.read_msg(read_val)


if __name__ == '__main__':
    fp = R503()

    # for k, v in fp.read_sys_para_decode().items():
    #     print(k, v)
    # msg = fp.auto_enroll()
    # msg = fp.read_valid_template_num()
    # print(msg)
    # msg = fp.get_image_ex()
    # print(msg)
    # if msg == 0:
    #     print('generating char file')
    #     msg2 = fp.img2tz(buffer_id=1)
    #     print(msg2)

    # fp.manual_enroll()
    vt = fp.auto_identify()
    print(vt)
    print('end.')
    fp.ser_close()
