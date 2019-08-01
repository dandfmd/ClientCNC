# Machine Client
Machine Client converts any device into a remote IOT CNC controller.  works alongside the Production Cloud Server.

hello

### Integration with the production server
The client can be understood as a g-code file queue container installed on a local machine that can perform certain tasks remotely from the production server, such as:
 - Live CNC control and g-code previsualization with [Tiny-G](https://github.com/synthetos/TinyG) and [GRBL](https://github.com/grbl/grbl) controlled machines with [Chilipeppr](http://chilipeppr.com/)
 - Remote USB emulator for machines with their own working UI (client must be installed on [rpi zero](https://www.raspberrypi.org/products/raspberry-pi-zero-w/))
 - USB hub for file transfer (all g-code files in queue are copied to an external USB when inserted into the host computer)

### Install

 1. [Download ZIP file from GitHub.](https://github.com/dfmdmx/ProductionCloud_MachineClient/archive/master.zip)
 2. Unzip the file and open or cd into the recently extracted folder named `ProductionCloud_MachineClient-master`.
 3. Run the client:  
  -  **Linux:**  
 Type `python3 MachineClient.py` into the console. You might need to install some extra libraries from pip. Try running `python3 MachineClient.py -setup` for the script to attempt to install them. For manual install run `pip install -y pbkdf2 websockets requests fcntl asyncio psutil shutil`.

  - **Windows:**  
   Double click any of the executable files. Use Console version for the first setup.
     - `MachineClient_Console_win64.exe`
     - `MachineClient_NoConsole_win64.exe`

 4. Login into the production server. Under machines menu select new machine. You will be prompted to name your new connected client, continue until machine setup completes. You may need to reload the page to access the new machine.

 **Note:** Windows users can't change the host's computers Wi-Fi settings.

### Live control using Chilipeppr
 In order to connect to a [Tiny-G](https://github.com/synthetos/TinyG) or [GRBL](https://github.com/grbl/grbl) CNC machine just plug the controller into the computer's USB port. The machine client will then run [Chilipeppr](http://chilipeppr.com/) `serial-port-json-server` to interface with the CNC controller. This file is stored externally in a folder named `chilipeppr_serial`.

 **Note:** Windows users might need to unblock the `serial-port-json-server` file.

### USB hub
You will need to place an empty text file named after your machine in the root directory of your external USB in order to be detected by the client. For example if your machine's name is OldShapeoko then the file should be named `OldShapeoko.txt`. Once inserted into the computer the client will delete and update all the `.nc` and `.txt` files in the root directory. We recommend using a dedicated USB stick to avoid problems.
