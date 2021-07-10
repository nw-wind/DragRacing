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

counters=dict(
    leftPin: {'count': 0, 'distance':0, 'speed': 0},
    rightPin: {'count': 0, 'distance':0, 'speed': 0},
    )

# МКА



# Классы

class Signal(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=interrupt, bouncetime=2)

    def interrupt(self, pin):
        counters[pin]['count']+=1
        print(f"Interrupt {pin}, count={counters[pin]['count']}")

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
        print("in thread")
        preStartCleanUp()
        win.startButton.setText("Поехали...")
        print("button")
        ldist=0
        rdist=0
        for i in range(1000): # время гонки
            print(f"t={i}")
            ldist = counters[leftPin]['count']
            rdist = counters[rightPin]['count']
            self.progress.emit(ldist, rdist)
            print("emited")
            time.sleep(0.2)
            print("wakeup")
        print("look ends")
        self.finished.emit()
        print("finished")

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() 
        uic.loadUi('DragRacing.ui', self)
        self.newButton.clicked.connect(self.newRace)
        self.startButton.clicked.connect(self.startRace)
        self.stopButton.clicked.connect(self.stopRace)
        self.showMaximized()

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

    def stopRace(self):
        print("Остановка")

    def reportProgress(self,n, m):
        print(f"repo {n}")
        self.leftBar.setValue(n)
        self.leftSpeed.setText(str(n%100))
        self.leftDistance.setText(str(n))
        self.rightBar.setValue(m)
        self.rightSpeed.setText(str(m%100))
        self.rightDistance.setText(str(m))
        print(f"reported")

def preStartCleanUp():
    # Очищает всё в момент старта.
    print("Очистка")

GPIO.setmode(GPIO.BCM)
leftData = Signal(leftPin)
rightData = Signal(rightPin)
GPIO.setup(leftLed, GPIO.OUT)
GPIO.setup(rightLed, GPIO.OUT)

# Гуй
app = QtWidgets.QApplication([])
win = Ui()
# Надо нажать New... или заполнить поля.
win.startButton.setEnabled(True)
win.stopButton.setEnabled(False)
# Пыщ!


rc = app.exec()
GPIO.cleanup()
sys.exit(rc)