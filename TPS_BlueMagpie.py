import os, sys, time, random
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QGridLayout, QFileDialog, QInputDialog, QAction,
                             QCheckBox, QGroupBox, QSpinBox, QProgressBar, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QSpacerItem, QSizePolicy, QAction, QPushButton, qApp, QPlainTextEdit, QFormLayout, QAction,
                             QScrollBar,QSplitter,QTableWidgetItem,QTableWidget,QComboBox,QVBoxLayout,QGridLayout,
                             QPushButton, QMainWindow,QMessageBox,QLabel,QTextEdit,QProgressBar)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, QDate, QTime, QDateTime, QObject, QEvent, pyqtSignal, pyqtSlot
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import pyqtgraph as pg
import numpy as np

# import written .py
from pyepics_device import Devices as ped
from pyepics_tmp_device import TmpDevices as petd
from plotting import plot_function as qtplt
import epics as e


class RIXS(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        # Window attributes

        self.setFixedSize(1300, 750)
        self.setWindowTitle('TPS blue magpie')


        # Buttons

        exitAct = QAction(QIcon('exit.png'), ' &Quit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)

        emccdMenu = menubar.addMenu("EMCCD")
        emccdMenu.addAction("cooling on")
        emccdMenu.addAction("cooling off")

        '''To be continued'''
        #sddMenu = menubar.addMenu('SDD')
        #slitMenu = menubar.addMenu('Slits')
        #helpMenu = menubar.addMenu('Help')

        # Import panel
        self.panel_widget = Panel(self)
        self.setCentralWidget(self.panel_widget)
        self.show()



class Panel(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)


        # Import designed UI
        self.UI_layout()

    def UI_layout(self):
        self.setFixedSize(1300, 750)
        self.setWindowTitle('TPS blue magpie')

        # Left_Column

        hbox = QHBoxLayout(self)
        groupBox1 = QGroupBox()
        vbox = QVBoxLayout(groupBox1)
        image_widget = ImagingWidget(self)
        vbox.addWidget(image_widget, 1)
        command_widget=Command(self)
        vbox.addWidget(command_widget)



        # Right_Column

        rightcolumn = QVBoxLayout()

        status_box = QGroupBox("Experiment No.  1234;   PI: A. B. C. ", self)
        status_contents = QVBoxLayout(status_box)

        flay = QFormLayout()

        status = QLabel("Entrance slit: 5 um\n"
                        "AGM: 530 eV\n"
                        "Exit slit: 50 um\n"
                        "Sample: x=  , y=  , z=   , u=  , v=  , w=  , Ta=  , Tb=  K\n"
                        "AGS: 530 eV\n", status_box)
        flay.addRow(status)
        status_contents.addLayout(flay, 1)


        spectrum_widget = SpectrumWidget(self)

        rightcolumn.addWidget(status_box)
        rightcolumn.addWidget(spectrum_widget)

        hbox.addWidget(groupBox1, 1)
        hbox.addLayout(rightcolumn, 1)

        self.show()


class ImagingWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = ImagingCanvas(self, width=5, height=4)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

    def plot(self):
        print("ok.")


class SpectrumWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = SpectrumCanvas(self, width=5, height=4)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)



class SpectrumCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()


    # random spectrum display
    def plot(self):
        data = [random.random() for i in range(250)]
        ax = self.figure.add_subplot(111)
        ax.plot(data, 'r-', linewidth=0.5)
        ax.set_title('RIXS spectrum')
        ax.set_xlabel('Energy Loss (eV)')
        ax.set_ylabel('RIXS counts')
        self.draw()


class ImagingCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        ###Command.plot_image.connect(Command.plot)
        self.plot()

    # random image display
    def plot(self):
        xlist = np.linspace(-3.0, 3.0, 3)
        ylist = np.linspace(-3.0, 3.0, 4)
        X, Y = np.meshgrid(xlist, ylist)
        Z = np.sqrt(X ** 2 + Y ** 2)

        ax = self.figure.add_subplot(111)
        ax.contourf(X, Y, Z)
        ax.set_title('RIXS image')
        self.draw()

class Command(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # message
        self.command_message = QTextEdit(self)
        time = QTime.currentTime()
        welcome_message = ('<font color=blue>' + time.toString() + ' >> Welcome to TPS_BlueMagpie!</font>')
        self.command_message.setText(welcome_message)
        self.command_message.setReadOnly(True)
        #optional: string format:print('Hello, {:s}. You have {:d} messages.'.format('Rex', 999))

        # user input
        self.command_input= QLineEdit(self)
        self.command_input.setFocusPolicy(Qt.StrongFocus)
        self.command_input.setPlaceholderText("Type help to list commands ...")
        self.command_input.returnPressed.connect(self.send)

        # call history text
    #    history_text =
    #    self.command_input.upPressed.connct(self.history)

        # widget design
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.command_message)
        self.layoutVertical.addWidget(self.command_input)


        # PyEPICS devices
        self.hexapod_x = ped("hx", "41a:hexapod:x")

        self.tsa = petd("tmp1", "41a:sample:tmp1")
        self.tsb = petd("tmp2", "41a:sample:tmp2")

        self.currentPV0 = "41a:sample:i0"
        self.currentPV1 = "41a:sample:phdi"

        self.AGM = e.Motor("41a:AGM:Energy")
        self.AGS = e.Motor("41a:AGS:Energy")

    def send(self):
        text = self.command_input.text()
        timestamp = QTime.currentTime()

        if text == "help":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = ("help: List all commands.\n"
                          "history: Recall previously typed messages.\n"
                          "mv: Set a parameter to its absolute value.\n")
        elif text == "draw":
            ImagingWidget.plot(self) # test communication
            SpectrumCanvas.plot(SpectrumCanvas)
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = ("Signal emitted.")
            # Call Parameters
        elif text == "x":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = (str(self.hexapod_x.getValue()))
        elif text == "Tsa":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = (str(self.tsa.getValue()))
        elif text == "Tsb":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = (str(self.tsb.getValue()))
        elif text == "I01":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = (str(e.caget(self.currentPV0)))
        elif text == "I02":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = (str(e.caget(self.currentPV1)))
        elif text == "AGM":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = (str(self.AGM.get_position()))

        # Call Commands

        else:
           return_text = ("Type 'help' to list commands")


        #self.history_text = text
        self.command_message.append(return_text)
        self.command_input.setText("")


def main():
    app = QApplication(sys.argv)
    ex = RIXS()
    cmd = Command()
    imgc = ImagingCanvas()

    cmd.command_input.setFocus()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()