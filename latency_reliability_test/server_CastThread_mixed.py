# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 11:09:51 2015
@author: marcus
"""
from __future__ import division
import time
import datetime
import numpy as np
import socket
from psychopy import event
import CastThread
import os

f = open('batch.txt')
my_ip = UDP_IP_LOCAL = socket.gethostbyname(socket.gethostname())

# time to wait for a response from the clients
# The clients should run for at least this time
max_wait_time = 20

IP_prefix = '192.168.1.'
UDP_IP_SEND =   IP_prefix+'255'

UDP_PORT = 9090
current_ip = UDP_IP_SEND

# Reference timestamp
epoch = datetime.datetime(2015, 9, 1, 2)

def create_broadcast_socket(ip = '0.0.0.0',port=9090):
    # Start broadcasting
    sock = socket.socket(socket.AF_INET, # Internet
                                  socket.SOCK_DGRAM) # UDP    
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    sock.bind((ip,port))             
    return sock                              

def getTimestamp():
    '''
    Gets current time stamp, returns float
    '''
    return (datetime.datetime.now() - epoch).total_seconds()
        
def get_ip_addresses(time_to_listen):
    '''
    Listen for a while to see which clients are active
    '''
    t0 = xyCasting.getTimestamp()
    ip_list = []
    while True:    
        allData = xyCasting.consumeAll()
        for data, addr, time_arrive in allData:
            if data:
                if addr[0] not in ip_list and addr[0] != my_ip:
                    ip_list.append(addr[0])
        if (xyCasting.getTimestamp() - t0) > time_to_listen:
            break
    return ip_list
    
def wait_for_clients(wait_time,ip_list):
    '''
    Wait until all clients have finished their tasks
    The clients sent a 'done' message when they have finished
    If a client has not finished within x s after the first client is done,
    first ask them politely to stop, and then kill them!
    '''
    
    i = 0
    first_timestamp_received = np.inf
    wait_till_done = True
    key_pressed = False
    success = True
    
    # Do this to empty the buffer
    allData = xyCasting.consumeAll()
    print('Numbers of clients at work: ',len(ip_list))
    while wait_till_done and not key_pressed:
                                    
            # If all the clients have answered that they're done, we can return
            if len(ip_list) == 0:
                print('All clients finished successfully')
                wait_till_done = False
        
            # If enough time has passed from the time the first client was done, try to stop all others
            if (xyCasting.getTimestamp() - first_timestamp_received) > wait_time and i == 1:
                xyCasting.send('stop!')
                time.sleep(1)
                xyCasting.send('stop!')
                print('Try to stop the remaining clints')
                i += 1
                
            # If enough time has passed from the time the first client was done, try to stop all others
            # Broadcast message
            if (getTimestamp() - first_timestamp_received) > wait_time*2:
                success = False
                wait_till_done = False
                                        
            # Receive data from clints
            allData = xyCasting.consumeAll()
            for data, addr, time_arrive in allData:
                if data and addr[0] != my_ip:   # prevent adding self to list, or we'll never exit
                    #print(data)
                    if 'done' in data and addr[0] in ip_list:
                        ip_list.remove(addr[0])
                        #print(addr[0]+' done!')
                        if i == 0:
                            first_timestamp_received = xyCasting.getTimestamp()
                            print('First client done!',data,addr[0])
                            i += 1                        
                        
            # Check if someone pressed the escape key
            keyname = event.getKeys(keyList=['escape'])
            if keyname:
                key_pressed = True        
    return success, ip_list   
###############################################################################    
# MAIN SCRIPT STARTS HERE
###############################################################################
sock = create_broadcast_socket()
sock.sendto('taskkill /im python.exe /f /t', (UDP_IP_SEND, UDP_PORT))
time.sleep(1)

# Turn off screens
nircmd_path =  os.path.join('C:',os.sep,'Share','hgDee')
#sock.sendto(''.join([nircmd_path,os.sep,'nircmd.exe monitor off']), (UDP_IP_SEND, UDP_PORT))

for l in f:
    
    # if ip-address, set to current
    if l[0].isdigit() or 'self' in l:
        current_ip = l.strip('\n')
        #print(current_ip)
    elif '#' in l:
        pass
    elif not l:
        pass
    elif 'wait' in l:
        wait_time =  int(l.split('=')[1])/1000.0# parse string to extract time in s.
        print('wait: '+str(wait_time)+' '+current_ip)        
        time.sleep(wait_time)
    else:
        # else python command to do something
        #print(l, (current_ip, UDP_PORT))
        if 'self' in current_ip:
            pass
        else:
            sock.sendto(l.strip('\n'), (current_ip, UDP_PORT))
        
        # if the server script is started with command 'server_CastThread.py 1'
        if 'server_CastThread.py' in l:
            # Switch from broadcasting to multicasting
            #sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            time.sleep(2)
            xyCasting = CastThread.MultiCast()
            xyCasting.start()
            t0 = xyCasting.getTimestamp()
            
            message = ','.join(('start', str(t0)))
            xyCasting.send(message) # Perhaps something addition is required to sent individual messages to multicast gorup
            time.sleep(1)
            
            # Get the ip-addresses of all the clients that are currently working
            ip_list = get_ip_addresses(max_wait_time/2)
            print(ip_list)
            
            # Wait for the clients to finish
            all_clients_completed, ip_list = wait_for_clients(max_wait_time,ip_list)
            print(ip_list)
            
            print(xyCasting.getTimestamp()-t0)
            # Switch back to broadcasting
            xyCasting.stop() # stop multicasting
            xyCasting.clean_up() 
            time.sleep(1)
            sock = create_broadcast_socket()
            if not all_clients_completed:
                for ip in ip_list:
                    sock.sendto('taskkill /im python.exe /f /t', (ip, UDP_PORT))
                print('Some clients did not finish and were killed: '+str(ip_list))
            
        #print(l)
        
#sock.sendto(''.join([nircmd_path,os.sep,'nircmd.exe monitor on']), (UDP_IP_SEND, UDP_PORT))

sock.shutdown(socket.SHUT_RDWR)
sock.close()    