import PyQt5
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys, os
from os import path

class MacroMonitor(QWidget):
    '''
    Popup a window to monitor macro running status.
    '''
    errorMsg = pyqtSignal(str,str)
    macroMsg = pyqtSignal(str)
    openEditor = pyqtSignal(int)
    windowclosed = pyqtSignal()

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath # inherited from Mainwindow
        self.__mainwindow()
        self.__layout()
        self.__load()
        self.running = True
        self.current_index = 0
        
    def __mainwindow(self):
        self.setWindowTitle("Macro Monitor - {}".format(path.basename(self.filepath)))
        self.resize(50, 80)
        self.setWindowFlags(self.windowFlags() & Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)

    def __layout(self):
        self.monitor = QTextEdit(self)
        self.monitor.setReadOnly(True)
        self.monitor.setFocusPolicy(Qt.StrongFocus)
        self.monitor.setFocus()
        self.monitor.setStyleSheet("color: black; background-color: Floralwhite")
        self.modify_button = QPushButton("modify", self)
        self.modify_button.clicked.connect(self.modify)  
        self.window_layout = QVBoxLayout(self)
        self.window_layout.addWidget(self.monitor)
        self.window_layout.addWidget(self.modify_button)
      
    def __load(self):
        try:
            with open(self.filepath, 'r') as f:
                data = f.read()
                self.monitor.setText(data)
        except:
            self.errorMsg.emit('failed to load file {}'.format(self.filepath),'err')
            print('failed to load file{}'.format(self.filepath))

    def __readFile(self):
        '''
        Return command lines as list
        '''
        filelist=[]
        with open(self.filepath,"r") as f:
            for x in f:
                x = x.replace("\n", "")
                filelist.append(x)
        return filelist

    def modify(self):
        '''
        popup editor window for user modification, running macro will be paused
        '''
        if self.current_index < len(self.__readFile()):
            with open(self.filepath, "a") as f:
                f.write("\n###MacroPause###")       # for MainWindow to check pause, will be overwrited when new file is saved
            self.openEditor.emit(self.current_index)

    def update(self, macro_index):
        '''
        Receive index of the running command from Mainwindow QThread,
        mark commands in different colors. 
        '''
        self.currnet_index = macro_index
        filelist = self.__readFile()
        if macro_index <= len(filelist):         # macro_index = running line
            for i in range(0, macro_index+1):
                line = filelist[i]
                filelist[i] = '<font color = gray> {} </font>'.format(line)
            self.monitor.setText('<br>'.join(filelist))

    def closeEvent(self, event):
        '''
        Ignore close event while macro is running.
        '''
        if self.running == False:
            self.windowclosed.emit()
            event.accept()
        else:
            self.errorMsg.emit('Can\'t close macro monitor while macro is running.', 'err')
            event.ignore()

    def marcoStart(self, name):
        '''
        setup for macro monitor if window was already opened.
        '''
        self.running = True
        self.filepath = name
        self.__load()
        self.modify_button.setEnabled(True)

    def macroFinished(self):
        self.running = False
        self.modify_button.setDisabled(True)
     
# test running independently
#app = QApplication(sys.argv)
#macro = MacroMonitor("a")
#macro.show()
#sys.exit(app.exec_())