# -*- coding: utf-8 -*-
"""
Sync the clock on a client against a time server. Keep trying until
the desired accuracy is met, or until a time out.

Requirements: one computer on the network set up as a time server.

Example call: 
'python C:\Share\client_sync_clock.py 5 10 3 0'

Input arguments:
0 - number of syncs to try to reach the offset
1 - method to set clock (0 - SP Timesync [must be installed], 1 - win32dll, 
                         2 - no sync, just check accuracy)
2 - run_i counter (nice to have these number in the text file)
3 - sync_i counter                          

- write results of best sync to txt-file.                                    
"""

import win32api
from socket import gethostname, gethostbyname
import os, sys, ntplib, time, datetime
import constants_clock

def main(argv):
    
    # Change directory
    this_dir = os.path.abspath(os.path.dirname(__file__))  # os.getcwd()
    os.chdir(this_dir)   
     
    # Use input parameters or defaults        
    if argv:    
        n_sync_checks = int(argv[0])
        method_to_set_clock =  int(argv[1]) #
        run_i =  argv[2]
        sync_i =  argv[3]
        
    else: # Default values if no input variables are given
        n_sync_checks = 10
        method_to_set_clock = 0 # default is to set the clock with SP timesynch
        run_i = str(0)
        sync_i = str(0)
        
    # Use SP Time sync to sync clocks
    c = ntplib.NTPClient() # Get a connection to the time client 
       
    # Create text file and write header
    t = datetime.datetime.now()
    ip = gethostbyname(gethostname()).split('.')[-1]
    f_name = '_'.join([ip,run_i,sync_i,str(t.year),str(t.month),str(t.day),
                       str(t.hour),str(t.minute),str(t.second)])
    f = open(f_name+'.txt','w')
    f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'    %
            ('sync_eval_i','time(ms)','offset(ms)','delay(ms)',
             'method_to_set_clock', 't_client_sent','t_server_received',
             't_server_sent', 't_client_received'))

    #--------------------------------------------------------------------------
    # Sync clocks
    #--------------------------------------------------------------------------  
        
    # Choose between different methods to set the clock.
    if method_to_set_clock == 0:
        sync_str = '"SP TimeSync.exe" auto'
        try:
            os.system(sync_str) # Execute DOS-command (must be administrator)
            print('Clock set using SP TimeSync')
        except:
            print('no sync performed...')
    elif method_to_set_clock == 1:
    
        # Get server time
        try:
            response = c.request(constants_clock.SERVER_ADDRESS,timeout=0.5)
            server_time = datetime.datetime.fromtimestamp(response.tx_time)
            
            # ..and set the clock
            win32api.SetSystemTime(server_time.year, server_time.month, 0, 
                                   server_time.day, server_time.hour-2, 
                                   server_time.minute, server_time.second, 
                                   int(server_time.microsecond/1000))            
            print('Clock set using win32api.SetSystemTime')                                       
            
        except:
            print("no response")
            time.sleep(0.1)
    else:
        print('Do not set the clock, just check the accuracy')                

        
    #--------------------------------------------------------------------------
    # Check how well the clocks are synched   
    #--------------------------------------------------------------------------        
    t = time.clock() # Reset clock

    for i in range(n_sync_checks):
        try:
            response = c.request(constants_clock.SERVER_ADDRESS,timeout=0.1)
            offset = response.offset  # Offset between server time and local time
            delay = response.delay    # Round-trip latency

            t_client_sent       = response.orig_timestamp
            t_server_received   = response.recv_timestamp        
            t_server_sent       = response.tx_timestamp
            t_client_received   = response.dest_timestamp
            
            t_ms = (time.clock() - t)*1000

            # Write results to text file
            f.write('%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.4f\t%.4f\t%.4f\t%.4f\n' % 
                    (i,t_ms,offset*1000,delay*1000,method_to_set_clock,
                     t_client_sent,t_server_received,t_server_sent,
                     t_client_received))
            
        except:
            print("no response")
            continue

           

    f.close()   # Close the text file for reading
#    p.kill()    # Close the TimerTool process 
   
if __name__ == "__main__":
    main(sys.argv[1:])
