# -*- coding: utf-8 -*-
"""
Created on Wed Sep 09 13:04:53 2015

* If TimerTool.exe is running, kill the process.
* If input parameter is given, start TimerTool and set clock resolution
Starts TimerTool.exe and sets the clock resolution to argv[0] ms

Ex: python set_clock_resolution 1
"""

from win32com.client import GetObject
import sys, subprocess, time
import os

def main(argv):
    
    # Change directory
    this_dir = os.path.abspath(os.path.dirname(__file__))  # os.getcwd()
    os.chdir(this_dir)  
    
    WMI = GetObject('winmgmts:')
    processes = WMI.InstancesOf('Win32_Process')
    
    # First close all open TimerTool.exe processes (if any)
    TimerTool_running = True
    while TimerTool_running:
        if "TimerTool.exe" in [process.Properties_('Name').Value for process in processes]:
            subprocess.Popen('TaskKill /F /IM TimerTool.exe')    # if it is, kill it!
            time.sleep(1)            
            processes = WMI.InstancesOf('Win32_Process')
            
        else:
            TimerTool_running = False
     
    # If an input parameter is given, start TimerTool.exe and set the resolution     
    if argv:    
        subprocess.Popen(''.join(['TimerTool.exe -t ',str(argv[0]),' -minimized']))    

if __name__ == "__main__":
    main(sys.argv[1:])    