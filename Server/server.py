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
import cv2
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes

def pad_message(message_bytes):
    block_size = AES.block_size
    padding_length = block_size - (len(message_bytes) % block_size)
    padding = bytes([padding_length] * padding_length)
    return message_bytes + padding

def encrypt_data(message_bytes, password):
    # Derive a key from the password
    salt = get_random_bytes(50)
    key = scrypt(password, salt, key_len=32, N=2 ** 14, r=8, p=1)

    # Generate an IV (Initialization Vector)
    iv = get_random_bytes(AES.block_size)

    # Pad the message
    padded_message = pad_message(message_bytes)

    # Initialize AES cipher in CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Encrypt the padded message
    encrypted_message = cipher.encrypt(padded_message)

    # Return the encrypted message, salt, and IV (for decryption)
    return encrypted_message, salt, iv


# create tcp
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# wait for connection
server_port = ('localhost', 6980)
s.bind(server_port)

s.listen(1)

p = pyaudio.PyAudio()

sample_rate = 48000
bytes_per_sample = p.get_sample_size(pyaudio.paInt16)


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

streaminput = p.open(format=pyaudio.paInt16, channels=2, rate=sample_rate, input=True, input_device_index=device_index_input)
streaminput2 = p.open(format=pyaudio.paInt16, channels=2, rate=sample_rate, input=True, input_device_index=device_index_input2)


def encodelogoimage(path, quality=50):
    image = cv2.resize(cv2.imread(path), (128, 128))
    # Encode the image as JPEG with higher compression (lower quality)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]  # Adjust quality (50 is just an example)
    result, encoded_image = cv2.imencode('.jpg', image, encode_param)
    encoded_bytes = np.array(encoded_image).tobytes()
    return encoded_bytes


RDS = {
    "PS": "DPRadio",
    "RT": "Testing internet radio",
    "PI": 0x27C8, # static
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
        # can add more here
    ],
    "ContentInfo": {
        "Codec": "opus",
        "bitrate": 64000,
        "channel": 2,
        "samplerates": sample_rate
    },
    "images": {
        "logo": encodelogoimage(r"C:\Users\sansw\3D Objects\dpstream iptv logo.png")
    }
}

RDS2 = {
    "PS": "DPTest",
    "RT": "Testing internet radio",
    "PI": 0x27C6,
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
        "Codec": "Opus",
        "bitrate": 8000,
        "channel": 2,
        "samplerates": sample_rate
    },
    "images": {
        "logo": None
    }
}


lock = threading.Lock()

def update_RDS():
    global RDS
    with lock:
        while True:
            pstext = "DPRadio Testing Broadcasting          "
            for i in range(0, len(pstext)):
                RDS["PS"] = scrollTextBySteps(pstext, i)
                time.sleep(1)

def update_RDS_time():
    global RDS
    while True:
        RDS["CT"]["Local"] = datetime.now().timestamp()
        RDS["CT"]["UTC"] = datetime.utcnow().timestamp()
        time.sleep(1)

def update_RDS_images():
    global RDS
    while True:
        RDS["images"]["logo"] = encodelogoimage(r"C:\Users\sansw\3D Objects\dpstream iptv logo.png", 25)
        time.sleep(10)
        RDS["images"]["logo"] = encodelogoimage(r"C:\Users\sansw\3D Objects\140702_hi-res-logo.jpg", 25)
        time.sleep(10)
        RDS["images"]["logo"] = encodelogoimage(r"IDRBfavicon.jpg", 25)
        time.sleep(10)

thread = threading.Thread(target=update_RDS)
thread.start()

thread2 = threading.Thread(target=update_RDS_time)
thread2.start()

thread4 = threading.Thread(target=update_RDS_images)
thread4.start()

# Create a shared queue for encoded audio packets
channel1 = Queue()

channel2 = Queue()

# Function to continuously encode audio and put it into the queue
def encode_audio():
    encoder = OpusBufferedEncoder()
    encoder.set_application("audio")
    encoder.set_sampling_frequency(sample_rate)
    encoder.set_channels(2)
    encoder.set_bitrates(64000)
    encoder.set_frame_size(60)

    while True:
        pcm = np.frombuffer(streaminput.read(1024, exception_on_overflow=False), dtype=np.int16)

        encoded_packets = encoder.buffered_encode(memoryview(bytearray(pcm)))
        for encoded_packet, _, _ in encoded_packets:
            # Put the encoded audio into the buffer

            channel1.put(encoded_packet.tobytes())

def encode_audio2():
    encoder2 = OpusBufferedEncoder()
    encoder2.set_application("audio")
    encoder2.set_sampling_frequency(sample_rate)
    encoder2.set_channels(2)
    encoder2.set_bitrates(8000)
    encoder2.set_frame_size(60)

    while True:
        pcm2 = np.frombuffer(streaminput2.read(1024, exception_on_overflow=False), dtype=np.int16)

        encoded_packets = encoder2.buffered_encode(memoryview(bytearray(pcm2)))
        for encoded_packet, _, _ in encoded_packets:
            # Put the encoded audio into the buffer
            channel2.put(encoded_packet.tobytes())

        #channel2.put(pcm2.tobytes()) # if you use pcm

audio_thread = threading.Thread(target=encode_audio)
audio_thread.start()

audio_thread2 = threading.Thread(target=encode_audio2)
audio_thread2.start()

connectionlist = []
connected_users = 0

first = True

def handle_client():
    global connected_users, first
    try:
        while True:
            # Get the encoded audio from the buffer
            ENchannel1 = channel1.get()

            # encrypt data
            #ENC1encrypted, ENC1salt, ENC1iv = encrypt_data(ENchannel1, "password")

            #ENchannel1 = ENC1encrypted + b'|||||' + ENC1salt + b'|||||' + ENC1iv

            ENchannel2 = channel2.get()
            content = {
                "mainchannel": 1,
                "channel": {
                    1: {
                        "Station": "DPRadio+",
                        "Encrypt": b'|||||' in ENchannel1, # check if encrypt
                        "ContentSize": len(ENchannel1),
                        "Content": ENchannel1,
                        "RDS": RDS
                    },
                    2: {
                        "Station": "DPTest",
                        "Encrypt": b'|||||' in ENchannel2,
                        "ContentSize": len(ENchannel2),
                        "Content": ENchannel2,
                        "RDS": RDS2
                    }
                },
                "serverinfo": {
                    "Listener": connected_users,
                    "Country": "TH",
                    "Startat": time.time()
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
            # check if no user
            if not connectionlist:
                first = True
                break
    except Exception as e:
        print(f'Error: {e}')

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
        #client_thread.daemon = True  # Set the thread as a daemon so it exits when the main thread exits
        client_thread.start()
        first = False