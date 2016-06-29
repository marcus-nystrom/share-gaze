# -*- coding: utf-8 -*-
"""
Parameters used when synching clocks.
"""
import os

CLIENTS                 = [1,2,3,4,5,6,7,8,9,10,
                            11,12,13,14,15,16,18,19,20,
                            21,22,23,24,25] # Set the clock on these clients
                                                        
CLIENT_PATH             = os.path.join('C:',''.join([os.sep,'Share',os.sep,'sync_clocks',os.sep]))

IP_prefix               = '192.168.1.'
UDP_IP_LISTEN           = '0.0.0.0'
UDP_PORT                = 9090
SERVER_ADDRESS          = IP_prefix + '28'


CLOCK_RESOLUTION        = 15.6  # In ms

nRUNS                   = 1     # Number of times the sync-test should be run.
nCLOCK_SYNCS            = 2     # Number of times the clocks should be synched. 
                                # Each sync producesa text file with the results on the client machine.
                                # If nCLOCK_SYNCS < 2, only a check is made; the clock is not set.

TIME_BETWEEN_RUNS       = 0 # in s
TIME_BETWEEN_CLIENTS    = 0 # in s. Make sure taht the clock sync is done serially      
TIME_BETWEEN_SYNCS      = 0 # in s.

nSYNC_CHECKS            = 100 # Number of time to check the accuracy of the clock sync.
METHOD_TO_SET_CLOCK     = 0   # SP TimeSync is 0

CHECK_ONLY              = False # Set to True when you don't want to set the clock, only check its accuracy

