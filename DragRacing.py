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

racer_data = dict()

# Сюда включать датчики.
left_pin = 23
right_pin = 24

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
diameter = 108.0  # mm
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
        self.speed = 0.0  # надо считать
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
        if self.pin == pin and racer_data[self.pin].counting:
            # print(f"Interrupt {pin}/{self.pin} {racer_data[self.pin].counting} =
            # {racer_data[self.pin].rotations} {racer_data[self.pin].distance} {distance} ")
            racer_data[self.pin].rotations += 1
            racer_data[self.pin].distance = racer_data[self.pin].rotations * circle
            racer_data[self.pin].time = time.time() - racer_data[self.pin].startTime
            # print(f"{racer_data[self.pin].time} = {time.time()} - {racer_data[self.pin].startTime}")
            if racer_data[self.pin].distance >= distance:
                racer_data[self.pin].counting = False
                racer_data[self.pin].distance = distance
                print(f"Закончили считать")
            if not MACOSX:
                GPIO.output(self.led, racer_data[self.pin].rotations % 2)  # Лучше бы на каждый метр...
            # print(f"Interrupt {self.pin}, count={racer_data[self.pin].rotations}")
        else:
            # print(f"Missing int call {self.pin} vs {pin}")
            pass


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

    def set_color(self, color):
        self.setStyleSheet(f"background:{color}")

    def close_me(self):
        print("close SL")
        self.close()


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal()

    def run(self):
        pre_start_cleanup()
        win.startButton.setText("Поехали...")
        for i in range(raceLoops):  # время гонки
            if not working:
                break
            time.sleep(refreshProgress)
            if MACOSX:
                for fake in range(random.randint(50, 100)):
                    leftData.interrupt(left_pin)
                    # time.sleep(0.01)
                for fake in range(random.randint(20, 70)):
                    rightData.interrupt(right_pin)
                    # time.sleep(0.01)
            self.progress.emit()
            if not (racer_data[left_pin].counting or racer_data[right_pin].counting):
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
        self.left = racer_data[left_pin] = Racer(left_pin)
        self.fill(self.left)
        self.right = racer_data[right_pin] = Racer(right_pin)
        self.fill(self.right)
        # пыщ!
        # self.showMaximized()
        self.showFullScreen()

    def fill(self, racer):
        if racer.pin == left_pin:
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
            self.timer.timeout.connect(sl.close_me)
            self.timer.start(2000)
            sl.set_color(c)
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
                                        self.left.name, self.left.model,
                                        str(self.left.maxSpeed), str(self.left.time),
                                        self.right.name, self.right.model,
                                        str(self.right.maxSpeed), str(self.right.time)]) + "\n")
        except Exception as e:
            print(f"Error with report {e}")

    def stop_race(self):
        global working
        print("Остановка")
        working = False

    def report_progress(self):
        print(f"обновляем...")
        try:
            racer_data[left_pin].speed = ((racer_data[left_pin].distance -
                                           racer_data[left_pin].lastDistance
                                           ) / 1000000
                                          ) / ((racer_data[left_pin].time - racer_data[left_pin].lastTime
                                                ) / 3600
                                               )
        except ZeroDivisionError:
            print(f"zero division")
        print(f"{racer_data[left_pin].speed} = ({racer_data[left_pin].distance} - " +
              "{racer_data[left_pin].lastDistance}) / 1000000 / ({racer_data[left_pin].time} - " +
              "{racer_data[left_pin].lastTime}) / 3600")
        racer_data[left_pin].lastTime = racer_data[left_pin].time
        racer_data[left_pin].lastDistance = racer_data[left_pin].distance
        if racer_data[left_pin].speed >= racer_data[left_pin].maxSpeed and \
                racer_data[left_pin].time >= 2 * refreshProgress:
            racer_data[left_pin].maxSpeed = racer_data[left_pin].speed

        try:
            racer_data[right_pin].speed = ((racer_data[right_pin].distance - racer_data[
                right_pin].lastDistance) / 1000000) / \
                                          ((racer_data[right_pin].time - racer_data[right_pin].lastTime) / 3600)
        except ZeroDivisionError:
            print(f"zero division")
        print(f"{racer_data[right_pin].speed} = ({racer_data[right_pin].distance} - " +
              "{racer_data[right_pin].lastDistance}) / 1000000 / " +
              "({racer_data[right_pin].time} - {racer_data[right_pin].lastTime}) / 3600")
        racer_data[right_pin].lastTime = racer_data[right_pin].time
        racer_data[right_pin].lastDistance = racer_data[right_pin].distance
        if racer_data[right_pin].speed >= racer_data[right_pin].maxSpeed and \
                racer_data[right_pin].time >= 2 * refreshProgress:
            racer_data[right_pin].maxSpeed = racer_data[right_pin].speed

        self.leftBar.setValue(int(racer_data[left_pin].distance / 1000))
        self.leftSpeed.setText("{:.2f}".format(racer_data[left_pin].maxSpeed))
        self.leftDistance.setText("{:.2f}".format(racer_data[left_pin].distance / 1000))
        self.leftTime.setText("{:.2f}".format(racer_data[left_pin].time))

        self.rightBar.setValue(int(racer_data[right_pin].distance / 1000))
        self.rightSpeed.setText("{:.2f}".format(racer_data[right_pin].maxSpeed))
        self.rightDistance.setText("{:.2f}".format(racer_data[right_pin].distance / 1000))
        self.rightTime.setText("{:.2f}".format(racer_data[right_pin].time))


def pre_start_cleanup():
    # Очищает всё в момент старта.
    print("Очистка")
    for pin, racer in racer_data.items():
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
leftData = Signal(left_pin, leftLed)
rightData = Signal(right_pin, rightLed)

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
