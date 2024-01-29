import time
from datetime import datetime

import cv2
import numpy as np

from damp11113 import scrollTextBySteps


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
        "samplerates": 48000
    },
    "images": {
        "logo": encodelogoimage(r"IDRBfavicon.jpg", 25)
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
        "samplerates": 48000
    },
    "images": {
        "logo": None
    }
}


def update_RDS():
    global RDS
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
        RDS2["CT"]["Local"] = datetime.now().timestamp()
        RDS2["CT"]["UTC"] = datetime.utcnow().timestamp()
        time.sleep(1)

def update_RDS_images():
    global RDS
    while True:
        RDS["images"]["logo"] = encodelogoimage(r"dpstream iptv logo.png", 25)
        time.sleep(10)
        RDS["images"]["logo"] = encodelogoimage(r"140702_hi-res-logo.jpg", 25)
        time.sleep(10)
        RDS["images"]["logo"] = encodelogoimage(r"IDRBfavicon.jpg", 25)
        time.sleep(10)

