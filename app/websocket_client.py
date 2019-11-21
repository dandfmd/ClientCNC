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
# Find us at: http://www.ingenierialinarand.com

import websockets
import asyncio
import time
import urllib.request
import os.path
import zipfile
import shutil
import traceback
import logging
from pathlib import Path
from concurrent.futures.thread import ThreadPoolExecutor
import math

from .constants import SERVER_HOST
from .answerable_channels import FunctionalChannel,remote
from . import wifi_module as wifi
from . import utils
from . import usb_module

class Client(FunctionalChannel):
    @remote
    async def reconfigure(self):
        utils.set_id(None)
        utils.set_secret(None)
        utils.set_name(None)
        utils.save_data()
        await authenticate()
    
    sync_lock=asyncio.Lock()
    sync_executor = ThreadPoolExecutor(max_workers=4)
    @remote
    async def sync_queue_folder(self,server_files):
        async with Client.sync_lock:
            folder=Path(utils.get_queue_sync_folder())
            folder.mkdir(exist_ok=True,parents=True)
            md5=[]
            files=[]
            names=[]
            
            #construimos la lista de archivos que tenemos
            for file in folder.iterdir():
                if not file.is_file():continue
                name=file.name
                try:
                    _,gcode_name=name.split(" ",1)
                    _=int(_)
                except ValueError:
                    file.unlink()
                    continue
                md5_future=asyncio.get_event_loop().run_in_executor(Client.sync_executor,utils.file_md5,str(file))
                
                files.append(file)
                md5.append(md5_future)
                names.append(gcode_name)
            md5=await asyncio.gather(*md5)
            local_files=[{"md5":md5[i],"name":names[i],"file":files[i]} for i in range(len(files))]
            
            #calculamos archivos que tenemos que elimar, renombrar y descargar
            to_remove={l["file"] for l in local_files}
            to_download=set()
            to_rename=set()
            
            if server_files:
                zero_pad=int(math.log10(len(server_files))+1)
            for i,server_file in enumerate(server_files):
                name=server_file["name"]
                filename="%s %s"%(str(i+1).zfill(zero_pad),name)
                md5=server_file["md5"]
                for local_file in local_files[:]:
                    if local_file["name"]==name and local_file["md5"]==md5:
                        file=local_file["file"]
                        to_remove.discard(file)
                        if file.name!=filename:
                            to_rename.add((file,file.with_name(filename)))
                        
                        local_files.remove(local_file) #esto es porque si hay repetidos, no podemos mover mas de una vez
                            #seria bueno copiar los repetidos en vez de volver a descargar... pero meh
                        break
                else:
                    to_download.add((server_file["url"],folder/filename))
            
            #elimianos
            for file in to_remove: file.unlink()
            
            #renombramos
            temporal_prefix="tempname"
            for current,new in to_rename:
                current.rename(current.with_name(temporal_prefix+current.name))
            for current,new in to_rename:
                current.with_name(temporal_prefix+current.name).rename(new)

            down_futs=[]
            
            #descargamos
            for url,file in to_download:
                down_futs.append(asyncio.get_event_loop().run_in_executor(Client.sync_executor,urllib.request.urlretrieve,SERVER_HOST+url,str(file)))
            await asyncio.gather(*down_futs)
            
        
    async def send_ac_message(self,m):
        await _ws.send(m)
client=Client()
server=client.remote
async def authenticate():
   
    local_ip = wifi.get_ip_address()
    if not local_ip: local_ip = utils.get_localip()
    if not local_ip: local_ip = input("manualy insert ip:")
    data=await server.authenticate(id=utils.get_id(),secret=utils.get_secret(),local_ip=local_ip,client_version=utils.get_client_version())
    if data["status"]=="success":
        if 'cnc_name' in data and utils.get_cnc_name() != data["cnc_name"]:
            utils.set_name(data["cnc_name"])
            utils.save_data()
        if 'cnc_name' in data: print('%s at: %s' % (data["cnc_name"],local_ip) )
        else: print('Setup new client at: http://cloud.dfmd.mx/new-cnc')
    else:
        if "solution" in data:
            if data["solution"]=="reconfigure":
                await client.reconfigure()
            if data["solution"]=="update":
                print("Nueva version disponible (Actual: %s,Nueva: %s)"%(utils.get_client_version(),data["update_data"]["new_version"]))
                logging.info("Actualizando cliente a nueva version (Actual: %s,Nueva: %s)"%(utils.get_client_version(),data["update_data"]["new_version"]))
                await utils.update_client(data["update_data"]["file_url"])
                
_exit=False
async def run():
    global _ws
    while not _exit:
        try:
            async with websockets.connect(SERVER_HOST.replace("http", "ws") + '/ws/cnc') as ws:
                _ws=ws
                asyncio.ensure_future(authenticate())
                while True:
                    m=await _ws.recv()
                    asyncio.ensure_future(client.on_ac_message(m))
        except Exception as e:
            logging.exception("Client Error :(")
        if not _exit: await asyncio.sleep(1)
async def exit_():
    global _exit
    _exit=True
    await _ws.close()