import socket
import time
import pyaudio
from pyogg import OpusBufferedEncoder
import numpy as np
import pickle
import threading
from damp11113 import scrollTextBySteps
from queue import Queue
from datetime import datetime, timezone

# create tcp
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# wait for connection
server_port = ('localhost', 6980)
s.bind(server_port)

s.listen(1)


p = pyaudio.PyAudio()

sample_rate = 48000
bytes_per_sample = p.get_sample_size(pyaudio.paInt16)

codec = "opus" # opus, pcm, aac

# Create an Opus encoder
bitrates = 64000 #Kbps
channel = 2 # Stereo
framesize = 60


if bitrates >= 500000:
    bitrates = 500000

encoder = OpusBufferedEncoder()
encoder.set_application("audio")
encoder.set_sampling_frequency(sample_rate)
encoder.set_channels(channel)
encoder.set_bitrates(bitrates)
encoder.set_frame_size(framesize)

device_name_input = "Line 5 (Virtual Audio Cable)"
device_index_input = 0
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev['name'] == device_name_input:
        device_index_input = dev['index']
        break

streaminput = p.open(format=pyaudio.paInt16, channels=2, rate=sample_rate, input=True, input_device_index=device_index_input)

RDS = {
    "PS": "DPRadio",
    "RT": "Testing internet radio",
    "PI": 0x27C8,
    "PTY": 0,
    "PTY+": "Testing",
    "Country": "TH",
    "Coverage": "All",
    "CT": {
        "Local": None,
        "UTC": None,
    },
    "PIN": 12345,
    "TMC": {
        "TP": False,
        "TA": False,
        "Messages": None
    },
    "ECC": None,
    "LIC": None,
    "AudioMode": "Stereo", # mono, stereo, surround 5.1/7.1, HRTF
    "ArtificialHead": False,
    "Compressed": False,
    "DyPTY": False,
    "EPG": None,
    "AS": [ # AS = Alternative Server
        # can add more server here
    ],
    "EON": [
        # can add more server here
    ],
    "ContentInfo": {
        "Codec": codec,
        "bitrate": bitrates,
        "channel": channel,
        "samplerates": sample_rate
    },
    "Listener": 0
}
lock = threading.Lock()

def update_RDS():
    global RDS
    with lock:
        while True:
            pstext = "DPRadio Testing Broadcasting"
            for i in range(0, len(pstext)):
                RDS["PS"] = scrollTextBySteps(pstext, i)
                time.sleep(1)

def update_RDS_time():
    global RDS
    while True:
        RDS["CT"]["Local"] = datetime.now().timestamp()
        RDS["CT"]["UTC"] = datetime.now(timezone.utc).timestamp()
        time.sleep(1)

connected_users = 0

def update_RDS_system():
    global RDS
    while True:
        RDS["Listener"] = connected_users
        time.sleep(1)

thread = threading.Thread(target=update_RDS)
thread.start()

thread2 = threading.Thread(target=update_RDS_time)
thread2.start()

thread3 = threading.Thread(target=update_RDS_system)
thread3.start()


# Create a shared queue for encoded audio packets
byte_queue = Queue()

# Function to continuously encode audio and put it into the queue
def encode_audio():
    while True:
        pcm = np.frombuffer(streaminput.read(1024, exception_on_overflow=False), dtype=np.int16)
        encoded_packets = encoder.buffered_encode(memoryview(bytearray(pcm)))
        for encoded_packet, _, _ in encoded_packets:
            # Put the encoded audio into the buffer
            byte_queue.put(encoded_packet.tobytes())

audio_thread = threading.Thread(target=encode_audio)
audio_thread.daemon = True
audio_thread.start()

connectionlist = []
def handle_client():
    global connected_users
    try:
        while True:
            # Get the encoded audio from the buffer
            encoded_audio = byte_queue.get()
            content = {
                "channellist": 1,
                "channel": {
                    1: {
                        "ContentSize": len(encoded_audio),
                        "Content": encoded_audio,
                        "RDS": RDS
                    }
                }
            }
            #connection.sendall(pickle.dumps(content))
            for i in connectionlist:
                try:
                    i.sendall(pickle.dumps(content))
                except Exception as e:
                    #print(f'Error sending data to {i.getpeername()}: {e}')
                    # Remove disconnected client from the list
                    if i in connectionlist:
                        i.close()
                        connectionlist.remove(i)
                        connected_users -= 1
    except Exception as e:
        print(f'Error: {e}')

first = True

# Your main server logic using threading for handling connections
while True:
    print("Waiting for a connection...")
    connection, client_address = s.accept()
    print(f"Connected to {client_address}")

    connectionlist.append(connection)
    connected_users += 1
    if first:
        # Start a: new thread to handle the client
        client_thread = threading.Thread(target=handle_client)
        client_thread.daemon = True  # Set the thread as a daemon so it exits when the main thread exits
        client_thread.start()
        first = False
