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

import json,os
import sys
from os import execl
import urllib
from io import BytesIO
import zipfile
import shutil
import asyncio
import hashlib
from pathlib import Path
import subprocess
import os
import socket

from .constants import SERVER_HOST

current_path = os.path.dirname(os.path.abspath(__file__)) if not 'Temp' in os.path.abspath(__file__) else ''
config_folder = os.path.join(os.path.dirname(current_path),'config')
try:
    with open(os.path.join(config_folder,'file_paths.json'),'r') as f: FILE_PATHS = json.loads(f.read())
except:
    with open(os.path.join('config','file_paths.json'),'r') as f: FILE_PATHS = json.loads(f.read())

def get_current_path():
    return os.path.dirname(os.path.abspath(__file__))

def isWindows():
    return os.name == 'nt'

def isRaspberry():
    try: return os.uname()[4][:3] == 'arm'
    except: return False  
    
def get_serial_number():
    # Extract serial from cpuinfo file
    cpuserial = None
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
          if line[0:6]=='Serial':
            cpuserial = line[10:26]
        f.close()
    except: cpuserial = None
    return cpuserial
_local_data={}
def set_id(new_id):
    _local_data["id"]=new_id
def set_secret(secret):
    _local_data["secret"]=secret
def set_name(name):
    _local_data["name"]=name
def get_cnc_name():
    return _local_data["name"] if 'name' in _local_data else None
def load_data():
    global _local_data
    if os.path.exists(FILE_PATHS['data_file']):
        with open(FILE_PATHS['data_file'], 'r') as f:       
            try:
                _local_data=json.loads(f.read())
            except: _local_data={}
    else:_local_data={}
    
async def update_client(url):
    file_url=SERVER_HOST+url
    response = urllib.request.urlopen(file_url)
    _file = BytesIO(response.read())
    if zipfile.is_zipfile(_file):
        zfl=zipfile.ZipFile(_file)
        members=zfl.namelist()[:]
        root_path=None
        for n in members[:]:
            if os.path.basename(n)==os.path.basename(FILE_PATHS['data_file']):
                members.remove(n)
            elif os.path.basename(n)=="linclient.py":
                if not root_path:
                    root_path=os.path.dirname(n)
        if root_path is not None:
            for n in members[:]:
                if not n.startswith(root_path):
                    members.remove(n)
        for m in members:       
            source = zfl.open(m)
            file_target=os.path.join(FILE_PATHS['current_path'],os.path.relpath(m, root_path))
            if os.path.basename(m)=="": #es directorio
                if not os.path.exists(file_target):
                    os.makedirs(file_target)
            else: #es archivo
                target = open(file_target, "wb")
                with source, target:
                    shutil.copyfileobj(source, target)  
        await restart()
        
def save_data():
    with open(FILE_PATHS['data_file'], 'w') as f:          
        f.write(json.dumps(_local_data))
def get_localip():
    
    if isWindows():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip if ip else None
    else:
        ifconfig = str(subprocess.check_output("ifconfig")).split(" ")
        for i in ifconfig:
            if "192.168" in i: return i.split(":")[-1].strip()
        
def get_id():
    return _local_data.get("id")
def get_secret():
    return _local_data.get("secret")

def get_client_version():
    
    #from .constants import VERSION
    #return VERSION
    
    if os.path.isfile(FILE_PATHS['version_file']):
        with open(FILE_PATHS['version_file'], 'r') as f:
            return float(f.read().strip())
    else:
        from .constants import VERSION
        with open(FILE_PATHS['version_file'],'w') as f:
            f.write(str(VERSION))
        return float(VERSION)
    
def get_queue_sync_folder():
    if not os.path.isdir(FILE_PATHS['cut_queue_folder']):
        os.makedirs(FILE_PATHS['cut_queue_folder'])
    return FILE_PATHS['cut_queue_folder']

async def execute_commnd(c):
    p=await asyncio.subprocess.create_subprocess_shell(c,stderr = asyncio.subprocess.PIPE, stdout = asyncio.subprocess.PIPE)
    (out,err)=await p.communicate()
    return out
async def restart():
    from . import websocket_server, websocket_client,usb_module
    await websocket_server.exit_()
    await websocket_client.exit_()
    await usb_module.exit_()
    execl(sys.executable, *([sys.executable]+sys.argv))
def file_md5(filename):
    h = hashlib.md5()
    with open(filename, 'rb', buffering=0) as f:
        for b in iter(lambda : f.read(128*1024), b''):
            h.update(b)
    return h.hexdigest()
