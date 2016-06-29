# -*- coding: utf-8 -*-
'''
Constants used in the Wally demo
Set up these to match the geometry in your own setup
'''

import os

SCREEN_RES              = [1680,1050]   # Pixels
SCREEN_WIDTH            = 47            # width of screen in cm
SCREEN_EYE_DIST         = 70            # Distance between eye and screen, i.e., the viewing distance

WALLY_POS               = (0.0,-9.5)    # Position of Wally in the picture (in deg), (0,0)
                                # denote center of screen            

PSYCHOPY_MONITOR_NAME= 'testMonitor'


CLIENT_PATH             = os.path.join('C:',''.join([os.sep,'Share',os.sep,'demo_shared_gaze',os.sep]))
CLIENTS                 = [21,22,24] # Set the clock on these clients
                            
MAX_SEARCH_TIME         = 20             

EYE_TRACKING            = False
SERVER_CONTROL          = True        
                            
IP_prefix               = '192.168.1.'
UDP_IP_SEND             =   IP_prefix+'255'
UDP_IP_LISTEN           = '0.0.0.0'
UDP_PORT                = 9090                    




