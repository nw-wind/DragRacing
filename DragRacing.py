#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import platform

if platform.system() == 'Darwin':
    MACOSX = True
else:
    MACOSX = False

from PyQt5 import uic
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import sys
import os
import time
from datetime import datetime
import logging

if MACOSX:
    import random
else:
    import RPi.GPIO as GPIO

# Глобальное

logging.basicConfig(format='%(levelname).1s: %(module)s:%(lineno)d: %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Сюда включать датчики.
left_pin = 23
right_pin = 24

# default_input = GPIO.PUD_UP
default_input = GPIO.PUD_DOWN

# light_on = 0
# light_off = 1
light_on = 1
light_off = 0

# Подсветка работы. 
# Повтор прерываний.
leftLed = 20
rightLed = 21
# Работа:
# Готовность: Зелёный. Гаснет при нажатии старта. Зажигается, когда новая гонка прописана.
# Старт: Красный. Стоп - красный гаснет.
# Сетап - настройка идёт
readyLed = 17
startLed = 27
setUpLed = 22

# Светофор
tl_red = 13
tl_yellow = 19
tl_green = 26

# Кнопки
startKnob = 5
stopKnob = 6

refreshProgress = 0.1
raceLoops = int(600 / refreshProgress)

pi = 3.1416826
diameter = 108.0  # mm
circle = diameter * pi
distance = 402.0 * 1000.0

working = False
win = None

false_start_enable = True

work_dir = os.path.split(os.path.abspath(os.path.realpath(sys.argv[0])))[0]
try:
    with open(f'{work_dir}/nofs') as f:
        print(readline(f))
except Exception as e:
    print(e)
    false_start_enable = False

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
        self.last_time = 0.0
        self.last_distance = 0.0
        self.max_speed = 0.0
        self.false_start = False


racer_data = {left_pin: Racer(left_pin), right_pin: Racer(right_pin)}


def led_on(led):
    GPIO.output(led, light_on)


def led_off(led):
    GPIO.output(led, light_off)


class TrafficLight(QtWidgets.QDialog):
    def __init__(self, parent=None, color='red', title="Старт", led=None):
        super(TrafficLight, self).__init__(parent)
        self.setWindowTitle(title)
        self.color = color
        self.led = led
        self.timer = QtCore.QTimer(
            self,
            interval=2000,
            timeout=self.stop
        )
        self.timer.start()
        self.resize(400, 400)

    @QtCore.pyqtSlot()
    def stop(self):
        led_off(self.led)
        log.warning(f"Светофор погасил {self.color}.")
        self.timer.stop()
        self.close()

    def paintEvent(self, event):
        led_on(self.led)
        log.warning(f"Светофор зажёг {self.color}.")
        p = QtGui.QPainter(self)
        p.setBrush(QtGui.QColor(self.color))
        p.setPen(QtCore.Qt.black)
        p.drawEllipse(self.rect().center(), 150, 150)


class FalseStart(QtWidgets.QDialog):
    def __init__(self, parent=None, text=''):
        super(FalseStart, self).__init__(parent)
        self.setWindowTitle(f"Проблема :(")
        self.text = text
        log.warning(f"Фальстарт окошко!.")
        self.timer = QtCore.QTimer(
            self,
            interval=10000,
            timeout=self.stop
        )
        self.timer.start()
        self.resize(600, 400)

    @QtCore.pyqtSlot()
    def stop(self):
        log.warning(f"Фальстарт погасил {self.text}.")
        self.timer.stop()
        self.close()

    def paintEvent(self, event):
        log.warning(f"Фальстарт зажёг {self.text}.")
        p = QtGui.QPainter(self)
        f = p.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() * 4)
        p.setFont(f)
        p.setPen(QtCore.Qt.red)
        p.drawText(self.rect(), QtCore.Qt.AlignCenter, self.text)


class Signal(object):
    def __init__(self, pin, led):
        self.pin = pin
        self.led = led
        if not MACOSX:
            log.debug(f"set int {pin}")
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=default_input)
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.interrupt, bouncetime=2)
        log.debug(f"Сигналы от {pin}.")

    def interrupt(self, pin):
        global working
        if self.pin == pin and racer_data[self.pin].counting:
            log.debug(f"Interrupt {pin}/{self.pin} {racer_data[self.pin].counting} =" +
                      f"{racer_data[self.pin].rotations} {racer_data[self.pin].distance} {distance} ")
            racer_data[self.pin].rotations += 1
            racer_data[self.pin].distance = racer_data[self.pin].rotations * circle
            racer_data[self.pin].time = time.time() - racer_data[self.pin].startTime
            log.debug(f"{racer_data[self.pin].time} = {time.time()} - {racer_data[self.pin].startTime}")
            if racer_data[self.pin].distance >= distance:
                racer_data[self.pin].counting = False
                racer_data[self.pin].distance = distance
                log.debug(f"Закончили считать")
            if not MACOSX:
                GPIO.output(self.led, racer_data[self.pin].rotations % 2)  # Лучше бы на каждый метр...
            log.debug(f"Interrupt {self.pin}, count={racer_data[self.pin].rotations}")
        else:
            # Здесь фальстарт!
            if false_start_enable and not working:
                log.warning(f"Missing int call {self.pin} vs {pin} and {racer_data[self.pin].counting}. Фальстарт!")
                if not racer_data[self.pin].false_start:
                    log.info(f"Гонщик {racer_data[self.pin].name} поспешил!")
                    racer_data[self.pin].false_start = True


class Dialog(QtWidgets.QDialog):
    def __init__(self):
        super(Dialog, self).__init__()
        uic.loadUi(f'{work_dir}/dialog.ui', self)
        self.show()
        self.setWindowTitle("Новая гонка, запись участников...")


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
                log.debug(f"Приехали оба.")
                break
        self.finished.emit()


class Ui(QtWidgets.QMainWindow):
    start_app = pyqtSignal(int)
    stop_app = pyqtSignal(int)

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(f'{work_dir}/DragRacing.ui', self)
        self.thread = None
        self.worker = None
        self.newButton.clicked.connect(self.new_race)
        self.startButton.clicked.connect(self.start_race)
        self.stopButton.clicked.connect(self.stop_race)
        # Заполнить гончегов
        self.left = racer_data[left_pin] = Racer(left_pin)
        self.fill(self.left)
        self.right = racer_data[right_pin] = Racer(right_pin)
        self.fill(self.right)
        self.start_app.connect(self.start_race)
        GPIO.setup(startKnob, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(startKnob, GPIO.RISING, callback=self.start_app.emit, bouncetime=1000)
        self.stop_app.connect(self.stop_race)
        GPIO.setup(stopKnob, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(stopKnob, GPIO.RISING, callback=self.stop_app.emit, bouncetime=1000)
        # пыщ!
        # self.showMaximized()
        self.showFullScreen()

    def fill(self, racer):
        if racer.pin == left_pin:
            self.leftName.setText(racer.name)
            self.leftModel.setText(racer.model)
            self.leftSpeed.setText(str(racer.max_speed))
            self.leftDistance.setText(str(racer.distance))
            self.leftTime.setText(str(racer.time))
            self.leftBar.setValue(int(racer.distance))
        else:
            self.rightName.setText(racer.name)
            self.rightModel.setText(racer.model)
            self.rightSpeed.setText(str(racer.max_speed))
            self.rightDistance.setText(str(racer.distance))
            self.rightTime.setText(str(racer.time))
            self.rightBar.setValue(int(racer.distance))

    def new_race(self):
        # Старт -
        # Настройка *
        # Готов -
        led_off(startLed)
        led_on(setUpLed)
        led_off(readyLed)
        d = Dialog()
        if d.exec():
            log.debug("ok")
            self.leftName.setText(d.leftNameEdit.text())
            self.leftModel.setText(d.leftModelEdit.text())
            self.rightName.setText(d.rightNameEdit.text())
            self.rightModel.setText(d.rightModelEdit.text())
            pre_start_cleanup()
            self.report_progress()
        else:
            log.info("Ничего не делаем")
        # Старт -
        # Настройка -
        # Готов *
        led_off(startLed)
        led_off(setUpLed)
        led_on(readyLed)

    def fin_conn(self):
        # Старт -
        # Настройка -
        # Готов *
        led_off(startLed)
        led_off(setUpLed)
        led_on(readyLed)
        self.startButton.setEnabled(True)
        self.startButton.setText("Старт!")
        self.stopButton.setEnabled(False)
        self.newButton.setEnabled(True)

    def start_race(self):
        global reportFile
        global working
        if working:
            return
        for i in range(5):
            log.info("Старт...")
        # Старт *
        # Настройка -
        # Готов -
        led_on(startLed)
        led_off(setUpLed)
        led_off(readyLed)
        #
        for p, r in racer_data.items():
            r.false_start = False
        log.warning("Светофор включаем.")
        w = TrafficLight(parent=self, color='red', title="На старт...", led=tl_red)
        w.exec_()
        log.warning(f"Светофор красный отработал.")
        w = TrafficLight(parent=self, color='yellow', title="Внимание...", led=tl_yellow)
        w.exec_()
        log.warning(f"Светофор жёлтый отработал.")
        if racer_data[left_pin].false_start or racer_data[right_pin].false_start:
            working = False
            log.info("Фальстарт! Остановка гонки.")
            t = "ФАЛЬСТАРТ!\n"
            t += racer_data[left_pin].name + "\n" if racer_data[left_pin].false_start else ""
            t += racer_data[right_pin].name + "\n" if racer_data[right_pin].false_start else ""
            w = FalseStart(parent=self, text=t)
            w.show()
            # self.stop_race()
            return
        # Старт!
        working = True
        w = TrafficLight(parent=self, color='green', title="МАРШ!", led=tl_green)
        w.show()
        log.warning(f"Светофор зелёный отработал. Можно стартовать. {working}")
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
        # Раскраска фамилий?
        # Запись отчёта.
        try:
            reportFile.write("\t".join([datetime.now().strftime("%c"),
                                        self.left.name, self.left.model,
                                        str(self.left.max_speed), str(self.left.time),
                                        self.right.name, self.right.model,
                                        str(self.right.max_speed), str(self.right.time)]) + "\n")
        except Exception as e:
            log.error(f"Error with report {e}")

    def stop_race(self):
        global working
        if not working:
            return
        log.info("Остановка")
        working = False

    def report_progress(self):
        log.debug(f"обновляем...")
        if racer_data[left_pin].time - racer_data[left_pin].last_time != 0:
            try:
                racer_data[left_pin].speed = ((racer_data[left_pin].distance -
                                               racer_data[left_pin].last_distance
                                               ) / 1000000
                                              ) / ((racer_data[left_pin].time - racer_data[left_pin].last_time
                                                    ) / 3600
                                                   )
            except ZeroDivisionError:
                log.debug(f"zero division на обновлении {racer_data[left_pin].time} - {racer_data[left_pin].last_time}")
            log.debug(f"{racer_data[left_pin].speed} = ({racer_data[left_pin].distance} - " +
                      "{racer_data[left_pin].last_distance}) / 1000000 / ({racer_data[left_pin].time} - " +
                      "{racer_data[left_pin].last_time}) / 3600")
            racer_data[left_pin].last_time = racer_data[left_pin].time
            racer_data[left_pin].last_distance = racer_data[left_pin].distance
            if racer_data[left_pin].speed >= racer_data[left_pin].max_speed and \
                    racer_data[left_pin].time >= 2 * refreshProgress:
                racer_data[left_pin].max_speed = racer_data[left_pin].speed
        else:
            log.info("Левый медленно едет.")

        if racer_data[right_pin].time - racer_data[right_pin].last_time != 0:
            try:
                racer_data[right_pin].speed = ((racer_data[right_pin].distance - racer_data[
                    right_pin].last_distance) / 1000000) / \
                                              ((racer_data[right_pin].time - racer_data[right_pin].last_time) / 3600)
            except ZeroDivisionError:
                log.debug(f"zero division на обновлении "
                          "{racer_data[right_pin].time} - {racer_data[right_pin].last_time}")
            log.debug(f"{racer_data[right_pin].speed} = ({racer_data[right_pin].distance} - " +
                      "{racer_data[right_pin].last_distance}) / 1000000 / " +
                      "({racer_data[right_pin].time} - {racer_data[right_pin].last_time}) / 3600")
            racer_data[right_pin].last_time = racer_data[right_pin].time
            racer_data[right_pin].last_distance = racer_data[right_pin].distance
            if racer_data[right_pin].speed >= racer_data[right_pin].max_speed and \
                    racer_data[right_pin].time >= 2 * refreshProgress:
                racer_data[right_pin].max_speed = racer_data[right_pin].speed
        else:
            log.error(f"Правый медленно едет.")

        self.leftBar.setValue(int(racer_data[left_pin].distance / 1000))
        self.leftSpeed.setText("{:.2f}".format(racer_data[left_pin].max_speed))
        self.leftDistance.setText("{:.2f}".format(racer_data[left_pin].distance / 1000))
        self.leftTime.setText("{:.2f}".format(racer_data[left_pin].time))

        self.rightBar.setValue(int(racer_data[right_pin].distance / 1000))
        self.rightSpeed.setText("{:.2f}".format(racer_data[right_pin].max_speed))
        self.rightDistance.setText("{:.2f}".format(racer_data[right_pin].distance / 1000))
        self.rightTime.setText("{:.2f}".format(racer_data[right_pin].time))
        for p, r in racer_data.items():
            log.info(f"Данные: pin={p} rotations={r.rotations}, startTime={r.startTime}")


def pre_start_cleanup():
    # Очищает всё в момент старта.
    log.info("Очистка")
    for pin, racer in racer_data.items():
        racer.rotations = 0
        racer.distance = 0
        racer.speed = 0.0
        racer.time = 0.0
        racer.startTime = time.time()
        racer.counting = True
        racer.last_time = 0.0
        racer.last_distance = 0.0
        racer.max_speed = 0.0
        racer.false_start = False


if not MACOSX:
    log.info(f"RPI mode")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(leftLed, GPIO.OUT)
    GPIO.setup(rightLed, GPIO.OUT)
    GPIO.setup(tl_red, GPIO.OUT)
    GPIO.setup(tl_yellow, GPIO.OUT)
    GPIO.setup(tl_green, GPIO.OUT)
    GPIO.setup(readyLed, GPIO.OUT)
    GPIO.setup(startLed, GPIO.OUT)
    GPIO.setup(setUpLed, GPIO.OUT)
    for pin in [leftLed, rightLed, tl_red, tl_yellow, tl_green, readyLed, startLed, setUpLed]:
        GPIO.output(pin, light_off)
leftData = Signal(left_pin, leftLed)
rightData = Signal(right_pin, rightLed)

# Гуй
app = QtWidgets.QApplication([])
win = Ui()
# Старт -
# Настройка -
# Готов *
led_off(startLed)
led_off(setUpLed)
led_on(readyLed)
#
# Надо нажать New... или заполнить поля.
win.startButton.setEnabled(True)
win.stopButton.setEnabled(False)
# Пыщ!
with open('report.txt', 'w') as reportFile:
    rc = app.exec()
if not MACOSX:
    GPIO.cleanup()
sys.exit(rc)
