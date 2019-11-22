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

import os
import shutil
import time
import logging
import asyncio
from pathlib import Path

from . import utils
if utils.isWindows(): import psutil

GCODE_EXTENSIONS = ['nc']

def clean_usb(usb_folder):
    if os.path.isdir(usb_folder):
        usb_files = os.listdir(usb_folder)
        for usb_file in usb_files:
            if usb_file.split('.')[-1] in GCODE_EXTENSIONS:
                os.remove(os.path.join(usb_folder,usb_file))
                #print(usb_file)
        return usb_folder
    else:
        return False
    
def clone_dir(source_folder,usb_folder):
    if os.path.isdir(source_folder):
        source_files = os.listdir(source_folder)
        for source_file in sorted(source_files):
            if source_file.split('.')[-1] in GCODE_EXTENSIONS:
                usb_file = os.path.join(usb_folder,source_file)
                shutil.copy2(os.path.join(source_folder,source_file),usb_file)
                print("%s copiado" % usb_file)
        return source_files
    else:
        return False

def get_usb_folder():
    if utils.isWindows():
        removable_disks = [d.device for d in psutil.disk_partitions() if 'removable' in d.opts]
    else:
        #media_path = str(Path.home()).replace("home","media") if utils.isRaspberry() else '/media'
        media_path = '/media'
        if not os.path.isdir(media_path): return
        removable_disks = [os.path.join(media_path,d) for d in os.listdir(media_path)]
    cnc_name = utils.get_cnc_name()
    if not cnc_name: return
    for disk in removable_disks:
        files = os.listdir(disk)
        for file in files:
            if cnc_name in file:
                return disk
        
        #Revisa si hay una carpeta con el nombre de la maquina y lo regres
        #No sirve en maquinas que no abren la carpeta en el control, como la ar works
        #folder = os.path.join(disk,cnc_name)
        #if os.path.exists(folder): return folder


_exit=False
async def run():
    sync = True
    source_folder = utils.get_queue_sync_folder()
    while not _exit:
        try:
            usb_folder = get_usb_folder()
            if usb_folder and sync:
                clean_usb(usb_folder)
                clone_dir(source_folder, usb_folder)
                sync = False
            elif not usb_folder and not sync:
                sync = True
        except Exception as e:
            logging.exception("USB Error :(")
        if not _exit: await asyncio.sleep(3)
async def exit_():
    global _exit
    _exit=True