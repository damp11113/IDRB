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

import time
from datetime import datetime
import cv2
import numpy as np
from damp11113 import scrollTextBySteps
import threading
import Settings
import logging

RDSLog = logging.getLogger("RDS")

def encodelogoimage(path, quality=50):
    image = cv2.resize(cv2.imread(path), (128, 128))
    # Encode the image as JPEG with higher compression (lower quality)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]  # Adjust quality (50 is just an example)
    result, encoded_image = cv2.imencode('.jpg', image, encode_param)
    encoded_bytes = np.array(encoded_image).tobytes()
    return encoded_bytes

def sendimagelazy(data, chunk_size, RDSimage, imagetype, delay=0.1):
    if not RDSimage["images"][imagetype]["lazy"]:
        RDSimage["images"][imagetype]["contents"] = data
        return

    # Break the data into chunks
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    total_chunks = len(chunks)
    RDSimage["images"][imagetype]["part"]["total"] = total_chunks

    # Send each chunk
    for i, chunk in enumerate(chunks):
        RDSimage["images"][imagetype]["contents"] = chunk
        RDSimage["images"][imagetype]["part"]["current"] = i

        #print(f"[contentpart={chunk}, currentpart={i}, totalpart={total_chunks}]")
        time.sleep(delay)

    RDSimage["images"][imagetype]["contents"] = b''
    RDSimage["images"][imagetype]["part"]["current"] = 0
    RDSimage["images"][imagetype]["part"]["total"] = 0

ServerRDS = {
    "ServerName": Settings.ServerName,
    "ServerDesc": Settings.ServerDesc,
    "Country": Settings.Country,
    "AS": [ # AS = Alternative Server
        # can add more server here
    ]
}

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
    "EON": [
        # can add more here
    ],
    "AS": [ # AS = Alternative Server
        # can add more server here
    ],
    "ContentInfo": {
        "Codec": "opus",
        "bitrate": 64000,
        "channel": 2,
        "samplerates": 48000
    },
    "images": {
        "logo": {
            "lazy": False,
            'contents': b'',
            "part": {
                "current": 0,
                "total": 0
            }
        }
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
    "EON": [
        # can add more server here
    ],
    "AS": [ # AS = Alternative Server
        # can add more server here
    ],
    "ContentInfo": {
        "Codec": "Opus",
        "bitrate": 8000,
        "channel": 2,
        "samplerates": 48000
    },
    "images": {
        "logo": None
    }
}

def update_RDS():
    RDSLog.info("Starting RDS Users...")
    global RDS
    while True:
        pstext = "DPRadio Testing Broadcasting          "
        for i in range(0, len(pstext)):
            RDS["PS"] = scrollTextBySteps(pstext, i)
            time.sleep(1)

def update_RDS_time():
    RDSLog.info("Starting RDS Times...")
    global RDS
    while True:
        RDS["CT"]["Local"] = datetime.now().timestamp()
        RDS["CT"]["UTC"] = datetime.utcnow().timestamp()
        RDS2["CT"]["Local"] = datetime.now().timestamp()
        RDS2["CT"]["UTC"] = datetime.utcnow().timestamp()
        time.sleep(1)

def update_RDS_images():
    RDSLog.info("Starting RDS Images...")
    global RDS
    while True:
        sendimagelazy(encodelogoimage(r"C:\Users\sansw\3D Objects\dpstream iptv logo.png", 25), 100, RDS, "logo")
        time.sleep(10)
        sendimagelazy(encodelogoimage(r"C:\Users\sansw\3D Objects\140702_hi-res-logo.jpg", 25), 100, RDS, "logo")
        time.sleep(10)
        sendimagelazy(encodelogoimage(r"IDRBfavicon.jpg", 25), 100, RDS, "logo")
        time.sleep(10)

def startRDSThread():
    RDSLog.info("Starting RDS...")
    thread = threading.Thread(target=update_RDS)
    thread2 = threading.Thread(target=update_RDS_time)
    thread3 = threading.Thread(target=update_RDS_images)

    thread.start()
    thread2.start()
    thread3.start()

