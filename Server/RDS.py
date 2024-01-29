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

        print(f"[contentpart={chunk}, currentpart={i}, totalpart={total_chunks}]")
        time.sleep(delay)

    RDSimage["images"][imagetype]["contents"] = b''
    RDSimage["images"][imagetype]["part"]["current"] = 0
    RDSimage["images"][imagetype]["part"]["total"] = 0

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
        "logo": {
            "lazy": True,
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
        sendimagelazy(encodelogoimage(r"C:\Users\sansw\3D Objects\dpstream iptv logo.png", 25), 100, RDS, "logo")
        time.sleep(10)
        sendimagelazy(encodelogoimage(r"C:\Users\sansw\3D Objects\140702_hi-res-logo.jpg", 25), 100, RDS, "logo")
        time.sleep(10)
        sendimagelazy(encodelogoimage(r"IDRBfavicon.jpg", 25), 100, RDS, "logo")
        time.sleep(10)

