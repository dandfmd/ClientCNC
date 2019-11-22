# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright 2015,2016,2017,2018 Daniel Fernandez (daniel@dfmd.mx), Saul Pilatowsky (saul@dfmd.mx) 
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Find us at: http://www.dfmd.mx
#
# Wifi module based on:
# Copyright (c) 2003-2005 by Peter Astrand <astrand@lysator.liu.se>
#
# Licensed to PSF under a Contributor Agreement.
# See http://www.python.org/2.4/license for licensing details.

import sys

if sys.version_info[0] < 3: 
    print('Error: The client needs to run on python3')
    quit()

if len(sys.argv) > 1 and sys.argv[1] == '-setup':
    from app import setup
    setup.install_dependencies()
    quit()

from threading import Thread
import asyncio
import logging
import os
import json

files = {}
current_path = os.path.dirname(os.path.abspath(__file__))
config_folder = os.path.join(current_path,'config')
if not os.path.isdir(config_folder): os.makedirs(config_folder)
files['data_file'] = os.path.join(config_folder,"data.json")
files['version_file'] =os.path.join(config_folder,"client_version")
files['cut_queue_folder'] = os.path.join(config_folder,"cutqueue")
files['chilipeppr_folder'] = os.path.join(current_path,"chilipeppr_serial")
files['current_path'] = current_path
with open(os.path.join(config_folder,'file_paths.json'),'w') as f: f.write(json.dumps(files))

from app import websocket_server
from app import websocket_client
from app import utils
from app import wifi_module as wifi
from app import usb_module
    
logger = logging.getLogger()
logPan = os.path.join(os.path.dirname( __file__ ), "log.log")
fh = logging.FileHandler(logPan)
fh.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s:%(name)s:"
    "%(levelname)s:%(message)s")
fh.setFormatter(formatter)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(console)

utils.load_data()
wifi.check_interfaces_file()
ev=asyncio.get_event_loop()
asyncio.ensure_future(websocket_server.run())
asyncio.ensure_future(websocket_client.run())
asyncio.ensure_future(usb_module.run())
ev.set_debug(False)
ev.run_forever()

