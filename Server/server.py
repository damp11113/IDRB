import socket
import time
import pyaudio
from pyogg import OpusBufferedEncoder
import numpy as np
import pickle
import threading
import RDS as _RDS
from queue import Queue
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
import zmq

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


protocol = "ZMQ_WS"
server_port = ('*', 6980)

if protocol == "TCP":
    # create tcp
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # wait for connection
    s.bind(server_port)
    s.listen(1)
elif protocol == "ZMQ":
    context = zmq.Context()
    s = context.socket(zmq.PUB)
    s.bind(f"tcp://{server_port[0]}:{server_port[1]}")
elif protocol == "ZMQ_WS":
    context = zmq.Context()
    s = context.socket(zmq.PUB)
    s.bind(f"ws://{server_port[0]}:{server_port[1]}")
    protocol = "ZMQ"
else:
    print(f"{protocol} not supported")
    exit()

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


thread = threading.Thread(target=_RDS.update_RDS)
thread.start()

thread2 = threading.Thread(target=_RDS.update_RDS_time)
thread2.start()

thread4 = threading.Thread(target=_RDS.update_RDS_images)
thread4.start()

# Create a shared queue for encoded audio packets
channel1 = Queue()

channel2 = Queue()

# Function to continuously encode audio and put it into the queue
def encode_audio():
    encoder = OpusBufferedEncoder()
    encoder.set_application("audio")
    encoder.set_sampling_frequency(sample_rate)
    encoder.set_channels(_RDS.RDS["ContentInfo"]["channel"])
    encoder.set_bitrates(_RDS.RDS["ContentInfo"]["bitrate"])
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

audio_thread = threading.Thread(target=encode_audio)
audio_thread.start()

audio_thread2 = threading.Thread(target=encode_audio2)
audio_thread2.start()

connectionlist = []

if protocol == "TCP":
    connected_users = 0
elif protocol == "ZMQ":
    connected_users = "Unknown"
else:
    print(f"{protocol} not supported")
    exit()
timestart = time.time()

first = True

firstcontent = {
    "first": True,
    "mainchannel": 1,
    "channel": {
        1: {
            "Station": "DPRadio+",
            "RDS": _RDS.RDS
        },
        2: {
            "Station": "DPTest",
            "RDS": _RDS.RDS2
        }
    },
    "serverinfo": {
        "Listener": connected_users,
        "Country": "TH",
        "Startat": timestart
    }
}

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
                "first": False,
                "mainchannel": 1,
                "channel": {
                    1: {
                        "Station": "DPRadio+",
                        "Encrypt": b'|||||' in ENchannel1, # check if encrypt
                        "ContentSize": len(ENchannel1),
                        "Content": ENchannel1,
                        "RDS": _RDS.RDS
                    },
                    2: {
                        "Station": "DPTest",
                        "Encrypt": b'|||||' in ENchannel2,
                        "ContentSize": len(ENchannel2),
                        "Content": ENchannel2,
                        "RDS": _RDS.RDS2
                    }
                },
                "serverinfo": {
                    "Listener": connected_users,
                    "Country": "TH",
                    "Startat": timestart
                }
            }
            #connection.sendall(pickle.dumps(content))
            if protocol == "TCP":
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
            elif protocol == "ZMQ":
                s.send(pickle.dumps(content))
    except Exception as e:
        print(f'Error: {e}')

# Your main server logic using threading for handling connections
if __name__ == "__main__":
    print("server is running")
    if protocol == "TCP":
        while True:
            print("Waiting for a connection...")
            connection, client_address = s.accept()
            print(f"Connected to {client_address}")

            connectionlist.append(connection)
            connected_users += 1
            if first:
                # Start a: new thread to handle the client
                client_thread = threading.Thread(target=handle_client)
                # client_thread.daemon = True  # Set the thread as a daemon so it exits when the main thread exits
                client_thread.start()
                first = False
    elif protocol == "ZMQ":
        client_thread = threading.Thread(target=handle_client)
        # client_thread.daemon = True  # Set the thread as a daemon so it exits when the main thread exits
        client_thread.start()