import os, sys, time, random
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QGridLayout, QFileDialog, QInputDialog, QAction,
                             QCheckBox, QGroupBox, QSpinBox, QProgressBar, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QSpacerItem, QSizePolicy, QAction, QPushButton, qApp, QPlainTextEdit, QFormLayout, QAction,
                             QScrollBar,QSplitter,QTableWidgetItem,QTableWidget,QComboBox,QVBoxLayout,QGridLayout,
                             QPushButton, QMainWindow,QMessageBox,QLabel,QTextEdit,QProgressBar)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, QDate, QTime, QDateTime

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np


class RIXS(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        ###Window_size
        self.setFixedSize(1300, 750)
        ###Window_Title
        self.setWindowTitle('TPS blue magpie')
        exitAct = QAction(QIcon('exit.png'), ' &Quit', self)
        ###Quit_button
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)
        ###Menu_Bar
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)
        ###EMCCD_button
        emccdMenu = menubar.addMenu("EMCCD")
        emccdMenu.addAction("cooling on")
        emccdMenu.addAction("cooling off")
        ###SDD_button
        sddMenu = menubar.addMenu('SDD')
        ###Slit_button
        slitMenu = menubar.addMenu('Slits')
        ###Help_button
        helpMenu = menubar.addMenu('Help')

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()


###GUI_design
class MyTableWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        """
        Import designed UI
        """
        self.initUI()

    def initUI(self):
        self.setFixedSize(1300, 750)
        self.setWindowTitle('TPS blue magpie')

        ###Left_Column
        hbox = QHBoxLayout(self)
        groupBox1 = QGroupBox()
        vbox = QVBoxLayout(groupBox1)
        image_widget = ImagingWidget(self)
        vbox.addWidget(image_widget, 1)
        command_widget=Command(self)
        vbox.addWidget(command_widget)

        hbox.addWidget(groupBox1, 1)

        ###Status_area
        vbox2 = QVBoxLayout()
        groupBox2 = QGroupBox("Experiment No.  1234;   PI: A. B. C. ", self)
        vbox3 = QVBoxLayout(groupBox2)
        flay = QFormLayout()

        label1 = QLabel("Entarnce slit: 5 um", groupBox2)
        flay.addRow(label1)
        label2 = QLabel("AGM: 530 eV", groupBox2)
        flay.addRow(label2)
        label3 = QLabel("Exit slit: 50 um", groupBox2)
        flay.addRow(label3)
        label4 = QLabel("Sample: x=  , y=  , z=   , u=  , v=  , w=  , Ta=  , Tb=  K", groupBox2)
        flay.addRow(label4)
        label5 = QLabel("AGS: 530 eV", groupBox2)
        flay.addRow(label5)

        vbox3.addLayout(flay, 1)
        vbox2.addWidget(groupBox2)

        groupBox3 = QGroupBox()

        vbox4 = QVBoxLayout(groupBox3)
        m2 = SpectrumWidget(self)
        vbox2.addWidget(m2)
        hbox.addLayout(vbox2, 1)

        self.show()


class ImagingWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = ImagingCanvas(self, width=5, height=4)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)


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
        welcome_message = '''
        Welcome to TPS_BlueMagpie!
        Type help to list commands.'''
        self.command_message.setText(welcome_message)
        self.command_message.setReadOnly(True)
        #optional: string format:print('Hello, {:s}. You have {:d} messages.'.format('Rex', 999))

        # user input
        self.command_input= QLineEdit(self)
        self.command_input.returnPressed.connect(self.send)

        # widget design
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.command_message)
        self.layoutVertical.addWidget(self.command_input)

    def send(self):
            text = self.command_input.text()
            if text == "help":
                time = QTime.currentTime()
                self.command_message.append('<font color=blue>' + time.toString() + ' >> '+ text+ '</font>')
                return_text = ("help: List all commands.\n"
                               "history: Recall previously typed messages.\n"
                               "mv: Set a parameter to its absolute value.\n")

            else:
                return_text = ("Type 'help' to list commands")

            self.command_message.append(return_text)
            self.command_input.setText("")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RIXS()
    sys.exit(app.exec_())
