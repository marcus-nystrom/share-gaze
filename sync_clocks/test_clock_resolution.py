# -*- coding: utf-8 -*-
"""
Created on Wed Sep 09 13:04:53 2015

* If TimerTool.exe is running, kill the process.
* If input parameter is given, start TimerTool and set clock resolution
Starts TimerTool.exe and sets the clock resolution to argv[0] ms

Ex: python set_clock_resolution 0.5
@author: marcus
"""

import time, datetime
from socket import gethostname, gethostbyname
import os
import numpy as np

def main():
    
    my_path = os.path.join('C:',os.sep,'Share','sync_clocks')
    os.chdir(my_path)
    
    # Initial timestamps
    t1 = time.clock()
    t2 = time.time()
    t3 = datetime.datetime.now()
    
    td1 = []
    td2 = []
    td3 = []
    for i in xrange(100):
        td1.append(time.clock()-t1)
        td2.append(time.time() -t2)    
        td3.append((datetime.datetime.now()-t3).total_seconds())        
        time.sleep(0.001)
        
    # Create text file and write header
    t = datetime.datetime.now()
    ip = gethostbyname(gethostname()).split('.')[-1]
    f_name = '_'.join([ip,'test_clock_res',str(t.year),str(t.month),str(t.day),
                       str(t.hour),str(t.minute),str(t.second)])
    f = open(f_name+'.txt','w')
    f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'    %
            ('mean_clock','median_clock','sd_clock',
             'mean_time','median_time','sd_time',
             'mean_datetime','median_datetime','sd_datetime',))     
        
    # Write results to text file
    f.write('%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n' % 
            (np.mean(np.diff(td1))*1000, np.median(np.diff(td1))*1000,np.std(np.diff(td1))*1000,
             np.mean(np.diff(td2))*1000, np.median(np.diff(td2))*1000,np.std(np.diff(td2))*1000,
             np.mean(np.diff(td3))*1000, np.median(np.diff(td3))*1000,np.std(np.diff(td3))*1000))
             
    f.close()

if __name__ == "__main__":
    main()    