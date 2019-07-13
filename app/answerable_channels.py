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

from random import randint
import json,asyncio
from abc import ABCMeta,abstractmethod
#esta clase nos deja usar un canal de tipo socket (read/write) como uno de request-response asyncronicamente
class Channel(metaclass=ABCMeta):
    def __init__(self,*args,**kargs):
        super(Channel, self).__init__(*args,**kargs)
        self._ac_futures={}
    @abstractmethod
    def send_ac_message(self,string):
        """sobreescribir con una funcion que envie el mensaje a remote"""
        pass
    @abstractmethod
    async def on_ac_request(self,command, data):
        pass
    async def _call_maybe_await(self,f,*args,**kargs):
        if asyncio.iscoroutinefunction(f):
            return await f(*args,**kargs)
        else:
            return f(*args,**kargs)
    async def on_ac_message(self,data):
        d=json.loads(data)
        resp=d.get("resp")
        if resp is not None:
            self._ac_futures.get(resp,asyncio.Future()).set_result(d.get("d"))
        else:
            req=d.get("req")
            if req is None: return
            try:
                response=await self._call_maybe_await(self.on_ac_request,d.get("d",{}).get("c"),
                            d.get("d",{}).get("d",None))
            except Exception as e:
                response={"s":False,"e":str(e)}

            else:
                response={"s":True,"r":response}
            try:
                await self._call_maybe_await(self.send_ac_message,json.dumps({"d":response,"resp":req},separators=(',', ':')))
            except: pass
    async def send_request(self,command,_dont_care_about_response=False,**data):
        req={"c":command}
        if len(data)!=0:
            req["d"]=data
        d={"d":req,"req":randint(0,1000000000)}
        await self._call_maybe_await(self.send_ac_message,json.dumps(d,separators=(',', ':')))
        if _dont_care_about_response:
            return
        fut=asyncio.Future()
        self._ac_futures[d["req"]]=fut
        try:
            result= await asyncio.wait_for(fut,10*60)
        finally:
            del self._ac_futures[d["req"]]
        if result.get("s",False):
            return result.get("r")
        else:
            raise RemoteException(result.get("e"))
    def send_request_and_forget(self,command,*args,**data):
        asyncio.ensure_future(self.send_request(command,*args,_dont_care_about_response=True,**data))
        
class FunctionalChannel(Channel):
    def __init__(self,*args,**kargs):
        super(FunctionalChannel, self).__init__(*args,**kargs)
        self.remote=Remote(self)
    async def on_ac_request(self,command,data):
        try:
            function=getattr(self, command)
        except AttributeError:
            raise Exception("Function %s not found"%command)
        if not _is_remote_func(function): raise Exception("Cannot call non-remote function %s: decorate using @remote"%command)
        if data is None: data={}
        return await function(**data)
    
class Remote():
    def __init__(self,channel):
        self.channel=channel
    def __getattr__(self,fname):
        async def function(**data):
            return await self.channel.send_request(fname,**data)
        return function
def _is_remote_func(func):
    return getattr(func, "__remote_function__",False)
def remote(func):
    if not asyncio.iscoroutinefunction(func): func=asyncio.coroutine(func)
    func.__remote_function__=True
    return func
class RemoteException(Exception):
    pass
