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

import requests
import threading
import time
import Settings
import json
import logging

ThaiSDRDirLog = logging.getLogger("ThaiSDRDir")

content = {}

protocolclientconvert = {
    "TCP": "TCP",
    "ZMQ": "ZeroMQ",
    "ZMQ_WS": "ZeroMQ (WS)"
}

def mainprocess():
    while True:
        currentcontent = content
        try:
            Station = {}

            try:
                for channel_number, channel_info in currentcontent["channel"].items():
                    Station.update(
                        {
                            channel_number: {
                                "StationName": channel_info["Station"],
                                "StationDesc": channel_info["StationDesc"],
                                "StationEncrypted": channel_info["Encrypt"],
                                "Audio": {
                                    "AudioChannel": channel_info["RDS"]["ContentInfo"]["channel"],
                                    "Codec": channel_info["RDS"]["ContentInfo"]["Codec"].upper(),
                                    "Bitrate": channel_info["RDS"]["ContentInfo"]["bitrate"],
                                }
                            }
                        }
                    )
            except:
                continue



            Sendcontent = {
                "ServerName": currentcontent["serverinfo"]["RDS"]["ServerName"],
                "ServerDesc": currentcontent["serverinfo"]["RDS"]["ServerDesc"],
                "ConnectionUser": currentcontent["serverinfo"]["Listener"],
                "ServerURL": Settings.ServerIP,
                "ServerPort": Settings.ServerPort,
                "ServerProtocol": protocolclientconvert.get(Settings.protocol.upper(), "Unknown"),
                "Station": Station
            }

            jsondata = json.dumps(Sendcontent)

            response = requests.post("https://thaisdr.damp11113.xyz/api/idrbdir/updateserver", data=jsondata, headers={"apikey": Settings.ThaiSDRkey, "Content-Type": "application/json"})

            if response.status_code == 200:
                ThaiSDRDirLog.info("Update succeeded!")
            else:
                response_json = response.json()
                ThaiSDRDirLog.error(f"Update failed, your server cannot be listed on ThaiSDR Directory! Reason: {response_json['message']}")

            time.sleep(300)
        except Exception as e:
            ThaiSDRDirLog.error(f"ThaiSDR Directory Error: {str(e)}")
            time.sleep(5)
            continue

def run():
    if Settings.protocol != None and Settings.ThaiSDRkey != "":
        ThaiSDRDirLog.info("server is soon getting listed on ThaiSDR Directory")
        TDIR = threading.Thread(target=mainprocess)
        TDIR.start()
    else:
        if Settings.ThaiSDRkey == "":
            ThaiSDRDirLog.error("ThaiSDR Directory can't work without APIKey.")
        else:
            ThaiSDRDirLog.error("ThaiSDR Directory can't work without protocol.")