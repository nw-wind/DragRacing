#!/usr/bin/python
# coding: utf8

from Tkinter import *
from tkFont import *
import serial
import time
import re
import codecs

def BclearCallBack():
	SleftVar=SrightVar=0
	Sleft.set(SleftVar)
	Sright.set(SrightVar)


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
			global lastTimeA, lastTimeB,lastDistA, lastDistB
			global upRightTextS,upLeftTextS,Sleft,Sright,leftText,rightText
			if pA[1] == 'FINISH':
				SleftVar=402
				upLeftTextS.set(u"FINISH")
				# finish
			else:
				speedA=float(int(pA[1])-lastDistA)/float(int(pA[0])-lastTimeA)*3.6
				print "Speed A = "+str(speedA)+" "+str(lastDistA)+" "+str(lastTimeA)
				leftText.set("%03d.%03d %.1f" % ( int(pA[0])/1000, int(pA[0])%1000, speedA ) )
				lastTimeA=int(pA[0])
				lastDistA=int(pA[1])
			 	SleftVar=int(pA[1])/1000
			if pB[1] == 'FINISH':
				SrightVar=402
				upRightTextS.set(u"FINISH")
				# finish
			else:
				speedB=float(int(pB[1])-lastDistB)/float(int(pB[0])-lastTimeB)*3.6
				rightText.set("%03d.%03d %.1f" % (int(pB[0])/1000,int(pB[0])%1000,speedB))
				lastTimeB=int(pB[0])
				lastDistB=int(pB[1])
				SrightVar=int(pB[1])/1000
			Sleft.set(SleftVar)
			Sright.set(SrightVar)
		top.update()
	top.after(50,readSerial)
	
lastTimeA=0
lastTimeB=0
lastDistA=0
lastDistB=0

ser = serial.Serial('/dev/tty.usbserial-A50285BI', 115200, timeout=1)
top = Tk()
top.geometry("800x600")
helv36 = Font(family="Helvetica",size=36,weight="bold")

#cv=Canvas(top,bg="white")
#img=PhotoImage(file="HD.png")
#bgL=Label(top,image=img)
#bgL.place(x=0,y=0,relwidth=1, relheight=1)
#cv.pack()

upLeftText=StringVar()
upLeftText.set("Трек А")
upLabelLeft= Label(textvariable=upLeftText, font=helv36, fg="red")
upLabelLeft.grid(row=0,column=0,columnspan=2,sticky="n")

upRightText=StringVar()
upRightText.set("Трек Б")
upLabelRight= Label(textvariable=upRightText, font=helv36, fg="blue")
upLabelRight.grid(row=0,column=2,columnspan=2,sticky="n")

upLeftTextS=StringVar()
upLeftTextS.set("Старт")
upLabelLeftS= Label(textvariable=upLeftTextS, font=helv36, bg="red")
upLabelLeftS.grid(row=1,column=1,sticky="ne")

upRightTextS=StringVar()
upRightTextS.set("Старт")
upLabelRightS= Label(textvariable=upRightTextS, font=helv36, bg="blue")
upLabelRightS.grid(row=1,column=2,sticky="nw")

bottomText=StringVar()
bottomText.set(u"Ожидание подключения")
bottom = Label(textvariable=bottomText)
bottom.grid(row=3,column=0)

Bclear = Button(text ="Очистить", command = BclearCallBack)
Bclear.grid(row=3,column=1,columnspan=2)

Bexit = Button(text ="Выход", command = BexitCallBack)
Bexit.grid(row=3,column=3)

leftText=StringVar()
leftText.set("000.000")
Lleft = Label(textvariable=leftText, font=helv36)
Lleft.grid(row=2,column=0)

SleftVar=0
Sleft = Scale(orient=VERTICAL, to=0, length=402, from_=402, digits=3, font=helv36, width=50, bg="red")
Sleft.grid(row=2,column=1)

SrightVar=0
Sright = Scale(orient=VERTICAL, to=0, length=402, from_=402, digits=3, font=helv36, width=50, bg="blue")
Sright.grid(row=2,column=2)

rightText=StringVar()
rightText.set("000.000")
Lright = Label(textvariable=rightText, font=helv36)
Lright.grid(row=2,column=3)

top.rowconfigure(2, weight=1)
top.columnconfigure(0, weight=1)
top.columnconfigure(3, weight=1)

top.after(50,readSerial)
top.mainloop()


 
