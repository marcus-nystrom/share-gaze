# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 11:09:51 2015
REMEMBER TO START TIME SERVER!
@author: marcus
"""
from __future__ import division
import time
import socket
import CastThread
import os
from psychopy import visual, core, event
import constants_wally



def create_broadcast_socket(ip = '0.0.0.0',port=9090):
    # Start broadcasting
    sock = socket.socket(socket.AF_INET, # Internet
                                  socket.SOCK_DGRAM) # UDP    
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    sock.bind((ip,port))             
    return sock                              

        
  
###############################################################################    
# MAIN SCRIPT STARTS HERE
###############################################################################
# Setup psychopoy screen
win =   visual.Window([800,600],screen=1)
text =  visual.TextStim(win,text='',wrapWidth = 0.5,height = 0.1)

my_ip = UDP_IP_LOCAL = socket.gethostbyname(socket.gethostname())


eye_tracking = constants_wally.EYE_TRACKING
server_control = constants_wally.SERVER_CONTROL

sock = create_broadcast_socket()
sock.sendto('taskkill /im python.exe /f /t', (constants_wally.UDP_IP_SEND, constants_wally.UDP_PORT))
time.sleep(1)

# start eye tracker
if eye_tracking:
    sock.sendto("C:\Program Files (x86)\SMI\RED-m Configuration Tool\iViewREDm-Client.exe", 
                (constants_wally.UDP_IP_SEND, constants_wally.UDP_PORT))
    time.sleep(5)


# Start script by broadcasting message
call = ' '.join(['client_wally.py',str(int(eye_tracking)),str(int(server_control))])
filename =  os.path.join(constants_wally.CLIENT_PATH,call)


text.setText('Press any key to start scripts on clients: '+str(constants_wally.CLIENTS))
text.draw()
win.flip()
event.waitKeys()

for i in constants_wally.CLIENTS:
    print('python '+filename)
    sock.sendto('python '+filename, (constants_wally.IP_prefix+str(i), constants_wally.UDP_PORT))

# Close broadcast socket and start multicast thread
sock.close()
#time.sleep(2)

text.setText('Clients started: '+str(constants_wally.CLIENTS))
text.draw()
win.flip()
time.sleep(2)

if server_control:
    
    xyCasting = CastThread.MultiCast()
    xyCasting.start()      
    
    # Tell the clients to start the calibration
    time.sleep(1)
    if eye_tracking:
        text.setText('Press any key to start a calibration')
        text.draw()
        win.flip()        
        event.waitKeys()
        xyCasting.send('calibrate') 
        

        # Don't proceed until all the clients have reported that they're done!
        ip_list_temp = constants_wally.CLIENTS[:]        
        text.setText('Calibration in progress\n\n Remaining clients: '+str(ip_list_temp))
        text.draw()
        win.flip()        
        time.sleep(1)
        while ip_list_temp:
            allData = xyCasting.consumeAll()
            for data, addr, time_arrive in allData:
                if 'done_calibrating' in data:
                    print(addr[0] + ' done calibrating')
                    ip_list_temp.remove(int(addr[0].split('.')[-1]))
                    text.setText('Calibration in progress\n\n Remaining clients: '+str(ip_list_temp))
                    text.draw()
                    win.flip()        
                    
            # proceed also if 'q' is pressed
            k = event.getKeys(['q'])
            if k:
                break
            
                    
                    
                
    # Start experiment when all clients are done calibrating
    #xyCasting.stop()
    text.setText('Press any key to start the experiment')
    text.draw()
    win.flip()   
    event.waitKeys()
    xyCasting.send('start') 

    
    # Wait for the clients to finish and store reaction times
    ip_list_temp = constants_wally.CLIENTS[:]  
    search_time = []       
    text.setText('Waiting for clients to finish\n\n Remaining clients: '+str(ip_list_temp))
    text.draw()
    win.flip()        
    time.sleep(1)    
    t0 = core.getTime()
    while ip_list_temp:
        allData = xyCasting.consumeAll()
        #print(allData)
        for data, addr, time_arrive in allData:
            if 'exp_done' in data:
                ip = int(addr[0].split('.')[-1])
                rt = float(data.split(' ')[1])
                ip_list_temp.remove(ip)
                search_time.append([ip,rt])
                text.setText('Waiting for clients to finish\n\n Remaining clients: '+str(ip_list_temp))
                text.draw()
                win.flip()    
                
        # Stop all clients if the maximum search time has been reached
        if (core.getTime() - t0) >= constants_wally.MAX_SEARCH_TIME:
            xyCasting.send('stop') 
            break
        time.sleep(0.001)   
        
        # proceed also if 'q' is pressed
        k = event.getKeys(['q'])
        if k:
            xyCasting.send('stop') 
            break

# Close the multicast socket
xyCasting.stop()
xyCasting.clean_up() 

text.setText('Done!')
text.draw()
win.flip()
time.sleep(10)
win.close()

# Print reaction times and winners
if search_time:
    print(sorted(search_time, key=lambda st: st[1]) )


core.quit()
#sock.shutdown(socket.SHUT_RDWR)
#sock.close()    