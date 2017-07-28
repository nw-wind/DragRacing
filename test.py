#!/usr/bin/python

import Tkinter
import serial

#top = Tkinter.Tk()
# Code to add widgets will go here...
#top.mainloop()

import time
ser = serial.Serial('COM3', 9600, timeout=0)
 
while 1:
 try:
  print ser.readline()
  time.sleep(1)
 except ser.SerialTimeoutException:
  print('Data could not be read')
  time.sleep(1)
