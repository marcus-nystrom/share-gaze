# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 11:09:51 2015
REMEMBER TO START TIME SERVER!
@author: marcus
"""
from __future__ import division
import time
import datetime
import socket
import CastThread
import os
from psychopy import visual, monitors, core, event



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


eye_tracking = True
server_control = True

IP_prefix = '192.168.1.'
UDP_IP_SEND =   IP_prefix+'255'

UDP_PORT = 9090
current_ip = UDP_IP_SEND

# Reference timestamp
IP_prefix = '192.168.1.'
UDP_IP_SEND =   IP_prefix+'255'

UDP_PORT = 9090
current_ip = UDP_IP_SEND    
    
# Enter ip-addresses of computers you want to use
ip_list = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
#ip_list = [2,22]

# Maximum allowed search time
max_search_time = 60

sock = create_broadcast_socket()
sock.sendto('taskkill /im python.exe /f /t', (UDP_IP_SEND, UDP_PORT))
time.sleep(1)

# start eye tracker
sock.sendto("C:\Program Files (x86)\SMI\RED-m Configuration Tool\iViewREDm-Client.exe", 
            (UDP_IP_SEND, UDP_PORT))
time.sleep(5)


# Start script by broadcasting message
call = ' '.join(['client_wally.py',str(int(eye_tracking)),str(int(server_control))])
filename =  os.path.join('C:',os.sep,'Share','demo_shared_gaze',call)


text.setText('Press any key to start scripts on clients: '+str(ip_list))
text.draw()
win.flip()
event.waitKeys()

for i in ip_list:
    print('python '+filename)
    sock.sendto('python '+filename, (IP_prefix+str(i), UDP_PORT))

# Close broadcast socket and start multicast thread
sock.close()
#time.sleep(2)

text.setText('Clients started: '+str(ip_list))
text.draw()
win.flip()
time.sleep(2)

if server_control:
    
    xyCasting = CastThread.MultiCast()
    
    # Tell the clients to start the calibration
    time.sleep(1)
    if eye_tracking:
        text.setText('Press any key to start a calibration')
        text.draw()
        win.flip()        
        event.waitKeys()
        xyCasting.send('calibrate') 
        

        # Don't proceed until all the clients have reported that they're done!
        ip_list_temp = ip_list[:]        
        text.setText('Calibration in progress\n\n Remaining clients: '+str(ip_list_temp))
        text.draw()
        win.flip()        
        time.sleep(1)
        xyCasting.start()      
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
    ip_list_temp = ip_list[:]  
    search_time = []       
    text.setText('Waiting for clients to finish\n\n Remaining clients: '+str(ip_list_temp))
    text.draw()
    win.flip()        
    time.sleep(1)    
    t0 = core.getTime()
    print(ip_list)
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
        if (core.getTime() - t0) >= max_search_time:
            xyCasting.send('stop') 
            break
        time.sleep(0.01)   
        
        # proceed also if 'q' is pressed
        k = event.getKeys(['q'])
        if k:
            xyCasting.send('stop') 
            break

# Close the multicast socket
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