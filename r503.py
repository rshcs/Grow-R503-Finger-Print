import serial
from time import sleep, time
from struct import pack, unpack
import sys
import json


class R503:
    header = pack('>H', 0xEF01)
    pid_cmd = 0x01  # pid_command packet
    
    def __init__(self, port=8, baud=57600, pw=0, addr=0xFFFFFFFF, timeout=1, recv_size=128):
        self.pw = pack('>I', pw)
        self.addr = pack('>I', addr)
        self.recv_size = recv_size
        try:
            self.ser = serial.Serial(f'COM{port}', baudrate=baud, timeout=timeout)
        except serial.serialutil.SerialException:
            sys.exit('Serial port not found !')

    def conf_codes(self):
        """
        Read confirmation codes from the json file
        returns: json object
        """
        with open('confirmation_codes.json', 'r') as jf:
            jsob = json.load(jf)
        return jsob

    def ser_close(self):
        """
        Close the serial port
        """
        self.ser.close()

    def set_pw(self, new_pw):
        """
        Set modules handshaking password
        parameters: (int) new_pw - New password
        returns: (int) confirmation code
        """
        self.pw = pack('>I', new_pw)
        recv_data = self.ser_send(pid=0x01, pkg_len=0x07, instr_code=0x12, pkg=self.pw)
        return recv_data[4]

    def set_address(self, new_addr):
        """
        Set module address
        *Set the new address when setting the class object next time*
        parameter: (int) new_addr
        returns: (int) confirmation code => 0 [success], 1, 24, 99
        """
        self.addr = pack('>I', new_addr)
        recv_data = self.ser_send(pid=0x01, pkg_len=0x07, instr_code=0x15, pkg=self.addr)
        return recv_data[4]

    def read_msg(self, data_stream):
        """
        Unpack byte stream to readable data
        returns: (tuple) header, address, package id, package len, confirmation code, package, checksum
        """
        hdr_rd, adr_rd, pkg_id_rd, pkg_len_rd, conf_code_rd = unpack('>HIBHB', data_stream[:10])
        pkg = data_stream[10:len(data_stream)-2]
        chksum_rd = unpack('>H', data_stream[-2:])
        return hdr_rd, adr_rd, pkg_id_rd, pkg_len_rd, conf_code_rd, None if pkg == b'' else pkg, sum(chksum_rd)

    def cancel(self):
        """
        Cancel instruction
        returns: (int) confirmation code
        """
        recv_data = self.ser_send(pid=0x01, pkg_len=3, instr_code=0x30)
        return recv_data[4]

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
        return rd[4]

    def set_sys_para(self, parameter, content):
        """
        Set system parameters: baud rate or security level or packet content length
        **Set baud parameter accordingly when creating the class object next time if you changed the baud rate here**
        parameters: parameter: (str) 'baud' or 'security' or 'pkt_len'
                    content: (int) if parameter == 'baud' then content => 9600, 19200, 38400, 57600[default], 115200
                       if parameter == 'security' then content => 1, 2, 3, 4, 5
                       if parameter == 'pkt_len' then content => 32, 64, 128, 256
        returns: 0(success), 1, 26, 24 or -1
        """
        if parameter == 'baud':
            parameter = 4
            content0 = int(content / 9600)
            if content0 not in [1, 2, 4, 6, 12]:
                return -1
        elif parameter == 'security':
            parameter = 5
            content0 = content
            if content0 not in [1, 2, 3, 4, 5]:
                return -1
        elif parameter == 'pkt_len':
            parameter = 6
            content0 = {32: 0, 64: 1, 128: 2, 256: 3}.get(content)
            if content0 not in [0, 1, 2, 3]:
                return -1
        else:
            return -1
        recv_data = self.ser_send(pid=0x01, pkg_len=0x05, instr_code=0x0E, pkg=pack('>BB', parameter, content0))
        status = recv_data[4]
        if not status:
            if parameter == 4:
                self.ser.baudrate = content
            elif parameter == 6:
                self.recv_size = content
        return status

    def read_sys_para(self):
        """
        Status register and other basic configuration parameters
        returns: (list) status_reg, sys_id_code, finger_lib_size, security_lvl, device_addr, data_packet_size, baud_rate
        """
        read_pkg = self.ser_send(pkg_len=0x03, instr_code=0x0F)
        return 99 if read_pkg[4] == 99 else unpack('>HHHHIHH', read_pkg[5])

    def read_sys_para_decode(self):
        """
        Get decoded system parameters in more human-readable way
        returns: (dictionary) system parameters
        """
        rsp = self.read_sys_para()
        if rsp == 99:
            return 99
        return {
            'system_busy': bool(rsp[0] & 1),
            'matching_finger_found': bool(rsp[0] & 2),
            'pw_verified': bool(rsp[0] & 4),
            'valid_image_in_buffer': bool(rsp[0] & 8),
            'system_id_code': rsp[1],
            'finger_library_size': rsp[2],
            'security_level': rsp[3],
            'device_address': hex(rsp[4]),
            'data_packet_size': {0: 32, 1: 64, 2: 128, 3: 256}[rsp[5]],
            'baud_rate': rsp[6] * 9600,
        }

    def verify_pw(self, pw=0x00):
        """
        Verify modules handshaking password
        returns: (int) confirmation code
        """
        recv_data = self.ser_send(pkg_len=0x07, instr_code=0x13, pkg=pack('>I', pw))
        return recv_data[4]

    def handshake(self):
        """
        Send handshake instructions to the module, Confirmation code 0 receives if the sensor is normal
        returns: (int) confirmation code
        """
        recv_data = self.ser_send(pkg_len=0x03, instr_code=0x40)
        return recv_data[4]

    def check_sensor(self):
        """
        Check whether the sensor is normal
        returns: (int) confirmation code
        """
        recv_data = self.ser_send(pkg_len=0x03, instr_code=0x36)
        return recv_data[4]

    def confirmation_decode(self, c_code):
        """
        Decode confirmation code to understandable string
        parameter: (int) c_code - confirmation code
        returns: (str) decoded confirmation code
        """
        cc = self.conf_codes()
        c_code = str(c_code)
        return cc[c_code] if c_code in cc else 'others: system reserved'

    def load_char(self, page_id, buffer_id=1):
        """
        Load template ath the specified location of flash library to template buffer
        parameters: page_id => (int) page number
                    buffer id => (int) character buffer id
        """
        pkg = pack('>BH', buffer_id, page_id)
        recv_data = self.ser_send(pid=0x01, pkg_len=0x06, instr_code=0x07, pkg=pkg)
        return recv_data[4]

    def up_image(self, timeout=5, raw=False):
        """
        Upload the image in Img_Buffer to upper computer
        every image contains the data around 20kilo bytes
        parameter: (int) timeout: timeout could vary if you change the baud rate, for 57600baud 5seconds is sufficient
        If you use a lower baud rate timeout may have to be increased.
        returns: (bytesarray) if raw == True
                 else (list of lists)
        In raw mode returns the data with all headers (address byte, status bytes etc.)
        raw == False mode only returns the image data [all other header bytes are filtered out]
        """
        send_values = pack('>BHB', 0x01, 0x03, 0x0A)
        check_sum = sum(send_values)
        send_values = self.header + self.addr + send_values + pack('>H', check_sum)
        self.ser.write(send_values)
        self.ser.timeout = timeout
        read_val = self.ser.read(22000)
        if read_val == b'':
            return -1
        if read_val[9]:
            return read_val[9]
        return read_val if raw else [img_data[3:] for img_data in read_val.split(sep=self.header + self.addr)][2:]

    def down_image(self, img_data):
        """
        Download image from the upper computer to the image buffer
        parameters: img_data (list of lists) image data as a list of lists
        returns: confirmation code
        """
        recv_data0 = self.ser_send(pid=0x01, pkg_len=0x03, instr_code=0x0B)
        if not recv_data0[4]:
            return recv_data0[4]
        for img_pkt in img_data[:-1]:
            pkt_len = len(img_pkt) + 2
            recv_data = self.ser_send(pid=0x02, pkg_len=pkt_len, pkg=img_pkt)
            if recv_data[4]:
                return recv_data[4]
        pkt_len = len(img_data[-1]) + 2
        return self.ser_send(pid=0x02, pkg_len=pkt_len, pkg=img_data[-1])[4]

    def up_char(self, timeout=5, raw=False):
        """
        Upload the data in template buffer to the upper computer
        parameter: (int) timeout: timeout could vary if you change the baud rate, for 57600baud 5seconds is sufficient
        If you use a lower baud rate timeout may have to be increased.
        returns: (bytearray) if raw == True
                 else (list of lists)
        In raw mode returns the data with all headers (address byte, status bytes etc.)
        raw == False mode only returns the image data [all other header bytes are filtered out]
        """
        send_values = pack('>BHBB', 0x01, 0x04, 0x08, 0x01)
        check_sum = sum(send_values)
        send_values = self.header + self.addr + send_values + pack('>H', check_sum)
        self.ser.write(send_values)
        self.ser.timeout = timeout
        read_val = self.ser.read(22000)
        if read_val == b'':
            return -1
        if read_val[9]:
            return read_val[9]
        return read_val if raw else [img_data[3:] for img_data in read_val.split(sep=self.header + self.addr)][2:]

    def down_char(self, img_data, buffer_id=1):
        """
        Download a template from the upper computer to modular buffer
        returns: (int) confirmation code
        """
        recv_data0 = self.ser_send(pid=0x01, pkg_len=0x04, instr_code=0x09, pkg=pack('>B', buffer_id))
        if not recv_data0[4]:
            return recv_data0[4]
        for img_pkt in img_data[:-1]:
            pkt_len = len(img_pkt) + 2
            recv_data = self.ser_send(pid=0x02, pkg_len=pkt_len, pkg=img_pkt)
            if recv_data[4]:
                return recv_data[4]
        pkt_len = len(img_data[-1]) + 2
        return self.ser_send(pid=0x02, pkg_len=pkt_len, pkg=img_data[-1])[4]

    def read_info_page(self):
        """
        Read the information page
        returns: (int) confirmation code or (bytearray) info page contents
        """
        send_values = pack('>BHB', 0x01, 0x03, 0x16)
        send_values = self.header + self.addr + send_values + pack('>H', sum(send_values))
        self.ser.write(send_values)
        read_val = self.ser.read(580)
        return 99 if read_val == b'' else read_val[9] or read_val[21:-2]

    def get_img(self):
        """
        Detect a finger and store it in image_buffer
        returns: (int) confirmation code
        """
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x01)
        return read_conf_code[4]

    def get_image_ex(self):
        """
        Detect a finger and store it in image_buffer return 0x07 if image poor quality
        returns: (int) confirmation code
        """
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x28)
        return read_conf_code[4]

    def img2tz(self, buffer_id):
        """
        Generate character file from the original image in Image Buffer and store the file in CharBuffer 1 or 2
        parameter: (int) buffer_id, 1 or 2
        returns: (int) confirmation code
        """
        read_conf_code = self.ser_send(pkg_len=0x04, instr_code=0x02, pkg=pack('>B', buffer_id))
        return read_conf_code[4]

    def reg_model(self):
        """
        Combine info of character files in CharBuffer 1 and 2 and generate a template which is stored back in both
        CharBuffer 1 and 2
        input parameters: None
        returns: (int) confirmation code
        """
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x05)
        return read_conf_code[4]

    def store(self, buffer_id, page_id, timeout=2):
        """
        Store the template of buffer1 or buffer2 on the flash library
        """
        package = pack('>BH', buffer_id, page_id)
        read_conf_code = self.ser_send(pkg_len=0x06, instr_code=0x06, pkg=package, timeout=timeout)
        return read_conf_code[4]

    def manual_enroll(self, location, buffer_id=1, timeout=10, num_of_fps=4, loop_delay=.3):
        """
        Manually enroll a new fingerprint.

        Args:
            location: The memory location to store the fingerprint.
            buffer_id: The buffer id to store intermediate data. Default 1.
            timeout: The timeout in seconds. Default 10.
            num_of_fps: The number of fingerprints to capture. Default 4.
            loop_delay: The delay between capture attempts in seconds. Default 0.3.

        This function will:
            - Prompt the user to place their finger on the sensor and capture fingerprints.
            - Generate character files from the fingerprints.
            - Register a fingerprint model once num_of_fps prints are captured.
            - Store the fingerprint model in the specified memory location.
            - Timeout after timeout seconds if fingerprints are not captured.
        """
        inc = 1
        printed = False
        t1 = time()
        finger_prints = 0
        while True:
            if not printed:
                print(f'Place your finger on the sensor: {inc}')
                printed = True
            if not self.get_image_ex():
                print('Reading the finger print')
                if not self.img2tz(buffer_id=inc):
                    print('Character file generation successful.')
                    finger_prints += 1
                else:
                    print('Character file generation failed !')
                    inc -= 1
                if finger_prints >= num_of_fps:
                    print('registering a finger print')
                    if not self.reg_model():
                        if not self.store(buffer_id=buffer_id, page_id=location):
                            print('finger print registered successfully.')
                        else:
                            print('finger print register failed !')
                        break
                inc += 1
                t1 = time()
                printed = False
            sleep(loop_delay)
            if time() - t1 > timeout:
                print('Timeout')
                break

    def delete_char(self, page_num, num_of_temps_to_del=1):
        """
        Delete stored fingerprint templates.

        Args:
            page_num: The page number to delete templates from.
            num_of_temps_to_del: The number of templates to delete. Default is 1.

        Returns:
            Confirmation code integer.

        This function will:
            - Pack the page number and number of templates to delete into a packet.
            - Send the delete instruction packet to the sensor.
            - Return the confirmation code response from the sensor.
        """
        package = pack('>HH', page_num, num_of_temps_to_del)
        recv_code = self.ser_send(pid=0x01, pkg_len=0x07, instr_code=0x0C, pkg=package)
        return recv_code[4]

    def match(self):
        """
        Compare the recently extracted character with the templates in the ModelBuffer, providing matching result.
        returns: (tuple) status: [0: matching, 1: error, 8: not matching], match score
        """
        rec_data = self.ser_send(pid=0x01, pkg_len=0x03, instr_code=0x03)
        return rec_data[4], rec_data[5]

    def search(self, buff_num=1, start_id=0, para=200):
        """
        Search the whole finger library for the template that matches the one in CharBuffer 1 or 2
        parameters: buff_num = character buffer id, start_id = starting from, para = end position
        returns: (tuple) status [success:0, error:1, no match:9], template number, match score
        """
        self.get_image_ex()
        self.img2tz(1)
        package = pack('>BHH', buff_num, start_id, para)
        recv_data = self.ser_send(pid=0x01, pkg_len=0x08, instr_code=0x04, pkg=package)
        if recv_data[4] == 99:
            return 99
        temp_num, match_score = unpack('>HH', recv_data[5])
        return recv_data[4], temp_num, match_score

    def empty_finger_lib(self):
        """
        Empty all stored fingerprints.

        This function will:
            - Send the empty library instruction to the sensor.
            - Return the confirmation code response.

        Returns:
            Confirmation code integer.
        """
        read_conf_code = self.ser_send(pkg_len=0x03, instr_code=0x0d)
        return read_conf_code[4]

    def read_valid_template_num(self):
        read_pkg = self.ser_send(pkg_len=0x03, instr_code=0x1d)
        return unpack('>H', read_pkg[5])[0]

    def read_index_table(self, index_page=0):
        """
        Read the fingerprint template index table
        parameters: (int) index_page = 0/1/2/3
        returns: (list) index which fingerprints saved already
        """
        index_page = pack('>B', index_page)
        temp = self.ser_send(pkg_len=0x04, instr_code=0x1f, pkg=index_page)
        if temp[4] == 99:
            return 99
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
        return read_pkg[4]

    def auto_identify(self, security_lvl=3, start_pos=0, end_pos=199, ret_key_step=0, num_of_fp_errors=1):
        """
        Search and verify a fingerprint
        return: (tuple) fp store location, match score
        """
        package = pack('>BBBBB', security_lvl, start_pos, end_pos, ret_key_step, num_of_fp_errors)
        read_pkg = self.ser_send(pkg_len=0x08, instr_code=0x32, pkg=package, timeout=10)
        if read_pkg[4] == 99:
            return 99
        _, position, match_score = unpack('>BHH', read_pkg[5])
        return position, match_score

    def read_prod_info(self):
        info = self.ser_send(pkg_len=0x03, instr_code=0x3c)
        if info[4] == 99:
            return 99
        info = info[5]
        return info[:16], info[16:20], info[20:28], info[28:30], info[30:38], info[38:40], info[40:42], info[42:44], info[44:46]

    def read_prod_info_decode(self):
        inf = self.read_prod_info()
        if inf == 99:
            return 99
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

    def get_fw_ver(self):
        recv_data = self.ser_send(pid=0x01, pkg_len=3, instr_code=0x3A)
        return (recv_data[4], recv_data[5])

    def get_alg_ver(self):
        recv_data = self.ser_send(pid=0x01, pkg_len=3, instr_code=0x39)
        return (recv_data[4], recv_data[5])

    def soft_reset(self):
        recv_data = self.ser_send(pid=0x01, pkg_len=3, instr_code=0x3D)
        return recv_data[4]

    def get_random_code(self):
        """
        Generates a random number
        returns: (unsigned 4 bytes integer)
        """
        read_pkg = self.ser_send(pkg_len=0x03, pid=0x01, instr_code=0x14)
        return unpack('>I', read_pkg[5])[0]

    def get_available_location(self, index_page=0):
        """
        Provides next available location in fingerprint library
        parameters: (int) index_page
        Returns: (int) next available location
        """
        return min(set(range(200)).difference(self.read_index_table(index_page)), default=None)

    def write_notepad(self, page_no, content):
        """
        Write data to the specific flash pages: 0 to 15, each page contains 32bytes of data, any data type is given to
        the content will be converted to the string data type before writing to the notepad.
        parameters:
            page_no: (int) 1 - 15, page number
            content: (any) data to write to the flash
        returns: (int) status code => 0 - success, 1 - error when receiving pkg, 18 - error when write flash,
        """
        content = str(content)
        len_content = len(content)
        if len_content > 32 or page_no > 0x0F or page_no < 0:
            return 101
        pkg = pack('>B32s', page_no, content.encode())
        recv_data = self.ser_send(pid=0x01, pkg_len=0x24, instr_code=0x18, pkg=pkg)
        return recv_data[4]

    def read_notepad(self, page_no):
        """
        Read the specific page of the flash memory
        returns: (int) status code, (bytearray) data in the page
        """
        if page_no > 0x0F or page_no < 0:
            return -1
        recv_data = self.ser_send(pid=0x01, pkg_len=0x04, instr_code=0x19, pkg=pack('>B', page_no))
        return recv_data[4], recv_data[5]

    def ser_send(self, pkg_len, instr_code, pid=pid_cmd, pkg=None, timeout=1):
        """
        pid, pkg_len, instr_code, pkg
        """
        send_values = pack('>BHB', pid, pkg_len, instr_code)
        if pkg is not None:
            send_values += pkg
        check_sum = sum(send_values)
        send_values = self.header + self.addr + send_values + pack('>H', check_sum)
        self.ser.timeout = timeout
        self.ser.write(send_values)
        read_val = self.ser.read(self.recv_size)
        return [0, 0, 0, 0, 99, None, 0] if read_val == b'' else self.read_msg(read_val)


if __name__ == '__main__':
    fp = R503()

    # msg = fp.read_valid_template_num()
    # print(msg)
    # msg = fp.get_image_ex()
    # print(msg)
    # if msg == 0:
    #     print('generating char file')
    #     msg2 = fp.img2tz(buffer_id=1)
    #     print(msg2)

    # loc = fp.get_available_location()
    # print(loc)
    # fp.manual_enroll(location=loc)
    # sleep(3)
    # vt = fp.search()
    # print(vt)
    # indx_table = fp.read_index_table()
    # print(indx_table)

    # x = fp.get_image_ex()
    # print(f'image captured: {x}')
    # y = fp.up_image()
    # print(y)
    # print('Put the finger on the sensor...')
    # sleep(3)
    # fp_get = fp.get_image_ex()
    # print('error' if fp_get else 'success')
    # x = fp.up_image()
    # print(len(x))
    # for y in x:
    #     print(y)
    # print('reading completed')
    # y = fp.down_image(x)
    # print(y)
    print(fp.read_prod_info_decode())
    # print(fp.verify_pw())
    print('end.')
    fp.ser_close()
