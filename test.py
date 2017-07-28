#!/usr/bin/python

from Tkinter import *
from tkFont import *
import serial
import time

def BexitCallBack():
	exit()

top = Tk()
m1 = PanedWindow(top, orient=VERTICAL)
m1.pack(fill=BOTH, expand=1)
m2 = PanedWindow(m1, orient=HORIZONTAL)
m1.add(m2)
helv36 = Font(family="Helvetica",size=36,weight="bold")
bottom = Label(m1, text="bottom pane",anchor=W)
m1.add(bottom)
Bexit = Button(top, text ="Exit", command = BexitCallBack)
m1.add(Bexit)
Lleft = Label(m2, text="left pane")
m2.add(Lleft)
SleftVar=50
Sleft = Scale(m2, orient=VERTICAL, variable=SleftVar, to=0, length=400, from_=400, digits=3, font=helv36)
m2.add(Sleft)
SrightVar=100
Sright = Scale(m2, orient=VERTICAL, variable=SrightVar, to=0, length=400, from_=400, digits=3, font=helv36)
m2.add(Sright)
Lright = Label(m2, text="right pane")
m2.add(Lright)
Sleft.set(50)
Sright.set(100)
top.mainloop()


# https://petrimaki.com/2013/04/28/reading-arduino-serial-ports-in-windows-7/
#ser = serial.Serial('COM3', 9600, timeout=0)
 
#while 1:
# try:
#  print ser.readline()
#  time.sleep(1)
# except ser.SerialTimeoutException:
#  print('Data could not be read')
#  time.sleep(1)
