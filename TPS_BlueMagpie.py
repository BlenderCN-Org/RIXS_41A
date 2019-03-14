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

# import written .py
from pyepics_device import Devices as ped
from pyepics_tmp_device import TmpDevices as petd
from plotting import plot_function as qtplt
import epics as e



# Global parameters

spectrum_widget_global = None


# Import data from epics while program executed
  
#row = pd.Series({'x': self.hexapod_x.getValue(), 
#                 'y': self.hexapod_y.getValue(), 
#                 'z': self.hexapod_z.getValue(),
#                 'u': self.hexapod_u.getValue(), 
#                 'v': self.hexapod_v.getValue(), 
#                 'w': self.hexapod_w.getValue(),
#                 'AGM_Energy': self.AGM.get_position(), 
#                 'I01': e.caget(self.currentPV0)},
#                 name='test')
#df_tmp = df_tmp.append(row)



    #self.df_tmp = pd.DataFrame(columns=parameter_list)

# Get current value from dataframe
    #def gcv(self, name):
    #    self.name = p
    #    return df_tmp([-1],str(p))

    # Assign dummy values for status

parameter_list = ['t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb']
st_row = pd.Series([0,0,0,0,0,0,0,0,0,0,0,0,0], index=parameter_list)
print(st_row)
    

class RIXS(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        # Window attributes
        self.setFixedSize(1300, 750)
        self.setWindowTitle('TPS blue magpie')


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
        
########DEALING WITH STATUS DISPLAY########
        self.status_bar = QLabel("Experiment No.  1234;   PI: A. B. C. ", self)
        self.status_box = QTextEdit(self)
        global st_row
        time = QTime.currentTime()
        # HTML supported
        status_text = ("<font color=blue><b><u>Parameters</b></u></font><br>"
                       " Entrance slit: " + str(st_row['s1']) + "&micro;m<br>"
                       " AGM: " + str(0) + " eV<br>"
                       " Exit slit: " + str(0) + " &micro;m<br>"
                       " Sample:  x= " + str(0) + " ; y= " + str(0) + "; z= " + str(0) + " <br>"
                       " _______u= " + str(0) + " ; v= " + str(0) + "; w= " + str(0) + " <br>"
                       "   Temperature:  T<sub>a</sub>=" + str(0) + "K; T<sub>b</sub>: " + str(0) + " K<br>"
                       "           AGS: " + str(0) + " eV<br>")
        self.status_box.setText(status_text)
        self.status_box.setReadOnly(True)

        rightcolumn.addWidget(self.status_bar)
        rightcolumn.addWidget(self.status_box)
        
        # Real time update solution
        #def update_label():
        #current_time = str(datetime.datetime.now().time())
        #ui.label.setText(current_time)
        #timer = QtCore.QTimer()
        #timer.timeout.connect(update_label)
        #timer.start(10000)  # every 10,000 milliseconds
        
        spectrum_widget = SpectrumWidget(self)
        global spectrum_widget_global
        spectrum_widget_global = spectrum_widget
        rightcolumn.addWidget(spectrum_widget)

        hbox.addWidget(groupBox1, 1)
        hbox.addLayout(rightcolumn, 1)

        self.show()




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

        # widget design
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.command_message)
        self.layoutVertical.addWidget(self.command_input)


        # PyEPICS devices
          # written but removed from this branch

    def checkfloat(self, x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    def userinput(self, x):
        timestamp = QTime.currentTime()
        t = timestamp.toString()
        self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + x + '</font>')

    def send(self):
        global parameter_list, st_row
        text = self.command_input.text()

        # time stamp
        timestamp = QTime.currentTime()
        t= timestamp.toString()

        # history
        #self.hlog_list = ['Time', 'Text']
        #self.history_log = pd.DataFrame(columns=self.hlog_list)
        #self.row = pd.Series({[t, text], columns=self.hlog_list}, ignore_index=True)
        #self.history_log = self.history_log.append(self.row)
        #self.history_log = pd.concat([pd.DataFrame([t, text], columns=self.hlog_list)], ignore_index=True)
        #print(self.history_log)



        if text == "help":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = ("help: List all commands.\n"
                          "history: Recall previously typed messages.\n"
                          "mv: Set a parameter to its absolute value.\n")
        elif text == "draw":

            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            return_text = ("Signal emitted.")

            # Call Parameters
              # written but removed from this branch

            # Call Commands
              # no in this branch
            
            # test plotting commands

        elif text == "test":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            spectrum_widget_global.test()
            return_text = ("test signal emitted.")
        elif text == "test1":
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            spectrum_widget_global.test1()
            return_text = ("test1 signal emitted.")
        elif text == 'p':
            self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
            p = str(parameter_list)
            return_text = (p)
        elif text[:3] == 'mv ':
        # All sequence below should be organized as function(text) which returns return_tex
            space = text.count(' ')
            sptext = text.split(' ')

            # check format
            if space == 2:
                if sptext[1] in parameter_list:
                    # mv,a,b
                    a = sptext[1]
                    p = st_row.get(a)
                    b = sptext[2]
                    if self.checkfloat(b) is True:
                        b = float(b)
                        p += b
                        p = str(p)
                        self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
                        return_text = (a + " has been moved to " + p)
                    else:
                        self.command_message.append(timestamp.toString() + ' >> ' + text)
                        return_text = ("<font color=red>Input error // value must be number or float</font>")
                else:
                    self.command_message.append(timestamp.toString() + ' >> ' + text)
                    return_text = ("<font color=red>Input error // parameter doesn't exist // hint: type p to list parameters</font>")
            else:
                self.command_message.append(timestamp.toString() + ' >> ' + text)
                return_text = ("<font color=red>Input error // correct format: mv parameter value</font>")
        else:
           self.command_message.append(timestamp.toString() + ' >> ' + text)
           return_text = ("Type 'help' to list commands")
       
        
        #self.history_text = text
        self.command_message.append(return_text)
        self.command_input.setText("")

   #def history(self, event):
    #    if event.key() == Qt.Key_Up:
    #        self.command_input.setText(a) 





class ImageWidget(QWidget):

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        self.plotWidget = PlotWidget(self)
        self.data = np.linspace(-5.0, 5.0, 10)
        self.imgplot(self, self.data)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)

    @staticmethod
    def imgplot(self, x):
        self.plotWidget.plot(x)
    


class SpectrumWidget(QWidget):

    def __init__(self, parent=None):
        super(SpectrumWidget, self).__init__(parent=parent)
        self.data = [random.random() for i in range(250)]
        self.plotWidget = PlotWidget(self)
        self.imgplot(self.data)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)

    def imgplot(self, x):
        #clear previous plot
        self.plotWidget.plotItem.clear()
        self.plotWidget.plot(x)

    def test(self):
        print("test cross class communication")

    def test1(self):
        self.plotWidget.plotItem.clear()
        self.data = [random.random() for i in range(250)]
        self.imgplot(self.data)

def main():
    app = QApplication(sys.argv)
    ex = RIXS()
    cmd = Command()
    cmd.command_input.setFocus()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()