#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import platform
if platform.system() == 'Darwin':
    MACOSX = True
else:
    MACOSX = False

from PyQt5 import QtWidgets
from PyQt5 import uic
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

pi = 3.1416826
diameter = 108.0   # mm
circle = diameter * pi
distance = 402.0 * 1000.0


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


class Signal(object):
    def __init__(self, pin, led):
        self.pin = pin
        self.led = led
        if not MACOSX:
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
        super(Dialog, self).__init__()
        uic.loadUi('StartLight.ui',self)
        self.show()
        self.setWindowTitle("На старт...")

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal()

    def pre_start_cleanup(self):
        # Очищает всё в момент старта.
        print("Очистка")
        for pin, racer in racerData.items():
            racer.rotations = 0
            racer.distance = 0
            racer.speed = 0.0
            racer.time = 0.0
            racer.startTime = time.time()
            racer.counting = True

    def run(self):
        self.pre_start_cleanup()
        win.startButton.setText("Поехали...")
        for i in range(600):    # время гонки
            if MACOSX:
                for fake in range(random.randint(50,100)):
                    leftData.interrupt(leftPin)
                for fake in range(random.randint(20, 70)):
                    rightData.interrupt(rightPin)
            self.progress.emit()
            if not (racerData[leftPin].counting or racerData[rightPin].counting):
                # Гонка закончена, оба приехали.
                print(f"Приехали оба.")
                break
            time.sleep(refreshProgress)
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
            self.leftSpeed.setText(str(racer.speed))
            self.leftDistance.setText(str(racer.distance))
            self.leftTime.setText(str(racer.time))
            self.leftBar.setValue(int(racer.distance))
        else:
            self.rightName.setText(racer.name)
            self.rightModel.setText(racer.model)
            self.rightSpeed.setText(str(racer.speed))
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
        else:
            print("Ничего не делаем")

    def start_race(self):
        global reportFile
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
        self.thread.finished.connect(
            lambda: self.startButton.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.startButton.setText("Старт!")
        )
        # d = StartLight()
        # d.exec()
        # Раскраска фамилий.
        # Запись отчёта.
        try:
            reportFile.write("\t".join([datetime.now(),
                                        self.left.name, self.left.model, self.left.speed, self.left.time,
                                        self.right.name, self.right.model, self.right.speed, self.right.time])+"\n")
        except Exception as e:
            print(f"Опаньки! {e}")

    def stop_race(self):
        print("Остановка")

    def report_progress(self):
        self.leftBar.setValue(int(racerData[leftPin].distance / 1000))
        self.leftSpeed.setText("{:.2f}".format(racerData[leftPin].speed))
        self.leftDistance.setText("{:.2f}".format(racerData[rightPin].distance / 1000))
        self.leftTime.setText("{:.2f}".format(racerData[leftPin].time))
        self.rightBar.setValue(int(racerData[rightPin].distance / 1000))
        self.rightSpeed.setText("{:.2f}".format(racerData[rightPin].speed))
        self.rightDistance.setText("{:.2f}".format(racerData[rightPin].distance / 1000))
        self.rightTime.setText("{:.2f}".format(racerData[rightPin].time))


if not MACOSX:
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
