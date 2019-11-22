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

import os
import socket
import logging
import struct
import subprocess

from . import wifi
from . import utils
from .wifi.exceptions import InterfaceError

if utils.isWindows(): from . import fcntl
else: import fcntl

default_network_file ="""\
auto lo
iface lo inet loopback
iface eth0 inet dhcp
auto wlan0
allow-hotplug wlan0
"""

WLAN = "wlan0"
extra_name = "-False"

INTERFACES_FILE =  "/etc/network/interfaces"

def check_interfaces_file():
    if not utils.isRaspberry(): return
    if not os.path.exists(INTERFACES_FILE):
        f = open(INTERFACES_FILE,"w")
        with f: f.write(default_network_file)

def remove_extra_name():
    if not utils.isRaspberry(): return
    f = open(INTERFACES_FILE,"r")
    network_file = f.read()
    f.close()
    
    if extra_name in network_file:
        f = open(INTERFACES_FILE,"w")
        f.write(network_file.replace(extra_name,""))
        f.close()
    

def get_ip_address_for(ifname):
    
    if utils.isWindows():
        try:
            ip = utils.get_localip()
#             hostname = socket.gethostname()
#             ip = socket.gethostbyname(hostname)
            return ip if ip else None
        except Exception as e: print('Win global ip error: %s' % e)
    
    if type(ifname)==str:
        ifname=ifname.encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack(b'256s', ifname[:15])
        )[20:24])
    except IOError:
        return None
def get_ip_address():
    for a in ["eth0","eno1",WLAN]: #le damos preferencia a la direccion ethernet
        ip=get_ip_address_for(a)
        if ip: return ip
    return None
def set_wifi_network(network,password):
        if not utils.isRaspberry(): return
        cells=get_available_networks() #buscamos la red
        
        for cell in cells:
            if cell.ssid==network: break
        else: return False
        
        last_scheme=wifi.Scheme.find(WLAN,None)
        
        if last_scheme is not None:
            last_scheme.delete()
        scheme=wifi.Scheme.for_cell(WLAN,False,cell,password)
        scheme.save()

        try:
            scheme.activate()
            #remove_extra_name()
            return True
        except:
            logging.exception("wifi error")
            scheme.delete()
            if last_scheme is not None:
                try:
                    last_scheme.save()
                    last_scheme.activate()
                except: logging.exception("wifi error")
            return False

def get_available_networks(retry=True):
    if not utils.isRaspberry(): return []
    try:
        cells=wifi.Cell.all(WLAN)
        
        try:
            cells =[d for d in sorted(cells, key=lambda k: -k.signal if hasattr(k,"signal") else 0)]
        except:
            pass
        cells_widthout_duplicates=[]
        ssids=[]
        for cell in cells:
            if not cell.encrypted:
                continue #no permitimos redes abiertas
            if not cell.ssid in ssids:
                cells_widthout_duplicates.append(cell)
                ssids.append(cell.ssid)
        return cells_widthout_duplicates
    except InterfaceError:
        if retry:
            try:
                subprocess.check_output("sudo ifconfig %s up"%WLAN, shell=True)
                return get_available_networks(False)
            except: pass
        return []

def get_current_connected_network():
    if not utils.isRaspberry(): return
    try:
        curr= subprocess.check_output("sudo iwgetid -r", shell=True).strip().decode()
        if curr=="":
            return None
        return curr
    except:
        return None
