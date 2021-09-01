#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import platform
if platform.system() == 'Darwin':
    MACOSX = True
else:
    MACOSX = False

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import sys
import time
from datetime import datetime

if MACOSX:
    import random
else:
    import RPi.GPIO as GPIO

# Глобальное

racerData = dict()

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
readyLed = 4
startLed = 22
setUpLed = 25

refreshProgress = 0.2
raceLoops = int(600 / refreshProgress)

pi = 3.1416826
diameter = 108.0   # mm
circle = diameter * pi
distance = 402.0 * 1000.0

working = False

# Классы

# Гонщик и его данные


class Racer:
    def __init__(self, pin, name='Гонщик', model='Мопед'):
        self.pin = pin
        self.name = name
        self.model = model
        self.rotations = 0
        self.distance = 0
        self.speed = 0.0    # надо считать
        self.time = 0.0
        self.startTime = 0.0
        self.counting = False
        # Для скорости
        self.lastTime = 0.0
        self.lastDistance = 0.0
        self.maxSpeed = 0.0


class Signal(object):
    def __init__(self, pin, led):
        self.pin = pin
        self.led = led
        if not MACOSX:
            print(f"set int {pin}")
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.interrupt, bouncetime=2)
        print(f"Сигналы от {pin}.")

    def interrupt(self, pin):
        if self.pin == pin and racerData[self.pin].counting:
            print(f"Interrupt {pin}/{self.pin} {racerData[self.pin].counting} = {racerData[self.pin].rotations} {racerData[self.pin].distance} {distance} ")
            racerData[self.pin].rotations += 1
            racerData[self.pin].distance = racerData[self.pin].rotations * circle
            racerData[self.pin].time = time.time() - racerData[self.pin].startTime
            print(f"{racerData[self.pin].time} = {time.time()} - {racerData[self.pin].startTime}")
            if racerData[self.pin].distance >= distance:
                racerData[self.pin].counting = False
                racerData[self.pin].distance = distance
                print(f"Закончили считать")
            if not MACOSX:
                GPIO.output(self.led, racerData[self.pin].rotations % 2)    # Лучше бы на каждый метр...
            print(f"Interrupt {self.pin}, count={racerData[self.pin].rotations}")
        else:
            print(f"Missing int call {self.pin} vs {pin}")


class Dialog(QtWidgets.QDialog):
    def __init__(self):
        super(Dialog, self).__init__() 
        uic.loadUi('dialog.ui', self)
        self.show()
        self.setWindowTitle("Новая гонка, запись участников...")

class StartLight(QtWidgets.QDialog):
    def __init__(self):
        super(StartLight, self).__init__()
        uic.loadUi('StartLight.ui', self)
        self.setWindowTitle("На старт...")

    def setColor(self, color):
        self.setStyleSheet(f"background:{color}")

    def closeMe(self):
        print("close SL")
        self.close()

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal()

    def run(self):
        pre_start_cleanup()
        win.startButton.setText("Поехали...")
        for i in range(raceLoops):    # время гонки
            if not working:
                break
            time.sleep(refreshProgress)
            if MACOSX:
                for fake in range(random.randint(50,100)):
                    leftData.interrupt(leftPin)
                    #time.sleep(0.01)
                for fake in range(random.randint(20, 70)):
                    rightData.interrupt(rightPin)
                    #time.sleep(0.01)
            self.progress.emit()
            if not (racerData[leftPin].counting or racerData[rightPin].counting):
                # Гонка закончена, оба приехали.
                print(f"Приехали оба.")
                break
        self.finished.emit()


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('DragRacing.ui', self)
        self.thread = None
        self.worker = None
        self.newButton.clicked.connect(self.new_race)
        self.startButton.clicked.connect(self.start_race)
        self.stopButton.clicked.connect(self.stop_race)
        # Заполнить горнчегов
        self.left = racerData[leftPin] = Racer(leftPin)
        self.fill(self.left)
        self.right = racerData[rightPin] = Racer(rightPin)
        self.fill(self.right)
        # пыщ!
        # self.showMaximized()
        self.showFullScreen()

    def fill(self, racer):
        if racer.pin == leftPin:
            self.leftName.setText(racer.name)
            self.leftModel.setText(racer.model)
            self.leftSpeed.setText(str(racer.maxSpeed))
            self.leftDistance.setText(str(racer.distance))
            self.leftTime.setText(str(racer.time))
            self.leftBar.setValue(int(racer.distance))
        else:
            self.rightName.setText(racer.name)
            self.rightModel.setText(racer.model)
            self.rightSpeed.setText(str(racer.maxSpeed))
            self.rightDistance.setText(str(racer.distance))
            self.rightTime.setText(str(racer.time))
            self.rightBar.setValue(int(racer.distance))

    def new_race(self):
        d = Dialog()
        if d.exec():
            print("ok")
            self.leftName.setText(d.leftNameEdit.text())
            self.leftModel.setText(d.leftModelEdit.text())
            self.rightName.setText(d.rightNameEdit.text())
            self.rightModel.setText(d.rightModelEdit.text())
            pre_start_cleanup()
            self.report_progress()
        else:
            print("Ничего не делаем")

    def fin_conn(self):
        self.startButton.setEnabled(True)
        self.startButton.setText("Старт!")
        self.stopButton.setEnabled(False)
        self.newButton.setEnabled(True)

    def start_race(self):
        global reportFile
        global working
        sl = StartLight()
        for c in ['red', 'yellow', 'green']:
            print(f"Color={c}")
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(sl.closeMe)
            self.timer.start(2000)
            sl.setColor(c)
            sl.show()
            sl.exec()
            time.sleep(0.5)
        working = True
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.report_progress)
        self.thread.start()
        self.startButton.setEnabled(False)
        self.newButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.thread.finished.connect(
            self.fin_conn
        )
        # d = StartLight()
        # d.exec()
        # Раскраска фамилий.
        # Запись отчёта.
        try:
            reportFile.write("\t".join([datetime.now().strftime("%c"),
                                        self.left.name, self.left.model, str(self.left.maxSpeed), str(self.left.time),
                                        self.right.name, self.right.model, str(self.right.maxSpeed), str(self.right.time)])+"\n")
        except Exception as e:
            print(f"Error with report {e}")

    def stop_race(self):
        global working
        print("Остановка")
        working = False

    def report_progress(self):
        print(f"обновляем...")
        try:
            racerData[leftPin].speed = ((racerData[leftPin].distance - racerData[leftPin].lastDistance) / 1000000) / \
                                       ((racerData[leftPin].time - racerData[leftPin].lastTime) / 3600)
        except ZeroDivisionError:
            print(f"ой, деление на ноль")
        print(f"{racerData[leftPin].speed} = ({racerData[leftPin].distance} - {racerData[leftPin].lastDistance}) / 1000000 / ({racerData[leftPin].time} - {racerData[leftPin].lastTime}) / 3600")
        racerData[leftPin].lastTime = racerData[leftPin].time
        racerData[leftPin].lastDistance = racerData[leftPin].distance
        if racerData[leftPin].speed >= racerData[leftPin].maxSpeed:
            racerData[leftPin].maxSpeed = racerData[leftPin].speed

        try:
            racerData[rightPin].speed = ((racerData[rightPin].distance - racerData[rightPin].lastDistance) / 1000000) / \
                                         ((racerData[rightPin].time - racerData[rightPin].lastTime) / 3600)
        except ZeroDivisionError:
            print(f"ой, деление на ноль")
        print(f"{racerData[rightPin].speed} = ({racerData[rightPin].distance} - {racerData[rightPin].lastDistance}) / 1000000 / ({racerData[rightPin].time} - {racerData[rightPin].lastTime}) / 3600")
        racerData[rightPin].lastTime = racerData[rightPin].time
        racerData[rightPin].lastDistance = racerData[rightPin].distance
        if racerData[rightPin].speed >= racerData[rightPin].maxSpeed:
            racerData[rightPin].maxSpeed = racerData[rightPin].speed

        self.leftBar.setValue(int(racerData[leftPin].distance / 1000))
        self.leftSpeed.setText("{:.2f}".format(racerData[leftPin].maxSpeed))
        self.leftDistance.setText("{:.2f}".format(racerData[leftPin].distance / 1000))
        self.leftTime.setText("{:.2f}".format(racerData[leftPin].time))

        self.rightBar.setValue(int(racerData[rightPin].distance / 1000))
        self.rightSpeed.setText("{:.2f}".format(racerData[rightPin].maxSpeed))
        self.rightDistance.setText("{:.2f}".format(racerData[rightPin].distance / 1000))
        self.rightTime.setText("{:.2f}".format(racerData[rightPin].time))

def pre_start_cleanup():
    # Очищает всё в момент старта.
    print("Очистка")
    for pin, racer in racerData.items():
        racer.rotations = 0
        racer.distance = 0
        racer.speed = 0.0
        racer.time = 0.0
        racer.startTime = time.time()
        racer.counting = True
        racer.lastTime = 0.0
        racer.lastDistance = 0.0
        racer.maxSpeed = 0.0

if not MACOSX:
    print(f"RPI mode")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(leftLed, GPIO.OUT)
    GPIO.setup(rightLed, GPIO.OUT)
leftData = Signal(leftPin, leftLed)
rightData = Signal(rightPin, rightLed)

# Гуй
app = QtWidgets.QApplication([])
win = Ui()
# Надо нажать New... или заполнить поля.
win.startButton.setEnabled(True)
win.stopButton.setEnabled(False)
# Пыщ!
with open('report.txt', 'w') as reportFile:
    rc = app.exec()
if not MACOSX:
    GPIO.cleanup()
sys.exit(rc)
