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

import threading
from queue import Queue
from pyogg import OpusBufferedEncoder
import numpy as np
import pyaudio
import RDS as _RDS
import logging

EncoderLog = logging.getLogger("Encoder")

EncoderLog.info("Init audio system...")

p = pyaudio.PyAudio()

device_name_input = "Line 5 (Virtual Audio Cable)"
device_index_input = 0
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev['name'] == device_name_input:
        device_index_input = dev['index']
        break

device_name_input = "Line 4 (Virtual Audio Cable)"
device_index_input2 = 0
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev['name'] == device_name_input:
        device_index_input2 = dev['index']
        break

streaminput = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=device_index_input)
streaminput2 = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=device_index_input2)

# Create a shared queue for encoded audio packets
channel1 = Queue()

channel2 = Queue()

# Function to continuously encode audio and put it into the queue
def encode_audio():
    encoder = OpusBufferedEncoder()
    encoder.set_application("audio")
    encoder.set_sampling_frequency(_RDS.RDS["ContentInfo"]["samplerates"])
    encoder.set_channels(_RDS.RDS["ContentInfo"]["channel"])
    encoder.set_bitrates(_RDS.RDS["ContentInfo"]["bitrate"])
    encoder.set_frame_size(60)
    encoder.set_bitrate_mode("VBR")
    encoder.set_compresion_complex(10)

    while True:
        pcm = np.frombuffer(streaminput.read(1024, exception_on_overflow=False), dtype=np.int16)

        encoded_packets = encoder.buffered_encode(memoryview(bytearray(pcm)))
        for encoded_packet, _, _ in encoded_packets:
            # Put the encoded audio into the buffer

            channel1.put(encoded_packet.tobytes())

def encode_audio2():
    encoder2 = OpusBufferedEncoder()
    encoder2.set_application("audio")
    encoder2.set_sampling_frequency(_RDS.RDS2["ContentInfo"]["samplerates"])
    encoder2.set_channels(_RDS.RDS2["ContentInfo"]["channel"])
    encoder2.set_bitrates(_RDS.RDS2["ContentInfo"]["bitrate"])
    encoder2.set_frame_size(60)

    while True:
        pcm2 = np.frombuffer(streaminput2.read(1024, exception_on_overflow=False), dtype=np.int16)

        encoded_packets = encoder2.buffered_encode(memoryview(bytearray(pcm2)))
        for encoded_packet, _, _ in encoded_packets:
            # Put the encoded audio into the buffer
            channel2.put(encoded_packet.tobytes())

        #channel2.put(pcm2.tobytes()) # if you use pcm

def StartEncoder():
    EncoderLog.info("Starting encoder")
    audio_thread = threading.Thread(target=encode_audio)
    audio_thread2 = threading.Thread(target=encode_audio2)

    audio_thread.start()
    audio_thread2.start()