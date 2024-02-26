"""
This file is part of IDRB Project.

IDRB Project is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDRB Project is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDRB Project.  If not, see <https://www.gnu.org/licenses/>.
"""
import queue
import time
from datetime import datetime
import cv2
import dearpygui.dearpygui as dpg
import threading
import socket
import requests
import pickle
import pyaudio
import zmq
from pyogg import OpusDecoder
import configparser
import ctypes
import zlib

from utils import *
import appcomponent


class App:
    def __init__(self):
        self.RDS = None
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.device_name_output = self.config["audio"]["device"]
        self.buffersize = 64 # can configable


        self.working = False
        self.readchannel = 1
        self.firstrun = True
        self.firststart = True
        self.device_index_output = 0
        self.ccdecryptpassword = None
        self.ccisencrypt = None
        self.ccisdecrypt = None
        self.ccisdecryptpassword = None
        self.paudio = pyaudio.PyAudio()
        self.cprotocol = None
        self.cciswaitlogoim = True
        self.ccthreadlogorecisworking = False
        self.ccserversecount = 0
        self.lsitem = None
        self.ccconwithpubselect = False
        self.buffer = queue.Queue(maxsize=self.buffersize)
        self.okbuffer = False
        self.firstrunbuffer = True

    def connecttoserverwithpubselect(self, sender, data):
        self.ccconwithpubselect = True
        dpg.configure_item("pubserverselectwindow", show=False)
        dpg.configure_item("connectbuttonpubserverselect", show=False)
        self.connecttoserver(None, None)

    def connecttoserver(self, sender, data):
        dpg.configure_item("connectservergroup", show=False)
        dpg.configure_item("serverstatus", default_value='connecting...', color=(255, 255, 0))
        if self.ccconwithpubselect:
            serverlabel = str(dpg.get_item_configuration(self.lsitem)["label"])
            protocol = serverlabel.split("|")[0].strip()
            ip = serverlabel.split("|")[1].split(":")[0].strip()
            port = serverlabel.split("|")[1].split(":")[1].strip()

            self.ccconwithpubselect = False
        else:
            protocol = dpg.get_value("serverprotocol").strip()
            ip = dpg.get_value("serverip").strip()
            port = dpg.get_value("serverport")

        self.cprotocol = protocol

        if protocol == "TCP":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((ip, port))
            except:
                dpg.configure_item("connectbutton", show=True)
        elif protocol == "ZeroMQ":
            context = zmq.Context()
            s = context.socket(zmq.SUB)
            s.connect(f"tcp://{ip}:{port}")
            s.setsockopt_string(zmq.SUBSCRIBE, "")
        elif protocol == "ZeroMQ (WS)":
            context = zmq.Context()
            s = context.socket(zmq.SUB)
            s.connect(f"ws://{ip}:{port}")
            s.setsockopt_string(zmq.SUBSCRIBE, "")
            self.cprotocol = "ZeroMQ"
        self.working = True

        self.device_index_output = 0
        for i in range(self.paudio.get_device_count()):
            dev = self.paudio.get_device_info_by_index(i)
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
        dpg.configure_item("logostatus", show=False)
        self.firstrun = True
        self.firststart = True
        self.ccdecryptpassword = None
        self.ccisencrypt = None
        self.ccisdecrypt = None
        self.ccisdecryptpassword = None
        self.cciswaitlogoim = True
        self.ccthreadlogorecisworking = False
        self.buffer = queue.Queue(maxsize=self.buffersize)
        self.okbuffer = False
        self.firstrunbuffer = True

    def RDSshow(self):
        try:
            dpg.configure_item("RDSinfo",
                               default_value=f'{self.RDS["PS"]} ({self.RDS["ContentInfo"]["Codec"].upper()} {self.RDS["ContentInfo"]["bitrate"] / 1000}Kbps {self.RDS["AudioMode"]})',
                               show=True)

            dpg.configure_item("RDSPS", default_value="PS: " + self.RDS["PS"])
            dpg.configure_item("RDSRT", default_value="RT: " + limit_string_in_line(self.RDS["RT"], 120))
            dpg.configure_item("RDSCTlocal", default_value="Time Local: " + datetime.fromtimestamp(self.RDS["CT"]["Local"]).strftime('%H:%M:%S'))
            dpg.configure_item("RDSCTUTC", default_value="Time UTC: " + datetime.fromtimestamp(self.RDS["CT"]["UTC"]).strftime('%H:%M:%S'))
            try:
                if self.RDS["images"]["logo"]["lazy"] and not self.ccthreadlogorecisworking:
                    if not self.RDS["images"]["logo"]["contents"] == b'':
                        print(self.RDS["images"]["logo"]["contents"] == b'',
                            self.RDS["images"]["logo"]["part"]["total"] == \
                            self.RDS["images"]["logo"]["part"]["current"],
                            self.RDS["images"]["logo"]["part"]["current"] > 0)
                        self.ccthreadlogorecisworking = True
                        logoreciveprocessingthread = threading.Thread(target=self.RDSlogorecivelazy)
                        logoreciveprocessingthread.start()
                else:
                    if not self.RDS["images"]["logo"]["lazy"]:
                        dpg.set_value("station_logo", CV22DPG(cv2.imdecode(np.frombuffer(self.RDS["images"]["logo"]["contents"], np.uint8), cv2.IMREAD_COLOR)))
                        dpg.configure_item("logostatus", show=False)
            except Exception as e:
                dpg.configure_item("station_logo_config", show=False)
                #print(e)

        except Exception as e:
            pass

    def RDSlogorecivelazy(self):
        try:
            received_data = b""
            received_data_current_past = b""
            received_data_current = b""
            try:
                print(self.RDS["images"]["logo"]["part"]["current"], self.RDS["images"]["logo"]["part"]["total"])
                while not self.RDS["images"]["logo"]["part"]["current"] == self.RDS["images"]["logo"]["part"]["total"]:
                    currentprocess = self.RDS["images"]["logo"]["part"]["current"]
                    totalprocess = self.RDS["images"]["logo"]["part"]["total"]

                    received_data_current = self.RDS["images"]["logo"]["contents"]

                    if received_data_current != received_data_current_past:
                        print(received_data_current)
                        received_data_current_past = received_data_current
                        received_data += received_data_current

                    dpg.configure_item("logostatus", color=(255, 255, 0), default_value=f"Receiving... ({currentprocess}/{totalprocess})")

                dpg.set_value("station_logo", CV22DPG(cv2.imdecode(np.frombuffer(received_data_current, np.uint8), cv2.IMREAD_COLOR)))
                dpg.configure_item("logostatus", color=(0, 255, 0), default_value=f"Received logo! waiting for new image...")
                dpg.configure_item("station_logo_config", show=True)
                self.ccthreadlogorecisworking = False
            except Exception as e:
                print("receive error", e)
                dpg.configure_item("logostatus", color=(255, 0, 0), default_value=f"Receive logo error! waiting for new image...")
                dpg.configure_item("station_logo_config", show=False)
                self.ccthreadlogorecisworking = False

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

        self.device_index_output = 0
        for i in range(self.paudio.get_device_count()):
            dev = self.paudio.get_device_info_by_index(i)
            if dev['name'] == self.device_name_output:
                self.device_index_output = dev['index']
                break

    def submitpassworddecrypt(self, sender, data):
        dpg.configure_item("requestpasswordpopup", show=False)
        self.ccdecryptpassword = dpg.get_value("requestpasswordinputpopup")
        self.ccisdecryptpassword = True

    def changeaudiodevice(self, sender, data):
        self.device_name_output = dpg.get_value(sender)
        self.config["audio"]["device"] = dpg.get_value(sender)
        self.config.write(open('config.ini', 'w'))

    def pubserverselectone(self, sender, data):
        if data == False:
            dpg.configure_item("connectbuttonpubserverselect", show=False)
            return
        else:
            dpg.configure_item("connectbuttonpubserverselect", show=True)

        if self.lsitem == None:
            self.lsitem = sender

        if self.lsitem != sender:
            dpg.set_value(self.lsitem, False)
            self.lsitem = sender

        if dpg.get_item_configuration(self.lsitem)["label"] == "N/A":
            dpg.configure_item("connectbuttonpubserverselect", show=False)


    def pubserverselectsearch(self, serversearch="", limit=10):
        self.lsitem = None
        if serversearch == "":
            dpg.configure_item("pubserverselectstatus", default_value="Please wait...", color=(255, 255, 0))
        else:
            dpg.configure_item("pubserverselectstatus", default_value="Searching...", color=(255, 255, 0))

        if self.ccserversecount != 0:
            # clear list
            for i in range(self.ccserversecount):
                dpg.delete_item(f"pubserverid{i}")

            self.ccserversecount = 0

        if serversearch == "":
            response = requests.get(f"https://thaisdr.damp11113.xyz/api/idrbdir/getallstation?limit={limit}")
        else:
            response = requests.get(f"https://thaisdr.damp11113.xyz/api/idrbdir/getallstation?limit={limit}&serversearch={serversearch}")

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse JSON data
            allstationdata = response.json()

            # Iterate over each station
            for server_id, server_details in allstationdata.items():
                with dpg.table_row(parent="pubserverlist", tag=f"pubserverid{self.ccserversecount}"):
                    if server_details['ServerURL'] == "" or server_details['ServerPort'] == "" or server_details['ServerProtocol'] == "":
                        dpg.add_selectable(label=f"N/A", span_columns=True, disable_popup_close=True, callback=self.pubserverselectone)
                    else:
                        dpg.add_selectable(label=f"{server_details['ServerProtocol']} | {server_details['ServerURL']}:{server_details['ServerPort']}", span_columns=True, disable_popup_close=True, callback=self.pubserverselectone)

                    dpg.add_selectable(label=server_details["ServerName"], span_columns=True, disable_popup_close=True, callback=self.pubserverselectone)
                    dpg.add_selectable(label=server_details["ServerDesc"], span_columns=True, disable_popup_close=True, callback=self.pubserverselectone)
                    dpg.add_selectable(label=server_details["ConnectionUser"], span_columns=True, disable_popup_close=True, callback=self.pubserverselectone)


                self.ccserversecount += 1

        dpg.configure_item("pubserverselectstatus", default_value=f"Founded {self.ccserversecount} server", color=(0, 255, 0))

    def pubserverselectopen(self, sender, data):
        dpg.configure_item("pubserverselectwindow", show=True)
        self.pubserverselectsearch()

    def streambuffer(self, socket):
        consecutive_above_threshold = 0  # Counter to track consecutive iterations above threshold
        tolerance_iterations = 5  # Number of consecutive iterations required above threshold
        while self.working:
            if self.cprotocol == "TCP":
                tempdata = b''
                # data = socket.recv(1580152)
                while True:
                    part = socket.recv(1024)
                    tempdata += part
                    if len(part) < 1024:
                        # either 0 or end of data
                        break
                self.buffer.put(tempdata)
            elif self.cprotocol == "ZeroMQ":
                self.buffer.put(socket.recv())
            else:
                self.buffer.put(b"")

            dpg.configure_item("bufferstatus", default_value=f'Buffer: {self.buffer.qsize()}/{self.buffersize}')

    def stream(self, socket):
        opus_decoder = None
        streamoutput = None
        tfrpx = list(range(250))
        altfrpy = [0] * 250
        adcctfrpy = [0] * 250
        imcctfrpy = [0] * 2500
        bytesconunt = 0
        bytesconunt_frame = 0
        codecbytesconunt = 0
        start_time = time.time()
        evaluation_audio_X = None
        decodecodec = None


        SBT = threading.Thread(target=self.streambuffer, args=(socket,))
        SBT.start()

        while True:
            try:
                if self.working:
                    if self.buffer.not_empty:
                        data = self.buffer.get()
                    else:
                        continue

                    bytesconunt += len(data)


                    if bytesconunt_frame >= 10:
                        stoptime = time.time()
                        speed_kbps = calculate_speed(start_time, stoptime, bytesconunt)
                        dpg.configure_item("serverstatus", default_value=f'connected {int(speed_kbps)}Kbps ({len(data)})', color=(0, 255, 0))

                        codec_kbps = calculate_throughput(start_time, stoptime, codecbytesconunt)

                        dpg.configure_item("codecbitratestatus", default_value=f'{self.RDS["ContentInfo"]["Codec"].upper()} {self.RDS["ContentInfo"]["bitrate"] / 1000}/{codec_kbps:.2f} Kbps')

                        dpg.configure_item("bufferstatus", default_value=f'Buffer: {self.buffer.qsize()}/{self.buffersize}')

                        start_time = time.time()
                        bytesconunt_frame = 0
                        bytesconunt = 0
                        codecbytesconunt = 0

                    if len(altfrpy) > 250:
                        altfrpy.pop(0)
                    altfrpy.append(len(data))
                    dpg.set_value('transferatealldataplot', [tfrpx, altfrpy])

                    if len(data) == 0:
                        dpg.configure_item("serverstatus", default_value='lost connected', color=(255, 0, 0))
                        socket.close()
                        if self.cprotocol == "TCP":
                            socket.close()
                        elif self.cprotocol == "ZeroMQ":
                            try:
                                message = socket.recv(zmq.NOBLOCK)
                                if message is None:
                                    break  # No more messages
                                # Process the received message if needed
                                print(f"Received message: {message.decode()}")
                            except zmq.error.ZMQError as e:
                                if e.errno == zmq.EAGAIN:
                                    break  # No more messages
                                else:
                                    raise
                            socket.close()
                        else:
                            socket.close()
                        self.disconnectserver()
                        break

                    try:
                        decompressed_data = zlib.decompress(data)

                        datadecoded = pickle.loads(decompressed_data)
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
                            dpg.configure_item("ServerNamedisp", default_value="Server: " + str(datadecoded["serverinfo"]["RDS"]["ServerName"]))
                            dpg.configure_item("ServerDescdisp", default_value="Description: " + str(datadecoded["serverinfo"]["RDS"]["ServerDesc"]))

                    except:
                        pass

                    if self.firstrun:
                        decodecodec = datadecoded["channel"][self.readchannel]["RDS"]["ContentInfo"]["Codec"]

                        if decodecodec.upper() == "OPUS":
                            opus_decoder = OpusDecoder()
                            opus_decoder.set_channels(self.RDS["ContentInfo"]["channel"])
                            opus_decoder.set_sampling_frequency(self.RDS["ContentInfo"]["samplerates"])

                        streamoutput = self.paudio.open(format=pyaudio.paInt16, channels=self.RDS["ContentInfo"]["channel"], rate=self.RDS["ContentInfo"]["samplerates"], output=True, output_device_index=self.device_index_output)
                        evaluation_audio_X = np.fft.fftfreq(1024, 1.0 / self.RDS["ContentInfo"]["samplerates"])[:1024 // 2]

                        if len(datadecoded["channel"]) > 1:
                            channel_info = []
                            for i in range(1, len(datadecoded["channel"]) + 1):
                                channel_info.append(f'{i} {"[Encrypt]" if datadecoded["channel"][i]["Encrypt"] else "[No Encrypt]"} {datadecoded["channel"][i]["Station"]} ({datadecoded["channel"][i]["RDS"]["ContentInfo"]["Codec"]} {datadecoded["channel"][i]["RDS"]["ContentInfo"]["bitrate"] / 1000}Kbps {datadecoded["channel"][i]["RDS"]["AudioMode"]})')
                            dpg.configure_item("mediachannelselect", show=True, items=channel_info)

                        dpg.configure_item("morerdsbutton", show=True)
                        dpg.configure_item("serverinfobutton", show=True)
                        dpg.configure_item("logostatus", show=True)

                        try:
                            if self.RDS["images"]["logo"]["lazy"] and not self.ccthreadlogorecisworking:
                                if not self.RDS["images"]["logo"]["contents"] == b'' or \
                                        self.RDS["images"]["logo"]["part"]["total"] == \
                                        self.RDS["images"]["logo"]["part"]["current"] or \
                                        self.RDS["images"]["logo"]["part"]["current"] > 0:
                                    self.ccthreadlogorecisworking = True
                                    logoreciveprocessingthread = threading.Thread(target=self.RDSlogorecivelazy)
                                    logoreciveprocessingthread.start()
                            else:
                                if not self.RDS["images"]["logo"]["lazy"]:
                                    dpg.set_value("station_logo", CV22DPG(
                                        cv2.imdecode(np.frombuffer(self.RDS["images"]["logo"]["contents"], np.uint8),
                                                     cv2.IMREAD_COLOR)))
                                    dpg.configure_item("station_logo_config", show=True)
                                    dpg.configure_item("logostatus", show=False)
                        except:
                            dpg.configure_item("station_logo_config", show=False)
                        dpg.configure_item("disconnectbutton", show=True)
                        dpg.configure_item("RDSPI", default_value=f"PI: {hex(self.RDS['PI'])[2:].upper()}")
                        if self.firststart and len(datadecoded["channel"]) > 1:
                            self.readchannel = datadecoded["mainchannel"]
                            dpg.configure_item("mediachannelselect", show=True, default_value=channel_info[self.readchannel - 1])
                        elif self.firststart:
                            self.readchannel = datadecoded["mainchannel"]
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

                        if len(data) == 0:
                            dpg.configure_item("serverstatus", default_value=f'connected but no audio', color=(255, 0, 0))

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
                            codecbytesconunt += len(data)

                            if decodecodec.upper() == "OPUS":
                                decoded_pcm = opus_decoder.decode(memoryview(bytearray(data)))
                            else: # pcm
                                decoded_pcm = data

                            # Check if the decoded PCM is empty or not
                            if len(decoded_pcm) > 0:
                                pcm_to_write = np.frombuffer(decoded_pcm, dtype=np.int16)

                                streamoutput.write(pcm_to_write.tobytes())

                                audioL = pcm_to_write[::2]
                                audioR = pcm_to_write[1::2]

                                Lnormalized_data = audioL * np.hanning(len(audioL))
                                Lfft_data = np.abs(np.fft.fft(Lnormalized_data))[:1024 // 2]

                                Rnormalized_data = audioR * np.hanning(len(audioR))
                                Rfft_data = np.abs(np.fft.fft(Rnormalized_data))[:1024 // 2]

                                dpg.set_value('audioinfoleftplot', [evaluation_audio_X, Lfft_data])
                                dpg.set_value('audioinforightplot', [evaluation_audio_X, Rfft_data])

                            else:
                                print("Decoded PCM is empty")

                        if len(adcctfrpy) > 250:
                            adcctfrpy.pop(0)
                        adcctfrpy.append(len(datadecoded["channel"][self.readchannel]["Content"]))
                        dpg.set_value('transferateaudiodataoncchannelplot', [tfrpx, adcctfrpy])

                    bytesconunt_frame += 1

                else:
                    SBT.join()
                    streamoutput.close()
                    if self.cprotocol == "TCP":
                        socket.close()
                    elif self.cprotocol == "ZeroMQ":
                        try:
                            message = socket.recv(zmq.NOBLOCK)
                            if message is None:
                                break  # No more messages
                            # Process the received message if needed
                            print(f"Received message: {message.decode()}")
                        except zmq.error.ZMQError as e:
                            if e.errno == zmq.EAGAIN:
                                break  # No more messages
                            else:
                                raise
                        socket.close()
                    else:
                        socket.close()
                    self.disconnectserver()
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
                    if self.cprotocol == "TCP":
                        socket.close()
                    elif self.cprotocol == "ZeroMQ":
                        try:
                            message = socket.recv(zmq.NOBLOCK)
                            if message is None:
                                break  # No more messages
                            # Process the received message if needed
                            print(f"Received message: {message.decode()}")
                        except zmq.error.ZMQError as e:
                            if e.errno == zmq.EAGAIN:
                                break  # No more messages
                            else:
                                raise
                        socket.close()
                    else:
                        socket.close()
                    self.disconnectserver()

                    break

    def init(self):
        if self.config["debug"]["hideconsole"] == "true":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

        ctypes.CDLL("opus.dll")

        dpg.create_context()
        dpg.create_viewport(title=f'IDRB Client v1.6.1 Beta', width=1280, height=720, large_icon="IDRBfavicon.ico", clear_color=(43, 45, 48))  # set viewport window
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
            dpg.add_static_texture(width=512, height=256, default_value=data, tag="app_logo_background")

        with dpg.window(no_background=True, no_title_bar=True, no_move=True, no_resize=True, tag="backgroundviewportlogo"):
            dpg.add_image("app_logo_background")
            dpg.add_text("ThaiSDR Solutions", pos=(230, 230))

        appcomponent.window(self)
        appcomponent.menubar(self)

        num_devices = self.paudio.get_device_count()
        output_devices = []
        for i in range(num_devices):
            device_info = self.paudio.get_device_info_by_index(i)
            if device_info['maxOutputChannels'] > 0:
                output_devices.append(device_info['name'])

        dpg.configure_item("selectaudiooutputdevicecombo", items=output_devices, default_value=self.config["audio"]["device"])

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
        try:
            dpg.fit_axis_data("x_axis")
            dpg.fit_axis_data("y_axis1")
            dpg.fit_axis_data("y_axis2")
            dpg.fit_axis_data("y_axis3")

            dpg.fit_axis_data("x_axis_1")

            dpg.configure_item("backgroundviewportlogo", pos=(dpg.get_viewport_width() - 550, dpg.get_viewport_height() - 300))
        except:
            pass

    def exit(self):
        dpg.destroy_context()



app = App()
app.init()
