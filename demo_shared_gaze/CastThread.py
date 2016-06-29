# -*- coding: utf-8 -*-
"""
Class to multicast (send and receive) eye gaze or simulated gaze in real time in a separate thread
and also to syncronize clocks and check time diffs against clients (initiated by server PC)
Clients may connect and disconnect to a session ad hock.

Written by Henrik Garde, Humanities Lab, LU <henrik.garde@humlab.lu.se>
Marcus Nystrom, Humanities Lab, LU  <marcus.nystrom@humlab.lu.se>
Diederick Niehorster, Humanities Lab, LU  <diederick_c.niehorster@humlab.lu.se>

Incorporates code from IOhub written by Sol Simpson and a class written by
Michael MacAskill <michael.macaskill@nzbri.org>.

See client_xyCastThread.py as a sample on how to use this class.
"""
import threading  
import socket
import datetime
import sys
import struct
from collections import deque

# 26 colors from The Colour Alphabet Project suggested by Paul Green-Armytage
# designed for use with white background:
col = (240,163,255),(0,117,220),(153,63,0),(76,0,92),(25,25,25),\
      (0,92,49),(43,206,72),(255,204,153),(128,128,128),(148,255,181),\
      (143,124,0),(157,204,0),(194,0,136),(0,51,128),(255,164,5),\
      (255,168,187),(66,102,0),(255,0,16),(94,241,242),(0,153,143),\
      (224,255,102),(116,10,255),(153,0,0),(255,255,128),(255,255,0),(255,80,5)

# for timestamping. Don't use Unix epoch but something
# recent so we have enough precision in the returned timestamp
epoch = datetime.datetime(2015, 9, 1, 2)

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
        
        # do not request exclusive access to the socket (or something loike that), should sovle the issue where a socket appears blocked
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #TODO : Check meaning of this binding 'bind':
        self.server_address = ('', dcMultiPort)
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
        self.outputCache  = [None for i in range(32)]   # each computer will have one slot in here, by IP address. Our's go till 28, have a few extra in case assigned by DHCP

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
    
    def getNewest(self):
        while self.outputBuffer:
            a = self.outputBuffer.popleft()
            ip = int(a[1][0].split('.')[-1])
            self.outputCache[ip] = a
        
        # clear out missing and return
        return [x for x in self.outputCache if x is not None]
        
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
                #print (data,addr,self.getTimestamp())
            except Exception:
                # TODO: when does this occur?
                #print 'exception'
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
       
    def get26colors(self,i):
        if i > 25:
            i = 0
        return '#%02x%02x%02x' % col[i]       