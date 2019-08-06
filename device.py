import PyQt5
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import sys, os
import pvlist

class Configurations(QWidget):
    errorMsg = pyqtSignal(str,str)
    cmdMsg = pyqtSignal(str)
    reconnect = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        # default configurations
        self.safeflags = dict(ccd= 1, xyzstage = 1, chmbr =1, tth =1, 
                              det = 1, th = 1, agm = 1, ags = 1, ta = 1, tb = 1, heater = 1,
                              I0 =1, Iph = 1, Itey = 1, Iring = 1, thoffset = 1)
        # to be added: shutter, s1, s2; removed: hexapod
        self.popup()

    def popup(self):
        self.__mainwindow__()
        self.__checkbox__()
        self.__layout__()
        self.show()

    def __mainwindow__(self):
        self.setWindowTitle("Device Connections")
        self.resize(400, 150)
        self.setWindowFlags(self.windowFlags() & Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
    # using dictionary for checkbox arrangements
    def __checkbox__(self):
        self.checkbox = {} 
        # check box individually
        for p in self.safeflags.keys():
            self.checkbox[p] = QCheckBox(p, self)
            if self.safeflags[p] == 1:
                self.checkbox[p].setChecked(True)
            self.checkbox[p].stateChanged.connect(self.integrityCheck)
        # check box for all flags
        self.checkbox['test'] = QCheckBox('all', self) 
        self.checkbox['test'].stateChanged.connect(self.allCheck)
        self.checkbutton = QPushButton('OK', self)
        self.cancelbutton = QPushButton('cancel', self)
        self.checkbutton.clicked.connect(self.okPressed)
        self.cancelbutton.clicked.connect(self.cancelPressed)

    def __layout__(self):
        self.__window_layout = QVBoxLayout(self)
        self.__device_layout = QHBoxLayout()
        self.__indicator_layout = QHBoxLayout()
        self.__buttons_layout = QHBoxLayout()
        for p in self.safeflags.keys():
            if p in ['ccd', 'xyzstage', 'chmbr', 'th', 'det', 'agm', 'ags', 'tth', 'heater']:
                self.__device_layout.addWidget(self.checkbox[p])
            else:
                self.__indicator_layout.addWidget(self.checkbox[p])
        self.__buttons_layout.addWidget(self.checkbutton,20)
        self.__buttons_layout.addWidget(self.cancelbutton ,20)
        self.__window_layout.addWidget(self.checkbox['test'])
        self.__window_layout.addWidget(QLabel('Devices'))
        self.__window_layout.addLayout(self.__device_layout)
        self.__window_layout.addWidget(QLabel('Indicators'))
        self.__window_layout.addLayout(self.__indicator_layout)
        self.__window_layout.addLayout(self.__buttons_layout)
    # all checkbox
    def allCheck(self):
        state = self.checkbox['test'].checkState()
        if state != Qt.PartiallyChecked: # all checked or all unchecked
            if state == Qt.Checked:
                flag = True
            elif state == Qt.Unchecked:
                flag = False
            for p in self.safeflags: 
                self.checkbox[p].setChecked(flag)
    # individual check for all
    def integrityCheck(self):
        i, n = 0, 0
        for p in self.safeflags:
            n += 1
            if self.checkbox[p].checkState() == Qt.Checked:
                i += 1
        if 0 < i and i < n :
            self.checkbox['test'].setTristate()
            self.checkbox['test'].setCheckState(Qt.PartiallyChecked)
        elif i==0:
            self.checkbox['test'].setCheckState(Qt.Unchecked)
        else:
            self.checkbox['test'].setChecked(True)
    # OK button
    def okPressed(self):
        # compare new configurations with current status (no need to reconnect if before = after)
        for p in self.safeflags.keys():
            flag = 1 if (self.checkbox[p].checkState() == Qt.Checked) else 0
            # if before != after, reconnect
            if self.safeflags[p] != flag:
                self.safeflags[p] = flag
                print(p, ' changed')
            else:
                print(p, ' not changed')
        QMessageBox.information(self, 'Message', 'changes saved.')
    # Cancel button
    def cancelPressed(self):
        QMessageBox.information(self, 'Message', 'no option changed, closing window ...')
        self.close()
    
    def testReconnect(text):
        print('reconnecting ... ', text)

    # Individual device safe check called by main program
    def checkSafe(p):  
        if self.safeflags["test"] == 0:
            if p in ['x', 'y', 'z']:
                if self.safeflags["xyzstage"] == 1:
                    return True
            elif p in ["ccd", "gain", "Tccd"]:
                if self.safeflags['ccd'] == 1:
                    return True
            elif self.safeflags[p] == 1:
                return True
            else:
                return False
        else:
            return False
# Testing independently
def run():
    app = QApplication(sys.argv)
    GUI = Configurations()
    sys.exit(app.exec_())

run()