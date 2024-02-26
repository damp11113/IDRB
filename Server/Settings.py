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

# Server Settings
protocol = "ZMQ_WS" # TCP ZMQ ZMQ_WS
server_port = ('*', 6980) # if use other protocol ZMQ please use 0.0.0.0
compression_level = 9 # 0-9

# Server Info
ServerName = "DPCloudev"
ServerDesc = "Testing Server"
Country = "TH"

"""
If you want your server to be listed publicly on ThaiSDR Directory, following this steps
1. goto dashboard.damp11113.xyz and login or signup your account
2. goto click "APIKey"
3. click create
4. select api type "ThaiSDR Directory"
5. click done
6. copy api key

"""
public = True
#ServerIP = "IDRB.damp11113.xyz" # do not add protocol before ip
ServerIP = "localhost"
#ServerPort = server_port[1]
ServerPort = 6980
ThaiSDRkey = "1N5LURICLIN1U9QNYZ4MHJ6FNXISFXFELZAX135CFM0HSD17O2.63E60BE9EEA2339C113A15EB"