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
import pyaudio
import RDS as _RDS
import logging
import tools

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

# Create a shared queue for encoded audio packets
channel1 = Queue()

channel2 = Queue()

channel1option = {
    "Bitrates": 64000,
    "DeviceInputIndex": device_index_input
}

channel2option = {
    "Bitrates": 18000,
    "InputWAVFile": "./Samples/audiotest.wav"
}


EncoderChannel1 = tools.AudioEncoder(_RDS.RDS, channel1option, channel1)

EncoderChannel2 = tools.AudioEncoder(_RDS.RDS2, channel2option, channel2, "wav")

def StartEncoder():
    EncoderLog.info("Starting encoder")

    EncoderChannel1.startencoder()
    EncoderChannel2.startencoder()