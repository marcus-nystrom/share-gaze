# -*- coding: utf-8 -*-
"""
Code to run a find Wally experiment.
"""

#from psychopy import parallel, core
from psychopy import visual, monitors, core, event
from iView import iview_SDK 
import CastThread
import socket
import numpy as np
import sys, os
import constants_wally # Imports variables from the constants_wally.py file.


def main(argv):
    '''
    Example call: client_demo.py 1 1
    '''
    
    this_dir = os.path.abspath(os.path.dirname(__file__))  # os.getcwd()
    os.chdir(this_dir)
    
    RT = core.Clock()
    
    # Default parameters
    eye_tracking   = False   # Use eye tracker of just simulate data
    server_control = False   # Controlled by server (or participant control)
    
    ## If any input parameters are given
    if len(argv) > 0:    
        eye_tracking   = int(argv[0]) == 1
    if len(argv) > 1:
        server_control = int(argv[1]) == 1
        
    # Set up monitor
    mon = monitors.Monitor(constants_wally.PSYCHOPY_MONITOR_NAME)
    mon.setWidth(constants_wally.SCREEN_WIDTH)    # Width of screen (cm)
    mon.setDistance(constants_wally.SCREEN_EYE_DIST) # Distance eye / monitor (cm) 
    mon.setSizePix(constants_wally.SCREEN_RES)
    
    #create a window to draw in
    scale_f_window = 1 # Make the PsychoPy window smaller than the screen?
    win =   visual.Window(constants_wally.SCREEN_RES*scale_f_window,fullscr=False,allowGUI=False,color=(0,0,0), monitor=mon, units='deg',screen=0)
    
    # An instruction text object
    instruction_text = visual.TextStim(win,text='',wrapWidth = 20,height = 0.5)
    dotStim = visual.GratingStim(win, color='red', tex=None, mask='circle',size=0.4)
    dotStim_c = visual.GratingStim(win, color='black', tex=None, mask='circle',size=0.55)
    
    
    # Add the picture
    im_search = visual.ImageStim(win, image='wally_search.jpg')
    im_face = visual.ImageStim(win, image='wally_face.jpg')
    wally_pos = constants_wally.WALLY_POS
    
    # Multicast xy and Listen (UDP)
    my_ip  = socket.gethostbyname(socket.gethostname())
    xyCasting = CastThread.MultiCast(my_ip)
    xyCasting.setReceiveOwn(receiveOwn = True)
    xyCasting.start()
    
    # Each participant's dot should have a different color
    dot_color = []
    for i in range(26):
        dot_color.append(xyCasting.get26colors(int(i)))     
    
    # Wait for a multicast message 'calibrate'
    if server_control and eye_tracking:
        instruction_text.setText('Waiting for message to start calibration ')
        instruction_text.draw()
        win.flip()    
        message_received = False
        while not message_received:
            allData = xyCasting.consumeAll()
            for data, addr, time_arrive in allData:
                if 'calibrate' in data:
                    message_received = True            
    
    # Initializes the eye tracker class and calibrates
    if eye_tracking:
        et = iview_SDK.mySDK_class(computer_setup = 'one_PC') 
        et.setup_calibration_parameters(bg_color=128,fg_color = 64)
    
        # Calibrate and validate the eye tracker
        et.calibrate(win,instruction_text) 
        
        # Send message that calibration is successfully performed
        if server_control:
            xyCasting.send('done_calibrating') # optionally send calibration accuracy
            
    # This is Wally
    im_face.pos = (0,-5)
    im_face.draw()       
    
    # Wait for the server script to start the experiment
    if server_control:
        
        instruction_text.setText('Press the spacebar as soon as you have found Walley \n\n Please wait for the experiment to start. ')
        instruction_text.draw()
        win.flip()        
        
        message_received = False
        while not message_received:
            allData = xyCasting.consumeAll()
            for data, addr, time_arrive in allData:
                if 'start' in data:
                    message_received = True     
                    
    else:
        instruction_text.setText('Press the spacebar as soon as you have found Walley \n\n Press a key to start. ')
        instruction_text.draw()
        win.flip()
        event.waitKeys()
    
    event.clearEvents()
    
    # Show image
    im_search.draw()
    win.flip()
    
    RT.reset()
    
    if eye_tracking:
        et.start_recording()
        et.start()
    #core.wait(1)
    
    # Display a gaze contingent marker
    key_pressed = False
    k = ''
    while not key_pressed:
            
        # Get samples
        if eye_tracking:
            t,x,y = et.get_all_samples(mon = mon)
            t = np.mean(t)
            x = np.mean(x)
            y = np.mean(y)
            #print(x,y)
        else:
            t = 0
            # NB: this all operates in degrees!
            x = np.random.rand(1) + float(my_ip.split('.')[-1])*.75
            y = np.random.rand(1) + float(my_ip.split('.')[-1])*.75
            x = x[0]
            y = y[0]
    
        # Draw image        
        im_search.draw()
        
        # Multicast data to all clients in multicast group
        xyCasting.send(','.join([str(t),str(x),str(y)]))
        
        
        # Read multicast data and draw positions
        #allData = xyCasting.consumeAll()
        allData = xyCasting.getNewest()
        #print(x,y,allData) 
        for data, addr, time_arrive in allData:
            
            if 'stop' in data:
                key_pressed = True
                rt = np.inf
                break
            
            if 'exp_done' in data:
                continue
            
            # Check whether the data contains the right number of elements
            data_t = data.split(',')
            if len(data_t) == 3:
                # Get t,x,y and draw on screen
                ti, xi, yi = data_t
                xi = float(xi)
                yi = float(yi)    
            else:
                continue

            # Get color for specific client  
            temp_ip = int(addr[0].split('.')[-1])
            if temp_ip > 25:
                ci = xyCasting.get26colors(int(temp_ip))
            else:
                ci = dot_color[temp_ip]            
            
            # Draw position
            dotStim.color = ci
            dotStim.pos = ((xi,yi))
            dotStim_c.pos = ((xi,yi))
            dotStim_c.draw()
            dotStim.draw()
            
        # Show screen when all data have been received
        win.flip()
            
        # Check for keypress
        k = event.getKeys(timeStamped = RT)
        if k:
            key_pressed = True
            rt = k[0][1]  # Store reaction time
    
    # Send message that experiment is done and the search time
    if server_control:
        xyCasting.send(' '.join(['exp_done',str(rt)]))
        
    xyCasting.stop()
    xyCasting.clean_up()
    
    # Stop multicasting thread
    if eye_tracking:
        et.stop()
        et.stop_recording()
        et.clear_buffer()
        et.disconnect()
    
    # Highlight the correct location of Wally
    im_search.draw()
    instruction_text.setColor('blue')
    instruction_text.setHeight(1.5)
    instruction_text.setPos((wally_pos[0],wally_pos[1]+2))
    instruction_text.setText('Here is Wally')
    instruction_text.draw()    
    instruction_text.setHeight(3)
    instruction_text.setPos(wally_pos)
    instruction_text.setText('o')
    instruction_text.draw()
    
    # Also draw the gaze location at the time of the decision (TODO)
    
    win.flip()
    core.wait(5)
    
    
    win.close()
    core.quit()

if __name__ == "__main__":
    main(sys.argv[1:])




