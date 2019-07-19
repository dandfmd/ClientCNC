# Machine Client
Machine Client converts any device into a remote IOT CNC controller. It works alongside the Production Cloud Server.

### Integration with the production server
The client can be understood as a g-code file queue container installed on a local machine that can perform certain tasks remotely from the production server, such as:
 - Live CNC control and g-code previsualization with Tiny-G and GRBL controlled machines with Chilipeppr (only on localhost network)
 - Remote USB emulator for non compatible machines (client must be installed on rpi-zero)
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
