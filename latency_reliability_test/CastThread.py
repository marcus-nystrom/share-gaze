# Class to multicast (send and receive) eye gaze or simulated gaze in real time in a separate thread
# and also to syncronize clocks and check time diffs against clients (initiated by teachers PC)
# Clients may connect and disconnect to a session ad hock.
# ==================================================================================================
#
# Usage Notes: See client_xyCastThread.py as a sample on how to use this class.
#
# Example Usage in short:
#
# import CastThread
# etThread = CastThread.xEyeTrack()
# dataMyET = etThread.receiveNoBlock()
# multicastThread = CastThread.MultiCast()
# multicastThread.send(data)
# dataOtherET = multicastThread.receiveNoBlock()
# #do something ...
# multicastThread.stop()
#
# DC Server stuff (run from Teacher PC):
# time_diff, ip = send_to_set_time(time2set)
# run_time_check_loop
#
# 2012-04-17: v0.1: initial implementation
# 2015-04-01: v1.0: full implementation tested
# 2015-06-20: v1.1: time stamping using G_dll.dll
# 2015-09-11: v1.2: removed G_dll.dll time stamping, using run method to read fast
#
# Started by Michael MacAskill <michael.macaskill@nzbri.org>
# Changed by Henrik Garde, Humanities Lab, LU <henrik.garde@humlab.lu.se>
#            Marcus Nystrom, Humanities Lab, LU  <marcus.nystrom@humlab.lu.se>
#            Diederick Niehorster, Humanities Lab, LU  <diederick_c.niehorster@humlab.lu.se>
# - incorporates code from IOhub written by Sol Simpson

import threading  # this class is a thread sub-class
import socket
import time
import datetime
from psychopy import core, event, visual, monitors, misc
import numpy as np
import sys
import struct
import os
from collections import deque

# 26 colors from The Colour Alphabet Project suggested by Paul Green-Armytage
# designed for use with white background:
col = (240,163,255),(0,117,220),(153,63,0),(76,0,92),(25,25,25),\
      (0,92,49),(43,206,72),(255,204,153),(128,128,128),(148,255,181),\
      (143,124,0),(157,204,0),(194,0,136),(0,51,128),(255,164,5),\
      (255,168,187),(66,102,0),(255,0,16),(94,241,242),(0,153,143),\
      (224,255,102),(116,10,255),(153,0,0),(255,255,128),(255,255,0),(255,80,5)

def get26colors(i):
    if i > 25:
        i = 0
    return '#%02x%02x%02x' % col[i]

# for timestamping. Don't use Unix epoch but something
# recent so we have enough precision in the returned timestamp
epoch = datetime.datetime(2015, 9, 1, 2)


class xSmiEyeTrack(threading.Thread):

    # initialise with defaults:
    def __init__(self, port=5555, iViewIP="192.168.0.1", iViewPort=4444):
        
        # UDP port to listen for iView data on.
        # Set iView software to duplicate stream to this port number so that we don't conflict with 
        # the listening and sending on the main port number.
        
        # Ports that we send and receive on:
        self.port = port
        self.iViewPort = iViewPort
        
        # address to send some messages to iView
        self.iViewIP = iViewIP
        
        # Bind to all interfaces:
        self.host = '0.0.0.0'
        
        # Setup the socket:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # The size of the buffer we use for receiving:
        self.buffer = 4096
        
        # Bind to the local host and port
        self.sock.bind((self.host, self.port))
        
        # get iView to start streaming data
        self.send('ET_FRM "%ET %TU %SX %SY"')  # set the format of the datagram (see iView manual)
        self.send('ET_STR')  # start streaming (can also add optional integer to specify rate)

        # create self as a thread
        threading.Thread.__init__(self)
        
        self.__stop = False

    def getTimestamp(self):
        return (datetime.datetime.now() - epoch).total_seconds()
        #HG: Maybe '.utcnow.' is needed for pos diff tz on clients unless 2 overwrites the time zone
        # total_seconds() is equivalent to
        #   (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 computed with true division enabled.

    def disconnect(self):
        pass

    def stop_recording(self):
        pass


class iViewEyeTrack(threading.Thread):

    # initialise with own IP address and an optional standard calibration based on a PsychoPy win window:

#    mon = monitors.Monitor('default')
#    mon.setWidth(53.2)   # Width of screen (cm)
#    mon.setDistance(65)  # Distance eye monitor (cm)
#    screenSize = [1680, 1050]  # 'debug';: 800,600'
#    win = visual.Window(screenSize, fullscr=False, allowGUI=False, color=(0, 0, 0), monitor=mon, units='deg', screen=0)

    def __init__(self, mon, screenSize=[1680, 1050], skip_ringbuf=True,
                 port=5555, myIP=socket.gethostbyname(socket.gethostname()), iViewPort=4444,
                 pc_setup='one_PC',
                 calib_skip=False, calib_instruction_text='', calib_bg_color=128, calib_fg_color=64,
                 win=None):
        from iView import iview_SDK, iViewXAPI
        """
        above: 'None' inserted 20150422 by hg instead of:
        visual.Window(size=(800, 600),
                                   fullscr=False,
                                   allowGUI=False,
                                   color=(0, 0, 0),
                                   monitor=monitors.Monitor('default'),
                                   units='deg',
                                   screen=0)
        """

        # TODO??: (Henrik)
        # UDP port to listen for iView data on.
        # Set iView software to duplicate stream to this port number so that we don't conflict with
        # the listening and sending on the main port number.

        self.mon = mon
        self.mon.setWidth(53.2)   # Width of screen (cm)
        self.mon.setDistance(65)  # Distance eye monitor (cm)

        self.screenSize = screenSize
        self.skip_ringbuf = skip_ringbuf
        #misc (Henrik)
        self.my_ip = socket.gethostbyname(socket.gethostname())
        self.i = 0
        self.msg_i = 0
        self.x = 0
        self.y = 0
        self.state = 0
        self.res = 0

        # Create an instance of the eye tracker class (connects automatically)
        self.et = iview_SDK.mySDK_class(computer_setup=pc_setup)  # Also initializes the eye tracker

        # Calibrate and validate the eye tracker
        if not calib_skip:
            # Create PsychoPy window and text to show stimulus for calibration
            # TODO: Consider moving more text properties to class parameters
            self.calib_text = visual.TextStim(win, text=calib_instruction_text, wrapWidth=20, height=0.5)
            self.et.setup_calibration_parameters(bg_color=calib_bg_color, fg_color=calib_fg_color)
            self.et.calibrate(win, self.calib_text)



        # create self as a thread
        threading.Thread.__init__(self)

        self.__stop = False

    def getTimestamp(self):
        #return core.getTime()
        return (datetime.datetime.now() - epoch).total_seconds()
        #HG: Maybe '.utcnow.' is needed for pos diff tz on clients unless 2 overwrites the time zone
        # total_seconds() is equivalent to
        #   (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 computed with true division enabled.

    def start_recording(self):
        self.et.start_recording()

    def save_data(self, filename='test.idf'):
        # Save data
        self.et.save_data(filename)

    def disconnect(self):
        # Disconnect eye tracker
        self.et.disconnect()

    def stop_recording(self):
        # Stop eye tracker after 1 second
        core.wait(1.0)
        self.et.stop_recording()

    def next(self):
        # Get samples
        try:
            self.res, self.x, self.y = self.get_valid_data_sample()
#            print(self.res, self.x, self.y)
            if self.res is not 1:
                return 0, 0, 0
        except Exception:
            return 0, 0, 0
        else:
            return self.state, self.x, self.y


    def nextMsg(self):
        self.msg_i += 1

        # call next() first to update x,y, state

        message = ','.join((str(self.x),
                            str(self.y),
                            str(self.getTimestamp()),
                            str(self.msg_i),
                            str(self.state),
                            self.my_ip))
        return message


    def get_valid_data_sample(self):
        """
        Get onscreen samples, and convert to degrees
        Coordinate system is centered in the middle of the screen (0,0)
        """

        # Get samples
        x = 0
        y = 0
        res, sampleData = self.et.get_sample()
        if res == 1:

            # Make sure the the samples are on the screen
            xt = sampleData.rightEye.gazeX
            yt = sampleData.rightEye.gazeY

            # Make sure the the samples are on the screen and valid
            if np.any(xt <= 0 or xt > self.screenSize[0] or yt <= 0 or yt > self.screenSize[1]):
                pass
            else:
                x = xt - self.screenSize[0]/2
                y = -1 * (yt - self.screenSize[1]/2)
                x = misc.pix2deg(x, self.mon)
                y = misc.pix2deg(y, self.mon)

        return res, x, y


class simTrack(threading.Thread):

    # initialise:
    def __init__(self, simType="pingpong", casting=True):

        # A thread that streams a simulated track of x,y moving in optional patterns
        # Default is 'pinpong', a dot pendling from -1 to plus 1 at 60 Hz.

        # Type of data stream to generate
        self.simType = simType

        # Multicast data? True/False
        self.casting = casting

        # Iterator, stepsize and gaze direction
        self.my_ip = socket.gethostbyname(socket.gethostname())
        self.i = 0
        self.msg_i = 0
        self.x = 0
        self.y = 0
        self.x_step = 1.0 / 60.0 * 2.0
        self.x_dir = 1
        self.turn_i = 0
        self.state = 0
        self.state_changed = False

        # Create self as a thread
        threading.Thread.__init__(self)

        self.__stop = False

    def getTimestamp(self):
        return (datetime.datetime.now() - epoch).total_seconds()
        #HG: Maybe '.utcnow.' is needed for pos diff tz on clients unless 2 overwrites the time zone
        # total_seconds() is equivalent to
        #   (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 computed with true division enabled.

    def start_recording(self):
        self.msg_i = 0

    def nextMsg(self):
        self.msg_i += 1

        # call next() first to update x,y, state

        message = ','.join((str(self.x),
                            str(self.y),
                            str(self.getTimestamp()),
                            str(self.msg_i),
                            str(self.state),
                            self.my_ip))
        
        return message

    def next(self):
        self.x, turn_i = self.nextX()
        
        # Visualize state change (like dot color change) every 10th second
        if self.turn_i % 5 == 0:
            if not self.state_changed:
                self.state_changed = True
                self.state = -1
        else:
            self.state_changed = False
            self.state = 1
        
        return self.state, self.x, self.y

    def nextX(self):

        # returns x in a veritcal motion + a flag counting the turns if 'pingpong'
        if self.simType == "sinus":
            self.x = self.sinus(self.i * 0.1)
        else:
            self.x, self.x_dir, self.turn_i \
                = self.pingpong(self.x, self.x_step, self.x_dir, self.turn_i)
        self.i += 0.1

        return self.x, self.turn_i

    def sinus(self, i):
        return 0.5 * np.sin(i)

    def pingpong(self, x, x_step, x_dir, turn_i):
        # Animation for visual latency check
        x -= x_step * x_dir
        if x < -1.0:
            x_dir *= -1  # change direction
            turn_i += 1
        if x > 1.0:
            x_dir *= -1   # change direction
        return x, x_dir, turn_i

    def disconnect(self):
        pass

    def stop_recording(self):
        pass


class MultiCast(threading.Thread):

    # initialise:
    def __init__(self,  myIP="169.254.173.49", dcMultiPort=10000, dcMultiIP="224.0.0.9"):

        self.myIP = myIP
        # Ports that we send and receive on:
        self.dcMultiPort = dcMultiPort
        self.dcMultiIP = dcMultiIP
        self.multicastGroup = (dcMultiIP, dcMultiPort)

        # Create Socket object
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #TODO : Check meaning of this binding 'bind':
        self.server_address = ('', 10000)
        self.sock.bind(self.server_address)
        # TODO: internet suggests to use bind to the self.multicastGroup. difference is that if
        # ip is '', you get data from all multicast groups, if specific group ip, then you only get
        # data from that group

        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        group = socket.inet_aton(dcMultiIP)
        self.mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)
        # by defualt, don't receive own data:
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        # blocking, but with non-infinite timeout
        self.sock.settimeout(1)
        #self.sock.setblocking(0)
        self.buffer = 1024
        
        # deque for client to read from
        self.outputBuffer = deque()
        #self.outputBuffer = None

        # UDP port to listen and send x,y from sim or eyetracker data on.

        # create self as a thread
        threading.Thread.__init__(self)

        self.__stop = False
        
    def setReceiveOwn(self,receiveOwn):
        if receiveOwn:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        else:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

    def getTimestamp(self):
        return (datetime.datetime.now() - epoch).total_seconds()
        #HG: Maybe '.utcnow.' is needed for pos diff tz on clients unless 2 overwrites the time zone
        # total_seconds() is equivalent to
        #   (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 computed with true division enabled.

    def receiveNoBlock(self):
    # copied from iview.py
        """ Get any data that has been received
        If there is no data waiting it will return immediately
        Returns data (or 0 if nothing)"""

        self.sock.setblocking(0)
        try:
            data, addr = self.sock.recvfrom(1024)
        except Exception:
            return 0, 0
        else:
            return data, addr  #return xy?

    def receiveBlock(self,timeout=None):
    # copied from iview.py
        """ Get any data that has been received or wait until some is received
        If there is no data waiting it will block until some is received
        Returns data"""
        
        if timeout:
            self.sock.settimeout(timeout)
        else:
            self.sock.setblocking(1)
        try:
            data, addr = self.sock.recvfrom(self.buffer)
        except Exception:
            return 0, 0
        except self.sock.timeout:
            print >>sys.stderr, 'timed out, no more responses'
        else:
            return data, addr
    
    def consumeAll(self):
        ret = list()
        while self.outputBuffer:
            ret.append(self.outputBuffer.popleft())
        return ret
        
    def send(self, message):
        # Sending own data: x,y,time,i,ip
        try:
            self.sock.sendto(message, self.multicastGroup)
        except Exception:
            print "Could not send UDP message"
        #print(message)

    def send_to_client(self, message,ip,port=None):
        # Send data to specific client
        try:
            if port:
                self.sock.sendto(message, (ip, self.dcMultiPort))
            else:
                self.sock.sendto(message, (ip, port))          
        except Exception:
            print "Could not send UDP message"
        #print(message)
    # method which will run when the thread is called:
    # this assumes socket's read mode is blocking and is not changed out from under us
    def run(self):
        i = 0
        while True:
            if self.__stop:
                break
            i += 1
            try:
                data, addr = self.sock.recvfrom(self.buffer)
                self.outputBuffer.append((data,addr,self.getTimestamp()))
            except Exception:
                # TODO: when does this occur?
                pass
            except self.sock.timeout:
                print >>sys.stderr, 'timed out, no more responses'
            

    # so caller can ask for the thread to stop monitoring:
    def stop(self):
        #self.send("ET_EST")  # tell iView to stop streaming
        self.__stop = True   # the run() method monitors this flag
        
    def clean_up(self):
        '''
        Cleans up and makes sure the socket is ready for use next time        
        '''
#        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, self.mreq)
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()        