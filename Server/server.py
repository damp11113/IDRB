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
import pickle
import threading
import zmq
import logging
import lz4.frame
import queue
import math
import os

os.environ["damp11113_load_all_module"] = "NO"
os.environ["damp11113_check_update"] = "NO"

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
ServerLog = logging.getLogger("IDRBServer")

ServerLog.info("Server is starting...")

import ThaiSDRDir
import RDS as _RDS
import Encoder
import utils
import Settings

protocol = Settings.protocol
server_port = Settings.server_port
public = Settings.public

if protocol == "TCP":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

ServerLog.info('starting RDS')
_RDS.startRDSThread()

ServerLog.info('starting audio encoding')
Encoder.StartEncoder()

if protocol == "TCP":
    connected_users = 0
elif protocol == "ZMQ":
    connected_users = "Unknown"
else:
    print(f"{protocol} not supported")
    exit()

timestart = time.time()
connectionlist = []
first = True

Buffer = queue.Queue(maxsize=math.trunc(Settings.buffersize + (Settings.buffersize/2)))

# ---------------------------------- Config Muxer ---------------------------------------

def Muxer():
    while True:
        # Get the encoded audio from the buffer
        ENchannel1 = Encoder.channel1.get()

        # encrypt data
        # ENC1encrypted, ENC1salt, ENC1iv = utils.encrypt_data(ENchannel1, "password")

        # ENchannel1 = ENC1encrypted + b'|||||' + ENC1salt + b'|||||' + ENC1iv
        try:
            ENchannel2 = Encoder.channel2.get()
        except:
            ENchannel2 = b""
        content = {
            "first": False,
            "mainchannel": 1,
            "channel": {
                1: {
                    "Station": "DPRadio+",
                    "StationDesc": "The best station in the world!",
                    "Encrypt": b'|||||' in ENchannel1,  # check if encrypt
                    "ContentSize": len(ENchannel1),
                    "Content": ENchannel1,
                    "RDS": _RDS.RDS
                },
                2: {
                    "Station": "DPTest",
                    "StationDesc": "",
                    "Encrypt": b'|||||' in ENchannel2,
                    "ContentSize": len(ENchannel2),
                    "Content": ENchannel2,
                    "RDS": _RDS.RDS2
                }
            },
            "serverinfo": {
                "Listener": connected_users,
                "Startat": timestart,
                "RDS": _RDS.ServerRDS
            }
        }
        ThaiSDRDir.content = content

        compressedcontent = lz4.frame.compress(pickle.dumps(content), compression_level=Settings.compression_level)

        Buffer.put(compressedcontent)

# -----------------------------------------------------------------------------------------------

def handle_client():
    global connected_users, first
    try:
        while True:
            # Check if the buffer queue has enough data to send
            if Buffer.qsize() >= Settings.buffersize:  # Adjust the threshold as needed
                if protocol == "TCP":
                    for i in connectionlist:
                        try:
                            # Send data from the buffer queue to connected clients
                            for _ in range(Settings.buffersize):
                                i.sendall(Buffer.get())
                        except Exception as e:
                            if i in connectionlist:
                                i.close()
                                connectionlist.remove(i)
                                connected_users -= 1
                    if not connectionlist:
                        first = True
                        ServerLog.info('server is standby now')
                        break
                elif protocol == "ZMQ":
                    # Send data from the buffer queue to ZMQ socket
                    for _ in range(Settings.buffersize):
                        s.send(Buffer.get())
    except Exception as e:
        print(f'Error: {e}')


# Your main server logic using threading for handling connections
if __name__ == "__main__":
    if public:
        ServerLog.info('starting ThaiSDR Directory')
        ThaiSDRDir.run()

    ServerLog.info('starting Muxer')

    muxerthread = threading.Thread(target=Muxer)
    muxerthread.start()

    ServerLog.info('starting server')

    if protocol == "TCP":
        while True:
            connection, client_address = s.accept()
            ServerLog.info(f'{client_address} is connected')

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

    ServerLog.info('server is running')