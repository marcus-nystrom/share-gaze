# -*- coding: utf-8 -*-
"""
Server script to sync clocks
"""


import socket, time, os
import numpy as np
import constants_clock # Load constants

'''
Start windows time server if not done already. See
http://computerstepbystep.com/windows_time_service.html
for more information about how to interact with the time service
'''

# A way to check clock drifts
os.system('net start W32Time') 
time.sleep(3)


# Send message to all the clients
sock = socket.socket(socket.AF_INET, # Internet
                              socket.SOCK_DGRAM) # UDP

# Number (IP) of the clients you want to communicate with
clients = [str(s) for s in constants_clock.CLIENTS] 


sock.bind((constants_clock.UDP_IP_LISTEN,constants_clock.UDP_PORT)) 

# Set clock resolution to 0.5 ms
message = ''.join(['python ',constants_clock.CLIENT_PATH,''.join(['set_clock_resolution.py ',
                                                                  str(constants_clock.CLOCK_RESOLUTION)])])
print(message)
for c in clients:
    sock.sendto(message,         (''.join([constants_clock.IP_prefix,c]), constants_clock.UDP_PORT) )
    
time.sleep(5)

# Run a script that tests the clock resolution using
message = ''.join(['python ',constants_clock.CLIENT_PATH,'test_clock_resolution.py'])
print(message)
for c in clients:
    sock.sendto(message,         (''.join([constants_clock.IP_prefix,c]), constants_clock.UDP_PORT) )

time.sleep(5)

for i in np.arange(constants_clock.nRUNS):
    for j in np.arange(constants_clock.nCLOCK_SYNCS):
    
        # Just check the time, don't set the clock during the first iteration
        if j==0 or constants_clock.CHECK_ONLY:
            start_sync_message_first =  ''.join(['python ',constants_clock.CLIENT_PATH,'client_sync_clock.py',
                                                  ' ',str(constants_clock.nSYNC_CHECKS),' ','2',' ',
                                                  str(i),' ',str(j)])
            message = start_sync_message_first
        else:
            start_sync_message =        ''.join(['python ',constants_clock.CLIENT_PATH,'client_sync_clock.py',
                                                      ' ',str(constants_clock.nSYNC_CHECKS),' ',
                                                          str(constants_clock.METHOD_TO_SET_CLOCK),
                                                      ' ',str(i),' ',str(j)])         
            message = start_sync_message
    
        
        # Send message to all specified clients
        for c in clients:
            sock.sendto(message,         (''.join([constants_clock.IP_prefix,c]), constants_clock.UDP_PORT) )
            print(message,''.join([constants_clock.IP_prefix,c]))
            time.sleep(constants_clock.TIME_BETWEEN_CLIENTS)
            
        # Wait until the operation has finished (you need to estimate this funcion)
        time.sleep(constants_clock.TIME_BETWEEN_SYNCS)
        
        
        print(j)
    time.sleep(constants_clock.TIME_BETWEEN_RUNS)
    
time.sleep(5)

# Kill TimerTool process (resets clock to default value when no input parameter is given)
message = ''.join(['python ',constants_clock.CLIENT_PATH,'set_clock_resolution.py'])
for c in clients:
    sock.sendto(message,         (''.join([constants_clock.IP_prefix,c]), constants_clock.UDP_PORT) )

time.sleep(5)


## Send message to all specified clients
#message = ''.join(['python ',constants_clock.CLIENT_PATH,'collect_files.py',' -dc'])
#for c in clients:
#    sock.sendto(message,         (''.join([constants_clock.IP_prefix,c]), constants_clock.UDP_PORT) )
