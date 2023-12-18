import time
from datetime import datetime
import cv2
import dearpygui.dearpygui as dpg
import threading
import socket
import numpy as np
import pickle
import pyaudio
from pyogg import OpusDecoder
from damp11113 import CV22DPG
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes

librarylist = ["Opencv (opencv.org)", "PyOgg (TeamPyOgg)", "DearPyGui (hoffstadt)"]

def calculate_speed(start_time, end_time, data_size):
    elapsed_time = end_time - start_time
    speed_kbps = (data_size / elapsed_time) / 1024  # Convert bytes to kilobytes
    return speed_kbps

def limit_string_in_line(text, limit):
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        words = line.split()
        new_line = ''

        for word in words:
            if len(new_line) + len(word) <= limit:
                new_line += word + ' '
            else:
                new_lines.append(new_line.strip())
                new_line = word + ' '

        if new_line:
            new_lines.append(new_line.strip())

    return '\n'.join(new_lines)

def unpad_message(padded_message):
    padding_length = padded_message[-1]
    return padded_message[:-padding_length]

def decrypt_data(encrypted_message, password, salt, iv):
    # Derive the key from the password and salt
    key = scrypt(password, salt, key_len=32, N=2 ** 14, r=8, p=1)

    # Initialize AES cipher in CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Decrypt the message
    decrypted_message = cipher.decrypt(encrypted_message)

    # Unpad the decrypted message
    unpadded_message = unpad_message(decrypted_message)

    return unpadded_message

class App:
    def __init__(self):
        self.RDS = None
        self.device_name_output = "Speakers (2- USB Audio DAC   )"
        self.working = False
        self.readchannel = 1
        self.firstrun = True
        self.firststart = True
        self.device_index_output = 0
        self.ccdecryptpassword = None
        self.ccisencrypt = None
        self.ccisdecrypt = None
        self.ccisdecryptpassword = None

    def connecttoserver(self, sender, data):
        dpg.configure_item("connectservergroup", show=False)
        #protocol = dpg.get_value("serverprotocol")
        dpg.configure_item("serverstatus", default_value='connecting...', color=(255, 255, 0))
        ip = dpg.get_value("serverip")
        port = dpg.get_value("serverport")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, port))
        except:
            dpg.configure_item("connectbutton", show=True)
        self.working = True
        p = pyaudio.PyAudio()

        self.device_index_output = 0
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['name'] == self.device_name_output:
                self.device_index_output = dev['index']
                break

        thread = threading.Thread(target=self.stream, args=(s, ))
        thread.start()

    def disconnectserver(self, sender=None, data=None):
        dpg.configure_item("disconnectbutton", show=False)
        dpg.configure_item("serverstatus", default_value='disconnecting...', color=(255, 255, 0))
        self.working = False
        dpg.configure_item("serverinfobutton", show=False)
        dpg.configure_item("mediachannelselect", show=False)
        dpg.configure_item("morerdsbutton", show=False)
        dpg.configure_item("station_logo_config", show=False)
        dpg.configure_item("RDSinfo", show=False)
        dpg.configure_item("disconnectbutton", show=False)
        dpg.configure_item("connectservergroup", show=True)
        dpg.configure_item("serverstatus", default_value='disconnected', color=(255, 0, 0))
        self.firstrun = True
        self.firststart = True
        self.ccdecryptpassword = None
        self.ccisencrypt = None
        self.ccisdecrypt = None
        self.ccisdecryptpassword = None

    def RDSshow(self):
        try:
            dpg.configure_item("RDSinfo",
                               default_value=f'{self.RDS["PS"]} ({self.RDS["ContentInfo"]["Codec"]} {self.RDS["ContentInfo"]["bitrate"] / 1000}Kbps {self.RDS["AudioMode"]})',
                               show=True)
            dpg.configure_item("RDSPS", default_value="PS: " + self.RDS["PS"])
            dpg.configure_item("RDSRT", default_value="RT: " + limit_string_in_line(self.RDS["RT"], 120))
            dpg.configure_item("RDSCTlocal", default_value="Time Local: " + datetime.fromtimestamp(self.RDS["CT"]["Local"]).strftime('%H:%M:%S'))
            dpg.configure_item("RDSCTUTC", default_value="Time UTC: " + datetime.fromtimestamp(self.RDS["CT"]["UTC"]).strftime('%H:%M:%S'))
            try:
                dpg.set_value("station_logo", CV22DPG(
                    cv2.imdecode(np.frombuffer(self.RDS["images"]["logo"], np.uint8),
                                 cv2.IMREAD_COLOR)))
            except:
                dpg.configure_item("station_logo_config", show=False)

        except Exception as e:
            pass

    def changechannel(self, sender, data):
        dpg.configure_item("serverstatus", default_value='please wait...', color=(255, 255, 0))
        dpg.configure_item("station_logo_config", show=False)
        self.readchannel = int(dpg.get_value(sender).split(" ")[0])
        self.firstrun = True
        self.ccdecryptpassword = None
        self.ccisencrypt = None
        self.ccisdecrypt = None
        self.ccisdecryptpassword = None

        p = pyaudio.PyAudio()

        self.device_index_output = 0
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['name'] == self.device_name_output:
                self.device_index_output = dev['index']
                break

    def submitpassworddecrypt(self, sender, data):
        dpg.configure_item("requestpasswordpopup", show=False)
        self.ccdecryptpassword = dpg.get_value("requestpasswordinputpopup")
        self.ccisdecryptpassword = True

    def stream(self, socket):
        opus_decoder = None
        streamoutput = None
        tfrpx = list(range(250))
        altfrpy = [0] * 250
        adcctfrpy = [0] * 250
        imcctfrpy = [0] * 250
        bytesconunt = 0
        bytesconunt_frame = 0
        start_time = time.time()
        while True:
            try:
                if self.working:
                    #data = b''
                    data = socket.recv(1580152)
                    #while True:
                    #    part = socket.recv(1024)
                    #    data += part
                    #    if len(part) < 1024:
                    #        # either 0 or end of data
                    #        break

                    bytesconunt += len(data)

                    if bytesconunt_frame >= 10:
                        speed_kbps = calculate_speed(start_time, time.time(), bytesconunt)
                        dpg.configure_item("serverstatus", default_value=f'connected {int(speed_kbps)}Kbps ({len(data)})', color=(0, 255, 0))
                        start_time = time.time()
                        bytesconunt_frame = 0
                        bytesconunt = 0

                    if len(altfrpy) > 250:
                        altfrpy.pop(0)
                    altfrpy.append(len(data))
                    dpg.set_value('transferatealldataplot', [tfrpx, altfrpy])

                    if len(data) == 0:
                        dpg.configure_item("serverstatus", default_value='lost connected', color=(255, 0, 0))
                        socket.close()
                        self.disconnectserver()
                        break

                    try:
                        datadecoded = pickle.loads(data)
                    except:
                        pass

                    if len(imcctfrpy) > 250:
                        imcctfrpy.pop(0)
                    imcctfrpy.append(len(str(datadecoded["channel"][self.readchannel]["RDS"]["images"])))
                    dpg.set_value('transferateimagesoncchannelplot', [tfrpx, imcctfrpy])

                    try:
                        if datadecoded["channel"][self.readchannel]["RDS"] != self.RDS:
                            self.RDS = datadecoded["channel"][self.readchannel]["RDS"]
                            rdshow = threading.Thread(target=self.RDSshow)
                            rdshow.start()

                            dpg.configure_item("ServerListener", default_value="Listener: " + str(datadecoded["serverinfo"]["Listener"]) + " Users")
                    except:
                        pass

                    if self.firstrun:
                        p = pyaudio.PyAudio()
                        opus_decoder = OpusDecoder()
                        opus_decoder.set_channels(self.RDS["ContentInfo"]["channel"])
                        opus_decoder.set_sampling_frequency(self.RDS["ContentInfo"]["samplerates"])
                        streamoutput = p.open(format=pyaudio.paInt16, channels=self.RDS["ContentInfo"]["channel"], rate=self.RDS["ContentInfo"]["samplerates"], output=True, output_device_index=self.device_index_output)
                        if len(datadecoded["channel"]) > 1:
                            channel_info = []
                            for i in range(1, len(datadecoded["channel"]) + 1):
                                channel_info.append(f'{i} {"[Encrypt]" if datadecoded["channel"][i]["Encrypt"] else "[No Encrypt]"} {datadecoded["channel"][i]["Station"]} ({datadecoded["channel"][i]["RDS"]["ContentInfo"]["Codec"]} {datadecoded["channel"][i]["RDS"]["ContentInfo"]["bitrate"] / 1000}Kbps {datadecoded["channel"][i]["RDS"]["AudioMode"]})')
                            dpg.configure_item("mediachannelselect", show=True, items=channel_info)
                        dpg.configure_item("morerdsbutton", show=True)
                        dpg.configure_item("serverinfobutton", show=True)
                        try:
                            dpg.set_value("station_logo", CV22DPG(cv2.imdecode(np.frombuffer(datadecoded["channel"][self.readchannel]["RDS"]["images"]["logo"], np.uint8), cv2.IMREAD_COLOR)))
                            dpg.configure_item("station_logo_config", show=True)
                        except:
                            dpg.configure_item("station_logo_config", show=False)
                        dpg.configure_item("disconnectbutton", show=True)
                        dpg.configure_item("RDSPI", default_value=f"PI: {hex(self.RDS['PI'])[2:].upper()}")
                        if self.firststart:
                            self.readchannel = datadecoded["mainchannel"]
                            dpg.configure_item("mediachannelselect", show=True, default_value="mainchannel")

                        # check if channel is encrypted
                        if datadecoded["channel"][self.readchannel]["Encrypt"]:
                            dpg.configure_item("requestpasswordpopup", show=True)
                            dpg.configure_item("serverstatus", default_value='connected', color=(0, 255, 0))
                            self.ccisencrypt = True
                        else:
                            dpg.configure_item("serverstatus", default_value='connected --Kbps (----)', color=(0, 255, 0))

                        self.firstrun = False
                        self.firststart = False

                    if not self.firstrun:
                        data = datadecoded["channel"][self.readchannel]["Content"]

                        if self.ccisdecryptpassword and self.ccisencrypt:
                            try:
                                # decrypt data
                                encryptdata = data.split(b'|||||')[0]
                                salt = data.split(b'|||||')[1]
                                iv = data.split(b'|||||')[2]

                                data = decrypt_data(encryptdata, self.ccdecryptpassword, salt, iv)

                                if data == b'':
                                    self.ccisdecrypt = False
                                    self.ccdecryptpassword = None
                                else:
                                    self.ccisdecrypt = True
                            except:
                                dpg.configure_item("serverstatus", default_value="Decrypt Error", color=(255, 0, 0))

                        if self.ccisdecrypt or not self.ccisencrypt:
                            decoded_pcm = opus_decoder.decode(memoryview(bytearray(data)))

                            # Check if the decoded PCM is empty or not
                            if len(decoded_pcm) > 0:
                                pcm_to_write = np.frombuffer(decoded_pcm, dtype=np.int16)

                                streamoutput.write(pcm_to_write.tobytes())
                            else:
                                print("Decoded PCM is empty")

                        if len(adcctfrpy) > 250:
                            adcctfrpy.pop(0)
                        adcctfrpy.append(len(datadecoded["channel"][self.readchannel]["Content"]))
                        dpg.set_value('transferateaudiodataoncchannelplot', [tfrpx, adcctfrpy])

                    bytesconunt_frame += 1
                else:
                    streamoutput.close()
                    socket.close()
                    break
            except Exception as e:
                if str(e) == "An error occurred while decoding an Opus-encoded packet: corrupted stream":
                    dpg.configure_item("serverstatus", default_value="Unable to decode audio data", color=(255, 0, 0))
                else:
                    print("connection lost", e)
                    try:
                        streamoutput.close()
                    except:
                        pass
                    socket.close()
                    self.disconnectserver()
                    raise
                    break

    def window(self):
        with dpg.window(label="IDRB", width=320, height=520, no_close=True):
            dpg.add_button(label="Server info", callback=lambda: dpg.configure_item("Serverinfowindow", show=True), tag="serverinfobutton", show=False)
            dpg.add_button(label="disconnect", callback=self.disconnectserver, tag="disconnectbutton", show=False)
            dpg.add_text("not connect", tag="serverstatus", color=(255, 0, 0))
            dpg.add_combo([], label="Channel", tag="mediachannelselect", default_value="Main Channel", show=False, callback=self.changechannel)
            dpg.add_spacer()
            dpg.add_image("station_logo", show=False, tag="station_logo_config")
            dpg.add_text("", tag="RDSinfo", show=False)
            with dpg.child_window(tag="connectservergroup", label="Server", use_internal_label=True, height=105):
                dpg.add_button(label="select server", tag="selectserverbutton")
                dpg.add_input_text(label="server ip", tag="serverip", default_value="localhost")
                dpg.add_input_int(label="port", tag="serverport", max_value=65535, default_value=6980)
                #dpg.add_combo(["TCP", "Websocket"], label="protocol", tag="serverprotocol", default_value="TCP")
                dpg.add_button(label="connect", callback=self.connecttoserver, tag="connectbutton")
            dpg.add_spacer()
            dpg.add_button(label="More RDS info", callback=lambda: dpg.configure_item("RDSwindow", show=True), tag="morerdsbutton", show=False)

        with dpg.window(label="IDRB RDS Info", tag="RDSwindow", show=False, width=250):
            with dpg.tab_bar():
                with dpg.tab(label="Program"):
                    with dpg.child_window(label="Basic", use_internal_label=True, height=100):
                        dpg.add_text("PS: ...", tag="RDSPS")
                        dpg.add_text("PI: ...", tag="RDSPI")
                        dpg.add_text("RT: ...", tag="RDSRT")

                    dpg.add_text("Time Local: ...", tag="RDSCTlocal")
                    dpg.add_text("Time UTC: ...", tag="RDSCTUTC")
                with dpg.tab(label="EPG"):
                    pass
                with dpg.tab(label="Images"):
                    pass
                with dpg.tab(label="AS"):
                    pass
                with dpg.tab(label="EOM"):
                    pass

        with dpg.window(label="IDRB Server Info", tag="Serverinfowindow", show=False):
            dpg.add_text("Listener: ...", tag="ServerListener")
            dpg.add_spacer()
            #dpg.add_simple_plot(label="Transfer Rates", autosize=True, height=250, width=500, tag="transferateplot")


            with dpg.plot(label="Transfer Rates", height=250, width=500):
                # optionally create legend
                dpg.add_plot_legend()

                # REQUIRED: create x and y axes
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="x_axis", no_gridlines=True)
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis1", no_gridlines=True)
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis2", no_gridlines=True)
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis3", no_gridlines=True)

                # series belong to a y axis
                dpg.add_line_series([], [], label="All Data", parent="y_axis1", tag="transferatealldataplot")
                dpg.add_line_series([], [], label="Audio Data", parent="y_axis2", tag="transferateaudiodataoncchannelplot")
                dpg.add_line_series([], [], label="Images Data", parent="y_axis3", tag="transferateimagesoncchannelplot")

        with dpg.window(label="IDRB About", tag="aboutwindow", show=False, no_resize=True):
            dpg.add_image("app_logo")
            dpg.add_spacer()
            dpg.add_text("IDRB (Internet Digital Radio Broadcasting System) Client")
            dpg.add_spacer()
            dpg.add_text(f"IDRB Client v1.2 Beta")
            dpg.add_spacer()

            desc = "IDRB is a novel internet radio broadcasting alternative that uses HLS/DASH/HTTP streams, transferring over TCP/IP. This system supports images and RDS (Dynamic update) capabilities, enabling the transmission of station information. Additionally, it allows for setting station logos and images. IDRB offers multi-broadcasting functionalities and currently supports the Opus codec, with plans to incorporate PCM, MP2/3, AAC/AAC+, and more in the future, ensuring low delay. If you find this project intriguing, you can support it at damp11113.xyz/support."

            dpg.add_text(limit_string_in_line(desc, 75))

            dpg.add_spacer()
            with dpg.table(header_row=True):

                # use add_table_column to add columns to the table,
                # table columns use slot 0
                dpg.add_table_column(label="Libraries")

                # add_table_next_column will jump to the next row
                # once it reaches the end of the columns
                # table next column use slot 1
                for i in librarylist:
                    with dpg.table_row():
                        dpg.add_text(i)

            dpg.add_spacer(height=20)
            dpg.add_text(f"Copyright (C) 2023 ThaiSDR All rights reserved. (GPLv3)")

        with dpg.window(label="Password Required", tag="requestpasswordpopup", modal=True, no_resize=True, no_close=True, no_move=True, show=False):
            dpg.add_text("This channel is encrypt! Please enter password for decrypt.")
            dpg.add_spacer()
            dpg.add_input_text(label="password", tag="requestpasswordinputpopup")
            dpg.add_spacer()
            dpg.add_button(label="confirm", callback=self.submitpassworddecrypt)

    def menubar(self):
        with dpg.viewport_menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Exit", callback=lambda: self.exit())
            with dpg.menu(label="Settings"):
                dpg.add_menu_item(label="StyleEditor", callback=dpg.show_style_editor)
            with dpg.menu(label="Help"):
                dpg.add_menu_item(label="About", callback=lambda: dpg.configure_item("aboutwindow", show=True))

    def init(self):
        dpg.create_context()
        dpg.create_viewport(title=f'IDRB Client V1.2 Beta', width=1280, height=720, large_icon="IDRBfavicon.ico")  # set viewport window
        dpg.setup_dearpygui()
        # -------------- add code here --------------
        noimage_texture_data = []
        for i in range(0, 128 * 128):
            noimage_texture_data.append(20 / 255)
            noimage_texture_data.append(0)
            noimage_texture_data.append(20 / 255)
            noimage_texture_data.append(20 / 255)

        with dpg.texture_registry():
            dpg.add_raw_texture(128, 128, noimage_texture_data, tag="station_logo", format=dpg.mvFormat_Float_rgb)
            width, height, channels, data = dpg.load_image("IDRBlogo.png")

            dpg.add_static_texture(width=512, height=256, default_value=data, tag="app_logo")

        self.window()
        self.menubar()
        # -------------------------------------------
        dpg.show_viewport()
        # Start a separate thread for a task
        self.thread_stop_event = threading.Event()

        while dpg.is_dearpygui_running():
            self.render()
            dpg.render_dearpygui_frame()

        # Signal the thread to stop and wait for it to finish
        self.thread_stop_event.set()
        dpg.destroy_context()

    def render(self):
        # insert here any code you would like to run in the render loop
        # you can manually stop by using stop_dearpygui() or self.exit()
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis1")
        dpg.fit_axis_data("y_axis2")
        dpg.fit_axis_data("y_axis3")

    def exit(self):
        dpg.destroy_context()


app = App()
app.init()