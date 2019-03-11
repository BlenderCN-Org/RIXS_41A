import os, sys, time, random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QGridLayout, QFileDialog, QInputDialog, QAction,
                             QCheckBox, QGroupBox, QSpinBox, QProgressBar, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QSpacerItem, QSizePolicy, QAction, QPushButton, qApp, QPlainTextEdit, QFormLayout, QAction,
                             QScrollBar,QSplitter,QTableWidgetItem,QTableWidget,QComboBox,QVBoxLayout,QGridLayout,
                             QPushButton, QMainWindow,QMessageBox,QLabel,QTextEdit,QProgressBar)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, QDate, QTime, QDateTime, QObject, QEvent, pyqtSignal, QTimer, pyqtSlot
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import pyqtgraph as pg
from pyqtgraph import PlotWidget
import numpy as np
import pandas as pd


# Global Data

# Test without class
'''
data = np.linspace(-5.0, 5.0, 10)
data = pyqtSignal
data.valueChanged.connect(ImageWidget.imgplot)
'''

    


class Data(QWidget):
    data = np.linspace(-5.0, 5.0, 10)
    valueChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super(Data, self).__init__(parent)
        self._t = self.data

    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, value):
        self._t = value
        self.valueChanged.emit(value)
        print("Data emitted to plot.")
        
        #communicate with Command Widget
        
    @pyqtSlot(object)
    def get_new_data(self, value):
        self.t.setValue(value)
        print("new data value received")

    def make_cmd_connection(self, cmd_object):
        cmd_object.valueChanged.connect(self.get_new_data)

# Testing other dataset
'''
Y = np.linspace(-5.0, 5.0, 10)
Z = (X,Y)
imgdata = pd.DataFrame(X, Y)
'''

class RIXS(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        # Window attributes

        self.setFixedSize(2600, 1500)
        self.setWindowTitle('TPS blue magpie')


        # Menu Bar

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
        image_widget = ImageWidget(self)
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
        # Real time update solution
        '''
        def update_label():
        current_time = str(datetime.datetime.now().time())
        ui.label.setText(current_time)

        timer = QtCore.QTimer()
        timer.timeout.connect(update_label)
        timer.start(10000)  # every 10,000 milliseconds
        '''

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
    valueChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._v =  0

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
          # written but removed from this branch

    def send(self):
        text = self.command_input.text()
        timestamp = QTime.currentTime()

        if text == "help":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = ("help: List all commands.\n"
                          "history: Recall previously typed messages.\n"
                          "mv: Set a parameter to its absolute value.\n")
        elif text == "draw":
            Y = np.linspace(-1.0, 1.0, 20)
            self.v = Y
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = ("Signal emitted.")

            # Call Parameters
              # written but removed from this branch

            # Call Commands
              # no in this branch

        else:
           return_text = ("Type 'help' to list commands")
       
        
        
        #self.history_text = text
        self.command_message.append(return_text)
        self.command_input.setText("")

    @property
    def v(self):
        return self._v

    @v.setter
    def v(self, value):
        self._v = value
        self.valueChanged.emit(value)
        print("new data emitted.")
        


class ImageWidget(QWidget):

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        self.plotWidget = PlotWidget(self)
        self.imgplot(self, Data.data)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)

    @staticmethod
    def imgplot(self, x):
        self.plotWidget.plot(x)
    
    def make_data_connection(self, data_object):
        data_object.valueChanged.connect(self.get_data)

    @pyqtSlot(object)
    def get_data(self, val):
        self.imgplot(self, val)
        print("new data plot")



def main():
    app = QApplication(sys.argv)
    ex = RIXS()
    cmd = Command()
    cmd.command_input.setFocus()
    img=ImageWidget()
    dt=Data()
    img.make_data_connection(dt)
    dt.make_cmd_connection(cmd)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()