#!c:\Python27\python.exe
# coding: utf8

from Tkinter import *
from tkFont import *
import serial
import time
import re
import codecs

def BclearCallBack():
	global bottomText
	global cvLeft,cvRight
	global lastTimeA, lastTimeB,lastDistA, lastDistB
	global upRightTextS,upLeftTextS,Sleft,Sright,leftText,rightText
	Sleft.set(0)
	Sright.set(0)
	bottomText.set(u"Готов!")
	lastTimeA=lastTimeB=lastDistA=lastDistB=0
	upLeftTextS.set(u"Старт")
	upRightTextS.set(u"Старт")
	leftText.set("000.000s 000km/h")
	rightText.set("000.000s 000km/h")
	cvLeft.itemconfig("leftLight", fill="grey")
	cvRight.itemconfig("rightLight", fill="grey")


def BexitCallBack():
	exit()

def readSerial():
        global cvLeft,cvRight
	global lastTimeA, lastTimeB,lastDistA, lastDistB
	global upRightTextS,upLeftTextS,Sleft,Sright,leftText,rightText
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
		m = re.match('LIGHT (\d+)',ln)
		if m:
			lightIndex=int(m.group(1)[0])
			print "LIGHT="+str(lightIndex)
			if lightIndex == 0:
				cvLeft.itemconfig("leftLight", fill="red")
				cvRight.itemconfig("rightLight", fill="red")
			if lightIndex == 1:
				cvLeft.itemconfig("leftLight", fill="yellow")
				cvRight.itemconfig("rightLight", fill="yellow")
			if lightIndex == 2:
				cvLeft.itemconfig("leftLight", fill="green")
				cvRight.itemconfig("rightLight", fill="green")
		m = re.match('FALSE (\d+)',ln)
		if m:
			fs=int(m.group(1)[0])
			if fs == 0:
				upLeftTextS.set(u"ФАЛЬСТАРТ")
			else:
				upRightTextS.set(u"ФАЛЬСТАРТ")
		m = re.match('(\d+) (\w+) (\d+) (\w+)',ln)
		if m:
			pA=m.group(1,2)
			pB=m.group(3,4)
			if pA[1] == 'FINISH':
				SleftVar=402
				upLeftTextS.set(u"FINISH")
				# finish
			else:
				speedA=0
				try:
				  speedA=float(int(pA[1])-lastDistA)/float(int(pA[0])-lastTimeA)*3.6
				except:
				  print "Left stays"
				print "Speed A = "+str(speedA)+" "+str(lastDistA)+" "+str(lastTimeA)
				leftText.set("%03d.%03ds %03dkm/h" % ( int(pA[0])/1000, int(pA[0])%1000, speedA ) )
				lastTimeA=int(pA[0])
				lastDistA=int(pA[1])
			 	SleftVar=int(pA[1])/1000
			if pB[1] == 'FINISH':
				SrightVar=402
				upRightTextS.set(u"FINISH")
				# finish
			else:
				speedB=0
				try:
				  speedB=float(int(pB[1])-lastDistB)/float(int(pB[0])-lastTimeB)*3.6
				except:
				  print "Right stays"
				rightText.set("%03d.%03d %03dkm/h" % (int(pB[0])/1000,int(pB[0])%1000,speedB))
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

#ser = serial.Serial('/dev/tty.usbserial-A50285BI', 115200, timeout=1)
ser = serial.Serial('COM3', 115200, timeout=1)
top = Tk()
top.geometry("800x600")
helv36 = Font(family="Helvetica",size=36,weight="bold")
cour36 = Font(family="Lucida Console",size=42,weight="bold")

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

cvLeft=Canvas(width=80, height=80)
cvLeft.create_oval(5,5,70,70, fill="grey", tags="leftLight")
cvLeft.grid(row=1,column=0,sticky="ne")

cvRight=Canvas(width=80, height=80)
cvRight.create_oval(5,5,70,70, fill="grey", tags="rightLight")
cvRight.grid(row=1,column=3,sticky="nw")

bottomText=StringVar()
bottomText.set(u"Ожидание подключения")
bottom = Label(textvariable=bottomText)
bottom.grid(row=3,column=0)

Bclear = Button(text ="Очистить", command = BclearCallBack)
Bclear.grid(row=3,column=1,columnspan=2)

Bexit = Button(text ="Выход", command = BexitCallBack)
Bexit.grid(row=3,column=3)

leftText=StringVar()
leftText.set("000.000s 000km/h")
Lleft = Label(textvariable=leftText, font=cour36, wraplength=300)
Lleft.grid(row=2,column=0)

SleftVar=0
Sleft = Scale(orient=VERTICAL, to=0, length=402, from_=402, digits=3, font=helv36, width=80, bg="red")
Sleft.grid(row=2,column=1)

SrightVar=0
Sright = Scale(orient=VERTICAL, to=0, length=402, from_=402, digits=3, font=helv36, width=80, bg="blue")
Sright.grid(row=2,column=2)

rightText=StringVar()
rightText.set("000.000s 000km/h")
Lright = Label(textvariable=rightText, font=cour36, wraplength=300)
Lright.grid(row=2,column=3)

top.rowconfigure(2, weight=1)
top.columnconfigure(0, weight=1)
top.columnconfigure(1, weight=2)
top.columnconfigure(2, weight=2)
top.columnconfigure(3, weight=1)

top.after(50,readSerial)
top.mainloop()


 
