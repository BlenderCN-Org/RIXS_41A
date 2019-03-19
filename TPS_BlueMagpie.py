import os, sys, time, random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QGridLayout, QFileDialog, QInputDialog, QAction,
                             QCheckBox, QGroupBox, QSpinBox, QProgressBar, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QSpacerItem, QSizePolicy, QAction, QPushButton, qApp, QPlainTextEdit, QFormLayout, QAction,
                             QScrollBar,QSplitter,QTableWidgetItem,QTableWidget,QComboBox,QVBoxLayout,QGridLayout,
                             QPushButton, QMainWindow,QMessageBox,QLabel,QTextEdit,QProgressBar)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize, Qt, QDate, QTime, QDateTime, QObject, QEvent, pyqtSignal, QTimer, pyqtSlot
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import pyqtgraph as pg
from pyqtgraph import PlotWidget
import numpy as np
import pandas as pd
import time, datetime, math
# import written .py

#from pyepics_device import Devices as ped
#from pyepics_tmp_device import TmpDevices as petd
#import epics as e


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

# Global parameters

spectrum_widget_global = None
status_widget_global = None
cmd_global = None

param_index = ['t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb', 'I0']
param = pd.Series([0.00,2.00,50.00,710.00,720.00,11.00,22.00,33.00,0.00,0.00,0.00,10.00,30.00, 0.0], index=param_index)

scan_data = None
xas_data = None
rixs_data = None
scan_matrix = None
file_no = 0


# create temp dir for datasaving 
path=os.getcwd()
dir_date = datetime.datetime.today().strftime('%Y%m%d')
dir_name = dir_date+'temp'
if not os.path.exists(dir_name):
    os.makedirs(dir_name)
        
if '\\' in path:
    # dir for windows
    file_path = str(path) +'\\'+ dir_name +'\\' 
else:
    # dir fo linux
    file_path = str(path) +'/'+ dir_name +'/'


#pg.setConfigOption('background', 'k')
#pg.setConfigOption('background',rgb(192,192,192)
#pg.setConfigOption('foreground', 'w')



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

        #TODO: To be continued
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

        time = QTime.currentTime()
        self.status_bar = QLabel("Experiment No.  1234;   PI: A. B. C. ", self)
        self.status_box = QTextEdit(self)

        

        self.show_text()
        self.status_box.setStyleSheet("color: blue; background-color: Lemonchiffon")
        self.status_box.setFont(QtGui.QFont("Ubuntu Mono",14))
        self.status_box.setReadOnly(True)

        # Widget layout
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.status_bar)
        self.layoutVertical.addWidget(self.status_box)

        # Forced refresh

    def show_text(self):
        global param
        # index: param_index = ['t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb']
        parameter_text = ("<font color=black><b><u>Parameters</b></u></font><br>"
                       " Entrance slit: " + str(param['s1']) + " &micro;m<br>"
                       " AGM: " + str(param['agm']) + " eV<br>"
                       " Exit slit: " + str(param['s2']) + " &micro;m<br>"
                       " Sample:  x = " + str(param['x']) + ", y = " + str(param['y']) + ", z   = " + str(param['z']) + ", "
                       " u = " + str(param['u']) + ", v = " + str(param['v']) + ", w = " + str(param['w']) + " <br>"
                       "   Temperatures:  T<sub>a</sub> = " + str(param['ta']) + " K, T<sub>b</sub> = " + str(param['tb']) + " K<br>"
                       "           AGS: " + str(param['ags']) + " eV<br>")
        self.status_box.setText(parameter_text)
        
        #TODO : auto update parameter display in status widget

    #    timer = QTimer()
    #    timer.timeout.connect(self.auto_update)
    #    timer.start(1000)
    #def auto_update(self):
    #    global status_widget_global
    #    cur_time = datetime.strftime(datetime.now(), "%d.%m %H:%M:%S")
    #    object.setText(cur_time)
    #    status_widget_global.show_text()
        


class Command(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # message
        self.command_message = QTextEdit(self)
        ###test
        time = QTime.currentTime()
        welcome_message = ('<font color=blue>' + time.toString() + ' >> Welcome to TPS_BlueMagpie!</font>')
        self.command_message.setText(welcome_message)
        self.command_message.setReadOnly(True)
        #optional: string format:print('Hello, {:s}. You have {:d} messages.'.format('Rex', 999))

        # history
        self.history_index = ['Time','Text']
        self.history_log = pd.DataFrame(columns=self.history_index)
        self.history_size = 0

        # user input
        self.command_input= QLineEdit(self)
        self.command_input.setFocusPolicy(Qt.StrongFocus)
        self.command_input.setPlaceholderText("Type help to list commands ...")
        self.command_input.returnPressed.connect(self.send)

        # widget design
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.command_message)
        self.layoutVertical.addWidget(self.command_input)
        
        # redefine function of QLineEdit(originally support return only) 
    def keyPressEvent(command_input, event):
        global cmd_global
        if event.key() == Qt.Key_Up:
            Up_text = cmd_global.history_log[cmd_global.history_size]
            cmd_global.command_input.setText(Up_text)
        else:
            super(Command, command_input).keyPressEvent(event)

        # PyEPICS devices
          # written but removed from this branch

    def send(self):
        global param_index, param, cmd_global
        text = self.command_input.text()

        # time stamp
        timestamp = QTime.currentTime()
        t= timestamp.toString()

        # check input_string in command
        self.record = 0    #assume invalid input

        if text == "help":
            self.record = 1
            return_text = ("his: recall previously typed messages.\n"
                           "mv: set a parameter to its absolute value.\n"
                           "mvr: change a parameter in terms of a relative value.\n"
                           "p: list valid parameters.\n"
                           "scan: stepwise scan a parameter and plot selected paramters with some dwell time.\n")
        elif text == "draw":
            self.record = 1
            return_text = ("Signal emitted.")

        elif text == "his":
            # TODO: Flexible display?
            his_text = self.history_log.to_string(index_names=False, index=False, header=False, max_rows=10)
            return_text = (his_text)
            self.record = 1

            # Call Parameters
              # written but removed from this branch

            # Call Commands
              # no in this branch

            # test plotting commands

        elif text == 'p':
            self.record = 1
            p = str(param_index)
            return_text = (p)

        # MV function
        elif text == 'mv' or text[:3] == 'mv ':
        # All sequence below should be organized as function(text) which returns return_text
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2:
                if sptext[1] in param_index:
                    if self.checkFloat(sptext[2]) is True:
                        param[sptext[1]] = float(sptext[2])
                        print(float(sptext[2]))
                        return_text = (sptext[1] + " has been moved to " + sptext[2])
                        status_widget_global.show_text()
                        self.record = 1
                    else:
                        return_text = ("<font color=red>Input error // value must be number or float</font>")
                else:
                    return_text = ("<font color=red>Input error: parameter \'"+ sptext[1]+ "\' is invalid; type \'p\' to list valid parameters</font>")
            else:
                return_text = ("<font color=red>Input error // correct format: mv parameter value</font>")

        # MVR function
        elif text[:4] == 'mvr ':
        # All sequence below should be organized as function(text) which returns return_tex
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2:
                if sptext[1] in param_index:
                    if self.checkFloat(sptext[2]) is True:
                        param[sptext[1]] = float(param[sptext[1]])+float(sptext[2])
                        output = str(param[sptext[1]])
                        return_text = (sptext[1] + " has been moved to " + output)
                        status_widget_global.show_text()
                        self.record = 1
                    else:
                        return_text = ("<font color=red>Input error // value must be number or float</font>")
                else:
                    return_text = ("<font color=red>Input error: parameter \'"+ sptext[1]+ "\' is invalid; type \'p\' to list valid parameters</font>")
            else:
                return_text = ("<font color=red>Input error // correct format: mv parameter value</font>")

        # SCAN function
        # command format: scan (det1 det2 ...;) scan_param start end step dwell

        elif text == 'scan' or text[:5] == 'scan ':
            # if the input command is only 'scan' but not parameters return_text != 'OK',
            return_text = self.check_param_scan(text)   # checking input command and parameters
            if return_text == 'OK':
                if text.find(':') == -1: #scan x 1 10 1 0.1
                    c = 5
                    det=['I0'] #default detection parameter
                else: #scan y z; x 1 10 1 0.1
                    c = text.find(':')+2
                    det=text[5:c-2].split(' ') # list of detection parameters

                print('det=', det)
                sptext = text[c:].split(' ') # list of scan parameters
                scan_param = sptext[0]
                x1 = float(sptext[1]) # start
                x2 = float(sptext[2]) # end
                step = abs(float(sptext[3]))*np.sign(x2-x1) # step is negative if x1 > x2
                dwell = float(sptext[4])
                n = int(abs((x2-x1)/step)) #set the number of scanning steps

                param[scan_param] = x1
                status_widget_global.show_text()
                QtGui.QApplication.processEvents()
                time.sleep(0.5)
                t0=datetime.datetime.now()
                #self.command_message.append(t0.strftime("%c"))
                self.command_message.append('Scanning begins at ' + t0.strftime("%c"))
                t1 = time.time()

                #print('scan loop begins')
                spectrum_widget_global.scan_loop(det, sptext)
                dt = round(time.time()- t1, 3)
                print('timespan in senconds=', dt)
                return_text = 'Scanning is completed; timespan  = ' + self.convertSeconds(dt)
                self.record = 1

        else:
           return_text = ("Type 'help' to list commands")

        # collect user input
        self.validInput(text,t,self.record)
        # print system message
        self.command_message.append(return_text)
        # refresh and scroll down to latest message
        self.command_input.setText("")
        self.command_message.moveCursor(QtGui.QTextCursor.End)
        cmd_global.command_input.setFocus()

    # Check and store valid commands
    def validInput(self, x, t, v):
        if v == 1:
            # append text to history
            self.history_size += 1
            self.row = pd.Series([t,x], index = self.history_index, name = self.history_size)
            self.history_log = self.history_log.append(self.row)
            # append valid command
            return (self.command_message.append('<font color=blue>' + t + ' >> ' + x + '</font>'))
        else:
            # invalid command
            return (self.command_message.append('<font color=gray>' + t + ' >> ' + x + '</font>'))


        
    def pressUp(self, event):
        self.command_input.keyPressEvent(self, event)
        


    def convertSeconds(self,seconds):
        h = int(seconds//(60*60))
        m = int((seconds-h*60*60)//60)
        s = round(seconds-(h*60*60)-(m*60), 3)
        #print('h=   ', h)
        time_stg = '['+str(h)+' h, '+str(m)+' m, ' +str(s)+' sec]'
        return time_stg

    def checkFloat(self, x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    def check_param_scan(self, text):
        global param, scan_data, param_index
        # input text format: scan scan_param start end step dwell
        # or
        # input text format: scan det1 det2 ....: scan_param start end step dwell

        if text.find(':') == -1:
            sptext = text[5:].split(' ') # scan_param 1 10 1 0.1
            space = text.count(' ') #space =5, e.g. scan x 1 10 2 0.1
            c=5
            det=['I0']
        else:
            c = text.find(':')
            space = text[c:].count(' ') # space = 5, after truncating "scan y z ...:" => e.g. : x 1 10 2 0.1
            sptext = text[c+2:].split(' ') # scan_param 1 10 1 0.1
            det=text[5:c-2].split(' ') # list of detection parameter
        print('det=', det)

        scan_param = sptext[0]
        # if the input command is correct, sptext should be a list containing a scan_param
        # and 4 numbers, e.g. sptext = ['x', '1', '10', '2', '0.1']
        print('text=', text)
        print('sptext=', sptext)
        print('legn', len(sptext))
        print(sptext[0])
        if text[c+1:].find(':') == -1 and space == 5:
            if (sptext[0] != '') and (len(sptext) == 5):
                j=0 #check index
                for i in range(4): # i from 0 to 3
                    if self.checkFloat(sptext[i+1]) is True:
                        j +=1.0
                if j==4:
                    if sptext[0] in param_index:
                        if float(sptext[4]) > 0:  #float(sptext[4]) assigns dwell time
                            return_text = 'OK'
                        else:
                            return_text = ("<font color=red> Input error; dwell time must be positive.</font>")
                           
                    else:
                        return_text = ("<font color=red>Input error: parameter \'"+ sptext[0]+ "\' is invalid; type \'p\' to list valid parameters</font>")
                     
                else:
                    return_text = ("<font color=red> parameter values are invalid; \'start end step dwell\' shoiuld be numeric.</font>")
                     
            else:
                return_text = ("<font color=red> Input error; format: scan [det1 det2 .. :] parameter start end step well_time</font>")
                
        else:
            return_text = ("<font color=red> Input error; format: scan [det1 det2 ... :] parameter start end step well_time</font>")
            
        #checking if dection parameters have been correctly selected
        j=0 #check index
        for i in range(len(det)): # i from 0 to len(det)-1
            if det[i] in param_index: j +=1.0
        if j== len(det):
            return_text_det='OK'
        else: return_text_det='not OK'

        if return_text == 'OK' and return_text_det == 'OK': return_text ='OK'
        if return_text == 'OK' and return_text_det != 'OK': return_text ='<font color=red>Input error: invalid detection parameters</font>'

        return return_text


    def append_txt(self, text):
        self.command_message.append(text)



class ImageWidget(QWidget):

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        self.plotWidget = PlotWidget(self)
        self.data = np.linspace(-5.0, 5.0, 10)
        self.spectrumplot(self, self.data)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)

    @staticmethod
    def spectrumplot(self, x):
        self.plotWidget.plot(x)



class SpectrumWidget(QWidget):

    def __init__(self, parent=None):
        super(SpectrumWidget, self).__init__(parent=parent)
        self.data = [random.random() for i in range(250)]
        self.plotWidget = PlotWidget(self)
        self.spectrumplot(self.data)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)
        self.w = None

    def spectrumplot(self, x):
        #clear previous plot
        self.plotWidget.plotItem.clear()
        self.plotWidget.plot(x)


    def spectrumplot2(self, x, y):
        #clear previous plot
        self.plotWidget.plotItem.clear()
        self.plotWidget.plot(x, y, pen='r')

        #c1 = plt.plot(x, y, pen='b', symbol='x', symbolPen='b', symbolBrush=0.2, name='red')
        #c2 = plt.plot(x, y2, pen='r', symbol='o', symbolPen='r', symbolBrush=0.2, name='blue')

    def scan_loop(self, det, sptext):
        global file_no

        if det==[]:
            det=['I0']
        scan_param = sptext[0]
        
        x1 = float(sptext[1]) # start
        x2 = float(sptext[2]) # end
        step = abs(float(sptext[3]))*np.sign(x2-x1) # step is negative if x1 > x2
        dwell = float(sptext[4])
        n = int(abs((x2-x1)/abs(step))) #set the number of scanning steps
        x2_new = x1 +  step * (n+1)
        scan_x = [] # the 1st point of the list for the scanning parameter
        scan_data1 = [] # the 1st data point of measurement #1

        param[scan_param] = x1  # set the initial parameter value
        time.sleep(dwell)

        self.plotWidget.plotItem.setTitle(title="scanning "+ scan_param)
        self.plotWidget.plotItem.setXRange(float(x1), float(x2_new), padding=None, update=True)
        self.plotWidget.plotItem.setLabel('bottom', text=scan_param)
        self.plotWidget.plotItem.setLabel('left', text='Intensity', units='arb. units')

        self.plotWidget.plotItem.clear()
        print(x1, x2, step, dwell)
        print('for loop begins')
        #self.spectrumplot2(scan_x, scan_data1)
        self.curve = self.plotWidget.plot(scan_x, scan_data1, pen='g', linewidth=2)
       
        # create empty frame for scan
        scan_matrix = pd.DataFrame(columns = param_index)
        
        # scanning loop
        for i in range(n+1):
            scan_x.append(x1 + i*step)
            # set scanning parameters --> wait --> get data
            param[scan_param] = scan_x[i] # set scanning parameter
                      
            time.sleep(dwell)
            # scan_data = scan_x[i]**2 #get numeric data:  assuming  scan_x[i]**2,
            scan_data = 100*math.sin((scan_x[i]-(x1+x2)/2)/2) # math.cos(scan_x[i]/100) #get numeric data:  assuming  sin function
            param[det] = scan_data # detector
            print('i=',i, scan_x[i], scan_data)
            scan_data1.append(scan_data) #list
            status_widget_global.show_text()

            # show in status and command area
            self.curve.setData(scan_x, scan_data1)
            QtGui.QApplication.processEvents()
            cmd_global.append_txt('i = ' +str(i)+'   '+scan_param+' = '+ str(scan_x[i])+ ',  '+str(scan_data))
            
            # collect data
            new_param = pd.Series(param, name=i)
            scan_matrix = scan_matrix.append(new_param)

        print(scan_matrix)


        # data saving
        file_no += 1
        filename = str(dir_date)+"scan_"+str(file_no)
        # set file_path to folder
        scan_matrix.to_csv(file_path+filename, mode='w')
        # scan_matrix.to_hdf('', key='df', mode='w')
        

def main():
    app = QApplication(sys.argv)
    ex = RIXS()
    cmd_global.command_input.setFocus()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
