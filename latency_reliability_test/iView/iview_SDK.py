#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Load required packages 
from psychopy import core, event
from iViewXAPI import*
from iViewXAPIReturnCodes import* 
        

class mySDK_class:
    """
    Create a class that simplifies life for people wanting to use the SDK
    """
    def __init__(self, computer_setup='two_PC', port_listen=4444, port_send=5555):
        """
        Change IP-addresses to 127.0.0.1 if you're running a one computer setup
        """
        #TODO: 'one_PC': Why send via UDP to your own computer if you can just share memory? (Henrik is asking)
        # One or two computer setup [send IP, listen IP]
        setups = {'one_PC': ['127.0.0.1', '127.0.0.1'], 'two_PC': ['192.168.0.1', '192.168.0.2']}
        
        self.IP_address_listen = setups.get(computer_setup)[0]
        self.port_listen = port_listen
        self.port_send = port_send
        self.IP_address_send = setups.get(computer_setup)[1]
        
        # Connect to the eye tracker and setup calibration parameters directly 
        # when the object is created
        self.Fs = self.connect()
        self.setup_calibration_parameters()
        self.stop_recording()
        
    def connect(self):
        """
        Connect to eye tracker
        """
        res = iViewXAPI.iV_Connect(c_char_p(self.IP_address_listen),
                                   c_int(self.port_listen),
                                   c_char_p(self.IP_address_send),
                                   c_int(self.port_send))
        if res != 1:
            HandleError(res)
            exit(0)
        
        iViewXAPI.iV_StopRecording()
        res = iViewXAPI.iV_ClearRecordingBuffer()
        
        # Get system info 
        res = iViewXAPI.iV_GetSystemInfo(byref(systemData))
        Fs = systemData.samplerate
       
        return Fs
    
    def setup_calibration_parameters(self,
                                     autoaccept=1,
                                     bg_color=128,
                                     screen=0,
                                     fg_color=255,
                                     cal_method=5,  # number of calibration points
                                     cal_speed=1,
                                     target_size=20,  # in pixles
                                     target_shape=2,  # image - 0, circle -1, circle2 - 2 (default), cross - 3
                                     visualization=1,  # API visualization (use API to calibrate)
                                     target_filename=''):  # only if target_shape = 0
                                                            
        """
        Setup calibration parameters (but do not initiate calibration)
        An option to define position of calibration point (TODO)
        1-autoAccept
        2-background Brightness
        3- displayDevice
        4 - foreground Brightness
        5 - cal method
        6 - speed (cal)
        7 - target Filename[256]
        8 - targetShape
        9 - targetSize
        10 - visualization
        
        """
        calibrationData = CCalibration(cal_method,
                                       visualization,
                                       screen,
                                       cal_speed,
                                       autoaccept,
                                       fg_color,
                                       bg_color,
                                       target_shape,
                                       target_size,
                                       b"")
        res = iViewXAPI.iV_SetupCalibration(byref(calibrationData))
        
    def set_cal_positions(self, cal_positions):
        """
        Sets the positions of the calibration locations
        cal_positions is a dict:  {1:[x,y],2:[x,y],....}
        """
        if cal_positions:
            for k in cal_positions.keys():
                change_calibration_point(k, cal_positions[k][0], cal_positions[k][1])    
                
    def change_calibration_point(self, number, positionX, positionY):
        res = iViewXAPI.iV_ChangeCalibrationPoint(number, positionX, positionY)

    def calibrate(self, myWin, instructionText, show_instructions=True,
                  select_best_calibration=False, optional=False):
        """
        Calibrate the system until desired accuracy is met, or choose the best 
        calibration (selection with numerical value from keyboard)
        myWin is a psychopy window object, and instructionText is a psychopy text object
        """
        
        # Optional calibration
        if optional:
            instructionText.setText('Press q to calibrate or any other key to continue')
            instructionText.draw()
            myWin.flip()
            k = event.waitKeys()
            if not 'q' in k[0]:   
                return
                
        # Show calibration instructions
        if show_instructions:
            instructionText.setText(
                'A number of dots will be presented on the screen. Please look in the center of each dot\n '
                '(press space to begin).')
            instructionText.draw()
            myWin.flip()
            event.waitKeys()
            
        calibrationDone = False
        nCalibrations = 1
        deviations = []
        while not calibrationDone:
            
            myWin.winHandle.minimize()
            res = iViewXAPI.iV_Calibrate()
            res = iViewXAPI.iV_Validate()
            res = iViewXAPI.iV_GetAccuracy(byref(accuracyData), 0)
            
            # Show calibration screen (TODO)
            #TODO Save calib results to script (Henrik)
#            res = iViewXAPI.iV_ShowAccuracyMonitor()
            
            myWin.winHandle.maximize()
            myWin.winHandle.activate()
            
            # Save result of calibration
            if select_best_calibration:
                self.save_calibration(str(nCalibrations))
                deviations.append(''.join([' LX: ', str(accuracyData.deviationLX),
                                           ' LY: ', str(accuracyData.deviationLY),
                                           ' RX: ', str(accuracyData.deviationRX),
                                           ' RY: ', str(accuracyData.deviationRY)]))
                
                # Print a list of deviations from all calibrations and choose one to continue
                ins = ''
                for i in range(len(deviations)):
                    ins = ''.join([ins, 'Calibration: ', str(i+1), '\t', deviations[i]+'\n'])
                    
                #TODO Move theses customised parts out of SDK and out of class: Should be set in script (Henrik):
                ins = ''.join(['Tryck q för att kalibrera en gång till eller välj en av dem genom att mata in en siffra\n',
                               ins])
            else:
                ins = ''.join(['Accuracy: ',
                               ' LX: ',
                               str(accuracyData.deviationLX),
                               ' LY: ',
                               str(accuracyData.deviationLY),
                               ' RX: ',
                               str(accuracyData.deviationRX),
                               ' RY: ',
                               str(accuracyData.deviationRY),
                               '\n(Press q to calibrate again or Space to continue)'])
                
            instructionText.setText(ins.decode("utf-8"))
            instructionText.setPos((0, 0))
            core.wait(0.1)
            instructionText.draw()
            myWin.flip()
            
            # Wait until a valid key is pressed ('q' or a number indicating the calibration to be used)
            valid_choice = False
            while not valid_choice:
                k = event.waitKeys()
                if 'q' in k[0]:
                    nCalibrations += 1
                    valid_choice = True
                elif 'space' in k[0]:
                    valid_choice = True
                    calibrationDone = True
                elif k[0].isdigit():
                    if any([s for s in range(nCalibrations+1) if s == int(k[0])]):
                        self.load_calibration(k[0])  # Load the selected calibration
                        myWin.flip()
                        calibrationDone = True
                        valid_choice = True
                else:
                    instructionText.setText('Invalid choice')
            myWin.flip()
            
        return accuracyData

    def save_calibration(self, name):
        res = iViewXAPI.iV_SaveCalibration(c_char_p(name))
    
    def load_calibration(self, name):
        res = iViewXAPI.iV_LoadCalibration(c_char_p(name))

    def disconnect(self):
        res = iViewXAPI.iV_Disconnect()    
        
    def save_data(self, filename, session):
        res = iViewXAPI.iV_SaveData(filename, session, "", 1)
        
    def send_image_message(self, msg):
        iViewXAPI.iV_SendImageMessage(c_char_p(msg)) 
        
    def send_message(self, msg):
        iViewXAPI.iV_SendCommand(c_char_p(msg)) 
        
    def send_log_message(self, msg):
        iViewXAPI.iV_Log(c_char_p(msg))         
        
    def send_idf_log_message(self, msg):
        iViewXAPI.iV_SendCommand(c_char_p(''.join(['ET_AUX "',
                                                   msg, '"'])))

    def set_tracking_parameters(self, eye_type=0, parameter_type=3, activate=1):
        iViewXAPI.iV_SendCommand(c_char_p(''.join(["ET_SFT ",
                                                   str(eye_type), " ",
                                                   str(parameter_type), " ",
                                                   str(activate)])))

    def start_eye_image_recording(self, image_name):
#        print(''.join(["ET_EVB 1 ",image_name, " c:\\Marcus\\eyeimages\\"]))
        iViewXAPI.iV_SendCommand(c_char_p(''.join(["ET_EVB 1 ",
                                                   image_name,
                                                   " c:\\Marcus\\eyeimages\\"])))
        
    def stop_eye_image_recording(self):     
        iViewXAPI.iV_SendCommand("ET_EVE")
        
    def start_recording(self):
        iViewXAPI.iV_StartRecording()
        
    def get_sample(self):
        res = iViewXAPI.iV_GetSample(byref(sampleData))
        return res, sampleData
        
    def stop_recording(self):
        res = iViewXAPI.iV_StopRecording() 
         
    def increment_trial_number(self):
        res = iViewXAPI.iV_StopRecording()    
  
    def define_aoi_port(self, port):
        """
        Required to be able to send a gaze contingent TTL-trigger
        """
        res = iViewXAPI.iV_DefineAOIPort(port)
