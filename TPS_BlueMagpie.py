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
import epics as e



# Global parameters

spectrum_widget_global = None
status_widget_global = None
cmd_global = None


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




parameter_list = ['t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb']
param = pd.Series([0,2,50,710,720,11,22,33,0,0,0,10,30], index=parameter_list)
print(param)
    

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
        global cmd_global
        hbox = QHBoxLayout(self)
        leftcolumn = QVBoxLayout()
        image_widget = ImageWidget(self)
        leftcolumn.addWidget(image_widget, 1)
        command_widget=Command(self)
        cmd_global = command_widget
        leftcolumn.addWidget(command_widget)


        # Right_Column

        rightcolumn = QVBoxLayout()
        global status_widget_global, spectrum_widget_global
        status_widget=StatusWidget(self)
        status_widget_global = status_widget
        rightcolumn.addWidget(status_widget)
        spectrum_widget = SpectrumWidget(self) 
        spectrum_widget_global = spectrum_widget
        rightcolumn.addWidget(spectrum_widget)

        hbox.addLayout(leftcolumn, 1)
        hbox.addLayout(rightcolumn, 1)

        self.show()

#lblName = QLabel(cur_time,user_name_wdgt)
#
#def update_label(self):
#    cur_time = datetime.strftime(datetime.now(), "%d.%m %H:%M:%S")
#    lblName.setText(cur_time)
#
#timer = QTimer()
#timer.timeout.connect(update_label)
#timer.start(1000)


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


class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super(StatusWidget, self).__init__(parent=parent)

        global param, parameter_text
                
        self.status_bar = QLabel("Experiment No.  1234;   PI: A. B. C. ", self)
        self.status_box = QTextEdit(self)

        time = QTime.currentTime()
        self.show_text()
        self.status_box.setReadOnly(True)

        # Widget layout
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.status_bar)
        self.layoutVertical.addWidget(self.status_box)

        # Forced refresh

    def show_text(self):
        global param
        # index: parameter_list = ['t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb']
        parameter_text = ("<font color=blue><b><u>Parameters</b></u></font><br>"
                       " Entrance slit: " + str(param['s1']) + " &micro;m<br>"
                       " AGM: " + str(param['agm']) + " eV<br>"
                       " Exit slit: " + str(param['s2']) + " &micro;m<br>"
                       " Sample:  x = " + str(param['x']) + ", y = " + str(param['y']) + ", z   = " + str(param['z']) + ", "
                       " u = " + str(param['u']) + ", v = " + str(param['v']) + ", w = " + str(param['w']) + " <br>"
                       "   Temperatures:  T<sub>a</sub> = " + str(param['ta']) + " K, T<sub>b</sub> = " + str(param['tb']) + " K<br>"
                       "           AGS: " + str(param['ags']) + " eV<br>")
        self.status_box.setText(parameter_text)


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
        global parameter_list, param
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

            # Move function
        elif text[:3] == 'mv ':
        # All sequence below should be organized as function(text) which returns return_tex
            space = text.count(' ')
            sptext = text.split(' ')

            # check format
            if space == 2:
                if sptext[1] in parameter_list:
                    if self.checkfloat(sptext[2]) is True:
                        self.command_message.append('<font color=blue>' + timestamp.toString() + ' >> ' + text + '</font>')
                        param[sptext[1]] = float(sptext[2])
                        return_text = (sptext[1] + " has been moved to " + sptext[2])
                        status_widget_global.show_text()
                    else:
                        self.command_message.append(timestamp.toString() + ' >> ' + text)
                        return_text = ("<font color=red>Input error // value must be number or float</font>")
                else:
                    self.command_message.append(timestamp.toString() + ' >> ' + text)
                    return_text = ("<font color=red>Input error: parameter \'"+ sptext[1]+ "\' is invalid; type \'p\' to list valid parameters</font>")
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
    cmd_global.command_input.setFocus()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()