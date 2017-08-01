#!/usr/bin/python
# coding: utf8

from Tkinter import *
from tkFont import *
import serial
import time
import re
import codecs

def BexitCallBack():
	exit()

def readSerial():
	ln=ser.readline().rstrip()
	print "Read: '"+ln+"'"
	if ln != '':
        	if ln == 'READY':
			bottomText.set(u"Готов!")
			print "Ready to race"
		if ln == 'START':
			bottomText.set(u"Старт!")
			print "Start!"
		if ln == 'STOP':
			bottomText.set(u"Гонка остановлена")
			print "Stop!"
		m = re.match('(\d+) (\w+) (\d+) (\w+)',ln)
		if m:
			pA=m.group(1,2)
			pB=m.group(3,4)
			leftText.set("%03d.%03d" % (int(pA[0])/1000,int(pA[0])%1000))
			if pA[1] == 'FINISH':
				SleftVar=402
				# finish
			else:
			 	SleftVar=pA[1]
			rightText.set("%03d.%03d" % (int(pB[0])/1000,int(pB[0])%1000))
			if pB[1] == 'FINISH':
				SrightVar=402
				# finish
			else:
				SrightVar=pB[1]
			Sleft.set(SleftVar)
			Sright.set(SrightVar)
			print "Arr= "+SleftVar+" ["+",".join(map(str,pA))+"], "+SrightVar+" ["+",".join(map(str,pB))+"]"
		top.update()
	top.after(50,readSerial)
	


ser = serial.Serial('/dev/tty.usbserial-A50285BI', 115200, timeout=1)
top = Tk()
top.geometry("800x600")
helv36 = Font(family="Helvetica",size=36,weight="bold")
m1 = PanedWindow(top, orient=VERTICAL)
m1.pack(fill=BOTH, expand=1)
mUp = PanedWindow(m1, orient=HORIZONTAL)
m1.add(mUp)
m2 = PanedWindow(m1, orient=HORIZONTAL)
m1.add(m2)

upLeftText=StringVar()
upLeftText.set("Трек А")
upLabelLeft= Label(mUp, textvariable=upLeftText)
mUp.add(upLabelLeft)

upRightText=StringVar()
upRightText.set("Трек Б")
upLabelRight= Label(mUp, textvariable=upRightText)
mUp.add(upLabelRight)

bottomText=StringVar()
bottom = Label(m1, textvariable=bottomText, anchor=W)
bottomText.set(u"Ожидание подключения")
m1.add(bottom)
Bexit = Button(top, text ="Exit", command = BexitCallBack)
m1.add(Bexit)
leftText=StringVar()
leftText.set("000.000")
Lleft = Label(m2, textvariable=leftText)
m2.add(Lleft)
SleftVar=0
Sleft = Scale(m2, orient=VERTICAL, to=0, length=402, from_=402, digits=3, font=helv36, width=50, bg="red")
m2.add(Sleft)
SrightVar=0
Sright = Scale(m2, orient=VERTICAL, to=0, length=402, from_=402, digits=3, font=helv36, width=50, bg="blue")
m2.add(Sright)
rightText=StringVar()
rightText.set("000.000")
Lright = Label(m2, textvariable=rightText)
m2.add(Lright)
top.after(50,readSerial)
top.mainloop()


 
