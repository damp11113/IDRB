import asyncio
from datetime import datetime
import dearpygui.dearpygui as dpg
import threading
import socket
import numpy as np
import pickle
import pyaudio
import websockets
from pyogg import OpusDecoder

class App:
    def __init__(self):
        self.RDS = None
        self.device_name_output = "Speakers (4- USB Audio DAC   )"
        self.working = False

    def connecttoserver(self, sender, data):
        dpg.configure_item("connectbutton", show=False)
        protocol = dpg.get_value("serverprotocol")
        dpg.configure_item("serverstatus", default_value='connecting...', color=(255, 255, 0))
        if protocol == "Websocket":
            asyncio.create_task(self.WSstream())
            return

        ip = dpg.get_value("serverip")
        port = dpg.get_value("serverport")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, port))
        except:
            dpg.configure_item("connectbutton", show=True)
        self.working = True
        p = pyaudio.PyAudio()

        device_index_output = 0
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['name'] == self.device_name_output:
                device_index_output = dev['index']
                break

        thread = threading.Thread(target=self.stream, args=(s, device_index_output))
        thread.start()

    def disconnectserver(self, sender, data):
        dpg.configure_item("disconnectbutton", show=False)
        dpg.configure_item("serverstatus", default_value='disconnecting...', color=(255, 255, 0))
        self.working = False

    def RDSshow(self):
        try:
            dpg.configure_item("RDSinfo",
                               default_value=f'{self.RDS["PS"]} ({self.RDS["ContentInfo"]["Codec"]} {self.RDS["ContentInfo"]["bitrate"] / 1000}Kbps {self.RDS["AudioMode"]})',
                               show=True)
            dpg.configure_item("RDSPS", default_value="PS: " + self.RDS["PS"])
            dpg.configure_item("RDSRT", default_value="RT: " + self.RDS["RT"])
            dpg.configure_item("RDSCTlocal", default_value="Time Local: " + datetime.fromtimestamp(self.RDS["CT"]["Local"]).strftime('%H:%M:%S'))
            dpg.configure_item("RDSCTUTC", default_value="Time UTC: " + datetime.fromtimestamp(self.RDS["CT"]["UTC"]).strftime('%H:%M:%S'))
            dpg.configure_item("RDSListener", default_value="Listener: " + str(self.RDS["Listener"]) + " Users")

        except Exception as e:
            pass

    def stream(self, socket, deviceindex):
        opus_decoder = OpusDecoder()
        streamoutput = None
        firstrun = True
        while True:
            try:
                if self.working:
                    data = socket.recv(650000)

                    if len(data) == 0:
                        dpg.configure_item("serverstatus", default_value='lost connected', color=(255, 0, 0))
                        socket.close()
                        dpg.configure_item("showRDS", show=False)
                        dpg.configure_item("RDSinfo", show=False)
                        dpg.configure_item("disconnectbutton", show=False)
                        dpg.configure_item("connectbutton", show=True)
                        break

                    try:
                        datadecoded = pickle.loads(data)
                    except:
                        pass

                    if datadecoded["RDS"] != self.RDS:
                        self.RDS = datadecoded["RDS"]
                        rdshow = threading.Thread(target=self.RDSshow)
                        rdshow.start()

                    if firstrun:
                        p = pyaudio.PyAudio()
                        opus_decoder.set_channels(self.RDS["ContentInfo"]["channel"])
                        opus_decoder.set_sampling_frequency(self.RDS["ContentInfo"]["samplerates"])
                        streamoutput = p.open(format=pyaudio.paInt16, channels=self.RDS["ContentInfo"]["channel"], rate=self.RDS["ContentInfo"]["samplerates"], output=True, output_device_index=deviceindex)
                        dpg.configure_item("showRDS", show=True)
                        dpg.configure_item("serverstatus", default_value='connected', color=(0, 255, 0))
                        dpg.configure_item("disconnectbutton", show=True)
                        firstrun = False

                    decoded_pcm = opus_decoder.decode(memoryview(bytearray(datadecoded["Content"])))

                    # Check if the decoded PCM is empty or not
                    if len(decoded_pcm) > 0:
                        pcm_to_write = np.frombuffer(decoded_pcm, dtype=np.int16)

                        streamoutput.write(pcm_to_write.tobytes())
                    else:
                        print("Decoded PCM is empty")
                else:
                    streamoutput.close()
                    socket.close()
                    self.working = False
                    dpg.configure_item("showRDS", show=False)
                    dpg.configure_item("RDSinfo", show=False)
                    dpg.configure_item("connectbutton", show=True)
                    dpg.configure_item("serverstatus", default_value='disconnected', color=(255, 0, 0))
                    break
            except Exception as e:
                if str(e) == "An error occurred while decoding an Opus-encoded packet: corrupted stream":
                    dpg.configure_item("serverstatus", default_value="Unable to decode audio data", color=(255, 0, 0))
                else:
                    print("connection lost", e)
                    self.working = False
                    streamoutput.close()
                    socket.close()
                    dpg.configure_item("showRDS", show=False)
                    dpg.configure_item("RDSinfo", show=False)
                    dpg.configure_item("connectbutton", show=True)
                    dpg.configure_item("serverstatus", default_value='disconnected', color=(255, 0, 0))
                    break

    def window(self):
        with dpg.window(label="IDRB", width=320):
            dpg.add_text("", tag="RDSinfo", show=False)
            dpg.add_input_text(label="server ip", tag="serverip", default_value="localhost")
            dpg.add_input_int(label="port", tag="serverport", max_value=65535, default_value=6980)
            dpg.add_combo(["TCP", "Websocket"], label="protocol", tag="serverprotocol", default_value="TCP")
            dpg.add_button(label="connect", callback=self.connecttoserver, tag="connectbutton")
            dpg.add_button(label="disconnect", callback=self.disconnectserver, tag="disconnectbutton", show=False)
            dpg.add_spacer()
            dpg.add_text("not connect", tag="serverstatus", color=(255, 0, 0))
            dpg.add_spacer()
            with dpg.collapsing_header(label="RDS", show=False, tag="showRDS"):
                dpg.add_text("PS: ...", tag="RDSPS")
                dpg.add_text("RT: ...", tag="RDSRT")
                dpg.add_text("Listener: ...", tag="RDSListener")
                dpg.add_text("Time Local: ...", tag="RDSCTlocal")
                dpg.add_text("Time UTC: ...", tag="RDSCTUTC")



    def init(self):
        dpg.create_context()
        dpg.create_viewport(title='[ThaiSDR] IDRB (Internet Digital Radio Broadcasting) V1 Beta', width=1280, height=720, small_icon="favicon.ico")  # set viewport window
        dpg.setup_dearpygui()
        # -------------- add code here --------------
        self.window()
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
        pass

    def exit(self):
        dpg.destroy_context()


app = App()
app.init()
