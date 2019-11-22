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

import websockets
import os.path
import traceback
import subprocess
import functools
import logging
from concurrent.futures.thread import ThreadPoolExecutor

from .answerable_channels import FunctionalChannel,remote
from .websocket_client import server
from . import utils
from . import wifi_module as wifi
import asyncio

if utils.isWindows(): import psutil

class LocalServer(FunctionalChannel):
    def __init__(self,ws):
        self.ws=ws
        super(LocalServer, self).__init__()
    async def send_ac_message(self,m):
        await self.ws.send(m)
    @remote
    async def get_config_status(self):
        status=await self.get_network_status()
        status["id"]=utils.get_id()
        return status
    @remote 
    def get_current_network(self): return {"current_network":wifi.get_current_connected_network()}
    
    other_wifi_things_async_executor = ThreadPoolExecutor()
    @remote 
    async def get_network_status(self):
        return {"status":"success",
                "available_networks":[n.ssid for n in wifi.get_available_networks()],
                "current_network":wifi.get_current_connected_network()
                }
    wifi_change_async_executor = ThreadPoolExecutor(max_workers=1)
    @remote 
    async def set_wifi_network(self, ssid=None,password=None):
        if await asyncio.get_event_loop().run_in_executor(LocalServer.wifi_change_async_executor,functools.partial(wifi.set_wifi_network,ssid, password)):
            return {"status":"success", "current_network":wifi.get_current_connected_network()}
        else:
            return {"status":"error", "current_network":wifi.get_current_connected_network()}
    @remote 
    async def send_config_data(self, **data):
        response=await server.configure(**data)
        utils.set_id(response["cnc_id"])
        utils.set_secret(response["cnc_secret"])
        utils.set_name(response["extra_info"]['cnc_name'])
        utils.save_data()
        return response["extra_info"]
    @remote
    async def is_chilipeppr_running(self):
        if utils.isWindows():
            try:
                is_running = 'serial-port-json-server.exe' in (p.name() for p in psutil.process_iter())
            except Exception as e:
                print('IsRunning error: %s' % e)
                is_running=False
        else:
            try:
                out = await utils.execute_commnd("pidof -x serial-port-json-server")
                is_running= out is not None and out.strip().decode()!=""
            except Exception as e:
                print(e)
                is_running=False
        
        return is_running
    @remote 
    async def start_chilipeppr_socket(self):
        port=8723
        if not await self.is_chilipeppr_running():

            json_server = "serial-port-json-server.exe" if utils.isWindows() else "serial-port-json-server"
            #TODO Revisar permisos de ejecucion archivo serial-port.... con ls -l archivo, si no tiene x ejecutar chmod +x archivo sin sudo. Solo si es linux
            p = subprocess.Popen([os.path.join(utils.FILE_PATHS['chilipeppr_folder'],json_server), '-addr',':%s'%port])
            await asyncio.sleep(2) #se tarda en abir un poco
            for l in local_listeners:
                l.send_request_and_forget("changed_chilipeppr_client_running",running=True)
        return {"address":"ws://%s:%s/ws"%(wifi.get_ip_address(),port)}
    @remote
    async def kill_chilipeppr_socket(self):
        if utils.isWindows():
            try:
                for p in psutil.process_iter():
                    if p.name() == 'serial-port-json-server.exe': p.kill()
            except Exception as e: print('kill error: %s' % e)
        else:
            await utils.execute_commnd("sudo pkill -f serial-port-json-server")
        for l in local_listeners:
            l.send_request_and_forget("changed_chilipeppr_client_running",running=False)
            
_local_server=None
local_listeners=set()
async def run():
    global _local_server
    async def _handle_connection(websocket, path):
        local_server=LocalServer(websocket)
        local_listeners.add(local_server)
        while True:
            try:
                asyncio.ensure_future(local_server.on_ac_message(await websocket.recv()))
            except websockets.exceptions.ConnectionClosed: break
            except Exception as e:
                logging.exception("Server Error")
        local_listeners.remove(local_server)
    _local_server= await websockets.server.serve(_handle_connection,"",8000)
    await _local_server.wait_closed()
async def exit_():
    if _local_server:_local_server.close()
    
