# Last edited:20190625 5pm
import os, sys, time, random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from pyqtgraph import PlotWidget, GraphicsLayoutWidget
import numpy as np
import pandas as pd
import datetime, re
import pvlist as pvl
import math
from spike import spikeRemoval, low_pass_fft
from scipy.ndimage import gaussian_filter
import macro

# Global for connection
spectrum_global = None
status_global = None
img_global = None
cmd_global = None
scan_data = None
xas_data = None  # XAS spectrum
rixs_data = None  # RIXS spectrum
rixs_img = None  # RIXS image data, np.ndrray

'''
Dir for datasaving and macro
 - create a project folder named after date
 - sub folders including log, macro, and data
 - TODO: build class?
'''

file_no = 0  # read file_no from exist log

dir_date = datetime.datetime.today().strftime("%Y%m%d")
dir_name = "project #0"
current_path = os.getcwd()

sla = '\\' if ('\\' in current_path) else '/'

project_path = str(current_path) + sla + dir_name + sla
macro_dir = str(project_path) + 'macro' + sla
log_dir = str(project_path) + 'log' + sla
data_dir = str(project_path) + 'data' + sla
img_dir = data_dir + 'img' + sla

if not os.path.exists(dir_name):
    os.makedirs(project_path)
    os.makedirs(macro_dir)
    os.makedirs(log_dir)
    os.makedirs(data_dir)
    os.makedirs(img_dir)

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
MACROBUSY = False

'''
global flag & parameters for multi-step process
'''
WorkingSTATUS = ""
CountDOWN = 0

# SETUP_parameters
# TODO: img?
param_index = ['f', 't', 's1', 's2', 'agm', 'ags', 'x', 'y', 'z', 'th', 'tth', 'ta', 'tb', 'I0', 'Iph',
               'imager', 'Tccd', 'shutter', 'ccd', 'gain', 'thoffset']
param_value = [file_no, 0., 2.0, 50., 710.,  720.,  0.,  0.,  0.,    0,    90,  20.,  30.,   0.,    0., 0, 25, 0, 0, 10, 0]
param = pd.Series(param_value, index=param_index)

# make a param_index for command input which excludes 'f', 'imager' and 'shutter'....
# note: we can't use param_index0 = param_index
non_movables = ['t', 'f', 's1', 's2', 'imager', 'shutter', 'ccd', 'I0', 'Iph', 'tb']
param_index0 = list(param_index)
for elements in non_movables:
    param_index0.remove(elements)
# movables: ['agm', 'ags', 'x', 'y', 'z','th', 'tth', 'ta','Tccd', 'gain']

# golable series for the parameter ranges set to protect instruments.
param_range = pd.Series({'agm': [480, 1200],'ags': [480, 1200], 'x': [-15, 5], 'y': [-5, 5], 'z': [-7, 12],
                         'th': [-10, 215], 'tth': [-35, 0], 'ta': [5, 350], 'tb': [5, 350], 'Tccd': [-100, 30],
                         'gain': [0, 100], 'thoffset':[-70, 70]})

# Individual device safety control
Device = pd.Series({
    "hexapod": 0, "ccd": 0, "xyzstage":0,
    "th": 0, "tth": 0,
    "agm": 0, "ags": 0,
    "ta": 0, "tb": 0,
    "I0": 0, "Iph": 0,
    "s1": 0, "s2": 0, "shutter": 0,
    "thoffset":0 , "Iring":0
})


def checkSafe(p):  # Individual device safe check
    if p in ['x', 'y', 'z']:
        if Device["xyzstage"] == 1:
            return True
    elif p in ["ccd", "gain", "Tccd"]:
        if Device['ccd'] == 1:
            return True
    elif Device[p] == 1:
        return True
    else:
        return False

if Device['ccd']==1:
    pvl.ccd("exposure", 2)
    pvl.ccd("gain", 10)
    pvl.ccd("acqmode", 2)   # 0: video; 1: single (obsolete); 2: accumulation
    pvl.ccd("accunum", 1)   # accunum to 1
    pvl.ccd("accutype", 0)  # 0: raw image; 2: differnece image

#TODO: restart PV while get None
#refresh param(pd.Series)
def get_param(p):
    global param, Device
    if checkSafe(p):
        v = pvl.getVal(p)
        if v == None: # turn off safe if get None by related PV
            if p in ['x','y','z']:
                Device["xyzstage"] = 0
            elif p in ["ccd", "gain", "Tccd"]:
                Device['ccd'] = 0
            else:
                Device[p] = 0
            v = param[p]
        else:
            if p in ['x', 'y']:  # for x, y, z display
                th = -(pvl.thOffset() * math.pi / 180)  # rad
                if p == 'x':
                    v = v * math.cos(th) - pvl.getVal('y') * math.sin(th)
                if p == 'y':
                    v = pvl.getVal('x') * math.sin(th) + v * math.cos(th)
        param[p] = v
    else:
        v = param[p]
    return v

def convertSeconds(seconds):
    m = str(int(seconds // 60)) + ' mins '
    s = str(int(seconds % 60)) + ' secs'
    if int(seconds // 60) == 0: m = ""
    time_stg = m + s
    return time_stg

def Read(p, form='.3f'):
    # get value by param_list index
    value = get_param(p)
    real = 1 if checkSafe(p) else 0
    if isinstance(value, str):  # got None from device
        string = "<font color= red>none</font><font color = black> </font>"
    else:
        if form == 'current':
            string = np.format_float_scientific(value, unique=False, precision=2, exp_digits=2)
        elif form == 'int':
            string = str(int(value))
        elif form == 'switch':
            string = 'close' if value == 0 else 'open'
        elif '.' in form:
            string = str(format(value, form))
        # real marked blue
        if real == 0: string = '<font color=gray>' + string + '</font>'
        if real == 1 and p not in ['Tccd', 'I0',  'gain', 'Iph']:
            if pvl.moving(p):
                string = '<font color=blue>' + string + '</font>'

    return string
'''
Start GUI construction
'''
class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setFixedSize(1300, 780)
        self.setWindowTitle('TPS blue magpie')

        exitAct = QAction(QIcon('exit.png'), ' &Quit',  self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.quitApplication)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)
        # Import panel
        self.panel_widget = Panel(self)
        self.setCentralWidget(self.panel_widget)
        #self.setFixedSize(self.layout)
        self.show()

    def closeEvent(self, event):
        self.quitApplication()
        event.accept()

    def quitApplication(self):
        global cmd_global
        cmd_global.fullLog("APP_CLOSED") #using space will cause pd reading problem
        qApp.quit()

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
        command_widget = Command(self)
        leftcolumn.addWidget(command_widget)

        # Right_Column
        rightcolumn = QVBoxLayout()
        status_widget = StatusWidget(self)
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

        # qtsignal/slot method
        spectrum_widget.errmsg.connect(command_widget.sysReturn)
        spectrum_widget.msg.connect(command_widget.sysReturn)
        spectrum_widget.setbkgd.connect(image_widget.setBkgd)
        spectrum_widget.showimg.connect(image_widget.setBkgd)
        spectrum_widget.saveRef.connect(image_widget.saveRef)
        command_widget.saveName.connect(spectrum_widget.saveName)
        command_widget.loadimage.connect(image_widget.loadImg)
        command_widget.setrixsplot.connect(spectrum_widget.setRIXSplot)
        command_widget.setrixsdata.connect(image_widget.plotSpectrum)
        command_widget.setref.connect(spectrum_widget.setRef)
        command_widget.setfactor.connect(spectrum_widget.setFactor)
        image_widget.setrixsdata.connect(spectrum_widget.setRIXSdata)
        image_widget.errmsg.connect(command_widget.sysReturn)

        self.bar_update = Barupdate()  # bar 0.5 sec
        self.bar_update.refresh.connect(status_global.show_bar)
        self.bar_update.start()

        self.text_update = Statupdate()  # status 1 sec
        self.text_update.refresh.connect(status_global.show_text)
        self.text_update.start()

        self.show()


class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super(StatusWidget, self).__init__(parent=parent)
        self.today = datetime.date.today() #for date change detection
        self.status_bar = QLabel(self)
        self.ring_current = QLabel(self)
        self.ring_current.setFont(QFont("UbuntuMono", 10))
        self.status_box = QTextEdit(self)
        self.status_box.setStyleSheet("color: black; background-color: Floralwhite")
        self.status_box.setFont(QFont("UbuntuMono", 10.5))
        self.status_box.setReadOnly(True)
        # Widget layout
        self.layoutVertical = QVBoxLayout(self)
        self.barhorizontal = QHBoxLayout()
        self.barhorizontal.addWidget(self.status_bar)
        self.barhorizontal.addWidget(self.ring_current)
        self.layoutVertical.addLayout(self.barhorizontal)
        self.layoutVertical.addWidget(self.status_box)
        self.t0 = 0  # for remaining time reference

    def show_bar(self):
        global param, file_no
        tt = datetime.datetime.now()
        time_str = tt.strftime("%H:%M:%S, %b %d %Y; ")
        param['f'] = file_no
        self.status_bar.setText("%s  Project #0;   PI: Testing; file number: %s;"
                                %(time_str, int(file_no)))
        self.ring_current.setText("<p align=\"right\">I<sub>ring</sub>: {0:.3f} mA</p>".format
                                  (pvl.getVal('ring') if Device['Iring']==1 else 0))

    def show_text(self):
        # called every 1 sec
        if CountDOWN > 1:
            if CountDOWN != self.t0:  # reset t0
                self.t0 = float(CountDOWN)  # reference
                self.t1 = self.t0

            self.t1 -= 1
            if self.t1 < 0: self.t1 = 0

            time_text = " ; remaining time = " + convertSeconds(self.t1)
        else:
            self.t0 = 0  # if no WorkingStatus to show
            time_text = ""

        parameter_text = (" AGM: " + Read('agm') + " eV<br>"
                        " AGS: " + Read('ags') + " eV<br>"
                        " <br>"
                        " entrance slit   s1= " + Read('s1','int') + " &micro;m ; "
                        " exit slit   s2= " + Read('s2', 'int') + " &micro;m<br>"
                        " shutter: " + Read('shutter', 'switch') + "<br>"
                        " <br>"
                        " sample:  <br>"
                        " x = " + Read('x') + " mm, y = " + Read('y') + " mm, z = " + Read('z') + " mm,  "
                        " thoffset = " + str(pvl.thOffset()) + "&#176; <br>"
                        " th = " + Read('th', '.2f') + "&#176;,  T<sub>a</sub> = " + Read('ta', '.2f') + " K,"
                        " T<sub>b</sub> = " + Read('tb', '.2f') + " K<br> <br>"
                        " photodiode angle tth = " + Read('tth', '.2f') + "&#176;<br> <br>"
                        " I<sub>0</sub> = " + Read('I0', 'current') + " Amp,"
                        " I<sub>ph</sub> = " + Read('Iph', 'current') + " Amp <br> <br>"
                        " RIXS imager:  <br>"
                        " temperature = " + Read('Tccd','.1f') + " \u2103" + ',   gain = ' + Read('gain', 'int') + " <br> <br>")
        status_text = "%s <font color =red> %s %s </font>" % (parameter_text, WorkingSTATUS, time_text)
        self.status_box.setText(status_text)

    # TODO: deglobalize
    # def setString(self, string=None): #destroy global parameters
    #     string = WorkingSTATUS
    #     return string
    #
    # def setTime(self, t=None):
    #     return t

    # Terminal

class Command(QWidget):
    popup = pyqtSignal()
    inputext = pyqtSignal(str)
    macrostat = pyqtSignal(str)
    pause = pyqtSignal(float)
    loadimage = pyqtSignal(str)
    saveName = pyqtSignal(str)
    plot_rixs = pyqtSignal(str)
    macrostarted = pyqtSignal(str)
    setrixsplot = pyqtSignal(str)
    setrixsdata = pyqtSignal()
    setref = pyqtSignal(bool)
    setfactor = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # message
        self.command_message = QTextEdit(self)
        # welcome message
        time = QTime.currentTime()
        welcome_message = ('<font color=blue>' + time.toString() + ' >> Welcome to TPS Blue Magpie!</font>')
        self.command_message.setText(welcome_message)
        self.command_message.setFont(QFont("UbuntuMono", 10))
        self.command_message.setReadOnly(True)

        # user input
        self.command_input = QLineEdit(self)
        self.command_input.setFocusPolicy(Qt.StrongFocus)
        self.command_input.setPlaceholderText("Type help to list commands ...")
        self.commandLock()

        # input function communications
        self.command_input.returnPressed.connect(self.send_message)
        self.inputext.connect(self.send)  # input string as signal
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
        self.history_index = ['Time', 'Text']
        self.history_log = pd.DataFrame(columns=self.history_index)
        # modify counting mechanism => get index directly => check pandas document
        self.history_loc = 0
        self.logname = str(dir_date) + "_commandlog"
        '''
        Full log (for KeyPressEvent function and file number)
         - inherit all log from same day.
        '''
        self.fullog_name = log_dir + str(dir_date) + "_fullog1.txt"  # Example: 20190509_fullog.txt
        self.fullog_col = ['Time', 'Text'] + param_index
        global file_no
        if os.path.exists(self.fullog_name):
            data = pd.read_csv(self.fullog_name, header=0, delimiter="|")
            if len(data) > 0 :
                file_no = int(data['f'][len(data)-1]) # refresh file_no from the final APP_CLOSED information
            self.fullog = data[data['Text'] != "APP_CLOSED"].reset_index(drop=True)
            self.fullog_i = len(self.fullog) # removed APP_CLOSED for keyboard calling
        else:
            self.fullog_i = 0
            self.fullog = pd.DataFrame(columns = self.fullog_col)
            file = open(self.fullog_name, "a")
            file.write("|".join(self.fullog_col) + "\n")
            file.close()


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
        self.Input = QHBoxLayout()
        self.Input.addWidget(self.command_input)
        self.Input.addWidget(self.abort_button)
        self.Commandlayout.addLayout(self.Input)


    def send_message(self):
        global ABORT
        ABORT = False
        txt = self.command_input.text()
        self.command_input.setText("")
        self.command_message.moveCursor(QTextCursor.End)
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
        self.macro = macro.MacroWindow(macro_dir)
        self.macro.macroMsg.connect(self.sysReturn)
        self.macro.errorMsg.connect(self.sysReturn)
        self.macrostarted.connect(self.macro.marcoStart)
        self.macro.show()

        '''
        Up and Down
         - redefine function of QLineEdit(originally support return only)
         - read fullog_i and fullog["Text"] for command convenience.
         - TODO: solve global problem

        '''

    def keyPressEvent(command_input, event): #detect keypress event in command_input area
        global cmd_global
        size = len(cmd_global.fullog)
        if event.key() == Qt.Key_Up and 0 < cmd_global.fullog_i <= size:
            cmd_global.fullog_i -= 1
            text = cmd_global.fullog['Text'][cmd_global.fullog_i]
            cmd_global.command_input.setText(text)
        elif event.key() == Qt.Key_Down and 0 <= cmd_global.fullog_i <= size-1:
            cmd_global.fullog_i += 1
            text = cmd_global.fullog['Text'][cmd_global.fullog_i] if cmd_global.fullog_i < size - 1 else ""
            cmd_global.command_input.setText(text)
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
        t = timestamp.toString()
        if v == "iv":
            # invalid command
            self.command_message.append(' ')
            self.command_message.append('<font color=gray>{0} >> {1}</font><font color=black> </font>'.format(t, x))

        elif v == "v":
            if log == True:
                self.abort_button.setEnabled(True)
                i = (self.history_log.size) / 2 # current_size
                self.history_loc = int(i + 1)
                row = pd.Series([t, x], index=self.history_index, name=self.history_loc) # append valid command to history
                self.history_log = self.history_log.append(row)
            self.command_message.append(' ')
            self.command_message.append('<font color=blue>{0} >> {1}</font><font color=black> </font>'.format(t, x))

        elif v == "err":
            self.command_message.append('<font color=red>{0}</font><font color=black> </font>'.format(x))
        else:
            self.command_message.append('<font color= black>{0}</font>'.format(x))

    def preFormatting(self, text):
        # remove whitespace spaces ("  ") in the end of command input
        if text[len(text) - 1] == ' ' and text != "":
            text = text[:len(text) - 1]
        # an elegant way to remove extra whitespace,  "import re" is needed/
        text = re.sub(' +', ' ', text)
        # remove space before comma
        c = text.find(',')
        if c != -1:
            if text[c - 1] == " ":
                print(text[:c - 1])
                print(text[c:])
                text = text[:c - 1] + text[c:]
        return text

    def fullLog(self,text): # used in self.send and closing App
        row = [datetime.datetime.now().isoformat(sep="_", timespec='seconds'), text] + param.astype(str).values.tolist()
        file = open(self.fullog_name, "a")
        file.write("|".join(row) + "\n")
        file.close()
        self.fullog.loc[len(self.fullog), :] = row  # append new_row to dataframe of logging
        self.fullog_i = len(self.fullog)

    def send(self, text):
        self.command_input.setDisabled(True)
        global param_index, param, cmd_global, file_no, img_global, BUSY, WorkingSTATUS, spectrum_global, CountDOWN
        # pre-formatting
        if len(text) != 0:
            text = self.preFormatting(text)
            self.fullLog(text)
        '''
        Check valid commands below ...
         - should be integrated as valid-command class
        '''
        if text == "help":
            self.sysReturn(text, "v")
            msg = ("<b>p</b>: list valid parameters.<br>\n"
                   "<b>r</b>: show all parameter ranges.<br>\n"
                   "<b>macro</b>: open a macro editor.<br>\n"
                   "<b>do</b>: open a text file to execute macro commands.<br>\n"
                   "<b>h</b>: recall previous commands executed successfully.<br>\n"
                   "<br>\n"
                   "<b>mv</b>: set a parameter to its absolute value.<br>\n"
                   "<b>scan</b>: stepwise scan a parameter and plot selected parameters with some dwell time.<br>\n"
                   "<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> "
                   "<font color=blue>scan <b>det,</b> (optional) param x1 x2 dx dt n </font> <br>\n"
                   "<b>xas</b>:  execute X-ray absorption.<br>\n"
                   "<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> <font color=blue>xas Ei Ef dE dt n </font> <br>\n"
                   "<b>img</b>:  take one RIXS image with an exposure time (default exposure time= 2). <br>\n"
                   "<b>rixs</b>:  take a series of RIXS images with a fixed exposure time (t).<br>\n"
                   "<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> <font color=blue>rixs t n </font> <br>\n"
                   "<br>\n"
                   "<b>setref</b>: set current spectrum as reference spectrum.<br>\n"
                   "<b>spec</b>: set processing parameters including x1, x2, d1, d2, f(spike factor), g(gaussian factor). <br>\n"
                   "<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> <font color=blue>spec x1/x2/d1/d2/f/g value </font> <br>\n"
                   "<b>spike</b>: turn on/off spike removal for data processing.  <font color=blue>e.g. spike on </font> <br>\n"
                   "<b>bkrm</b>: turn on/off background subtraction for data processing. <font color=blue>e.g. bkrm on </font> <br>\n"
                   "<b>fft</b>: turn on/off fast fourier transform for data processing. <font color=blue>e.g. fft on </font> <br>\n"
                   "<b>d</b>: turn on/off discrimination after background substraction. <font color=blue>e.g. d on </font> <br>\n"
                   # "<b>shut</b>: open or close the BL shutter.<br>\n"
                   "<b>load</b>: load an image file from project#0/data/img folder.<br>"
                   "<b>save</b>: save 1D data in txt from shown spectrum.<br>")
            self.sysReturn(msg)

        elif text == "h":
            self.sysReturn(text, "v")
            i = self.history_log.size
            if i > 0:
                # TODO: Flexible display?
                his_text = self.history_log.to_string(index_names=False, index=False, header=False, max_rows=10)
            else:
                his_text = "Blue Magpie has not executed any command yet."
            self.sysReturn(his_text)

        elif text == 'p':
            self.sysReturn(text, "v")
            # adjust return msg format of parameter index
            movable = ', '.join(param_index0)
            immovable = ', '.join(non_movables)
            self.sysReturn("movable : {}".format(movable))
            self.sysReturn("immovable : {}".format(immovable))

        # elif "shut" in text[:5]:
        #     space = text.count(' ')
        #     sptext = text.split(' ')
        #     if space == 1: # e.g. shut 0
        #         if sptext[1] in ['0', '1']:
        #             self.sysReturn(text,"v", True)
        #             param['shutter'] = float(sptext[1]) # sptext[1] is the parameter to be moved; sptext[2] is value to moved.
        #             if sptext[1]=='0': shutt ='close'
        #             if sptext[1]=='1': shutt ='open'
        #             self.sysReturn("The shutter is " + shutt)
        #         else:
        #             self.sysReturn(text,"iv")
        #             self.sysReturn('shutter parameter has to be 0 ot 1 for close and open, respectively.', "err")
        #     else:
        #         self.sysReturn(text,"iv")
        #         self.sysReturn('input error. use:   shut  0 or 1', 'err')

        elif 'img' in text[:4]:
            space = text.count(' ')
            sptext = text.split(' ')
            if text != 'img':
                t = sptext[1]
            else:
                t = 2 # default exposure time = 2
                space = 1
            if space == 1 and self.checkFloat(t):  # e.g. img t
                BUSY = True
                self.sysReturn(text, "v", True)
                WorkingSTATUS = "Taking image... "
                CountDOWN = float(t)+3.5
                pvl.ccd("exposure", t)
                self.exposethread = Expose(float(t), 0)
                self.exposethread.cmd_msg.connect(self.sysReturn)
                self.exposethread.get.connect(img_global.getData)
                self.exposethread.show.connect(img_global.showImg)
                self.exposethread.finished.connect(self.threadFinish)
                self.exposethread.finished.connect(self.imgFinish)
                self.exposethread.start()

            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   img(+ exposure_time)", "err")

        elif text == 'rixs' or text[:5] == 'rixs ':
            # All sequence below should be organized as function(text) which returns msg & log
            space = text.count(' ')
            sptext = text.split(' ')
            # check format
            if space == 2:  # e.g. rixs t n
                if self.checkFloat(sptext[1]) and self.checkInt(sptext[2]):
                    file_no += 1
                    # t as exposure time ; n as number of images.
                    t = float(sptext[1])
                    n = int(sptext[2])
                    self.sysReturn(text, "v", True)
                    tt = datetime.datetime.now()
                    self.sysReturn('RIXS %s begins at %s'%(file_no, tt.strftime("%c")))
                    self.rixsthread = Rixs(t, n)
                    self.rixsthread.cmd_msg.connect(cmd_global.sysReturn)
                    self.rixsthread.finished.connect(self.threadFinish)
                    self.rixsthread.setplot.connect(spectrum_global.setRIXSplot)
                    self.rixsthread.savespec.connect(spectrum_global.saveSpec)
                    self.rixsthread.start()
                else:
                    self.sysReturn(text, "iv")
                    self.sysReturn("Both t and n need to be numerical numbers.", "err")
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   rixs t n", "err")

        elif text == 'load':
            self.sysReturn(text, "v", True)
            self.fileOpen()

        elif text == 'save':
            self.sysReturn(text, "v", True)
            name = QFileDialog.getSaveFileName(self, 'Save File')
            print('name : {}'.format(name[0]))
            if type(name[0]) == str:
                self.saveName.emit(name[0])

        elif text == 'setref':
            self.sysReturn(text, "v", True)
            self.setref.emit(True)

        elif text == 'r':
            self.sysReturn(text, "v")
            msg = 'parameter ranges:\n'

            for i in range(param_range.size):
                msg += str(param_range.index[i]) + ' = ' + str(param_range[i]) + '\n'
            self.sysReturn(msg)

        # elif "s2" in text[:3]:
        #     space = text.count(' ')
        #     sptext = text.split(' ')
        #     if space == 1:  # e.g. s1 5
        #         if sptext[1] in ['5', '10', '20', '50', '100', '150']:
        #             self.sysReturn(text, "v", True)
        #             param['s2'] = float(
        #                 sptext[1])  # sptext[1] is the parameter to be moved; sptext[2] is value to moved.
        #             self.sysReturn("The exit slit opening has been set to " + sptext[1])
        #         else:
        #             self.sysReturn(text, "iv")
        #             self.sysReturn('s2 opening is discrete, 5, 10, 20, 50, 100 & 150', "err")
        #     else:
        #         self.sysReturn(text, "iv")
        #         self.sysReturn("input error. use:   s2 opening (5, 10, 20, 50, 100 or 150)", "err")

        # mv function
        elif text[:3] == 'mv ':
            space = text.count(' ')
            sptext = text.split(' ')
            if space == 2:  # e.g. mv x 1234
                p, v = sptext[1], sptext[2]
                if p in param_index0:
                    try:
                        v = eval(v)
                        if self.checkFloat(v):
                            if self.check_param_range(p, v) != 'OK':
                                self.sysReturn(text,'iv')
                                self.sysReturn(self.check_param_range(p, v), 'err')
                            else:
                                self.sysReturn('mv {0} {1}'.format(p, v), "v", True)
                                self.movethread = Move(p, float(v))  # check if finished or not
                                self.movethread.msg.connect(self.sysReturn)
                                self.movethread.finished.connect(self.threadFinish)
                                self.movethread.start()
                        else:
                            self.sysReturn(text, "iv")
                            self.sysReturn("{0} is not float.".format(v), "err")
                    except:
                        self.sysReturn(text, "iv")
                        self.sysReturn("failed to evaluate target position {0}.".format(sptext[2]), 'err')
                else:
                    self.sysReturn(text, "iv")
                    self.sysReturn("parameter \'" + p + "\' is invalid; type \'p\' to list valid parameters", "err")
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   mv parameter value", "err")

        elif text[:4] == 'mvr ':
            space = text.count(' ')
            sptext = text.split(' ')
            if space == 2:  # e.g. mvr x 1234
                p, vr = sptext[1], sptext[2]
                if p in param_index0:
                    try:
                        if self.checkFloat(eval(vr)):
                            v = get_param(p)+vr
                            if self.check_param_range(p, v) != 'OK':
                                self.sysReturn(text,'iv')
                                self.sysReturn(self.check_param_range(p, v), 'err')
                            else:
                                self.sysReturn('mvr {0} {1}'.format(p, eval(vr)), "v", True)
                                self.movethread = Move(p, float(v))  # check if finished or not
                                self.movethread.msg.connect(self.sysReturn)
                                self.movethread.finished.connect(self.threadFinish)
                                self.movethread.start()
                        else:
                            self.sysReturn(text, "iv")
                            self.sysReturn("{0} is not float.".format(vr), "err")
                    except:
                        self.sysReturn(text, "iv")
                        self.sysReturn("failed to evaluate target position {0}.".format(sptext[2]), 'err')
                else:
                    self.sysReturn(text, "iv")
                    self.sysReturn("parameter \'" + p + "\' is invalid; type \'p\' to list valid parameters", "err")
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   mv parameter value", "err")

        elif text[:5] == 'spec ':
            space, sptext = text.count(' '), text.split(' ')
            if space == 2:
                p, v = sptext[1], sptext[2]
                if p in ['x1', 'x2']:
                    if self.checkInt(v) and 1023 >= int(v) >= 0:
                            self.setfactor.emit(str(p), int(v))
                            self.sysReturn(text, "v", True)
                            self.sysReturn('spec {0} set to {1}'.format(p, eval(v)))
                    else:
                        self.sysReturn(text, "iv")
                        self.sysReturn("{} should be integer or in range(0, 1023)".format(v), "err")
                elif p in ['f', 'g']:
                    if self.checkFloat(v):
                        self.setfactor.emit(str(p), float(v))
                        self.sysReturn(text, "v", True)
                        self.sysReturn('spec {0} set to {1}'.format(p, eval(v)))
                elif p in ['d1', 'd2']:
                    if self.checkFloat(v):
                        self.setfactor.emit(str(p), float(v))
                        self.sysReturn(text, "v", True)
                        self.sysReturn('spec {0} set to {1}'.format(p, eval(v)))
                else:
                    self.sysReturn(text, "iv")
                    self.sysReturn("invalid parameter.  try: x1/x2/d1/d2/f/g", "err")
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   spec x1/x2/d1/d2/f/g value", "err")

        elif text[:5] == 'bkrm ':
            space, sptext = text.count(' '), text.split(' ')
            if space == 1 and sptext[1] in ['on', 'off']:
                self.sysReturn(text, "v", True)
                self.sysReturn("background subtraction turned {}".format(sptext[1]))
                if sptext[1] == 'on':
                    self.setfactor.emit('bkrm', True)
                elif sptext[1] == 'off':
                    self.setfactor.emit('bkrm', False)
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   bkrm on/off", "err")

        elif text[:4] == 'fft ':
            space, sptext = text.count(' '), text.split(' ')
            if space == 1 and sptext[1] in ['on', 'off']:
                self.sysReturn(text, "v", True)
                self.sysReturn("fast fourier transform after spike removal turned {}".format(sptext[1]))
                if sptext[1] == 'on':
                    self.setfactor.emit('fft', True)
                elif sptext[1] == 'off':
                    self.setfactor.emit('fft', False)
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   fft on/off", "err")

        elif text[:6] == 'spike ':
            space, sptext = text.count(' '), text.split(' ')
            if space == 1 and sptext[1] in ['on', 'off']:
                self.sysReturn(text, "v", True)
                self.sysReturn("spike removal turned {}".format(sptext[1]))
                if sptext[1] == 'on':
                    self.setfactor.emit('spike', True)
                elif sptext[1] == 'off':
                    self.setfactor.emit('spike', False)
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   spike on/off", "err")

        elif text[:2] == 'd ':
            space, sptext = text.count(' '), text.split(' ')
            if space == 1 and sptext[1] in ['on', 'off']:
                self.sysReturn(text, "v", True)
                self.sysReturn("discrimination turned {}".format(sptext[1]))
                if sptext[1] == 'on':
                    self.setfactor.emit('d', True)
                elif sptext[1] == 'off':
                    self.setfactor.emit('d', False)
            else:
                self.sysReturn(text, "iv")
                self.sysReturn("input error. use:   d on/off", "err")

        # scan function
        # command format: scan [plot1 plot2 ...:] scan_param begin end step dwell
        elif text[:5] == 'scan ':
            # if the input command is only 'scan' but not parameters check != 'OK',
            check = self.check_param_scan(text)  # checking input command and parameters
            if check == 'OK':
                self.sysReturn(text, 'v', True)  # "v": log text in history; True: mark blue
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
                    start_time = datetime.datetime.now()
                    self.sysReturn('Scan %s begins at %s'%(file_no, start_time.strftime("%c")))
                    self.scanthread = Scan(plot, scan_param, x1, x2, step, dwell, n, 1, False)
                    self.scanthread.scan_plot.connect(spectrum_global.scanPlot)
                    self.scanthread.cmd_msg.connect(cmd_global.sysReturn)
                    self.scanthread.set_data.connect(spectrum_global.liveplot)
                    self.scanthread.finished.connect(self.threadFinish)
                    self.scanthread.start()
                else:
                    self.sysReturn(text, "iv")
                    check_param = check_param1 if (check_param1 != 'OK') else check_param2
                    self.sysReturn(check_param, "err")
            else:
                # Return error message
                self.sysReturn(text, "iv")
                self.sysReturn(check, "err")

        elif text[:5] == "tscan":
            if self.checkTscanformat(text):
                [p, dt, n]=text.split(" ")[1:]
                self.sysReturn(text, 'v', True)
                timestamp = QTime.currentTime()
                t0 = timestamp.toString()
                self.sysReturn('tscan {0} begins at {1}'.format(file_no, t0))
                self.tscan = Tscan(p, t0, float(dt), int(n))
                self.tscan.cmd_msg.connect(self.sysReturn)
                self.tscan.setplot.connect(spectrum_global.tscanPlot)
                self.tscan.plot.connect(spectrum_global.liveplot)
                self.tscan.finished.connect(self.threadFinish)
                self.tscan.start()

        elif text[:3] == "xas":
            if self.checkXasformat(text):
                [e1, e2, dE, dwell] = text.split(" ")[1:5] # N times of scan
                N = 1 if text.count(' ') ==4 else text.split(" ")[-1]
                dE = abs(float(dE)) * np.sign(float(e2) - float(e1))  # step is negative if x1 > x2
                dwell = float(dwell)
                n = int(abs((float(e2) - float(e1)) / dE)) # n steps
                file_no += 1
                start_time = datetime.datetime.now()
                self.sysReturn(text, 'v', True)
                self.sysReturn('XAS %s begins at %s' % (file_no, start_time.strftime("%c")))
                self.xas = Xas(float(e1), float(e2), dE, dwell, n, int(N))
                self.xas.cmd_msg.connect(self.sysReturn)
                self.xas.xas_plot.connect(spectrum_global.setXASdata)
                self.xas.final_plot.connect(spectrum_global.plotXAS)
                self.xas.finished.connect(self.threadFinish)
                self.xas.start()


        elif text == "macro":
            # popup window
            self.sysReturn(text, "v")
            self.popup.emit()

        elif text[:3] == "do ":
            space = text.count(' ')
            sptext = text.split(' ')
            name = sptext[1]
            # read macro file
            if space is 1:
                self.doMacro(name)
            else:
                self.sysReturn(text, 'iv')
                self.sysReturn("input error. use:   do macroname","err")

        # TODO: wait command test after Thread
        elif text[:5] == "wait ":
            BUSY = True
            space = text.count(' ')
            sptext = text.split(' ')
            # set delay time
            if space == 1:
                t = sptext[1]
                if self.checkFloat(t):
                    self.sysReturn(text, "v", True)
                    self.sysReturn("wait for %s seconds..." %t)
                    self.pause[float].emit(float(t))
                else:
                    self.sysReturn(text, 'iv')
                    self.sysReturn("input error. Format: wait time", "err")

        elif text != "":
            self.sysReturn(text, "iv")
            self.sysReturn("Type 'help' to list commands", "err")

    def threadFinish(self):
        global BUSY, WorkingSTATUS, CountDOWN
        BUSY = False
        WorkingSTATUS = ""
        CountDOWN = 0

    def macroStart(self):
        global MACROBUSY
        MACROBUSY = True

    def macroFinish(self):
        global MACROBUSY, BUSY, WorkingSTATUS, CountDOWN
        MACROBUSY = False
        BUSY = False
        WorkingSTATUS = ""
        CountDOWN = 0

    def imgFinish(self):
        self.sysReturn("img taken (data not saved).")

    def checkFloat(self, x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    def checkInt(self, x):
        try:
            int(x)
            return True
        except ValueError:
            return False

    def check_param_range(self, param_name, param_value):
        if self.checkFloat(param_value):
            global param_range
            # if (parame_name in param_index0) and self.checkFloat(param_value) == True:
            j = float(param_value)
            if min(param_range[param_name]) <= j and j <= max(param_range[param_name]):
                check_msg = 'OK'
            else:
                check_msg = ('Oops! ' + param_name + ' value was out of range; type \'r\' to show parameter ranges.')
        else:
            check_msg = (param_name + " value must be number or float", "err")
        return check_msg

    def check_param_scan(self, text):
        global param, param_index
        # input text format: scan scan_param begin end step dwell
        # or  scan plot1 plot2 ....: scan_param begin end step dwell
        check_format = (' ')
        print('input command =', text)
        if text.find(',') == -1:
            sptext = text[5:].split(' ')  # scan_param 1 10 1 0.1
            space = text.count(' ')  # space =5, e.g. scan x 1 10 2 0.1
            c = 5
            plot = ['Iph']
        else:
            c = text.find(',')
            space = text[c:].count(' ')  # space = 5, after truncating "scan y z ...:" => e.g. , x 1 10 2 0.1
            sptext = text[c + 2:].split(' ')  # scan_param 1 10 1 0.1
            plot = text[5:c].split(' ')  # list of detection parameter

        if text[c + 1:].find(',') == -1 and space == 5:
            if (sptext[0] != '') and (len(sptext) == 5):
                j = 0  # check index
                for i in range(4):  # i from 0 to 3
                    if self.checkFloat(sptext[i + 1]):j += 1.0
                if j == 4:
                    if sptext[0] in param_index0:
                        if float(sptext[4]) > 0:  # float(sptext[4]) assigns dwell time
                            check_format = ('OK')
                        else:
                            check_msg = ("dwell time must be positive.")
                    else:
                        check_msg = ("parameter \'" + sptext[0] + "\' is invalid; type \'p\' to list valid parameters")
                else:
                    check_msg = ("parameter values are invalid; \'begin end step dwell\' shoiuld be numeric.")
            else:
                check_msg = ("format: scan [plot1 plot2 .. ,] parameter begin end step dwell_time")
        else:
            check_msg = ("format: scan [plot1 plot2 ... ,] parameter begin end step dwell_time")

        # checking if dection parameters have been correctly selected
        j = 0  # check index
        for i in range(len(plot)):  # i from 0 to len(plot)-1
            if (plot[i] in param_index) or (plot[i] == 'Iph'): j += 1.0
        #
        if j == len(plot) and j <= 5:  # max plot no. = 5
            check_plot = 'OK'
        else:
            check_plot = 'not OK'

        if check_format == 'OK' and check_plot == 'OK':
            check_msg = ('OK')
        elif check_format == 'OK' and check_plot != 'OK':
            check_msg = ('invalid plotting parameters')

        print('scan paramter check:', check_msg)
        return check_msg

    def checkTscanformat(self, text): #timescan, p, dt, n
        sptext = text.split(' ')
        if sptext[0] != 'tscan' or text.count(' ') != 3:
            self.sysReturn(text, 'iv')
            self.sysReturn('input error. Format: tscan p dt n', 'err')
            return False
        [p, dt, n] = sptext[1:]
        if p not in param_index:
            self.sysReturn(text, 'iv')
            self.sysReturn('p: {} is not a scannable parameter'.format(n), 'err')
            return False
        if not self.checkFloat(dt):
            self.sysReturn(text, 'iv')
            self.sysReturn('{} is not float.'.format(x), 'err')
            return False
        if not self.checkInt(n):
            self.sysReturn(text, 'iv')
            self.sysReturn('{} is not float.'.format(x), 'err')
            return False
        return True

    def checkXasformat(self, text):
        sptext = text.split(' ')
        if sptext[0] == 'xas':
            if text.count(' ') == 4:
                [e1, e2, de, dt] = sptext[1:]
                n = 1
            elif text.count(' ') == 5: # check format = xas Ei Ef dE dt n
                [e1, e2, de, dt, n] = sptext[1:]

                for x in [e1, e2, de, dt]: #check float: e1, e2, de, dt
                    if self.checkFloat(x) == False:
                        self.sysReturn(text, 'iv')
                        self.sysReturn('{} is not float.'.format(x), 'err')
                        return False
                if self.checkInt(n):
                    if self.check_param_range('agm', e1) == 'OK' and self.check_param_range('agm', e2) == 'OK':
                        return True
                    else:
                        self.sysReturn(text, 'iv')
                        if self.check_param_range('agm', e1) != 'OK': self.sysReturn(self.check_param_range('agm', e1),'err')
                        else: self.sysReturn(self.check_param_range('agm', e2),'err')
                        return False
                else:
                    self.sysReturn(text, 'iv')
                    self.sysReturn('n: {} should be integer'.format(n),'err')
                    return False
            else:
                self.sysReturn(text, 'iv')
                self.sysReturn('input error. Format: xas Ei Ef dE dt n', 'err')
                return False
        else:
            self.sysReturn(text,'iv')
            self.sysReturn('input error. Format: xas Ei Ef dE dt n','err')
            return False

        '''
        check function for Wait command
        '''

    def inputPause(self, t):
        global BUSY
        BUSY = True
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self.threadFinish)
        timer.start(1000 * float(t))  # count for t seconds then open user input

    def commandLock(self):
        timer = QTimer(self)
        timer.setSingleShot(False)
        timer.timeout.connect(self.lockInput)
        timer.start(100)  # repeat every 0.1 second

    def lockInput(self):
        if MACROBUSY:
            self.command_input.setDisabled(MACROBUSY)
        else:
            self.command_input.setDisabled(BUSY)
            if BUSY == False:
                self.command_input.setFocus()
    # not necessary
    def doMacro(self, name):
        macro_name = "%s%s.txt"%(macro_dir, name) # directory
        if os.path.exists(macro_name): # check file exist
            self.sysReturn('do %s'%name, "v", True)
            self.sysReturn("macro begins: %s.txt"%name)
            if self.macro == None: self.popup.emit()
            self.macrostarted.emit(macro_name) # to inform macro window which file is running and activate edit button
            self.macrothread = Macroloop(macro_name)
            self.macrothread.finished.connect(self.macroFinish)
            self.macrothread.finished.connect(self.macro.macroFinished)
            self.macrothread.number.connect(self.macro.macroNum)
            self.macrothread.started.connect(self.macroStart)
            self.macrothread.msg.connect(self.sysReturn)
            self.macrothread.send.connect(self.send)
            self.macrothread.setText.connect(self.command_input.setText)
            self.macrothread.start()
        else:
            self.sysReturn("macro file name: {0} not found in {1}.".format(name, macro_dir), "err")

    def fileOpen(self):
        filename = QFileDialog.getOpenFileName(self, 'Open image file',
                                            directory=img_dir
                                            , options=QFileDialog.ReadOnly)
        if filename != ('', ''):
            file = filename[0]
        try:#send directory
            self.loadimage.emit(file)
            self.setrixsplot.emit(os.path.basename(file))
            self.setrixsdata.emit()
            self.sysReturn("file opened: {0}".format(os.path.basename(file)))
        except:
            print('no file opened')

class ImageWidget(QWidget):
    setrixsdata = pyqtSignal(np.ndarray, bool, bool)
    errmsg = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        # Default Image
        a = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        npa = np.asarray(a)
        renpa = np.reshape(npa, (2, 5), order='F')
        self.imgdata = renpa  # default image when program startup
        # replace by RGB pixel Magpie picture?

        plt = pg.PlotItem(labels={'bottom': ('x pixel', ''), 'left': ('y pixel', '')})
        plt.getViewBox().setRange(yRange=(1, 2048), xRange=(1, 1024), disableAutoRange=False)
        plt.setLimits(minXRange=4, maxXRange=8192, minYRange=4, maxYRange=8192)

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

        self.showImg()
        # Widget layout
        self.status_bar = QLabel(self)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addWidget(self.status_bar)
        self.layoutVertical.addWidget(self.imv)
        # cross hair
        self.vLine = pg.InfiniteLine(angle=90, pen=pg.mkPen('w', width=0.5), movable=False)
        self.hLine = pg.InfiniteLine(angle=0, pen=pg.mkPen('w', width=0.5), movable=False)
        plt.addItem(self.vLine, ignoreBounds=True)
        plt.addItem(self.hLine, ignoreBounds=True)

        def mouseMoved(pos):
            data = self.imv.image
            nCols, nRows = data.shape
            mousePoint = plt.getViewBox().mapSceneToView(pos)
            row, col = int(mousePoint.y()), int(mousePoint.x())
            value = 0
            # update cross hair
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

            if (0 <= row < nRows) and (0 <= col < nCols):
                value = data[col, row]
            else:
                pass
            self.status_bar.setText("pixel = ({:d}, {:d}), z = {!r}".format(col, row, value))

        self.imv.scene.sigMouseMoved.connect(mouseMoved)

    def getData(self, rixs =False, num=0):
        if checkSafe('ccd'):
            raw_img = pvl.ccd("image")
            print(raw_img)
            img_list = np.asarray(raw_img)  # convert raw image to 1d numpy array
            img_np = np.reshape(img_list, (1024, 2048), order='F')  # reshape from 1d to 2d numpy array
        else:
            # else
            raw_img = np.random.uniform(0, 500 + 1, 1024 * 2048)
            img_list = np.asarray(raw_img)
            img_np = np.reshape(img_list, (1024, 2048), order='F')
        self.imgdata = img_np
        if rixs:
            self.saveImg(num)
            self.plotSpectrum(True, True)

    def saveImg(self, img_number):
        '''
        img_number = int
        save file as txt with header of parameters
        name format example: rixs_20190508_img001.img
        '''
        header = self.getHeader()                           # string of current parameter series
        data = self.imgdata if not ref else self.refimage   # 2d image
        # fill img_number string with 3 digits in normal(not ref) case
        if not ref:
            tail = 'img{}'.format(str(img_number).zfill(3))
        else:
            tail = 'ref'

        file_name0 = "rixs_{}_{}_{}.img".format(dir_date, file_no, tail)
        file_name = img_dir + file_name0                    # for saving in correct dir
        # append parameters as header
        np.savetxt(file_name, data, fmt='%9d', delimiter=',', header=header) # image data format
        cmd_global.sysReturn('image data saved: {}'.format(file_name0))

    def saveRef(self, ref=False):
        '''
        img_number = int
        save file as txt with header of parameters
        name format example: rixs_20190508_img001.img
        '''
        header = self.getHeader()                           # string of current parameter series
        data = self.refimage   # 2d image
        # fill img_number string with 3 digits in normal(not ref) case
        tail = 'ref'
        file_name0 = "rixs_{}_{}_{}.img".format(dir_date, file_no, tail)
        file_name = img_dir + file_name0                    # for saving in correct dir
        # append parameters as header
        np.savetxt(file_name, data, fmt='%9d', delimiter=',', header=header) # image data format
        cmd_global.sysReturn('image data saved: {}'.format(file_name0))

    def getHeader(self):
        # record param from global pd.Series
        index = ','.join(param.index.tolist())
        value = ','.join(['{:.2f}'.format(x) for x in param.tolist()])
        header_text = '{}\n{}'.format(index, value)
        return header_text

    def showImg(self):
        self.imv.setImage(self.imgdata)

    def setBkgd(self, data, bkgd=True):
        try:
            self.imgdata = data
            if bkgd:
                self.refimage = np.copy(data)
        except:
            print('failed to set background.')
        self.showImg()

    def loadImg(self, filename):
        try:
            raw_data = np.genfromtxt(filename, delimiter=',', skip_header=2)
            data = np.asarray(raw_data)
            print('size = ', data.size)
            print(data)
            if data.size > 2097152:
                data = data[np.logical_not(np.isnan(data))]
                print(data, data.size)
                data = np.take(data, list(range(0, 2097152))) #take 1024*2048 only
                print(data, data.size)
            print('size = ', data.size)
            print(data)
            self.imgdata = np.reshape(data, (1024, 2048), order='F')
            self.showImg()
        except:
            print('failed')
            self.errmsg.emit('failed to load data, might be a datashape problem.','err')

    def rixs_sum(self, image_data):
        rixs_tmp = np.zeros((1, 2048), float)

        for i in range(renpa.shape[0]):
            rixs_tmp = rixs_tmp + renpa[i, :]

        print(rixs_tmp.ndim, rixs_tmp.shape, rixs_tmp.dtype)
        print(rixs_tmp)

    def plotSpectrum(self, accum=False, save=False):
        data = np.copy(self.imgdata)
        self.setrixsdata.emit(data, accum, save)

    def enterEvent(self, event):
        self.status_bar.show()
        self.vLine.show()
        self.hLine.show()

    def leaveEvent(self, event):
        self.status_bar.clear()
        self.vLine.hide()
        self.hLine.hide()


class SpectrumWidget(QWidget):
    errmsg = pyqtSignal(str,str)
    msg = pyqtSignal(str)
    setbkgd = pyqtSignal(np.ndarray)
    showimg = pyqtSignal(np.ndarray, bool)
    saveRef = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__widgets__()
        self.__layout__()
        # cross hair
        self.vLine = pg.InfiniteLine(angle=90, pen=pg.mkPen('w', width=0.5), movable=False)
        self.hLine = pg.InfiniteLine(angle=0, pen=pg.mkPen('w', width=0.5), movable=False)
        self.plotWidget.addItem(self.vLine, ignoreBounds=True)
        self.plotWidget.addItem(self.hLine, ignoreBounds=True)
        # legend
        self.legend = self.plotWidget.addLegend((50, 30), offset=(450, 150))
        self.legenditems = []
        self.legend.setParentItem(self.plotWidget.plotItem)
        # rixs parameters
        self.data = [random.random() for i in range(2000)]
        self.curve = [None, None, None, None, None]
        self.rixs_x = list(range(0, 2048))
        self.rixs_y = np.empty(2048)
        self.ref_2d = np.zeros([1024,2048])
        self.rixs_n = 0
        self.rixs_name = None
        self.ref_x = list(range(0, 2048))
        self.ref_y = np.empty(2048)
        self.ref_name = None
        self.spikefactor= 1.5 #spike removal function discrimination factor
        self.d1 = 20 # discrimination factor for setref
        self.d2 = 200
        self.gfactor = 40 # gaussian factor
        self.x1, self.x2 = 0, 1023
        self.fft = False
        self.analyze = False #flag: False = scan/tscan/xas, True = rixs/load
        self.spikeremove = True #flag to apply spike removal while data processing 
        self.bkgdsubstract = False #flag to apply background substraction while data processing
        self.discriminate = False

        
        def mouseMoved(pos):
            mousePoint = self.plotWidget.getViewBox().mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.pos_bar.setText("pos = ({:.2f}, {:.2f})".format(mousePoint.x(), mousePoint.y()))

        self.plotWidget.scene().sigMouseMoved.connect(mouseMoved)
        self.plotWidget.plot(self.data)

    def __widgets__(self):
        self.plotWidget = PlotWidget(self)
        self.pos_bar = QLabel(self)
        self.refinfo = QLabel(self)
        self.fftinfo = QLabel(self)
        self.xval = QLabel(self)
        self.spikeinfo = QLabel(self) 
        self.dinfo = QLabel(self)

    def __layout__(self):
        self.layoutHorizontal = QHBoxLayout()
        self.layoutHorizontal.addWidget(self.spikeinfo)
        self.layoutHorizontal.addWidget(self.fftinfo)
        self.layoutHorizontal2 = QHBoxLayout()
        self.layoutHorizontal2.addWidget(self.refinfo)
        self.layoutHorizontal2.addWidget(self.dinfo)
        self.topHorizontal = QHBoxLayout()
        self.topHorizontal.addWidget(self.pos_bar)
        self.topHorizontal.addWidget(self.xval)
        self.layoutVertical = QVBoxLayout(self)
        self.layoutVertical.addLayout(self.topHorizontal)
        self.layoutVertical.addWidget(self.plotWidget)
        self.layoutVertical.addLayout(self.layoutHorizontal)
        self.layoutVertical.addLayout(self.layoutHorizontal2)

    def enterEvent(self, event):
        self.pos_bar.show()
        self.vLine.show()
        self.hLine.show()

    def leaveEvent(self, event):
        self.pos_bar.clear()
        self.vLine.hide()
        self.hLine.hide()

    def clearplot(self):
        if self.legenditems != []:
            for x in self.legenditems:
                self.legend.removeItem(x)
        self.plotWidget.plotItem.clear() # legends not in viewbox
        self.legenditems = []

    #=================================================
    #
    # SCAN - related functions
    #
    #=================================================
    def scanPlot(self, plot, scan_param, x1, x2, xas):
        self.analyze = False
        self.factorsinfo(False)
        if xas:
            title_plot = 'XAS {0}'.format(int(param['f']))
        else:
            title_plot = 'Scan {0} : scanning {1},  plotting {2}'.format(int(param['f']), scan_param, plot[0])
        for i in range(0, len(plot)):
            if i > 0: title_plot += ', ' + plot[i]
        self.clearplot()
        self.legenditems = plot
        self.plotWidget.plotItem.setTitle(title=title_plot)
        self.plotWidget.plotItem.setXRange(float(x1), float(x2), padding=None, update=True)
        self.plotWidget.plotItem.setLabel('bottom', text=scan_param)
        self.plotWidget.plotItem.setLabel('left', text='Intensity', units='A' if plot == 'Iph' else None)
        color = ['g', 'b', 'w', 'r', 'y']
        for i in range(0, len(plot)):
            self.curve[i] = self.plotWidget.plot([], [], pen=pg.mkPen(color=color[i], style=1, width=1),
                                                 name=plot[i])
        if xas:
            self.xas_curve = self.plotWidget.plot(self.xas_x, self.xas_y, pen=pg.mkPen(width=1),
                                                  name="mean I<sub>ph</sub>")
            self.legenditems.append("mean I<sub>ph</sub>")

    def tscanPlot(self, p, dt, n):
        self.analyze = False
        self.factorsinfo(False)
        self.clearplot()
        self.legenditems = [p]
        title = 'time scan {0} : {1}'.format(int(param['f']), p)
        self.plotWidget.plotItem.setTitle(title=title)
        self.plotWidget.plotItem.setXRange(0, float(dt * n), padding=None, update=True)  # t1= 0, t2= dt*n
        self.plotWidget.plotItem.setLabel('bottom', text='time (sec)')
        self.plotWidget.plotItem.setLabel('left', text=p)
        color = ['g', 'b', 'w', 'r', 'y']  # extendable
        self.curve[0] = self.plotWidget.plot([], [], pen=pg.mkPen(color=color[0], style=1, width=1), name=p)


    def liveplot(self, i, list_x, series_y):
        self.curve[i].setData(list_x, series_y)

    def setXASdata(self, sum_x, sum_y):
        self.xas_x = sum_x
        self.xas_y = sum_y

    def plotXAS(self):
        self.plotWidget.plotItem.clear()
        self.legend.removeItem('Iph')
        self.legenditems = ["mean I<sub>ph</sub>"]
        self.xas_curve = self.plotWidget.plot(self.xas_x, self.xas_y, pen=pg.mkPen(width=1))  # default pen = grey.
    # =================================================
    #
    # RIXS - related functions
    #
    # =================================================
    def setRIXSplot(self, name=None, y1=0, y2=2048):
        self.analyze = True
        self.factorsinfo()
        self.rixs_x = list(range(0, 2048))
        self.rixs_y = np.empty(2048)
        self.rixs_n = 0
        self.clearplot()
        self.legenditems = ['rixs']
        if name == None:
            name = "rixs {0}".format(file_no)
        self.rixs_name = name
        self.plotWidget.plotItem.setTitle(title=name)
        self.plotWidget.plotItem.setXRange(float(y1), float(y2), padding=None, update=True)
        self.plotWidget.plotItem.setLabel('bottom', 'y-pixel')
        self.plotWidget.plotItem.setLabel('left', text='Intensity (arb. units)')
        self.rixs = self.plotWidget.plot([], [], pen=pg.mkPen(color='g',style=1,width=1),name='rixs')

    def setRIXSdata(self, array, accum=False, save=False):
        self.data = np.copy(array)
        self.plotRIXS(accum, save)

    def plotRIXS(self, accum=False, save=False):  #processing
        data = np.copy(self.data) #avoid removing raw data
        if self.spikeremove:
            if self.spikefactor >= 1.05:
                data = spikeRemoval(data, self.x1, self.x2, self.spikefactor)[0] # save setref 2d image file
            else:
                self.errmsg.emit('spike factor should be bigger than 1.1','err')
        if self.bkgdsubstract:
            data = np.subtract(data, self.ref_2d) # default ref_2d = array of 0
        if self.discriminate:
            data[data < self.d1] = 0  # discrimination in Spectrum Widget
            data[data > self.d2] = 0
        senddata = np.copy(data)      # avoid inconsistency between data and 2D-image
        self.showimg.emit(senddata, False)              # show 2D in ImageWidget
        data = np.sum(data[self.x1:self.x2,:], axis=0)  # sum along x-axis, x1 to x2
        data = self.jointRemoval(data.flatten())
        if self.fft:
            data= low_pass_fft(data) #low-pass using fft. step= sample spacing (inverse of the sampling rate)
        
        if save: self.saveSpec()   # save = True only in Rixs(QThread), could be extended in another commandt
        if accum: # accum = True only in Rixs(QThread)
            self.rixs_y = np.average([self.rixs_y, data], axis = 0, weights=[self.rixs_n, 1])
            self.rixs_n += 1
        else:
            self.rixs_y = data
        self.rixs.setData(x=self.rixs_x[100:], y=self.rixs_y[100:]) # cut 0-117

    def jointRemoval(self, data):
        avg = np.mean(data) #data  = 1d array
        h = (data[1035] - avg)*0.80
        for i in range(1030, 1040):
            data[i] = data[i] - (h * np.exp(-((i - 1035) ** 2) / 2))
        return data

    def saveSpec(self, final=False):
        spec_number = str(1+self.rixs_n).zfill(3) if not final else ""
        filename="rixs_{0}_{1}_{2}".format(dir_date, file_no, spec_number)
        np.savetxt(data_dir + filename, self.rixs_y, fmt='%.2f', delimiter=' ')
        self.msg.emit('rixs data saved in {0}.txt'.format(filename))
        if final: self.saveRef.emit(True)

    def saveName(self, name=None):
        if name == None:
            name = data_dir + dir_date + 'test'
        if not self.analyze:
            print ('currently save spectrum only, not including scan data.')
        else:
            np.savetxt(name, self.rixs_y, fmt='%.2f', delimiter=' ')
            self.msg.emit('spectrum saved in {0}.txt'.format(os.path.basename(name)))

    def getHeader(self):
        pass

    def setRef(self, bool= True):
        if bool:
            if self.rixs_name != None:
                self.ref_name = self.rixs_name
                self.msg.emit('reference data set: {0}'.format(self.ref_name))
                data = spikeRemoval(self.data, self.x1, self.x2, 1.05)[0]
                self.ref_2d = gaussian_filter(data, sigma = self.gfactor)
                print('bkgd')
                print(self.ref_2d)
                self.setbkgd.emit(self.ref_2d)
                data = np.sum(self.ref_2d, axis=0)
                self.ref_y = data.flatten()
                self.rixs.setData(x=self.rixs_x[100:], y=self.ref_y[100:])
                self.bkgdsubstract = False
            else:
                self.errmsg.emit('no valid spectrum to set reference.','err')
        self.factorsinfo()

    def setFactor(self, p, v):
        if p == 'x1': self.x1 = v
        elif p == 'x2': self.x2 = v
        elif p == 'f': self.spikefactor = v
        elif p == 'spike': self.spikeremove = v
        elif p == 'bkrm':
            self.bkgdsubstract = v
            if self.bkgdsubstract == False and self.discriminate == True:
                self.discriminate = False # close d when turn off bkgd
        elif p == 'd': self.discriminate = v
        elif p == 'd1': self.d1 = v
        elif p == 'd2': self.d2 = v
        elif p == 'g': self.gfactor = v
        elif p == 'fft': self.fft = v
        else: print('invalid factor for setFactor function.')
        self.factorsinfo() # refresh parameter display
        if self.analyze : self.plotRIXS()
        # trigger processing if last plot is not scan/tscan/xas

    def factorsinfo(self, set=True):
        spikeflag = "<font color=green>ON</font>" if self.spikeremove else "<font color=red>OFF</font>"
        bkgdflag = "<font color=green>ON</font>" if self.bkgdsubstract else "<font color=red>OFF</font>"
        dflag = "<font color=green>ON</font>" if self.discriminate else "<font color=red>OFF</font>"
        fftflag = "<font color=green>ON</font>" if self.fft else "<font color=red>OFF</font>"
        if set:
            self.xval.setText('<p align=\"right\">x1 = {0}, x2 = {1}</p>'.format(self.x1, self.x2))
            self.spikeinfo.setText('spike factor [{}] = {} '.format(spikeflag, self.spikefactor))
            self.refinfo.setText('background [{}] = {}'.format(bkgdflag, self.ref_name))
            self.fftinfo.setText('<p align=\"right\">fast fourier transform [{}]</p>'.format(fftflag))
            self.dinfo.setText('<p align=\"right\">d1 = {}, d2 = {} [{}]</p>'.format(self.d1, self.d2, dflag))
        else:
            self.xval.setText('')
            self.spikeinfo.setText('')
            self.refinfo.setText('')
            self.fftinfo.setText('')
            self.dinfo.setText('')

class Barupdate(QThread):
    refresh = pyqtSignal()

    def __init__(self):
        super(Barupdate, self).__init__()

    def run(self):
        while True:
            self.refresh.emit()
            time.sleep(0.5)

class Statupdate(QThread):
    refresh = pyqtSignal()

    def __init__(self):
        super(Statupdate, self).__init__()

    def run(self):
        while True:
            self.refresh.emit()
            time.sleep(1)

class Move(QThread):
    msg = pyqtSignal(str)
    refresh = pyqtSignal()

    def __init__(self, p, v):
        super(Move, self).__init__()
        self.p = p
        self.v = v
        # list all write PVs and call later

    def run(self):
        global cmd_global, WorkingSTATUS, BUSY
        # p : index(name) of parameter, should be a string; v : range-checked value
        p, v, BUSY= self.p, self.v, True
        if checkSafe(p):  # check device safety
            if (p in param_index0) and (p not in ['x','y','z','Tccd', 'gain','ta','thoffset']):
                pvl.putVal(p, v)
                self.moveCheck(p, v)
            elif p in ['x', 'y']:
                # calculate new x, y
                if p == 'x':
                    y0= get_param('y')
                    xval, yval = self.rotation(x=v, y=y0)
                else:
                    x0= get_param('x')
                    xval, yval = self.rotation(x=x0, y=v)
                print('Calculated x, y = {0}, {1}'.format(xval, yval))
                self.xyzMotor('x', xval)
                print('x(motor) is now at {}'.format(pvl.getVal('x')))
                self.xyzMotor('y', yval)
                print('y(motor) is now at {}'.format(pvl.getVal('y')))

            elif p == 'z':
                self.xyzMotor('z', v)

            elif p == 'ta':
                pvl.putVal('heater', 1)
                pvl.putVal(p, v)
            elif p in ['Tccd', 'gain']:
                pvl.ccd(p, v)
            elif p == 'thoffset':
                pvl.thOffset(True, v)
        else:
            param[p] = v

        self.quit()

    def xyzMotor(self, p, v): # move with x, y, z with backlash
        v = self.transVal(p, v) # target pulse
        print('target pulse = ', v)
        current_pulse = self.transVal(p, pvl.getVal(p))
        print('current pulse = ', current_pulse)
        if abs(v - current_pulse) > 16: # delta pulse > 16
            if pvl.getVal(p) > v:
                print('target position {0} smaller than current position {1}, considering backlash'
                      .format(pvl.getVal(p), v))
                pvl.putVal(p, v - 500)  # considering backlash, put v-500 first
                self.moveCheck(p, v - 500)
            pvl.putVal(p, v)
            self.moveCheck(p, v)
        else:
            print('{0} is close to target :{1},  move aborted.'.format(p, v))

    def transVal(self, p, v): #get correct target value
        if p=="z":
            return int(v*32000)
        else:
            return int(v*8000)

    def rotation(self, x, y):
        print('sample :({0}, {1})'.format(x,y))
        th = pvl.thOffset()*math.pi/180 # rad
        x_new = x*math.cos(th) - y*math.sin(th)
        y_new = x*math.sin(th) + y*math.cos(th)
        print('motor : ({0}, {1})'.format(x_new,y_new))
        return (x_new, y_new)



    def moveCheck(self, p, v):
        t1 = time.time()
        while not pvl.moving(p):
            time.sleep(0.2)
            if pvl.moving(p) or (time.time() - t1) >= 1 or ABORT:
                break
        print('{0} started to move'.format(p))
        time.sleep(0.1)
        while pvl.moving(p) and not ABORT:
            time.sleep(0.2)  # hold here for BUSY flag
            if ABORT:
                if p in ['x','y','z','th','tth']:
                    pvl.stopMove(p)
                break
            if not pvl.moving(p):
                time.sleep(0.2)
                if p in ['th', 'tth']: #for th, tth PV.get() will not get correct number, need this to refresh
                   pvl.caget(p)
                if (abs(pvl.getVal(p) - v) >= 0.02) and (p not in ['x','y','z']):
                    error_message = ("<font color=red>" + p + " not moving correctly, value: "
                                     + str(pvl.getVal(p)) + "</font>")
                    self.msg.emit(error_message)
                break
        print('{0} finished moving'.format(p))

class Scan(QThread):
    scan_plot = pyqtSignal(list, str, float, float, bool)
    set_data = pyqtSignal(int, list, pd.Series)
    data_set = pyqtSignal(list, list) #for xas plot collection
    cmd_msg = pyqtSignal(str)

    def __init__(self, plot, scan_param, x1, x2, step, dwell, n, N, xas):
        super(Scan, self).__init__()
        self.plot, self.scan_param, self.step = plot, scan_param, step
        self.x1, self.x2, self.dwell, self.n = x1, x2, dwell, n
        self.start_point = Move(scan_param, x1)
        self.data_matrix = pd.DataFrame(columns=param_index)
        self.spec_number = N
        self.xas = xas # flag for file saving and other messages

    def run(self):
        global param, WorkingSTATUS, BUSY, CountDOWN
        BUSY = True
        t1 = time.time()
        plot, scan_param, x1, x2 = self.plot, self.scan_param, self.x1, self.x2
        step, dwell, n = self.step, self.dwell, self.n

        x2_new = x1 + step * n
        scan_x = []  # the empty list for the scanning parameter
        WorkingSTATUS = "moving {} ...".format(scan_param)

        # set_param(scan_param, x1)  # set the initial parameter value
        self.start_point.start()
        self.start_point.wait()

        self.scan_plot.emit(plot, scan_param, x1, x2_new, self.xas)
        '''
        Scanning loop
        set scanning parameters = > Data collection (averaging)  => plot data
        '''
        for i in range(n + 1):
            if ABORT:
                print("loop stopped")
                break
            '''
            Remaining time estimate
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

            WorkingSTATUS = ('scanning ' + scan_param + '... ' + str(i + 1) + '/' + str(n + 1))
            CountDOWN = float(remaining_time)

            '''
            Set scanning parameters
            '''
            scan_x.append(x1 + i * step)
            self.WorkerThread = Move(scan_param, scan_x[i])
            self.WorkerThread.start()
            self.WorkerThread.wait()  # wait move finish
            '''
            Data collection
            '''
            t0 = time.time()
            raw_array = np.array([])
            while (time.time() - t0) <= dwell:  # while loop to get the data within dwell time
                if (time.time() - t0) % 0.1 <= 0.0001:
                    #raw_array = np.append(raw_array, pvl.getVal('Iph'))   # Read Iph data through epics

                    for i in range(len(plot)):
                        value = get_param(plot[i])
                        raw_array = np.append(raw_array, value)

            current_param = pd.Series(param)  # generate series

            plot_list = [[], [], [], [], []] # prepare five empty list
            for i in range(raw_array.size):
                plot_list[int(i%len(plot))].append(raw_array[i])

            # average
            for i in range(len(plot)):
                data_array = np.array(plot_list[i])
                data_array = np.unique(data_array)  # remove the overlap
                data_ave = np.mean(data_array)
                current_param[plot[i]] = float(data_ave)  # replace param['Iph'] by averaged data

            current_param[scan_param] = get_param(scan_param) # for datasaving
            current_param['t'] = round(loop_time, 2)
            self.data_matrix.loc[len(self.data_matrix), :] = current_param.tolist()  # appending param to data_matrix
            '''
            plot from data_matrix
            '''
            for i in range(0, len(plot)):
                self.set_data.emit(i, scan_x, self.data_matrix.loc[:, plot[i]])

        '''
        Loop finished
        '''
        WorkingSTATUS = ""
        CountDOWN = 0
        print('[data_matrix]')
        print(self.data_matrix)
        dt = round(time.time() - t1, 3)
        print('time span in senconds=', dt)
        if self.xas: self.data_set.emit(scan_x, self.data_matrix.loc[:, 'Iph'].tolist())  # for accumulation in XAS

        if ABORT:
            self.cmd_msg.emit('Scaning loop has been terminated; time span  = %s'%convertSeconds(dt))
        else:
            if self.xas != True:
                self.cmd_msg.emit('scan %s completed; time span  = %s'%(scan_param ,convertSeconds(dt)))

        '''
        Data saving
        - File name from global, including directory and number
        - Can be saved as .csv or .hdf, but hdf format requires development.
        - Save terminated data?

        TODO: check exist number, don't overwrite old ones.
        '''
        self.saveSpec(self.spec_number, self.xas)
        self.quit()

    def saveSpec(self, spec_number, xas):
        if xas == False:
            filename0="scan_%s_%s_%s" % (dir_date, str(file_no), str(spec_number).zfill(3))
        else:
            filename0="xas_%s_%s_%s" % (dir_date, str(file_no), str(spec_number).zfill(3))
        filename = data_dir + filename0
        self.data_matrix.to_csv(filename)
        self.cmd_msg.emit('{0} data saved in {1}.txt'.format("XAS" if self.xas else "scan" ,filename0))

class Tscan(QThread):
    setplot = pyqtSignal(str, float, int)
    plot = pyqtSignal(int, list, pd.Series)
    cmd_msg = pyqtSignal(str)

    def __init__(self, p, t0, dt, n):
        super().__init__()
        self.p = p
        self.dt = dt
        self.n = n
        self.t0 = t0
        self.start_point = get_param(p)
        self.timelist = []                                      #as axis x
        self.data_matrix = pd.DataFrame(columns=param_index)    #as axis y

    def run(self):
        global param, WorkingSTATUS, BUSY, CountDOWN, file_no
        BUSY = True
        file_no += 1
        '''
        Data collection
        '''
        t1 = time.time()
        self.setplot.emit(self.p, self.dt, self.n)
        for i in range(self.n+1):
            if ABORT:
                break
            t01 = time.time()
            # timestamp = QTime.currentTime()
            # t = timestamp.toString()
            if i != 0:
                t = t01-t1
                v = get_param(self.p)
            else:
                t = 0
                v = get_param(self.p)
            self.timelist.append(t)
            # appending current_param to data_matrix
            current_param = pd.Series(param)
            current_param['t'] = t
            current_param[self.p] = v
            self.data_matrix.loc[len(self.data_matrix), :] = current_param.tolist()
            '''
            plot from data_matrix
            '''
            #for i in range(0, len(plot)):
            self.plot.emit(0, self.timelist, self.data_matrix.loc[:, self.p])
            dt = time.time()-t01
            time.sleep(self.dt-dt)
        '''
        Loop finished
        '''

        WorkingSTATUS = ""
        CountDOWN = 0
        print('[data_matrix]')
        print(self.data_matrix)
        dt = round(time.time() - t1, 3)
        print('time span in senconds=', dt)
        if ABORT:
            self.cmd_msg.emit('scaning loop has been terminated; time span  = %s'%convertSeconds(dt))
        else:
            self.cmd_msg.emit('scan %s completed; time span  = %s'%(self.p, convertSeconds(dt)))
        self.saveSpec()
        self.quit()

    def saveSpec(self):
        filename0="tscan_{0}_{1}".format(dir_date, file_no)
        filename = data_dir + filename0
        self.data_matrix.to_csv(filename)
        self.cmd_msg.emit('{0} data saved in {1}.txt'.format("tscan" , filename0))



class Xas(QThread):  # no dummy now
    cmd_msg = pyqtSignal(str)
    xas_plot = pyqtSignal(list, list)
    final_plot =pyqtSignal()
    def __init__(self, e1, e2, de, dwell, n, N):
        super(Xas, self).__init__()
        self.e1, self.e2, self.de, self.dwell, self.n, self.N = e1, e2, de, dwell, n, N
        self.done_i = 0
        self.sum_x, self.sum_y = [], []

    def run(self):
        global param, WorkingSTATUS, cmd_global, CountDOWN, BUSY, spectrum_global
        BUSY = True
        self.t0 = time.time()
        for i in range(self.N):
            if ABORT: break
            if i == 0: self.xas_plot.emit(self.sum_x, self.sum_y) #refresh accum
            cmd_global.command_input.setText("XAS [{0:d} / {1:d}] : scanning...".format(i+1, self.N))
            self.scanthread = Scan(['Iph'], 'agm', self.e1, self.e2, self.de, self.dwell, self.n, i+1, True)
            self.scanthread.scan_plot.connect(spectrum_global.scanPlot)
            self.scanthread.cmd_msg.connect(cmd_global.sysReturn)
            self.scanthread.set_data.connect(spectrum_global.liveplot)
            self.scanthread.data_set.connect(self.sumPlot)
            self.scanthread.start()
            self.scanthread.wait()
            if ABORT == False: self.done_i += 1

        '''
        Loop finished
        '''
        self.final_plot.emit()
        self.sum_x, self.sum_y = [], []
        spantime = time.time() - self.t0
        self.cmd_msg.emit('{0:d} xas scan{1} completed, time span= {2:.2f} sec'.format(self.done_i , "" if self.done_i ==1 else "s",spantime))
        cmd_global.command_input.setText("")
        self.quit()

    def sumPlot(self, x, y):
        if (self.sum_x == []):
            self.sum_x = x
        if (self.sum_y == []):
            self.sum_y = y
        else:
            self.sum_y = [(a + b*self.done_i)/(self.done_i+1) for a, b in zip(y, self.sum_y)]#initialize
        print('i = {0}, sum_x = {1}, sum_y = {2}'.format(self.done_i,self.sum_x,self.sum_y))
        self.xas_plot.emit(self.sum_x, self.sum_y)



class Rixs(QThread):  # no dummy now
    cmd_msg = pyqtSignal(str)
    setplot = pyqtSignal()
    savespec = pyqtSignal(bool)

    def __init__(self, t, n):
        super().__init__()
        self.t = t
        self.n = n
        self.taken_i = 0
        self.img_number = 0

    def run(self):
        global param, WorkingSTATUS, cmd_global, img_global, CountDOWN, BUSY, spectrum_global
        BUSY = True
        self.setplot.emit()
        pvl.ccd('exposure', self.t)
        self.t0 = time.time()
        for i in range(self.n):
            if ABORT: break
            '''
            Estimate remaining time
            '''
            if i == 0:
                dt = self.n * (self.t + 3)
            else:
                dt = ((time.time() - self.t0) / i) * (self.n - i)  # remaining time
            dt = round(dt, 2)

            WorkingSTATUS = ('Taking RIXS data ... ' + str(i + 1) + '/' + str(self.n))
            CountDOWN = dt

            self.img_number += 1
            self.exposethread = Expose(self.t, self.img_number, True)
            self.exposethread.cmd_msg.connect(cmd_global.sysReturn)
            self.exposethread.rixs.connect(img_global.getData)
            self.exposethread.show.connect(img_global.showImg)
            self.exposethread.save[int].connect(img_global.saveImg)
            self.exposethread.start()
            self.exposethread.wait()
            if ABORT == False: self.taken_i += 1

        '''
        Loop finished
        '''
        if self.n != 1: self.savespec.emit(True)
        WorkingSTATUS = " "
        CountDOWN = 0
        string = str(self.taken_i) + " images" if self.taken_i != 1 else str(self.taken_i) + " image"
        self.cmd_msg.emit(string + ' taken, time span= ' + str(round(time.time() - self.t0, 2)) + ' sec')

class Expose(QThread):
    get = pyqtSignal(bool)
    rixs = pyqtSignal(bool, int)
    show = pyqtSignal()
    save = pyqtSignal(int)
    cmd_msg = pyqtSignal(str)

    def __init__(self, t, n, plot=False):
        super(Expose, self).__init__()
        self.t = t
        self.n = n
        self.plot = plot

    def run(self):
        global WorkingSTATUS
        pvl.ccd('start', 1)  # 1 for activate
        t1 = time.time()
        while pvl.ccd("dataok") == 1:  # check for starting exposure
            pass
            if pvl.ccd("dataok") == 0:
                break

        while (time.time() - t1) < abs(self.t - 0.5):  # wait for exposure
            time.sleep(0.5)
            if ABORT:  # check ABORT every 0.5 sec
                pvl.ccd("stop", 1)
                self.cmd_msg.emit('RIXS aborted, CCD exposure stopped.')
                break

        if ABORT == False:
            while pvl.ccd("dataok") == 0:
                pass
                if pvl.ccd("dataok") == 1:
                    break

            dt = round(time.time() - t1, 3)
            print('image taken, time span in seconds= %s' % dt)
            if self.plot:
                self.rixs.emit(self.plot, self.n) # get data, if self.plot = True, also plot in Spectrum Widget.
                #self.save[int].emit(self.n)
            else:
                self.get.emit()
                self.show.emit()         # show image

class Macroloop(QThread):
    msg = pyqtSignal(str)
    send = pyqtSignal(str)
    number = pyqtSignal(int)
    setText = pyqtSignal(str)

    def __init__(self, name):
        super(Macroloop, self).__init__()
        self.name = name
        self.macro_n = 0 # start from zero
        self.macro_index = 0
        self.abort = False

    #TODO: 1. ABORT 2. changing macro
    def run(self):
        self.readFile()   #get self.macro_n
        while self.macro_index < self.macro_n:
            file = self.readFile()
            if file[-1] == "###MacroPause###":
                self.setText.emit("Macro paused: waiting for macro file edition")
                while True:
                    time.sleep(1)
                    read = self.readFile()[-1] #check every second during macro pause
                    if read != "###MacroPause###":
                        break
            line = file[self.macro_index]
            self.number.emit(self.macro_index) # to macrowindow
            self.send.emit(line)
            self.setText.emit("macro line [{0}] : {1}".format(str(self.macro_index+1), line))
            self.macro_index += 1
            time.sleep(0.5)
            while BUSY:
                time.sleep(1) # hold here to wait command finish
            if ABORT:
                break

        if ABORT == False:
            end_msg = "macro finished."
        else:
            end_msg = "macro has been terminated, executed macro line: %s."%self.macro_index
        self.setText.emit("")
        self.msg.emit(end_msg)
        self.quit()

    def readFile(self): # refresh macro number (length of file)
        #==============Macro start===============
        readfile=[]
        f = open(self.name,"r")
        for x in f:
            x = x.replace("\n","")
            readfile.append(x)
        self.macro_n = len(readfile) # refresh macro_n
        return readfile

    def abort(self):
        self.abort = True



if __name__ == '__main__':
    app = QApplication(sys.argv)
    BlueMagpie = MainWindow()
    sys.exit(app.exec_())
