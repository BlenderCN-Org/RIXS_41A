#Last edited:20190425 4pm
import os, sys, time, random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from pyqtgraph import PlotWidget, GraphicsLayoutWidget
import numpy as np
import pandas as pd
import time, datetime, math, re
from pyepics_device import Devices as ped
from pyepics_tmp_device import TmpDevices as petd
from pyepics_ccd_device import CcdDevices as pecd
import epics as e

# Global for connection
spectrum_global = None
status_global = None
img_global = None
cmd_global = None
scan_data = None
xas_data = None     # XAS spectrum
rixs_data = None    # RIXS spectrum
rixs_img = None     # RIXS image data, np.ndrray

'''
Abort
 - execution flag for commands.
   default : False
   if abort = True, breaks loop.
 - reset in Command(send function)
'''
ABORT = False

'''
Busy
 - check flag for complicated commands
   default : False
 - if busy = True, command_input will be disabled.
 - checked in Command(cmdDone function)
'''
BUSY = False
SCAN = False

'''
global flag & parameters for RIXS
'''
IMGDONE = False

workingSTATUS = ""

# SETUP_parameters
#TODO: img?
param_index = [   'f','t', 's1', 's2', 'agm', 'ags', 'x', 'y', 'z', 'u', 'v', 'w','th', 'tth', 'ta', 'tb', 'I0', 'Iph', 'imager', 'Tccd', 'shutter', 'ccd', 'gain']
param_value = [int(0), 0.,  2.0,  50.,  710.,  720.,  0.,  0.,  0.,  0.,  0.,  0.,   0,    90,  20.,  30.,   0.,    0.,        0,     25,         0,     0,     10]
param = pd.Series(param_value, index=param_index)

## gloable device PV names
pvName = pd.Series({'agm': "41a:AGM:Energy",
                    'ags': "41a:AGS:Energy",
                    "x": "41a:hexapod:x",
                    "y": "41a:hexapod:y",
                    "z": "41a:hexapod:z",
                    "u": "41a:hexapod:u",
                    "v": "41a:hexapod:v",
                    "w": "41a:hexapod:w",
                    "th": "41a:sample:th",
                    "tth": "41a:sample:tth",
                    "ta": "41a:sample:tmp1",
                    "tb": "41a:sample:tmp2",
                    "I0": "41a:sample:i0",
                    "Iph": "41a:sample:phdi"})

# make a param_index for command input which excludes 'f', 'imager' and 'shutter'....
# note: we can't use param_index0 = param_index
non_movables =  ['t','f', 's1', 's2','imager', 'shutter', 'ccd','I0','Iph', 'tb']
param_index0 = list(param_index)
for elements in non_movables:
    param_index0.remove(elements)
# movables: ['agm', 'ags', 'x', 'y', 'z', 'u', 'v', 'w','th', 'tth', 'ta','Tccd', 'gain']

# golable series for the parameter ranges set to protect instruments.
param_range = pd.Series({'t':[0,1000], 's1':[1,30], 's2':[5,200], 'agm': [480, 1200],
                        'ags': [480, 1200], 'x': [-10,10], 'y': [-10,10],'z': [-6.5,6.5], 'u': [-10,10],
                          'v': [-10,10], 'w': [-10,10], 'th':[-5, 185], 'tth':[-35, 0],
                        'ta':[5,350], 'tb':[5,350], 'I0': [0,1], 'Iph': [0,1], 'Tccd': [-100, 30], 'gain': [0, 100]})

# Individual device control
Device = pd.Series({
        "hexapod":0,"ccd":0,
        "th":1, "tth":1,
        "agm": 1, "ags": 1,
        "ta": 1, "tb": 1,
        "I0": 1, "Iph": 1,
        "s1" :0, "s2":0, "shutter":0
    })

def checkSafe(p): # Individual device safe check
    if SAFE:
        if p in ['x','y','z','u','v','w']:
            if Device["hexapod"] != 0:
                return True
        elif p in ["ccd","gain","Tccd"]:
            if Device['ccd']==1:
                return True
        elif Device[p] == 1:
            return True
    else:
        return False

def checkMoving(p): #check moving status
    if p in ['x','y','z','u','v','w','th','tth']:
        if e.caget(pvName[p]+'m') == 1: # 1: moving, 0: stop
            return True
    elif p in ['agm','ags']:
        if e.caget(pvName[p] + ".MOVN") ==1:
            return True
    else: #including gain
        return False

#SAFE = False
SAFE = True

# SETUP_epics
if SAFE:
    #setup_CCD
    CCD = pecd("emccd", "41a:ccd1")
    CCD.setExposureTime(2)
    CCD.setGain(10)
    CCD.setAcqMode(2)  #0: video; 1: single (obsolete); 2: accumulation
    CCD.setAccuType(0) #0: raw image; 2: differnece image

def get_param(p):
    if checkSafe(p):
        if p == 'agm' or p =='ags':
            v = e.caget(pvName[p]+".RBV", timeout=0.1)
        elif p == 'th' or p == 'tth':
            v = e.caget(pvName[p]+'r', timeout=0.2)
        elif p == 'Tccd':
            v = e.caget('41a:ccd1:tmpr', timeout=0.1)
        elif p == 'gain':
            v = e.caget('41a:ccd1:gain', timeout=0.1)
        else :
            v = e.caget(pvName[p], timeout=0.1)  # get PV name from pvName series
        if v == None:
            v = 'NoneType'
        param[p] = v

    else:
        v = param[p]

    return v

def convertSeconds(seconds):
    m = str(int(seconds//60)) + ' mins '
    s = str(round(seconds%60, 2)) + ' secs'
    if int(seconds // 60) == 0: m = ""
    time_stg = m + s
    return time_stg

'''
Dir for datasaving and macro
 - create a project folder named after date
 - sub folders including log, macro, and data
 - TODO: build class?
'''
file_no = 0                 #

dir_date = datetime.datetime.today().strftime("%Y_%b%d")
dir_name = "project #0"
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
img_dir = data_dir + 'img' + sla

if not os.path.exists(dir_name):
    os.makedirs(project_path)
    os.makedirs(macro_dir)
    os.makedirs(log_dir)
    os.makedirs(data_dir)
    os.makedirs(img_dir)


def Read(p, form=3):
    # get value by param_list index
    if checkSafe(p):
        value = get_param(p)
        real = 1
    else:
        value = param[p]
        real = 0

    if isinstance(value, str):  # got None from device
        string = "<font color= red>none</font><font color = black> </font>"
    else:
        if form == 'current': string = np.format_float_scientific(value, unique=False, precision=2, exp_digits=2)
        elif form == 'int': string = str(int(value))
        elif form == 'switch':
            if value == 0: string = 'close'
            else: string = 'open'
        else: string = str(format(value, '.3f'))

        # real marked blue
        if real == 0: string = '<font color=gray>'+ string +'</font>'
        if checkMoving(p): string = '<font color=blue>' + string + '</font>'
    return string

'''
Start GUI construction
'''
class RIXS(QMainWindow):

    def __init__(self):
        global status_global
        QMainWindow.__init__(self)
        # Window attributes
        self.setFixedSize(1300, 820)
#        self.setFixedSize(1900, 1600)
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
        global cmd_global, img_global, status_global, spectrum_global
        hbox = QHBoxLayout(self)
        leftcolumn = QVBoxLayout()
        image_widget = ImageWidget(self)
        leftcolumn.addWidget(image_widget, 1)
        command_widget=Command(self)
        leftcolumn.addWidget(command_widget)

        # Right_Column
        rightcolumn = QVBoxLayout()
        status_widget=StatusWidget(self)
        rightcolumn.addWidget(status_widget)
        spectrum_widget = SpectrumWidget(self)
        rightcolumn.addWidget(spectrum_widget)
        hbox.addLayout(leftcolumn, 1)
        hbox.addLayout(rightcolumn, 1)

        # for global connection
        cmd_global = command_widget
        img_global = image_widget
        spectrum_global = spectrum_widget
        status_global = status_widget

        #qtsignal/slot method
        command_widget.loadimage.connect(image_widget.loadImg)
        self.show()

class StatusWidget(QWidget):
    global param, parameter_text
    def __init__(self, parent=None):
        super(StatusWidget, self).__init__(parent=parent)
        self.status_bar = QLabel(self)
        self.status_box = QTextEdit(self)
        self.status_box.setStyleSheet("color: black; background-color: Floralwhite")
        self.status_box.setFont(QtGui.QFont("UbuntuMono",12))
        self.status_box.setReadOnly(True)
        # Widget layout
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.status_bar)
        self.layoutVertical.addWidget(self.status_box)

    def show_bar(self):
        q_time = QDateTime.currentDateTime()
        time_str = q_time.toString("yyyy-MM-dd hh:mm:ss")
        x = str(format(time.time()%1,'.3f'))
        self.status_bar.setText(time_str+x[1:]+"  Project #0;   PI: Testing;"
                                +" file number: "+ str(int(param['f'])))

    def show_text(self):
        parameter_text = ( "<u>Parameters</u></font><br>"
                           " AGM: " + Read('agm') + " eV<br>"
                           " AGS: " + Read('ags') + " eV<br>"
                           " <br>"
                           " entrance slit   s1= " + Read('s1','int') + " &micro;m ; "
                           " exit slit   s2= " + Read('s2','int') + " &micro;m<br>"
                           " shutter: " + Read('shutter','switch')+ "<br>"
                           " <br>"
                           " Sample:  <br>"
                           " x = " + Read('x') + ", y = " + Read('y') + ", z = " + Read('z') + " <br>"
                           " u = " + Read('u') + ", v = " + Read('v') + ", w = " + Read('w') + " <br>"
                           " th = "+ Read('th') + ", tth = " + Read('tth')+"<br>"
                           "   temperatures:  T<sub>a</sub> = " + Read('ta','int') + " K,"+
                           " T<sub>b</sub> = " + Read('tb','int') + " K<br>"
                           " I<sub>0</sub> = "+ Read('I0','current') + " Amp,"+
                           " I<sub>ph</sub> = "+ Read('Iph','current') + " Amp <br>"
                           " <br>"
                           " RIXS imager:  <br>"
                           " temperature = " + Read('Tccd',1) +" \u2103"+ ',   gain = ' + Read('gain',0) + " <br>"
                           " <br><font color =red>"
                           + workingSTATUS +"</font>")
        self.status_box.setText(parameter_text)

        #Terminal
class Command(QWidget):
    popup = pyqtSignal()
    inputext = pyqtSignal(str)
    macrostat = pyqtSignal(str)
    pause = pyqtSignal(float)
    loadimage = pyqtSignal(str)
    plot_rixs = pyqtSignal(str)
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

        # user input
        self.command_input= QLineEdit(self)
        self.command_input.setFocusPolicy(Qt.StrongFocus)
        self.command_input.setPlaceholderText("Type help to list commands ...")
        self.commandLock()

        # input function communications
        self.command_input.returnPressed.connect(self.send_message)
        self.inputext.connect(self.send)    # input string as signal
        self.pause.connect(self.inputPause)

        # macro related
        self.macro = None
        self.popup.connect(self.popupMacro)
        self.macrostat[str].connect(self.command_input.setText)
        self.macrotimer = QTimer(self)
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
        global ABORT
        ABORT = False
        self.abort_button.setEnabled(True)
        txt = self.command_input.text()
        self.command_input.setText("")
        self.command_message.moveCursor(QtGui.QTextCursor.End)
        self.inputext[str].emit(txt)
        '''
        Set global abort flag when button clicked
        (because scan loop is not in this class...)
        '''
    def abortCommand(self):
        global ABORT
        ABORT = True
        self.abort_button.setDisabled(True)
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
         - TODO: solve global problem

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
                # TODO: format arrangement
                name = log_dir + self.logname +".csv"
                row.to_csv(name, mode='a', header=False, index=False)
                #=================== history log========================

            self.command_message.append(' ')
            self.command_message.append('<font color=blue>' + t + ' >> ' + x + '</font><font color=black> </font>')

        elif v == "err":
            self.command_message.append('<font color=red> '+ x + '</font><font color=black> </font>')
        else:
            self.command_message.append('<font color= black>'+x+'</font>')

    def preFormatting(self, text):
        # remove whitespace spaces ("  ") in the end of command input
        if text[len(text) - 1] == ' ' and text != "":
            text = text[:len(text) - 1]
        # an elegant way to remove extra whitespace,  "import re" is needed/
        text = re.sub(' +', ' ', text)
        # remove space before comma
        c = text.find(',')
        if c!=-1:
            if text[c - 1] == " ":
                print(text[:c - 1])
                print(text[c:])
                text = text[:c - 1] + text[c:]
        return text

    def send(self, txt):
        self.command_input.setDisabled(True)
        text = txt
        global param_index, param, cmd_global, file_no, img_global, BUSY, IMGDONE, workingSTATUS, spectrum_global
        # pre-formatting
        if len(text) != 0:
            text = self.preFormatting(text)
        # keyboard log for Up and Down
        if text != "":
            self.kblog.append(text)
            self.kbi = len(self.kblog)

        '''
        Check valid commands below ...
         - should be integrated as valid-command class
        '''
        if text == "help":
            self.sysReturn(text, "v")
            msg = ("<b>p</b>: list valid parameters.<br>\n"
                   "<b>r</b>: show all parameter ranges.<br>\n"
                   #"<b>macro</b>: open a macro editor.<br>\n"
                   #"<b>do</b>: execute a macro by calling a text file.<br>\n"
                   "<b>h</b>: recall previous commands executed sucessfully.<br>\n"
                   "<br>\n"
                   "<b>mv</b>: set a parameter to its absolute value.<br>\n"
                   #"<b>mvr</b>: change a parameter in terms of a relative value.<br>\n"
                   "<b>scan</b>: stepwise scan a parameter and plot selected paramters with some dwell time.<br>\n"
                   "<b>xas</b>:  <br>\n"
                   "<b>rixs</b>:  take RIXS images, t sec per iamge for n images <br>\n"
                   "<br>\n"
                   "<b>s2</b>: set the opening of the exit slit.<br>\n"
                   "<b>shut</b>: open or close the BL shutter.<br>\n"
                   "<b>ccd</b>: turn on or turn off the CCD.<br>\n"
                   "<b>load</b>: load an image file.<br>")
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
            p = ', '.join(param_index0) # what does this line do?
            self.sysReturn(p)

        elif "shut" in text[:5]:
            space = text.count(' ')
            sptext = text.split(' ')
            if space == 1: # e.g. shut 0
                if sptext[1] in ['0', '1']:
                    self.sysReturn(text,"v", True)
                    param['shutter'] = float(sptext[1]) # sptext[1] is the parameter to be moved; sptext[2] is value to moved.
                    if sptext[1]=='0': shutt ='close'
                    if sptext[1]=='1': shutt ='open'
                    self.sysReturn("The shutter is " + shutt)
                else:
                    self.sysReturn(text,"iv")
                    self.sysReturn('shutter parameter has to be 0 ot 1 for close and open, respectively.', "err")
            else:
                self.sysReturn(text,"iv")
                self.sysReturn('input error. use:   shut  0 or 1', 'err')

        elif text == "ccd":
            space = text.count(' ')
            sptext = text.split(' ')
            set_ccd = sptext[1]
            if space == 1: # e.g. ccd 1
                if set_ccd in ['0', '1']:
                    self.sysReturn(text,"v", True)
                    param['ccd'] = float(set_ccd) # sptext[1] is the parameter to be moved; sptext[2] is value to moved.
                    if set_ccd=='0': shutt ='off'
                    if set_ccd=='1': shutt ='on'
                    self.sysReturn("The CCD is " + shutt)
                else:
                    self.sysReturn(text,"iv")
                    self.sysReturn('ccd parameter has to be 0 ot 1 for off and on, respectively.', "err")
            else:
                self.sysReturn(text,"iv")
                self.sysReturn('input error. use:   ccd  0 or 1', 'err')

        elif 'img' in text[:4]:
            # All sequence below should be organized as function(text)
            space = text.count(' ')
            sptext = text.split(' ')
            if space == 1:  # e.g. img t
                if self.checkFloat(sptext[1]):
                    t = sptext[1]
                    BUSY=True
                    self.sysReturn(text, "v", True)
                    workingSTATUS = "Taking image... ; Exposure time ="+str(t)
                    if SAFE:
                        CCD.setExposureTime(t)
                        self.sysReturn("getting ccd image ...")
                    else:
                        self.sysReturn("Warning: CCD not connected", "err")
                        self.sysReturn("generating random image by numpy...")
                    self.imageExposure()
                    BUSY = False  # global flag
                    workingSTATUS = " "
                else:
                    self.sysReturn(text, "iv")
                    self.sysReturn("input error. use:   img + exposure_time", "err")
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   img + exposure_time/off", "err")

        elif text == 'rixs' or text[:5] == 'rixs ':
            # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2:  # e.g. rixs t n
                # t as exposure time ; n as number of images.
                t = float(sptext[1])
                n = int(sptext[2])
                if self.checkFloat(t) and self.checkFloat(n):
                    BUSY = True
                    self.sysReturn(text, "v", True)
                    tt = datetime.datetime.now()
                    self.sysReturn('RIXS ' + str(int(param['f'])) + ' begins at ' + tt.strftime("%c"))
                    dwell_0 = 0 # buffer time
                    if SAFE:
                        CCD.setExposureTime(t)
                        dwell_0 = 5 #  extra time for the while loop
                    self.t0 = time.time()
                    for i in range(n):
                        if i ==0:
                            workingSTATUS = 'Taking RIXS data ... ' + str(i+1) + '/' + str(n)
                        #print('i = ',i,'   ABORT =', ABORT)
                        if ABORT:
                            break
                        IMGDONE = False
                        self.imageExposure() # QThread replaced
                        img_global.saveImg()
                        t1 = time.time()
                        if i == 0:
                            dt = n * (t+3)
                        else:
                            dt = ((time.time() - self.t0) / i) * (n - i)  # remaining time
                        dt = round(dt,2)
                        while (time.time() - t1) < t + dwell_0:
                            self.t2 = time.time()
                            workingSTATUS = ('Taking RIXS data ... ' + str(i+1) + '/' + str(n)+',  remaining time = ' + str(dt)+' sec')
                            if (self.t2 - t1)%0.2 <= 0.00003:
                                #QApplication.processEvents()
                                pass
                            if SAFE:
                                if IMGDONE:
                                    print('getData() finished.')
                                    break
                            if ABORT:
                                break
                        #print('while loop takes :',time.time() - t1)
                        img_number= str(i+1)+' image'
                        if i>0:
                            img_number +='s'
                        self.sysReturn(img_number+' taken, time span= '+str(round(time.time()-self.t0,2))+' sec')
                    BUSY = False  # global flag
                    workingSTATUS = " "
                    self.sysReturn('Completed taking RIXS images.')
                else:
                    self.sysReturn(text, "iv")
                    self.sysReturn("Both t and n need to be numerical numbers.", "err")
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   rixs t n", "err")

        elif 'load' in text[:5]:
            # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            print('text =', text)
            print('filename =', sptext[1])
            if space == 1 and text[4]==" ":  # e.g. load filename
                self.sysReturn(text, "v", True)
                file_name = sptext[1]+'.txt'
                self.loadimage[str].emit(file_name)
                #self.plot_rixs[str].emit(file_name)
                spectrum_global.plotRixs(file_name)

                self.sysReturn(file_name+" has been loaded.")
        elif text == 'r':
            self.sysReturn(text,"v")
            msg='parameter ranges:\n'
            for i in range(param_range.size):
                msg += str(param_range.index[i]) + ' = '+ str(param_range[i])+'\n'
            self.sysReturn(msg)

        elif text == 'u':
            #status_global.show_text()
            self.sysReturn(text,"v")
            self.sysReturn("Parameter values have been updated.")

        elif "s2" in text[:3]:
            space = text.count(' ')
            sptext = text.split(' ')
            if space == 1: # e.g. s1 5
                if sptext[1] in ['5', '10', '20', '50', '100', '150']:
                    self.sysReturn(text,"v", True)
                    param['s2'] = float(sptext[1]) # sptext[1] is the parameter to be moved; sptext[2] is value to moved.
                    self.sysReturn("The exit slit opening has been set to " + sptext[1])
                else:
                    self.sysReturn(text,"iv")
                    self.sysReturn('s2 opening is discrete, 5, 10, 20, 50, 100 & 150', "err")
            else:
                self.sysReturn(text,"iv")
                self.sysReturn("input error. use:   s2 opening (5, 10, 20, 50, 100 or 150)", "err")

        # mv function
        elif text == 'mv' or text[:3] == 'mv ':
        # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2: # e.g. mv x 1234
                # p as parameter ; v as value.
                p = sptext[1]
                v = sptext[2]
                if p in param_index0:
                    check_param =self.check_param_range(p, v)
                    if check_param == 'OK' and self.checkFloat(v):
                        self.sysReturn(text,"v", True)
                        self.WorkeThread = Move(p, float(v))
                        self.WorkeThread.finished.connect(self.finish_message)  # check if finished or not
                        self.WorkeThread.msg.connect(self.sysReturn)
                        self.WorkeThread.start()
                    else:
                        self.sysReturn(text,"iv")
                        self.sysReturn(check_param, "err")
                else:
                    self.sysReturn(text,"iv")
                    self.sysReturn("parameter \'"+ p+ "\' is invalid; type \'p\' to list valid parameters","err")
            else:
                self.sysReturn(text,"iv")
                self.sysReturn("input error. use:   mv parameter value", "err")

        # scan function
        # command format: scan [plot1 plot2 ...:] scan_param begin end step dwell
                # scan function
                # command format: scan [plot1 plot2 ...:] scan_param begin end step dwell
        elif 'scan' in text[:5]:
            # if the input command is only 'scan' but not parameters check != 'OK',
            check = self.check_param_scan(text)  # checking input command and parameters
            if check == 'OK':
                self.sysReturn(text, 'v', True)  # "v": log text in history; True: mark blue
                #QApplication.processEvents()
                if text.find(',') is -1:  # no "," i.e. scan x 1 10 1 0.1
                    c = 3
                    plot = ['Iph']  # default detection parameter
                else:  # scan y z, x 1 10 1 0.1
                    c = text.find(',')  # c= the location index of "," in text
                    print(text)
                    plot = text[5:c].split(' ')  # extract the parameter list of data plotting

                print('input plot=', plot)
                if plot == []: plot = ['Iph']
                sptext = text[c + 2:].split(' ')  # values of the scan parameter
                print('sptext=', sptext)

                scan_param = sptext[0]
                x1 = float(sptext[1])  # begin
                x2 = float(sptext[2])  # end
                step = abs(float(sptext[3])) * np.sign(x2 - x1)  # step is negative if x1 > x2
                dwell = float(sptext[4])  # dwell time in secconds
                n = int(abs((x2 - x1) / step))  # set the number of scanning steps
                check_param1 = self.check_param_range(sptext[0], x1)
                check_param2 = self.check_param_range(sptext[0], x2)

                if (check_param1 == 'OK') and (check_param2 == 'OK'):
                    file_no += 1
                    param['f'] = file_no  # print('file no =', file_no, 'param[\'f\']', param['f'])
                    start_time = datetime.datetime.now()
                    self.sysReturn('Scan ' + str(int(param['f'])) + ' begins at ' + start_time.strftime("%c"))
                    #spectrum_global.scan_loop(plot, scan_param, x1, x2, step, dwell, n)
                    self.scanthread = Scan(plot, scan_param, x1, x2, step, dwell, n)
                    self.scanthread.scan_plot.connect(spectrum_global.scanPlot)
                    self.scanthread.cmd_msg.connect(cmd_global.sysReturn)
                    self.scanthread.set_data.connect(spectrum_global.setScandata)
                    self.scanthread.start()
                else:
                    self.sysReturn(text, "iv")
                    if (check_param1 != 'OK'): check_param = check_param1
                    if (check_param2 != 'OK'): check_param = check_param2
                    self.sysReturn(check_param, "err")
            else:
                # Return error message
                self.sysReturn(text, "iv")
                self.sysReturn(check, "err")
        elif text == "macro":
            # popup window
            self.sysReturn(text,"v")
            self.popup.emit()

# =============================================================================
#         elif text[:3] == "do ":
#             space = text.count(' ')
#             sptext = text.split(' ')
#             name = sptext[1]
#             # read macro file
#             if space is 1:
#                 self.doMacro(name)
#             else:
#                 self.sysReturn("input error. use:   do macroname","err")
# =============================================================================
        #TODO: wait command test after Thread
        # elif text[:5] == "wait ":
        #     space = text.count(' ')
        #     sptext = text.split(' ')
        #     # set delay time
        #     if space == 1:
        #         t = sptext[1]
        #         if self.checkFloat(t):
        #             self.sysReturn(text, "v", True)
        #             self.sysReturn("wait for %s seconds..." %str(t))
        #             self.pause[float].emit(float(t))
        #         else:
        #             self.sysReturn("input error. use:   wait time", "err")

        elif text != "":
           self.sysReturn(text, "iv")
           self.sysReturn("Type 'help' to list commands", "err")

    def finish_message(self):
        print("Move thread finished")

    def checkFloat(self, x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    def check_param_range(self, param_name, param_value):
        if self.checkFloat(param_value) is True:
            global param_range
        #if (parame_name in param_index0) and self.checkFloat(param_value) == True:
            j= float(param_value)
            if min(param_range[param_name]) <= j  and j <= max(param_range[param_name]):
                check_msg = 'OK'
            else:
                check_msg = ('Oops! '+ param_name+ ' value was out of range; type \'r\' to show parameter ranges.')
        else:
            check_msg = (param_name + " value must be number or float", "err")
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
            plot=['Iph']
        else:
            c = text.find(',')
            space = text[c:].count(' ') # space = 5, after truncating "scan y z ...:" => e.g. , x 1 10 2 0.1
            sptext = text[c+2:].split(' ') # scan_param 1 10 1 0.1
            plot=text[5:c].split(' ') # list of detection parameter

        if text[c+1:].find(',') == -1 and space == 5:
            if (sptext[0] != '') and (len(sptext) == 5):
                j=0 #check index
                for i in range(4): # i from 0 to 3
                    if self.checkFloat(sptext[i+1]) is True:
                        j +=1.0
                if j==4:
                    if sptext[0] in param_index0:
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
            if (plot[i] in param_index0) or (plot[i]=='Iph'): j +=1.0
        #
        if j== len(plot) and j <= 5: # max plot no. = 5
            check_plot='OK'
        else:
            check_plot='not OK'

        if check_format == 'OK' and check_plot == 'OK':
            check_msg = ('OK')
        elif check_format == 'OK' and check_plot != 'OK':
            check_msg = ('invalid plotting parameters')

        print('scan paramter check:', check_msg)
        return check_msg

        '''
        check function for Wait command
        '''
    def inputPause(self, t):
        global BUSY
        BUSY = True
        timer = QTimer(self)
        timer.timeout.connect(self.cmdDone)
        timer.start(1000*float(t)) # count for t seconds then open user input

    def cmdDone(self):
        global BUSY, status_global
        BUSY = False

    def commandLock(self):
        timer = QTimer(self)
        timer.setSingleShot(False)
        timer.timeout.connect(self.lockInput)
        timer.start(1000) # repeat every second

    def lockInput(self):
        if SCAN:
            self.command_input.setDisabled(SCAN)
        else:
            self.command_input.setDisabled(BUSY)
            if BUSY == False:
                self.command_input.setFocus()

    def doMacro(self, name):
        #reset macro numbers
        self.macro_index = 0
        self.macro_n = 0
        macro_name = macro_dir + str(name) + ".txt"
        #check file exist
        if os.path.exists(macro_name):
            self.sysReturn(text,"v", True)
            self.readFile(macro_name) # to get macro_n
            self.sysReturn("macro begins: "+macro_name)
            self.macroLoop(self.macro_n, macro_name)
        else:
            self.sysReturn(text,"iv")
            self.sysReturn("macro file name: {0} not found in {1}.".format(name, macro_dir),"err")

    # def readFile(self, name):
    #     #==============Macro start===============
    #     readfile=[]
    #     f = open(name,"r")
    #     for x in f:
    #         x = x.replace('\n','')
    #         readfile.append(x)
    #     self.macro_n = len(readfile)
    #     return (readfile)
    #
    # def macroLoop(self,n,name):
    #     global BUSY
    #     while self.macro_index < self.macro_n:
    #         file = self.readFile(name)
    #         line = file[self.macro_index]
    #         msg = ("macro line [{0}] : {1}".format(str(self.macro_index), line))
    #         self.sysReturn(msg)
    #         while BUSY == True:
    #             timer = QTimer(self)
    #             timer.start(1000)
    #             # wait until not busy...
    #         #self.macrostat[str].emit(msg)
    #         self.send(line)
    #         self.macro_index += 1
    #     self.sysReturn("macro finished.")

    def imageExposure(self):
        if SAFE:
            CCD.start(1) # 1 for activate
            t1 = time.time()
            while e.PV("41a:ccd1:dataok").get() == 1:
                if (time.time()-t1)%0.2 <= 0.0001:
                    #QApplication.processEvents()
                    pass
                if e.PV("41a:ccd1:dataok").get() == 0:
                    break
        t1 = time.time()
        print('t1 =', t1)
        if SAFE:
            j = 0 # a counter to mimic timer
            while e.PV("41a:ccd1:dataok").get() == 0:
                j += 1
                if (time.time()-t1)%0.2 <= 0.0001:
                    #QApplication.processEvents()
                    pass
                if e.PV("41a:ccd1:dataok").get() == 1:
                    break
                if ABORT:
                    self.sysReturn('RIXS aborted', 'err')
                    break
        else:
            for self.i in range(0,3):
                #self.msg.emit('i now：{}'.format(self.i))
                #self.sleep(1)
                time.sleep(0.1)
        dt = round(time.time() - t1, 3)
        print('time span in seconds= %s'%dt)
        print('before get data')
        img_global.getData()
        img_global.plotImg()

class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        # Default Image
        a = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        npa = np.asarray(a)
        renpa = np.reshape(npa, (2, 5), order='F')
        self.imgdata = renpa # default image when program startup
                             # replace by RGB pixel Magpie picture?

        plt = pg.PlotItem(labels={'bottom':('x pixel',''), 'left':('y pixel','')})
        plt.getAxis('bottom').setTickSpacing(200, 2)  # This is the trick
        plt.getAxis('left').setTickSpacing(200, 2)  # This is the trick

        ## Set a custom color map
        rainbow_colors = [
            (0, 0, 255),
            (0, 128, 255),
            (0, 255, 128),
            (128, 255, 0),
            (255, 128, 0),
            (255, 0, 0)
        ]
        cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=rainbow_colors)

        self.imv = pg.ImageView(view=plt)
        self.imv.setColorMap(cmap)
        plt.invertY(False)
        plt.setAspectLocked(True)
        self.imv.ui.roiBtn.hide()
        self.imv.ui.menuBtn.hide()

        self.plotImg()
        # Widget layout
        self.status_bar = QLabel(self)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.status_bar)
        self.layoutVertical.addWidget(self.imv)
        #cross hair
        vLine = pg.InfiniteLine(angle=90, movable=False)
        hLine = pg.InfiniteLine(angle=0, movable=False)
        plt.addItem(vLine, ignoreBounds=True)
        plt.addItem(hLine, ignoreBounds=True)

        def mouseMoved(pos):
            data = self.imv.image
            nCols, nRows = data.shape
            mousePoint = plt.getViewBox().mapSceneToView(pos)
            row, col = int(mousePoint.y()), int(mousePoint.x())
            value = 0
            #update cross hair
            vLine.setPos(mousePoint.x())
            hLine.setPos(mousePoint.y())

            if (0 <= row < nRows) and (0 <= col < nCols):
                value = data[col, row]
            else:
                pass
            self.status_bar.setText("Image Pixel Information: " + "pos = ({:d}, {:d}), value = {!r}".format(col, row, value))
        self.imv.scene.sigMouseMoved.connect(mouseMoved)

    def getData(self):
        global IMGDONE, cmd_global
        if SAFE: # checked safe
            # check data OK
            #raw_img = e.PV("41a:ccd1:image").get() #calling pyepics_ccd_device.py
            raw_img = CCD.getImage()
            print("raw image: ")
            print(raw_img)
            img_list = np.asarray(raw_img)  # convert raw image to 1d numpy array
            img_np = np.reshape(img_list, (1024, 2048), order='F')  # reshape from 1d to 2d numpy array
            IMGDONE = True
        else:
            # else
            raw_img = np.random.uniform(0,500+1,1024*2048)
            img_list = np.asarray(raw_img)
            img_np = np.reshape(img_list, (1024, 2048), order='F')
        self.imgdata = img_np

    def saveImg(self):
        '''
        save file as .txt
        name format example: 2019_Apr18_142200(Hr/Min/Sec)
        '''
        datestamp = datetime.datetime.today().strftime("%Y_%b%d_%H%M%S") #Format : Year_MonDt
        file_name0 =datestamp + '_img'      # short ver. for display
        file_name = img_dir + file_name0   # for saving in correct dir
        np.savetxt(file_name, self.imgdata, fmt='%9d', delimiter=',')
        cmd_global.sysReturn('Image data saved as: '+file_name0)

    def plotImg(self):
        self.imv.setImage(self.imgdata)

    def loadImg(self, filename):
        global rixs_img
        '''
        raw_data = np.genfromtxt(name, delimiter=',', usecols=1)
        data = np.asarray(raw_data)
        print('data size = ', np.size(data))
        data = np.delete(data, 0)
        self.imgdata = np.reshape(data, (1024, 2061), order='F')
        '''
        raw_data=np.genfromtxt(filename, delimiter=',') # The type of data1 is <class 'numpy.ndarray'>
        self.imgdata=np.transpose(raw_data[:,0:1024]) #cconvert raw image to 1d numpy array
        rixs_img = np.copy(self.imgdata)
        self.plotImg()

    def rixs_sum(self, image_data):
        rixs_tmp = np.zeros((1, 2048), float)

        for i in range(renpa.shape[0]):
            rixs_tmp = rixs_tmp + renpa[i, :]

        print(rixs_tmp.ndim, rixs_tmp.shape, rixs_tmp.dtype)
        print(rixs_tmp)

class SpectrumWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.data = [random.random() for i in range(2000)]
        self.plotWidget = PlotWidget(self)
        self.spectrumPlot(self.data)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.plotWidget)
        self.w = None

    def spectrumPlot(self, x):
        #clear previous plot
        self.plotWidget.plotItem.clear()
        self.plotWidget.plot(x)

    def scanPlot(self, plot, scan_param, x1, x2_new):
        title_plot = 'Scan ' + str(int(param['f'])) + ': scanning ' + scan_param + ',  plotting '+ plot[0]
        for i in range(0, len(plot)):
            if i>0: title_plot += ', ' + plot[i]

        self.plotWidget.plotItem.clear()
        self.plotWidget.plotItem.setTitle(title=title_plot)
        self.plotWidget.plotItem.setXRange(float(x1), float(x2_new), padding=None, update=True)
        self.plotWidget.plotItem.setLabel('bottom', text=scan_param)
        self.plotWidget.plotItem.setLabel('left', text='Intensity', units='A')
        self.legend = self.plotWidget.addLegend((50, 30), offset=(450, 150))
        self.legend.setParentItem(self.plotWidget.plotItem)
        self.curve = [None, None, None, None, None]
        color = ['g', 'b', 'w', 'r', 'y']
        print('plot: ', plot, ', color: ', color)

        scan_x = []  # the empty list for the scanning parameter
        for i in range(0, len(plot)):
            self.curve[i] = self.plotWidget.plot(scan_x, [], pen=color[i], linewidth=2, name=plot[i])

    def setScandata(self, i, list_x, series_y):
        self.curve[i].setData(list_x, series_y)


    def plotRixs(self, filename):
        global rixs_img
        #self.plotWidget.plotItem.setTitle(title= title_plot)
        x1=0
        x2=2060

        ##### spike removal along s for continusly changing t (0-2060)
        # data: 2D numpy array
        # x1 and x2: region of interest along the x-pixel
        # d: discrimination factor; discriminator leve = data_avegera * d

        #data_sp=spike.spikeRemoval(rixs_img, 400, 600, 3)

        self.plotWidget.plotItem.setXRange(float(x1), float(x2), padding=None, update=True)
        self.plotWidget.plotItem.setLabel('bottom', 'y-pixel')
        self.plotWidget.plotItem.setLabel('left', text='Intensity', units='arb. units')
        self.plotWidget.addLegend((50,30), offset=(450,150))
        self.plotWidget.plotItem.clear()


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

class BarUpdate(QThread):
    refresh = pyqtSignal()
    def __init__(self):
        super(BarUpdate, self).__init__()
    def run(self):
        while True:
            self.refresh.emit()
            time.sleep(0.5)

class StatextUpdate(QThread):
    refresh = pyqtSignal()
    def __init__(self):
        super(StatextUpdate, self).__init__()
    def run(self):
        while True:
            self.refresh.emit()
            time.sleep(0.5)

class Move(QThread):
    msg = pyqtSignal(str)
    def __init__(self , p, v):
        super(Move, self).__init__()
        self.p = p
        self.v = v

    def run(self):
        global cmd_global, workingSTATUS, BUSY
        # p : index(name) of parameter, should be a string; v : range-checked value
        p, v, BUSY= self.p, self.v, True
        if checkSafe(p):  # check device safety
            if p in ['x','y','z','u','v','w','th','tth']:
                e.caput(pvName[p]+'w', v)
                # check moving status
                t1 = time.time()
                while e.caget(pvName[p] + 'm') == 0:  # = 0 not moving; = 1 moving
                    time.sleep(0.2)
                    if e.caget(pvName[p] + 'm') == 1 or (time.time() - t1) >= 1:
                        break

                # wait moving complete
                while e.caget(pvName[p] + 'm') == 1:
                    time.sleep(0.2)  # hold here for BUSY flag
                    if ABORT:
                        e.caput(pvName[p]+'s')
                        self.msg.emit("Move aborted.")
                        break
                    if e.caget(pvName[p] + 'm') == 0:
                        self.msg.emit('Move finished.')
                        if abs(e.caget(pvName[p] + 'r') - v) >= 0.02:
                            error_message = ("<font color=red>" + p + " not moving correctly, value: "
                                             + str(e.caget(pvName[p] + "r")) + "</font>")
                            self.msg.emit(error_message)
                        break

            elif p in ['agm', 'ags']:
                rbv = e.caget(pvName[p] + '.RBV') #avoid getting None
                while rbv == None:
                    rbv = e.caget(pvName[p] + '.RBV')
                if abs(rbv - v) >= 0.005:
                    e.caput(pvName[p], v)
                    # check moving status
                    t1 = time.time()
                    while e.caget(pvName[p] + ".MOVN") == 0:  # = 0 not moving; = 1 moving
                        time.sleep(0.1)
                        if e.caget(pvName[p] + ".MOVN") == 1 or (time.time() - t1) >= 1:
                            break

                    # wait moving complete
                    while e.caget(pvName[p] + ".MOVN") == 1:
                        time.sleep(0.1) # hold here for BUSY flag
                        if ABORT:
                            #e.caput(pvName[p] + 's')
                            self.msg.emit("Move aborted.")
                            break
                        if e.caget(pvName[p] + ".MOVN") == 0:
                            self.msg.emit('Move finished.')
                            if abs(e.caget(pvName[p] + '.RBV') - v) >= 0.02:
                                error_message = ("<font color=red>" + p + " not moving correctly, value: "
                                + str(e.caget(pvName[p] + ".RBV")) + "</font>")
                                self.msg.emit(error_message)
                            break

            if p == 'ta':
                e.caput("41a:sample:heater", 1)
                TSA.setValue(v)
            elif p == 'Tccd':
                CCD.setTemp(v)
            elif p == 'gain':
                CCD.setGain(v)
        else:
            param[p] = v
        BUSY = False
        self.quit()

class Scan(QThread):
    scan_plot = pyqtSignal(list, str, float, float)
    set_data = pyqtSignal(int, list, pd.Series)
    cmd_msg = pyqtSignal(str)
    def __init__(self, plot, scan_param, x1, x2, step, dwell, n):
        super(Scan, self).__init__()
        self.plot, self.scan_param, self.step = plot, scan_param, step
        self.x1, self.x2, self.dwell, self.n = x1, x2, dwell, n
        self.start_point = Move(scan_param, x1)
        self.data_matrix = pd.DataFrame(columns=param_index)

    def run(self):
        global file_no, param, BUSY, workingSTATUS, SCAN
        SCAN = True
        t1 = time.time()
        plot, scan_param, x1, x2= self.plot, self.scan_param, self.x1, self.x2
        step, dwell, n = self.step, self.dwell, self.n

        x2_new = x1 + step * n
        scan_x = []  # the empty list for the scanning parameter
        workingSTATUS = "moving " + scan_param + " ..."

        # set_param(scan_param, x1)  # set the initial parameter value
        self.start_point.start()
        self.start_point.wait()


        self.scan_plot.emit(plot, scan_param, x1, x2_new)
        '''
        Scanning loop
        - start time
        set scanning parameters = > Data collection (averaging)  => plot data
        '''
        print('Loop begin')
        for i in range(n + 1):
            if ABORT:
                print("loop stopped")
                break
            '''
            start time
            '''
            # time recording
            if i == 0:
                scan_loop_start_time = time.time()
                loop_time = 0
            else:
                loop_time = time.time() - scan_loop_start_time

            if i <= 10:
                remaining_time = (float(dwell) + 3.5) * int(n + 1 - i)
            else:
                remaining_time = (loop_time / i) * (n + 1 - i)

            workingSTATUS = ('scanning ' + scan_param + '... ' + str(i + 1) + '/' + str(n + 1) +
                             ', remaining time = ' + convertSeconds(remaining_time))
            '''
            Set scanning parameters
            '''
            scan_x.append(x1 + i * step)
            print("set ", scan_param, " to ", x1+i*step)
            self.WorkerThread = Move(scan_param, scan_x[i])
            self.WorkerThread.start()
            self.WorkerThread.wait() #wait move finish
            '''
            Data collection time
            '''
            t0 = time.time()
            raw_array = np.array([])
            while (time.time() - t0) <= dwell:  # while loop to get the data within dwell time
                if (time.time() - t0) % 0.2 <= 0.0001:
                    raw_array = np.append(raw_array, param['Iph'])  # Read Iph data through epics
                    # for i in range(len(plot)):
                    #     raw_array = np.append(raw_array, get_param(plot[i]))

            current_param = pd.Series(param)  # generate series

            # plot_list = [[], [], [], [], []] # prepare five empty list
            # for i in range(raw_array.size):
            #     plot_list[int(i%len(plot))].append(raw_array[i])

            # average
            # for i in range(len(plot)):
            #     data_array = np.array(plot_list[i])
            #     data_array = np.unique(data_array)  # remove the overlap
            #     data_ave = np.mean(data_array)
            #     current_param[plot[i]] = float(data_ave)  # replace param['Iph'] by averaged data

            data_array = np.array(raw_array)
            data_array = np.unique(data_array)  # remove the overlap
            data_ave = np.mean(data_array)
            current_param['Iph'] = float(data_ave)  # replace param['Iph'] by averaged data

            current_param['t'] = round(loop_time, 2)
            self.data_matrix.loc[len(self.data_matrix), :] = current_param.tolist()  # appending param to data_matrix
            '''
            plot from data_matrix
            '''
            for i in range(0, len(plot)):
                self.set_data.emit(i, scan_x, self.data_matrix.loc[:, plot[i]] )

        '''
        Loop finished
        '''
        workingSTATUS = " "
        print('[data_matrix]')
        print(self.data_matrix)

        dt = round(time.time() - t1, 3)
        print('time span in senconds=', dt)

        if ABORT:
            self.cmd_msg.emit('Scaning loop has been terminated; time span  = ' + convertSeconds(dt), 'err')
        else:
            self.cmd_msg.emit('Scan ' + str(int(param['f'])) + ' is completed; time span  = ' + convertSeconds(dt))

        '''
        Data saving
        - File name from global, including directory and number
        - Can be saved as .csv or .hdf, but hdf format requires development.
        - Save terminated data?

        TODO: check exist number, don't overwrite old ones.
        '''

        filename = str(dir_date) + "scan_" + str(file_no) + ".txt"  # change file_no to capital
        if os.path.exists(filename):
            file_no += 1
        filename = str(dir_date) + "scan_" + str(file_no) + ".txt"
        self.data_matrix.to_csv(data_dir + filename, mode='w', index_label="index")
        self.cmd_msg.emit('Scan data saved in [' + filename + ']')
        SCAN = False
        self.quit()


def main():
    global status_global
    app = QApplication(sys.argv)
    display_gui = RIXS()

    bar_update = BarUpdate()  # bar 0.2 sec
    bar_update.refresh.connect(status_global.show_bar)
    bar_update.start()

    text_update = StatextUpdate() # status 0.5 sec
    text_update.refresh.connect(status_global.show_text)
    text_update.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
