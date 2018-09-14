#!/usr/bin/env python3 

import RPi.GPIO as GPIO 
import time
import sys
from subprocess import call

RoAPin = 26    # pin11 
RoBPin = 19    # pin12 
RoSPin = 13    # pin13 
 
globalCounter = 0
clickvalue = 1

verbose = True 
flag = 0 
Last_RoB_Status = 0 
Current_RoB_Status = 0 

def volumio_cmd(cmd='next'):
    call('/usr/local/bin/volumio %s > /dev/null 2>&1' % cmd, shell=True)

def setup(): 
        GPIO.setmode(GPIO.BCM)       # Numbers GPIOs by physical location 
        GPIO.setup(RoAPin, GPIO.IN)    # input mode 
        GPIO.setup(RoBPin, GPIO.IN) 
        GPIO.setup(RoSPin,GPIO.IN,pull_up_down=GPIO.PUD_UP) 

def rotaryDeal(): 
        global flag 
        global Last_RoB_Status 
        global Current_RoB_Status 
        global globalCounter 
        Last_RoB_Status = GPIO.input(RoBPin) 
        while(not GPIO.input(RoAPin)): 
                Current_RoB_Status = GPIO.input(RoBPin) 
                flag = 1 
        if flag == 1: 
                flag = 0

                # Scroll up
                if (Last_RoB_Status == 0) and (Current_RoB_Status == 1):
                        globalCounter += clickvalue
                        if verbose: print ('globalCounter = %d' % globalCounter)
                        volumio_cmd('previous')

                # Scroll down
                elif (Last_RoB_Status == 1) and (Current_RoB_Status == 0):
                        globalCounter -= clickvalue
                        if verbose: print ('globalCounter = %d' % globalCounter)
                        volumio_cmd('next')

def clear(ev=None): 
        global globalCounter 
        globalCounter = 0 
        if verbose: print ('globalCounter = %d' % globalCounter) 
        time.sleep(1) 

def loop(): 
        #global globalCounter 
        while True: 
                rotaryDeal() 

 
def destroy(): 
        GPIO.cleanup()             # Release resource 

if __name__ == '__main__':     # Program start from here 
        setup() 
        try: 
                loop() 
        except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
                destroy()
        except:
            sys.exit(1)

