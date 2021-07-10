#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import sys, time, random
import RPi.GPIO as GPIO  

# Глобальное

# Сюда включать датчики.
leftPin = 23
rightPin = 24

# Подсветка работы. 
# Повтор прерываний.
leftLed = 20
rightLed = 21
# Работа:
# Готовность: Зелёный. Гаснет при нажатии старта. Зажигается, когда новая гонка прописана.
# Старт: Красный.
# Стоп - красный гаснет.
readyLed = 16
startLed = 17

# МКА



# Классы

# Гонщик и его данные
class Racer():
    def __init__(pin, name='Гонщик', model='Мопед'):
        self.pin = pin
        self.name = name
        self.model = model
        self.rotations = 0
        self.distance = 0
        self.speed = 0.0
        self.time = 0.0

class Signal(object):
    def __init__(self, pin, led):
        self.pin = pin
        self.led = led
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.interrupt, bouncetime=2)
        print(f"Сигналы от {pin}.")

    def interrupt(self, pin):
        if self.pin == pin:
            counters[self.pin]['count']+=1
            GPIO.output(self.led, counters[self.pin]['count']%2) # Лучше бы на каждый метр...
            print(f"Interrupt {self.pin}, count={counters[self.pin]['count']}")
        else:
            print(f"Miisng int call {self.pin} vs {pin}")

class Dialog(QtWidgets.QDialog):
    def __init__(self):
        super(Dialog, self).__init__() 
        uic.loadUi('dialog.ui', self)
        self.show()
        self.setWindowTitle("Новая гонка, запись участников...")

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)

    def run(self):
        preStartCleanUp()
        win.startButton.setText("Поехали...")
        ldist=0
        rdist=0
        for i in range(60): # время гонки
            ldist = counters[leftPin]['count']
            rdist = counters[rightPin]['count']
            self.progress.emit(ldist, rdist)
            time.sleep(1)
        self.finished.emit()

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('DragRacing.ui', self)
        self.newButton.clicked.connect(self.newRace)
        self.startButton.clicked.connect(self.startRace)
        self.stopButton.clicked.connect(self.stopRace)
        # Заполнить горнчегов
        self.left = Racer(leftPin)
        self.fill(left)
        self.right = Racer(rightPin)
        self.fill(right)
        # пыщ!
        self.showMaximized()

    def fill(self, racer):
        if racer.pin == leftPin:
            self.leftName.text(racer.name)
            self.leftModel.text(racer.model)
            self.leftSpeed.text(racer.speed)
            self.leftDistance.text(racer.distance)
            self.leftTime.text(racer.time)
            self.leftBar.setValue(racer.distance)
        else:


    def newRace(self):
        d = Dialog()
        if d.exec():
            print("ok")
            self.leftName.setText(d.leftModelEdit.text())
            self.leftModel.setText(d.leftModelEdit.text())
            self.rightName.setText(d.rightNameEdit.text())
            self.rightModel.setText(d.rightModelEdit.text())
        else:
            print("Ничего не делаем")

    def startRace(self):
        global reportFile
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        print("run!")
        self.thread.started.connect(self.worker.run)
        print("worker run!")
        self.worker.finished.connect(self.thread.quit)
        print("t q")
        self.worker.finished.connect(self.worker.deleteLater)
        print("w dl")
        self.thread.finished.connect(self.thread.deleteLater)
        print("t dl")
        self.worker.progress.connect(self.reportProgress)
        print("reportProgress")
        self.thread.start()
        print("started")
        self.startButton.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.startButton.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.startButton.setText("Старт!")
        )
        # Раскраска фамилий.
        # Запись отчёта.
        try:
            reportFile.write("\t".join([time.now(),
                leftName, leftModel,
                counters[leftPin]['speed'], counters[leftPin]['speed'],
                rightName,rightModel,rightSpeed,rightTime])+"\n")

    def stopRace(self):
        print("Остановка")

    def reportProgress(self,n, m):
        self.leftBar.setValue(n)
        self.leftSpeed.setText(str(n%100))
        self.leftDistance.setText(str(n))
        self.rightBar.setValue(m)
        self.rightSpeed.setText(str(m%100))
        self.rightDistance.setText(str(m))

def preStartCleanUp():
    # Очищает всё в момент старта.
    print("Очистка")

GPIO.setmode(GPIO.BCM)
leftData = Signal(leftPin, leftLed)
rightData = Signal(rightPin, rightLed)
GPIO.setup(leftLed, GPIO.OUT)
GPIO.setup(rightLed, GPIO.OUT)

# Гуй
app = QtWidgets.QApplication([])
win = Ui()
# Надо нажать New... или заполнить поля.
win.startButton.setEnabled(True)
win.stopButton.setEnabled(False)
# Пыщ!
with open('report.txt','w') as reportFile:
    rc = app.exec()
GPIO.cleanup()
sys.exit(rc)