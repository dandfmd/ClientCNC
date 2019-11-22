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

def install_dependencies():

    import subprocess
    import sys
    import pip
    import importlib
    
    requirements = [
        'pbkdf2',
        'websockets',
        'requests',
        'fcntl',
        'asyncio',
        'psutil',
        'shutil'
        ]
    
    print('This will attempt to install the required dependencies for the client')
    print('For manual install run: \'sudo pip install -y %s\'' % ' '.join(requirements))
    input('Press Enter to continue or Ctrl+C to exit')
    
    for requirement in requirements:
        try:
            importlib.import_module(requirement)
        except:
            try:
                call = subprocess.check_call([sys.executable, '-m', 'pip3' % version, 'install', requirement])
                print(call)
                print('%s installed' % requirement)
            except:
                print('Failed to install: %s'%requirement)
                if requirement == 'psutil': print('psutil only needed for windows client')
            
    print('Setup finished')
    print('Start client with: python3 linclient.py')

if __name__ == '__main__':
    install_dependencies()
