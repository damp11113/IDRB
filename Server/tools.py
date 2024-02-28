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
import socket
import time
from pyogg import OpusBufferedEncoder
import numpy as np
import pyaudio
import wave
import threading
from damp11113.randoms import rannum

class AudioEncoder:
    def __init__(self, RDS: dict, option: dict, queuebuffer, audioinputtype="device", audiocodec="opus", standalone=False):
        self.audiocodec = audiocodec.upper()
        self.audioinput = audioinputtype.upper()
        self.RDS = RDS
        self.option = option
        self.buffer = queuebuffer

        self.running = False
        self.encoder = None
        self.standalone = standalone

        self.runningthread = threading.Thread(target=self._running)
        self.sourceinput = None

        self._temp_ip = None
        self._temp_port = None

        self._temp_socket = None

    def _createencoder(self):
        self.RDS.update({
            "ContentInfo": {
                "Codec": self.audiocodec,
                "bitrate": self.option.get("Bitrates", 64000),
                "channel": self.option.get("Channel", 2),
                "samplerates": self.option.get("SamplesRates", 48000)
            }
        })

        if self.audiocodec == "PCM":
            pass
        elif self.audiocodec == "OPUS":
            self.encoder = OpusBufferedEncoder()
            self.encoder.set_application("audio")
            self.encoder.set_sampling_frequency(self.option.get("SamplesRates", 48000))
            self.encoder.set_channels(self.option.get("Channel", 2))
            self.encoder.set_bitrates(self.option.get("Bitrates", 64000))
            self.encoder.set_frame_size(self.option.get("opusFrameSize", 60))
            self.encoder.set_bitrate_mode(self.option.get("BitrateMode", "VBR").upper())
            self.encoder.set_compresion_complex(self.option.get("opusCompressionLevel", 10))

    def _createaudiosource(self):
        if self.audioinput == "DEVICE":
            p = pyaudio.PyAudio()
            self.sourceinput = p.open(format=pyaudio.paInt16, channels=self.option.get("Channel", 2), rate=self.option.get("SamplesRates", 48000), input=True, input_device_index=self.option.get("DeviceInputIndex", 0))
        elif self.audioinput == "WAV":
            file = self.option.get("InputWAVFile", "")
            if file == "":
                raise "No Audio wav Input Please use option 'InputWAVFile' to set wav file path"
            self.sourceinput = wave.open(file, "rb")
        elif self.audioinput == "SOCKET":
            IP = self.option.get("InputSocketIP", "0.0.0.0")
            Port = self.option.get("InputSocketPort", rannum(12000, 12300))

            self._temp_ip = IP
            self._temp_port = Port

            self._temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._temp_socket.bind((IP, Port))

        else:
            raise "No Audio Device Supported"

    def _running(self):
        framesize = self.option.get("InputFrameSize", 1024)
        samplesrates = self.option.get("SamplesRates", 48000)

        while self.running:
            # get audio
            if self.audioinput == "DEVICE":
                pcm = np.frombuffer(self.sourceinput.read(framesize, exception_on_overflow=False), dtype=np.int16)
            elif self.audioinput == "WAV":
                pcm = np.frombuffer(self.sourceinput.readframes(framesize * 2), dtype=np.int16)
                if len(pcm) == 0:
                    self.sourceinput.rewind()

                if self.standalone:
                    time.sleep(framesize / samplesrates)

            elif self.audioinput == "SOCKET":
                pcm = np.frombuffer(self.sourceinput.recv(framesize), dtype=np.int16)
            else:
                raise "no input data support"



            # encode audio
            if self.audiocodec == "PCM":
                self.buffer.put(pcm.tobytes())
            elif self.audiocodec == "OPUS":
                encoded_packets = self.encoder.buffered_encode(memoryview(bytearray(pcm)))
                for encoded_packet, _, _ in encoded_packets:
                    self.buffer.put(encoded_packet.tobytes())


    def startencoder(self):
        self._createaudiosource()
        self._createencoder()

        if self.audioinput == "SOCKET":
            self._temp_socket.listen(2)
            print(f"[Socket Input Beta] {self.__class__.__name__} audio incoming server is running on {self._temp_ip}:{self._temp_port}. (PCM Data only)")
            print(f"[Socket Input Beta] {self.__class__.__name__} waiting for data for start encoder")
            self.sourceinput, addr = self._temp_socket.accept()
            print(f"[Socket Input Beta] {self.__class__.__name__} {addr} is connected. encoder is starting")

            self._temp_socket.settimeout(self.option.get("InputSocketTimeout", 0.1))

        self.running = True
        self.runningthread.start()


    def stopencoder(self):
        self.running = False
        self.runningthread.join()