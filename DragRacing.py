#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import sys, time, random

# Глобальное

# МКА



# Классы

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
        win.startButton.setText("Поехали...")
        print("button")
        ldist=0
        rdist=0
        for i in range(100):
            print(f"t={i}")
            ldist += random.randint(0,4)
            rdist += random.randint(0,5)
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
            print("НИчего не делаем")

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

app = QtWidgets.QApplication([])
win = Ui()
# Надо нажать New... или заполнить поля.
win.startButton.setEnabled(True)
win.stopButton.setEnabled(False)
# Пыщ!
sys.exit(app.exec())