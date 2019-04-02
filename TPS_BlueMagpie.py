#Last edited:20190402 5pm by Jason
import os, sys, time, random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QGridLayout, QAction,
                             QGroupBox, QSpinBox, QProgressBar, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QSpacerItem, QSizePolicy, QAction, QPushButton, qApp, QPlainTextEdit, QFormLayout, QAction,
                             QScrollBar,QTableWidgetItem,QTableWidget,QComboBox,QVBoxLayout,QGridLayout,
                             QPushButton, QMainWindow,QMessageBox,QLabel,QTextEdit,QProgressBar)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize, Qt, QDate, QTime, QDateTime, QObject, QEvent, pyqtSignal, QTimer, pyqtSlot
import pyqtgraph as pg
from pyqtgraph import PlotWidget, GraphicsLayoutWidget
import numpy as np
import pandas as pd
import time, datetime, math, re
import threading
from threading import Thread

# Global parameters
spectrum_widget_global = None
status_global = None
cmd_global = None
scan_data = None
xas_data = None
rixs_data = None
data_matrix = None
param_index = ['f','t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb', 'I0']

'''
Abort
 - execution flag for commands.
   default : False
   if abort = True, breaks loop.
 - reset in Command(send function)
'''
ABORT = False

# PyEPICS Devices

# Don't Set True
SAFE = False

if SAFE == True:
# Import written .py
    from pyepics_device import Devices as ped
    from pyepics_tmp_device import TmpDevices as petd
    from pyepics_ccd_device import CcdDevices as pecd
    import epics as e
 #TODO: name hexapod as H811
    x = ped("hx", "41a:hexapod:x")
    y = ped("hy", "41a:hexapod:y")
    z = ped("hz", "41a:hexapod:z")
    u = ped("hu", "41a:hexapod:u")
    v = ped("hv", "41a:hexapod:v")
    w = ped("hw", "41a:hexapod:w")
    tsa = petd("tmp1", "41a:sample:tmp1")
    tsb = petd("tmp2", "41a:sample:tmp2")
    currentPV0 = "41a:sample:i0"
    currentPV1 = "41a:sample:phdi"
    AGM = e.Motor("41a:AGM:Energy")
    AGS = e.Motor("41a:AGS:Energy")

def getRow():
    global SAFE

    if SAFE == True:
        real_row = pd.Series({'f': 0, 't':0,
                              's1':0,
                              's2':0,
                              'agm': AGM.get_position(),
                              'ags': AGS.get_position(),
                              'x': x.getValue(),
                              'y': y.getValue(),
                              'z': z.getValue(),
                              'u': u.getValue(),
                              'v': v.getValue(),
                              'w': w.getValue(),
                              'ta':tsa.getValue(),
                              'tb':tsb.getValue(),
                              'I0': e.caget(currentPV0)})
        print(real_row)
        return real_row
    else:
        param = pd.Series([int(0), 0.00,2.00,50.00,710.00,720.00,5.00,5.00,5.00,2.00,2.00,2.00,20.00,30.00, 0.0], index=param_index)
        print (param)
        return param

param = getRow()


# golable series for the parameter ranges set to protect instruments.
param_range = pd.Series({'t':[0,1000], 's1':[1,30], 's2':[5,200], 'agm': [480, 1200],
                        'ags': [480, 1200], 'x': [0,10], 'y': [0,10],'z': [0,10], 'u': [0,10],
                      'v': [0,10], 'w': [0,10], 'ta':[5,350], 'tb':[5,350], 'I0': [0,1]})

'''
Dir for datasaving and macro
 - create a project folder named after date
 - sub folders including log, macro, and data
 - TODO: build class?

'''
file_no = 0

# Name of projectDir
dir_date = datetime.datetime.today().strftime("%Y_%b%d")
print(dir_date)
dir_name = "project #0"    

# very stupid way for test, probably os package has solution
current_path=os.getcwd()

if '\\' in current_path:
    # for windows
    sla = '\\'
else:
    # for linux
    sla = '/'
    
project_path = str(current_path)+ sla + dir_name + sla
macro_dir = str(project_path)+ 'macro' + sla
log_dir = str(project_path)+ 'log' + sla
data_dir = str(project_path)+ 'data' + sla
    

if not os.path.exists(dir_name):
    os.makedirs(dir_name)
    os.makedirs(macro_dir)
    os.makedirs(log_dir)
    os.makedirs(data_dir)


    
        





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
        global status_global, spectrum_widget_global
        rightcolumn = QVBoxLayout()

        status_widget=StatusWidget(self)
        status_global = status_widget
        rightcolumn.addWidget(status_widget)

        spectrum_widget = SpectrumWidget(self)
        spectrum_widget_global = spectrum_widget
        rightcolumn.addWidget(spectrum_widget)

        hbox.addLayout(leftcolumn, 1)
        hbox.addLayout(rightcolumn, 1)
        
        self.show()



class StatusWidget(QWidget):
    global param, parameter_text
    def __init__(self, parent=None):
        super(StatusWidget, self).__init__(parent=parent)
        self.status_bar = QLabel(self)
        self.show_bar()
        self.status_box = QTextEdit(self)
        self.show_text()
        self.status_box.setStyleSheet("color: black; background-color: Floralwhite")
        self.status_box.setFont(QtGui.QFont("UbuntuMono",14))
        self.status_box.setReadOnly(True)

        # Widget layout
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.status_bar)
        self.layoutVertical.addWidget(self.status_box)
        
        '''
        Update
         - repeat show_text function every 1 sec.
        '''
        self._status_update_timer = QTimer(self)
        self._status_update_timer.setSingleShot(False)
        self._status_update_timer.timeout.connect(self.show_text)
        self._status_update_timer.timeout.connect(self.show_bar)
        self._status_update_timer.start(500)

    def show_bar(self):
        time = QDateTime.currentDateTime()
        time_str = time.toString("yyyy-MM-dd hh:mm:ss")
        self.status_bar.setText(time_str+"  Experiment No.  1234;   PI: A. B. C. ")
    
# =============================================================================
#         self.UpdateSignal.connect(self.show_text)
#         self.checklist = param
#     
#         # check two list matches
#         match=[i for i, j in zip(self.checklist, param) if i == j]
#         if len(match) < len(param):
#             print ("parameters has been changed.")
#             # refresh checklist
#             self.checklist = param
#             self.updateSignal.emit()
# 
# =============================================================================


        # Forced refresh
    def show_text(self):
        # index: param_index = ['t', 's1', 's2', 'agm', 'ags','x', 'y', 'z', 'u', 'v', 'w', 'ta', 'tb']
        if SAFE:
            param = getRow()
        parameter_text = ( "<font color=black><b> file number: " + self.p('f','int') + "<b><br>"
                            " <br>"
                          "<u>Parameters</u></font><br>"
                           " AGM: " + self.p('agm') + " eV<br>"
                           " AGS: " + self.p('ags') + " eV<br>"
                           " <br>"
                           " Entrance slit: " + self.p('s1') + " &micro;m<br>"
                           " Exit slit: " + self.p('s2') + " &micro;m<br>"
                           " <br>"
                           " Sample:  <br>"
                           " x = " + self.p('x') + ", y = " + self.p('y') + ", z = " + self.p('z') + " <br>"
                           " u = " + self.p('u') + ", v = " + self.p('v') + ", w = " + self.p('w') + " <br>"
                           "   Temperatures:  T<sub>a</sub> = " + self.p('ta') + " K, T<sub>b</sub> = " + self.p('tb') + " K<br>"
                          # "Current"++""
                        )
        self.status_box.setText(parameter_text)

    # define format of displayed numbers
    # - default: round, 2
    def p(self, x, a='Round'):
        #get value by param_list index
        value =  param[x]
        if a =='Round':
            value = round(value,2)
        elif a =='int':
            value = int(value)
        return str(value)



        #Terminal
class Command(QWidget):
    popup = pyqtSignal()
    inputext = pyqtSignal(str)
    mcrostat = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        # message
        self.command_message = QTextEdit(self)

        '''
        Welcome message
        '''
        time = QTime.currentTime()
        welcome_message = ('<font color=blue>' + time.toString() + ' >> Welcome to TPS Blue Magpie!</font>')
        self.command_message.setText(welcome_message)
        self.command_message.setFont(QtGui.QFont("UbuntuMono", 10))
        self.command_message.setReadOnly(True)
        #optional: string format:print('Hello, {:s}. You have {:d} messages.'.format('Rex', 999))
        
        # user input
        self.command_input= QLineEdit(self)
        self.command_input.setFocusPolicy(Qt.StrongFocus)
        self.command_input.setPlaceholderText("Type help to list commands ...")
        ####
        self.command_input.returnPressed.connect(self.send_message)
        self.inputext.connect(self.send)
        
        # macro related
        self.macro = None
        self.popup.connect(self.popupMacro)
#        self.mcrostat[str].connect(self.command_input.setText)
    

        '''
        History
         - callable (command: h)
         - saved as log file.
        '''
        self.history_index = ['Time','Text']
        self.history_log = pd.DataFrame(columns=self.history_index)
        # modify counting mechanism => get index directly => check pandas document
        self.history_loc = 0
        self.logname = str(dir_date)+"_commandlog"
        
        '''
        Keyboard log (for KeyPressEvent function)
         - empty list
         - empty index
        '''
        self.kblog = []
        self.kbi = 0

        '''
        Abort Button
        default: closed
         - Button enabled while sysReturn function checked input as valid,
         - Disabled again with final sysReturn.
        '''
        # send/abort button
        self.abort_button = QPushButton('Abort', self)
        self.abort_button.clicked.connect(self.abortCommand)
        self.abort_button.setEnabled(False)
        
        # CommandWidget design
        self.Commandlayout = QVBoxLayout(self)
        self.Commandlayout.addWidget(self.command_message)
        self.Input= QHBoxLayout(self)
        self.Input.addWidget(self.command_input)
        self.Input.addWidget(self.abort_button)
        self.Commandlayout.addLayout(self.Input)
              
    def send_message(self):
        txt = self.command_input.text()
        self.inputext[str].emit(txt)
        
    '''
    set global abort flag when button clicked
    '''
    def abortCommand(self):
        global ABORT
        ABORT = True

        '''
        Macro Window
         - under construction
         - pop up TextEdit
        '''
        
    def popupMacro(self):
        print ("Opening a new popup window...")
        self.macro = MacroWindow()
        self.macro.setWindowTitle("Macro Editor")
        self.macro.resize(300,500)
        self.macro.setWindowFlags(self.macro.windowFlags() & QtCore.Qt.CustomizeWindowHint)
        self.macro.setWindowFlags(self.macro.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
        self.macro.macroMsg.connect(self.sysReturn)
        self.macro.show()
        

        '''
        Up and Down
         - redefine function of QLineEdit(originally support return only)
         - read kbi and kblog for command convenience.
         
        '''
    def keyPressEvent(command_input, event):
        global cmd_global
        size = len(cmd_global.kblog)
        if event.key() == Qt.Key_Up and 0 < cmd_global.kbi <= size:
            cmd_global.kbi += -1
            i = cmd_global.kbi
            Up_text = cmd_global.kblog[i]
            cmd_global.command_input.setText(Up_text)
        elif event.key() == Qt.Key_Down and 0 <= cmd_global.kbi < size:
            if cmd_global.kbi  < size-1:
                cmd_global.kbi += 1
                i = cmd_global.kbi
                Down_text = cmd_global.kblog[i]
                cmd_global.command_input.setText(Down_text)
            else:
                cmd_global.command_input.setText("")
        else:
            super(Command, command_input).keyPressEvent(event)

        '''
        Log and show
         - Decorate msg in command; assume normal message.
         - To mark color or log input_string;
        v=
                    "v":    valid => mark blue
              "v", True:      log => mark blue and log text in history
                   "iv":  invalid => mark gray
                  "err":    error => mark msg red
        '''
        
    def sysReturn(self, x, v="", log=False):
        # time stamp
        timestamp = QTime.currentTime()
        t= timestamp.toString()

        if v == "iv":
            # invalid command
            self.command_message.append('<font color=gray>' + t + ' >> ' + x + '</font><font color=black> </font>')

        elif v == "v":
            if log == True:
                self.abort_button.setEnabled(True)
                #=================== history log======================= 
                # current_size
                i = (self.history_log.size)/2
                self.history_loc = int(i+1)
                # append valid command to history
                row = pd.Series([t,x], index = self.history_index, name = self.history_loc)
                self.history_log = self.history_log.append(row)
                print(self.history_log)
                # TODO: format
                name = log_dir + self.logname +".csv"
                row.to_csv(name, mode='a', header=False, index=False)
                #=================== history log========================

            self.command_message.append('<font color=blue>' + t + ' >> ' + x + '</font><font color=black> </font>')


        elif v == "err":
            # for error messages
            #self.command_message.append('<font color=red>Input error; ' + x + '</font><font color=black> </font>')
            self.command_message.append('<font color=red> '+ x + '</font><font color=black> </font>')
        else:
            self.command_message.append(x)


    def send(self, txt):
        global param_index, param, cmd_global, ABORT, file_no
        ABORT = False

        # user input_string 
        text = txt
#        text = self.command_input.text()
        print('command input:  ',len(text), '   ',text )
        while text[len(text)-1] ==' ':
            text = text[:len(text)-1]
        text = re.sub(' +', ' ', text) # an elegant way to remove extra whitespace,  "import re" is needed/

        # keyboard log
        if text != "":
            self.kblog.append(text)
            self.kbi = len(self.kblog)
        # commands
        if text == "help":
            self.sysReturn(text, "v")
            msg = ("<b>h</b>: recall previous commands executed sucessfully.<br>\n"
                   "<b>mv</b>: set a parameter to its absolute value.<br>\n"
                   "<b>mvr</b>: change a parameter in terms of a relative value.<br>\n"
                   "<b>p</b>: list valid parameters.<br>\n"
                   "<b>r</b>: show all parameter ranges.<br>\n"
                   "<b>u</b>: update all parameter values.<br>\n"
                   "<b>scan</b>: stepwise scan a parameter and plot selected paramters with some dwell time.<br>\n"
                   "<b>macro</b>: to open a macro editor.<br>\n"
                   "<b>do</b>: execute macro by calling text file name.<br>\n")
            self.sysReturn(msg)
        elif text == "h":
            self.sysReturn(text, "v")
            i = self.history_log.size
            if i>0:
                # TODO: Flexible display?
                his_text = self.history_log.to_string(index_names=False, index=False, header=False, max_rows=10)
            else:
                his_text = "Blue Magpie has not executed any command yet."
            self.sysReturn(his_text)

        elif text == 'p':
            self.sysReturn(text,"v")
            #adjust return msg format of parameter index
            p = ', '.join(param_index) # what does this line do?
            self.sysReturn(p)

        elif text == 'r':
            self.sysReturn(text,"v")
            msg='parameter ranges:\n'
            for i in range(param_range.size):
                msg += str(param_range.index[i]) + ' = '+ str(param_range[i])+'\n'
            self.sysReturn(msg)

        elif text == 'u':
            status_global.show_text()
            self.sysReturn(text,"v")
            self.sysReturn("Parameter values have been updated.")

        # mv function
        elif text == 'mv' or text[:3] == 'mv ':
        # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2: # e.g. mv x 1234
                if sptext[1] in param_index:
                    check_param =self.check_param_range(sptext[1], sptext[2])
                    #print(check_param)
                    if check_param == 'OK':
                        self.sysReturn(text,"v", True)
                        param[sptext[1]] = float(sptext[2]) # sptext[1] is the parameter to be moved; sptext[2] is value to moved.
                        self.sysReturn(sptext[1] + " has been moved to " + sptext[2])
                    else:
                        self.sysReturn(text,"iv")
                        self.sysReturn(check_param, "err")
                else:
                    self.sysReturn(text,"iv")
                    self.sysReturn("parameter \'"+ sptext[1]+ "\' is invalid; type \'p\' to list valid parameters","err")
            else:
                self.sysReturn(text,"iv")
                self.sysReturn("correct format: mv parameter value", "err")

        # mvr function
        elif text[:4] == 'mvr ':
        # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2:
                if sptext[1] in param_index:
                    value= float(param[sptext[1]])+float(sptext[2])
                    check_param =self.check_param_range(sptext[1], value)
                    if check_param == 'OK':
                        self.sysReturn(text,"v", True)
                        param[sptext[1]] = float(param[sptext[1]])+float(sptext[2])
                        output = str(param[sptext[1]])
                        self.sysReturn(sptext[1] + " has been moved to " + output)
                    else:
                        self.sysReturn(text,"iv")
                        self.sysReturn(check_param, "err")
                else:
                    self.sysReturn(text,"iv")
                    self.sysReturn("parameter \'"+ sptext[1]+ "\' is invalid; type \'p\' to list valid parameters", "err")
            else:
                self.sysReturn(text,"iv")
                self.sysReturn("correct format: mv parameter value", "err")

        # scan function
        # command format: scan [plot1 plot2 ...:] scan_param begin end step dwell
        elif text == 'scan' or text[:5] == 'scan ':
            # if the input command is only 'scan' but not parameters check != 'OK',
            check = self.check_param_scan(text)   # checking input command and parameters
            if check == 'OK':
                self.sysReturn(text,"v", True)     # "v": log text in history; True: mark blue
                if text.find(',') == -1: #scan x 1 10 1 0.1
                    c = 3
                    plot=['I0'] #default detection parameter
                else: #scan y z: x 1 10 1 0.1
                    c = text.find(',')
                    plot=text[5:c].split(' ') # list of detection parameters

                print('index c of \',\' in the input command,  c=',c, ' (c=3 if there is no \',\')')
                print('input plot=', plot)
                sptext = text[c+2:].split(' ') # list of scan parameters
                print('sptext=', sptext)

                scan_param = sptext[0]
                x1 = float(sptext[1]) # begin
                x2 = float(sptext[2]) # end
                step = abs(float(sptext[3]))*np.sign(x2-x1) # step is negative if x1 > x2
                dwell = float(sptext[4])
                n = int(abs((x2-x1)/step)) #set the number of scanning steps
                check_param1 =self.check_param_range(sptext[0], x1)
                check_param2 =self.check_param_range(sptext[0], x2)
                if (check_param1 =='OK') and (check_param2 =='OK'):
# ==================Save file==================================================
                    file_no +=1
                    param['f'] =file_no
                    print('file no =', file_no)
                    print('param[\'f\']', param['f'])
# =============================================================================
                    cmd_global.command_input.setEnabled(False)
                    param[scan_param] = x1
                    QtGui.QApplication.processEvents()
                    time.sleep(0.5)
                    t0=datetime.datetime.now()
                    #self.command_message.append(t0.strftime("%c"))
                    self.sysReturn('Scan '+ str(int(param['f'])) +' begins at ' + t0.strftime("%c"))
                    spectrum_widget_global.scan_loop(plot, sptext)
                    cmd_global.command_input.setEnabled(True)
                else:
                    self.sysReturn(text, "iv")
                    if (check_param1 !='OK'): check_param = check_param1
                    if (check_param2 !='OK'): check_param = check_param2
                    self.sysReturn(check_param, "err")

            else:
                # Return error message
                self.sysReturn(text, "iv")
                self.sysReturn(check, "err")

        elif text[:5] == "macro":
            # popup window
            self.sysReturn(text,"v")
            self.popup.emit()
                
        elif text[:3] == "do ":
            space = text.count(' ')
            sptext = text.split(' ')
            # read macro file
            if space == 1:
                name = sptext[1]
                self.sysReturn(text,"v", True)
                self.doMacro(name)
            else:
                self.sysReturn("correct format: do macroname","err")
        
        elif text[:5] == "wait ":
            space = text.count(' ')
            sptext = text.split(' ')
            # set delay time
            if space == 1:
                t = sptext[1]
                if self.checkFloat(t):
                    self.lockInput(True)
                    self.sysReturn(text, "v")
                    self.sysReturn("wait for "+t+"seconds.")
                    _timer = QTimer(self)
                    _timer.timeout.connect(self.lockInput)
                    _timer.start(1000*float(t))
#                    self.command_input.setEnabled(True)
                else:
                    self.sysReturn("correct format: wait time", "err")
            
        elif text != "":
           self.sysReturn(text, "iv")
           self.sysReturn("Type 'help' to list commands", "err")

        # refresh and scroll down to latest message

        self.command_input.setText("")
        self.command_message.moveCursor(QtGui.QTextCursor.End)
        self.abort_button.setEnabled(False)
        cmd_global.command_input.setFocus()
        
    def lockInput(self, lock=False):
        if lock:
            self.command_input.setDisabled(True)
        else:
            self.command_input.setEnabled(True)
        
        
        
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

    def check_param_range(self, param_name, param_value):
        global param, param_index, param_range

        if self.checkFloat(param_value) is True:
        #if (parame_name in param_index) and self.checkFloat(param_value) == True:
            j= float(param_value)
            if min(param_range[param_name]) <= j  and j <= max(param_range[param_name]):
                check_msg = 'OK'
            else:
                check_msg = ('Oops! '+ param_name+ ' value was out of range; type \'r\' to show parameter ranges.')
        else:
            check_msg = (param_name + " value must be number or float", "err")
#        print('checking on the range of ', param_name, ':')
#        print(check_msg)
        return check_msg


    def check_param_scan(self, text):
        global param, scan_data, param_index
        # input text format: scan scan_param begin end step dwell
        # or  scan plot1 plot2 ....: scan_param begin end step dwell
        check_format = (' ')
        print('input command =', text)
        if text.find(',') == -1:
            sptext = text[5:].split(' ') # scan_param 1 10 1 0.1
            space = text.count(' ') #space =5, e.g. scan x 1 10 2 0.1
            c=5
            plot=['I0']

        else:
            c = text.find(',')
            #print('\':\' found in the input command, index c=',c)
            space = text[c:].count(' ') # space = 5, after truncating "scan y z ...:" => e.g. : x 1 10 2 0.1
            sptext = text[c+2:].split(' ') # scan_param 1 10 1 0.1
            plot=text[5:c].split(' ') # list of detection parameter

        #print('plot=', plot)
        # if the input command is correct, sptext should be a list of scan_param
        # and 4 numbers, e.g. sptext = ['x', '1', '10', '2', '0.1']
        #print('input text=', text)
        #print('sptext=', sptext)
        #print('legn', len(sptext))

        if text[c+1:].find(',') == -1 and space == 5:
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
                    check_msg = ("parameter values are invalid; \'begin end step dwell\' shoiuld be numeric.")
            else:
                check_msg = ("format: scan [plot1 plot2 .. ,] parameter begin end step dwell_time")
        else:
            check_msg = ("format: scan [plot1 plot2 ... ,] parameter begin end step dwell_time")


        # checking if dection parameters have been correctly selected
        j=0 #check index
        for i in range(len(plot)): # i from 0 to len(plot)-1
            if plot[i] in param_index: j +=1.0
        #
        if j== len(plot):
            check_plot='OK'
        else:
            check_plot='not OK'

        if check_format == 'OK' and check_plot == 'OK':
            check_msg = ('OK')
        elif check_format == 'OK' and check_plot != 'OK':
            check_msg = ('invalid plotting parameters')

        print('scan paramter check:', check_msg)
        return check_msg
    
    def doMacro(self, name):
        #start from 0
        self.macro_index = 0
        self.macro_n = 0
        readfile=[]
        macro_name = macro_dir + str(name) + ".txt"
        #check file exist
        if os.path.exists(macro_name):
            cmd_global.command_input.setEnabled(False)
            #==============Macro start===============
            f = open(macro_name,"r")  
            for x in f:
                x = x.replace('\n','')
                readfile.append(x)
            self.macro_n = len(readfile)
            self.sysReturn("macro begins: "+macro_name)
            #=============Macro cycle================
            self.runLine(self.macro_index, self.macro_n, macro_name)
            #==============Macro End=================
            self.sysReturn("macro completed.")
            cmd_global.command_input.setEnabled(True)
        else:
            self.sysReturn("macro file name: "+macro_name+" not found.","err")
            
    def runLine(self,i,n,name):
        if i<n:
            #==============Read again===============
            readfile=[]
            f = open(name,"r")
            for x in f:
                x = x.replace('\n','')
                readfile.append(x)
            self.macro_n = len(readfile)
            #======Execute command line by line=====
            run = readfile[i] 
            msg = ("<b>running line</b> ["+str(i)+"] : "+str(run))
            self.sysReturn(msg)
            self.send(run)
            self.macro_index+=1
            self.runLine(self.macro_index, self.macro_n, name)
        
        
class ImageWidget(QWidget):
    def __init__(self, parent=None):
        global SAFE
        super(ImageWidget, self).__init__(parent=parent)

        if SAFE:
            #ccd related
            emccd = pecd("emccd", "41a:ccd1")
            emccd.getExposureTime()
            exposure_time = 3
            print(emccd.getExposureTime())
            print(emccd.getCooler())
            print(emccd.getGain())
            print(emccd.getTemperature())
            print(emccd.getStatus())

#         emccd.setExposureTime(exposure_time)
#         emccd.setGain(10)
#         emccd.start(1)
# #        emccd.setCooler(0)
# #        emccd.setTemperature(-80)
# #        emccd.setCooler(1)

#        time.sleep(1)
            print(emccd.getExposureTime())
            print(emccd.getGain())
            print(emccd.getStatus())

#        time.sleep(exposure_time + 5)
            print(emccd.getStatus())
            a = emccd.getImage()

#            print(a)
            npa = np.asarray(a)
#            print(npa)
            renpa = np.reshape(npa, (1024, 2048), order='F')
#            print(renpa)

        else:
            a = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            npa = np.asarray(a)
#            print(npa)
            renpa = np.reshape(npa, (2, 5), order='F')
#            print(renpa)

        self.plotWidget = GraphicsLayoutWidget(self)
        self.vb = self.plotWidget.addViewBox()

        img = pg.ImageItem(renpa)
        self.vb.addItem(img)
        self.vb.autoRange()
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)

    def rixs_sum(self, image_data):
        rixs_tmp = np.zeros((1, 2048), float)

        for i in range(renpa.shape[0]):
            rixs_tmp = rixs_tmp + renpa[i, :]

        print(rixs_tmp.ndim, rixs_tmp.shape, rixs_tmp.dtype)
        print(rixs_tmp)

class SpectrumWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
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


    def scan_loop(self, plot, sptext):
        global file_no, param_index, param
        t1 = time.time()
        print('scan loop begins')
        print('scan no = ', file_no)
        if plot==[]:
            plot=['I0']

        scan_param = sptext[0]
        x1 = float(sptext[1]) # start
        x2 = float(sptext[2]) # end
        step = abs(float(sptext[3]))*np.sign(x2-x1) # step is negative if x1 > x2
        dwell = float(sptext[4])
        n = int(abs((x2-x1)/abs(step))) #set the number of scanning steps
        x2_new = x1 +  step * (n+1)
        scan_x = [] # the 1st point of the list for the scanning parameter
        scan_data1 = [] # the 1st data point of measurement #1#
        param[scan_param] = x1  # set the initial parameter value
        time.sleep(dwell)

        plot_no = min(len(plot),5.0) # maximum number of curves to be plotted is 5.
        plot = plot[:plot_no]
        title_plot = 'Scan '+ str(int(param['f']))+': scanning '+ scan_param +',  plotting'
        for i in range(plot_no):
            if i== 0: title_plot += ' ' + plot[i]
            else: title_plot += ', ' +plot[i]
        self.plotWidget.plotItem.setTitle(title= title_plot)
        self.plotWidget.plotItem.setXRange(float(x1), float(x2_new), padding=None, update=True)
        self.plotWidget.plotItem.setLabel('bottom', text=scan_param)
        self.plotWidget.plotItem.setLabel('left', text='Intensity', units='arb. units')
        self.plotWidget.addLegend((50,30), offset=(450,150))
        self.plotWidget.plotItem.clear()
        print(x1, x2, step, dwell)
        #self.spectrumplot2(scan_x, scan_data1)
        #self.curve0 = self.plotWidget.plot(scan_x, scan_data1, pen='g', linewidth=2)

        # create an empty dataframe for scaning; param_index = ['t', 's1', 's2', 'agm', 'ags',.....]
        data_matrix = pd.DataFrame(columns = param_index)
        #print('initial data_matrix=', data_matrix)

        # create an empty series for plotting during a scan
        data_plotting = pd.DataFrame(columns =plot)
        #print('initial scan_plotting=', scan_plotting)
        scan_data_ith = pd.Series(index = plot) #for i-th scan

        self.curve=[]
        color=['g', 'b', 'w','r', 'y']


        self.curve = self.curve[:plot_no]
        color = color[:plot_no]

        print('plot', plot)
        print('color', color)

        # TODO: reconstruct this part
        if plot_no >= 1: self.curve0 = self.plotWidget.plot(scan_x, scan_data1, pen='g', linewidth=2, name=plot[0])
        if plot_no >= 2: self.curve1 = self.plotWidget.plot(scan_x, scan_data1, pen='r', linewidth=2, name=plot[1])
        if plot_no >= 3: self.curve2 = self.plotWidget.plot(scan_x, scan_data1, pen='w', linewidth=2, name=plot[2])
        if plot_no >= 4: self.curve3 = self.plotWidget.plot(scan_x, scan_data1, pen='y', linewidth=2, name=plot[3])
        if plot_no >= 5: self.curve4 = self.plotWidget.plot(scan_x, scan_data1, pen='b', linewidth=2, name=plot[4])


        # scanning loop
        print('for loop begins')
        for i in range(n+1):
            if ABORT:
                print("loop stopped")
                break
            #print(i,'_th scanning point')
            scan_x.append(x1 + i*step)
            data_i =[]
            # set scanning parameters --> wait --> get data
            param[scan_param] = scan_x[i] # set scanning parameter
            time.sleep(dwell)

            #get data
            scan_plotting = pd.Series(index=plot)
            counts=[]
            for j in range(plot_no):
                param[plot[j]]=0.8**(j)*100*math.sin((10*j+1)*(scan_x[i]-(x1+x2)/2)/2) # math.cos(scan_x[i]/100) #get numeric data:  assuming  Sin function
                if j==1: param[plot[j]]=i
                data_i.append(param[plot[j]])
                #print('i= ', i, '  j=', j, '   ', scan_param, '=', scan_x[i], '     ', plot[j], '=', param[plot[j]])

            #after finishing the update of all param values
            data_matrix.loc[len(data_matrix), :] =  param.tolist() #appending param to data_matrix

            # TODO: reconstruct this part
            if plot_no >= 1: self.curve0.setData(scan_x, data_matrix.loc[:,plot[0]])
            if plot_no >= 2: self.curve1.setData(scan_x, data_matrix.loc[:,plot[1]])
            if plot_no >= 3: self.curve2.setData(scan_x, data_matrix.loc[:,plot[2]])
            if plot_no >= 4: self.curve3.setData(scan_x, data_matrix.loc[:,plot[3]])
            if plot_no >= 5: self.curve4.setData(scan_x, data_matrix.loc[:,plot[4]])

            #print('data_matrix.iloc[i,:]')
            #print(data_matrix.iloc[i,:])
            QtGui.QApplication.processEvents()
            msg=''
            j=0
            for j in range(plot_no):
                msg += str(round(param[plot[j]],3))+'     '

            if i%5 == 0:  cmd_global.sysReturn('')
            cmd_global.sysReturn('i = ' +str(i)+'   '+scan_param+' = '+ str(scan_x[i])+ "     plot =  "+msg)

        print('data_matrix')
        print(data_matrix)

        dt = round(time.time()- t1, 3)
        print('timespan in senconds=', dt)
        if ABORT:
            cmd_global.sysReturn('Scaning loop has been terminated; timespan  = ' + cmd_global.convertSeconds(dt),'err')
        else:
            cmd_global.sysReturn('Scan '+ str(int(param['f'])) +' is completed; timespan  = ' + cmd_global.convertSeconds(dt))

        '''
        Data saving
        - File name from global, including directory and number
        - Can be saved as .csv or .hdf, but hdf format requires development.
        - Save terminated data?

        TODO: check exist number, don't overwrite old ones.
        '''
        filename = str(dir_date)+"scan_"+str(file_no)
        data_matrix.to_csv(data_dir+filename, mode='w')
        #data_matrix.to_hdf(file_path+filename, key='df', mode='w')
        cmd_global.sysReturn('Scan data saved as ['+filename+'.csv]')

class MacroWindow(QWidget):
    macroMsg = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.macro_editor = QTextEdit(self)
        self.macro_editor.resize(300,400)
        self.save_button = QPushButton("save",self)
        self.save_button.clicked.connect(self.save_macro)
        self.window_layout = QVBoxLayout(self)
        self.window_layout.addWidget(self.macro_editor)
        self.window_layout.addWidget(self.save_button)
    
    
    def save_macro(self):
        text = self.macro_editor.toPlainText() 
        print(text)
        print(text.split("\n"))
        # will be extended as user defined macro name
        file_title = "macro"+".txt"
        #open new file
        txt_file = macro_dir + file_title
        file = open(txt_file, "w")
        # write line to output file
        file.write(text)
        file.close()
        self.macro_editor.append("file saved: "+txt_file)
        self.macro_editor.setEnabled(False)
      
        
    
    


def main():
    app = QApplication(sys.argv)
    ex = RIXS()
    cmd_global.command_input.setFocus()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
