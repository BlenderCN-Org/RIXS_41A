#Last edited:20190321 5pm

import os, sys, time, random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QGridLayout, QFileDialog, QInputDialog, QAction,
                             QCheckBox, QGroupBox, QSpinBox, QProgressBar, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QSpacerItem, QSizePolicy, QAction, QPushButton, qApp, QPlainTextEdit, QFormLayout, QAction,
                             QScrollBar,QSplitter,QTableWidgetItem,QTableWidget,QComboBox,QVBoxLayout,QGridLayout,
                             QPushButton, QMainWindow,QMessageBox,QLabel,QTextEdit,QProgressBar)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize, Qt, QDate, QTime, QDateTime, QObject, QEvent, pyqtSignal, QTimer, pyqtSlot
import pyqtgraph as pg
from pyqtgraph import PlotWidget, GraphicsLayoutWidget
import numpy as np
import pandas as pd
import time, datetime, math

# =============================================================================
#
# Import written .py
from pyepics_device import Devices as ped
from pyepics_tmp_device import TmpDevices as petd
from pyepics_ccd_device import CcdDevices as pecd
import epics as e
#

# Global parameters
spectrum_widget_global = None
status_widget_global = None
cmd_global = None

param_index = ['t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb', 'I0']
param = pd.Series([0.00,2.00,50.00,710.00,720.00,11.00,22.00,33.00,0.00,0.00,0.00,10.00,30.00, 0.0], index=param_index)


# =============================================================================
# PyEPICS Devices
#
# #TODO: name hexapod as H811
#x = ped("hx", "41a:hexapod:x")
#y = ped("hy", "41a:hexapod:y")
#z = ped("hz", "41a:hexapod:z")
#u = ped("hu", "41a:hexapod:u")
#v = ped("hv", "41a:hexapod:v")
#w = ped("hw", "41a:hexapod:w")
#
#tsa = petd("tmp1", "41a:sample:tmp1")
#tsb = petd("tmp2", "41a:sample:tmp2")
#
#currentPV0 = "41a:sample:i0"
#currentPV1 = "41a:sample:phdi"
#
#AGM = e.Motor("41a:AGM:Energy")
#AGS = e.Motor("41a:AGS:Energy")
#
#real_row = pd.Series({'t':0,
#                      's1':0,
#                      's2':0,
#                      'agm': AGM.get_position(),
#                      'ags': AGS.get_position(),
#                      'x': x.getValue(),
#                      'y': y.getValue(),
#                      'z': z.getValue(),
#                      'u': u.getValue(),
#                      'v': v.getValue(),
#                      'w': w.getValue(),
#                      'ta':tsa.getValue(),
#                      'tb':tsb.getValue(),
#                      'I0': e.caget(currentPV0)})
#print(real_row)
#
# =============================================================================


# =============================================================================
#   Don't Set False
#
safe = True
if safe == False:
    param = real_row
#
#
# =============================================================================


scan_data = None
xas_data = None
rixs_data = None
scan_matrix = None
file_no = 0


# Create temp dir for datasaving 
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


class RIXS(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        # Window attributes
        self.setFixedSize(1300, 820)
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
# =============================================================================
# 
#         #TODO: To be continued
#         sddMenu = menubar.addMenu('SDD')
#         slitMenu = menubar.addMenu('Slits')
#         helpMenu = menubar.addMenu('Help')
# 
# =============================================================================
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

# =============================================================================
# 
#  Random image display
# def plot(self):
#     xlist = np.linspace(-50.0, 50.0, 1024)
#     ylist = np.linspace(-100.0, 100.0, 2048)
#     X, Y = np.meshgrid(xlist, ylist)
#     Z = np.sqrt(X ** 2 + Y ** 2)
# 
#     ax = self.figure.add_subplot(111)
#     ax.contourf(X, Y, Z)
#     ax.set_title('RIXS image')
#     self.draw()
# 
# =============================================================================

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
                       " Sample:  <br>"
                       " x = " + str(param['x']) + ", y = " + str(param['y']) + ", z = " + str(param['z']) + " <br>"
                       " u = " + str(param['u']) + ", v = " + str(param['v']) + ", w = " + str(param['w']) + " <br>"
                       "   Temperatures:  T<sub>a</sub> = " + str(param['ta']) + " K, T<sub>b</sub> = " + str(param['tb']) + " K<br>"
                       "           AGS: " + str(param['ags']) + " eV<br>")
        self.status_box.setText(parameter_text)
        
        #TODO : auto update parameter display in status widget
# =============================================================================
# 
#         timer = QTimer()
#         timer.timeout.connect(self.auto_update)
#         timer.start(1000)
#     def auto_update(self):
#         global status_widget_global
#         cur_time = datetime.strftime(datetime.now(), "%d.%m %H:%M:%S")
#         object.setText(cur_time)
#         status_widget_global.show_text()
#         
# =============================================================================

        #Terminal
class Command(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # message
        self.command_message = QTextEdit(self)
        
        '''
        Welcome message
        '''
        time = QTime.currentTime()
        welcome_message = ('<font color=blue>' + time.toString() + ' >> Welcome to TPS_BlueMagpie!</font>')
        self.command_message.setText(welcome_message)
        self.command_message.setFont(QtGui.QFont("Times New Roman", 12))
        self.command_message.setReadOnly(True)
        #optional: string format:print('Hello, {:s}. You have {:d} messages.'.format('Rex', 999))

        '''
        History
         - callable (command: his)
         - saved as log file.
        '''
        self.history_index = ['Time','Text']
        self.history_log = pd.DataFrame(columns=self.history_index)
        # modify counting mechanism => get index directly => check pandas document
        self.history_loc = 0
        self.logname = str(dir_date)+"_commandlog"
#        self.history_log.to_csv(file_path + self.logname, mode='w')

        '''
        Keyboard log
         - empty list
         - empty index
        '''
        self.kblog = []
        self.kbi = 0
        
        # user input
        self.command_input= QLineEdit(self)
        self.command_input.setFocusPolicy(Qt.StrongFocus)
        self.command_input.setPlaceholderText("Type help to list commands ...")
        self.command_input.returnPressed.connect(self.send)

        # widget design
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.command_message)
        self.layoutVertical.addWidget(self.command_input)
        
        
    def keyPressEvent(command_input, event):
        '''
        Up and Down
         - redefine function of QLineEdit(originally support return only) 
         - read kbi and kblog to type commands easily.
        '''
        global cmd_global
        size = len(cmd_global.kblog)
        if event.key() == Qt.Key_Up and 0 < cmd_global.kbi <= size:
            cmd_global.kbi += -1
            i = cmd_global.kbi
            Up_text = cmd_global.kblog[i]
            cmd_global.command_input.setText(Up_text)
        elif event.key() == Qt.Key_Down and 0 <= cmd_global.kbi < size-1:
            cmd_global.kbi += 1
            i = cmd_global.kbi
            Down_text = cmd_global.kblog[i]
            cmd_global.command_input.setText(Down_text)
        else:
            super(Command, command_input).keyPressEvent(event)

        # PyEPICS devices
          # written but removed from this branch

    def send(self):
        global param_index, param, cmd_global
        
        # user input_string
        text = self.command_input.text()
        
        # keyboard log
        if text != "":
            self.kblog.append(text)
            self.kbi = len(self.kblog)
        
        # commands
        if text == "help":
            self.validInput(text)
            msg = ("his: recall previously typed messages.<br>\n"
                   "mv: set a parameter to its absolute value.<br>\n"
                   "mvr: change a parameter in terms of a relative value.<br>\n"
                   "p: list valid parameters.<br>\n"
                   "scan: stepwise scan a parameter and plot selected paramters with some dwell time.<br>\n")
            self.sysMsg(msg)

        elif text == "his":
            self.validInput(text)
            # TODO: Flexible display?
            his_text = self.history_log.to_string(index_names=False, index=False, header=False, max_rows=10)
            # TODO: figure out why this can't work
#            self.sysMsg(his_text)
            self.command_message.append(his_text)

        elif text == 'p':
            self.validInput(text)
            p = ', '.join(param_index)
            self.sysMsg(p)

        # MV function
        elif text[:2] == 'mv' or text[:3] == 'mv ':
        # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2:
                if sptext[1] in param_index:
                    if self.checkFloat(sptext[2]) is True:
                        self.validInput(text,"v")
                        param[sptext[1]] = float(sptext[2])
                        self.sysMsg(sptext[1] + " has been moved to " + sptext[2])
                        status_widget_global.show_text()
                    else:
                        self.validInput(text,"iv")
                        self.sysMsg("value must be number or float", "err")
                else:
                    self.validInput(text,"iv")
                    self.sysMsg("parameter \'"+ sptext[1]+ "\' is invalid; type \'p\' to list valid parameters","err")
            else:
                self.validInput(text,"iv")
                self.sysMsg("correct format: mv parameter value", "err")

        # MVR function
        elif text[:4] == 'mvr ':
        # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2:
                if sptext[1] in param_index:
                    if self.checkFloat(sptext[2]) is True:
                        self.validInput(text,"v")
                        param[sptext[1]] = float(param[sptext[1]])+float(sptext[2])
                        output = str(param[sptext[1]])
                        msg = (sptext[1] + " has been moved to " + output)
                        status_widget_global.show_text()
                    else:
                        self.validInput(text,"iv")
                        self.sysMsg("value must be number or float", "err")
                else:
                    self.validInput(text,"iv")
                    self.sysMsg("parameter \'"+ sptext[1]+ "\' is invalid; type \'p\' to list valid parameters", "err")
            else:
                self.validInput(text,"iv")
                self.sysMsg("correct format: mv parameter value", "err")

        # SCAN function
        # command format: scan (det1 det2 ...;) scan_param start end step dwell

        elif text == 'scan' or text[:5] == 'scan ':
            # if the input command is only 'scan' but not parameters check != 'OK',
            check = self.check_param_scan(text)   # checking input command and parameters
            if check == 'OK':
                self.validInput(text,"v")
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
                self.sysMsg('Scanning begins at ' + t0.strftime("%c"))
                t1 = time.time()

                #print('scan loop begins')
                spectrum_widget_global.scan_loop(det, sptext)
                dt = round(time.time()- t1, 3)
                print('timespan in senconds=', dt)
                self.sysMsg('Scanning is completed; timespan  = ' + self.convertSeconds(dt))
            else:
                # Return error message
                self.validInput(text, "iv")
                self.sysMsg(check, "err")
        else:
           self.validInput(text, "iv")
           self.sysMsg("Type 'help' to list commands", "err")

        
        # refresh and scroll down to latest message
        self.command_input.setText("")
        self.command_message.moveCursor(QtGui.QTextCursor.End)
        cmd_global.command_input.setFocus()

    # log and show
    def validInput(self, x, v=""):
        '''
        decorate & log input_string;
        when valid => log text in history & mark blue
             invalid => mark gray
        '''
        # time stamp
        timestamp = QTime.currentTime()
        t= timestamp.toString()
        
        if v == "iv":   
            # invalid command
            self.command_message.append('<font color=gray>' + t + ' >> ' + x + '</font>')
        else:
            if v == "v":
                # TODO: find efficient way in pandas
                # current_size
                i = (self.history_log.size)/2
                self.history_loc = int(i+1)
                # append valid command to history
                row = pd.Series([t,x], index = self.history_index, name = self.history_loc)
                self.history_log = self.history_log.append(row)
                print(self.history_log)
                name = file_path + self.logname +".csv"
                row.to_csv(name, mode='a', header=False)
            self.command_message.append('<font color=blue>' + t + ' >> ' + x + '</font>')
            
            
    def sysMsg(self, m, v=""):
        '''
        decorate msg in command; assume normal message.
        when err => mark msg red
        '''
        if v == "err":
            # for error messages
            self.command_message.append('<font color=red>Input error; ' + m + '</font>')
        else:
            self.command_message.append('<font color=black>\n'+m+'\n</font>\n')

    def convertSeconds(self,seconds):
        h = int(seconds//(60*60))
        m = int((seconds-h*60*60)//60)
        s = round(seconds-(h*60*60)-(m*60), 3)
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
#################
        text = sptext[0]
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
                            check_format = ('OK')
                        else:
                            check_msg = ("dwell time must be positive.")
                           
                    else:
                        check_msg = ("parameter \'"+ sptext[0]+ "\' is invalid; type \'p\' to list valid parameters")
                     
                else:
                    check_msg = ("parameter values are invalid; \'start end step dwell\' shoiuld be numeric.")
                     
            else:
                check_msg = ("format: scan [det1 det2 .. :] parameter start end step well_time")
                
        else:
            check_msg = ("format: scan [det1 det2 ... :] parameter start end step well_time")
            
        # checking if dection parameters have been correctly selected
        j=0 #check index
        for i in range(len(det)): # i from 0 to len(det)-1
            if det[i] in param_index: j +=1.0
        # 
        if j== len(det):
            check_det='OK'
        else: 
            check_det='not OK'

        if check_format == 'OK' and check_det == 'OK': 
            check_msg = ('OK')
        elif check_format == 'OK' and check_det != 'OK': 
            check_msg = ('invalid detection parameters')

        return check_msg




class ImageWidget(QWidget):

    def __init__(self, parent=None):

        #ccd related
        emccd = pecd("emccd", "41a:ccd1")
#        emccd.getExposureTime()
#        print(emccd.getExposureTime())

#        emccd.getRIXS()

        super(ImageWidget, self).__init__(parent=parent)
        self.plotWidget = GraphicsLayoutWidget(self)
        self.vb = self.plotWidget.addViewBox()
#        np.random.randn(2097152, 1)
        frame = np.random.normal(size=(1, 10))
#        print(frame)
        transarray = np.empty((10, 5), float)
#        print(transarray)
        a = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
#        print(a)
        npa = np.asarray(a)
#        print(npa)
        renpa = np.reshape(npa, (2, 5), order='F')
#        print(renpa)
#        frame = emccd.getImage()
        img = pg.ImageItem(renpa)
        self.vb.addItem(img)
        self.vb.autoRange()
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)


#     def spectrumplot(self, x):
# #        self.plotWidget.plotItem.clear()
#         self.plotWidget



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
            cmd_global.sysMsg('i = ' +str(i)+'   '+scan_param+' = '+ str(scan_x[i])+ ',  '+str(scan_data))
            
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
