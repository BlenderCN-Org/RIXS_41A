import PyQt5
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys, os

class MacroEditor(QWidget):
    errorMsg = pyqtSignal(str,str)
    macroMsg = pyqtSignal(str)
    windowclosed = pyqtSignal()
    def __init__(self, directory, filepath=None):
        super().__init__()
        self.running = True if (filepath != None) else False
        self.editing = True if (filepath != None) else False
        self.current_file = filepath
        self.directory = directory
        self.__mainwindow()
        self.__buttons()
        self.__editor()
        self.__layout()
        self.__checkMode()

    def __mainwindow(self):
        self.setWindowTitle("Macro Editor")
        self.resize(400, 600)
        self.setWindowFlags(self.windowFlags() & Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)

    def __editor(self):
        self.editor = QTextEdit(self)
        self.editor.setFocusPolicy(Qt.StrongFocus)
        self.editor.setFocus()

    def __buttons(self):
        self.save_button = QPushButton("save", self)
        self.open_button = QPushButton("open", self)
        self.resume_button = QPushButton("resume", self)
        self.save_button.clicked.connect(self.overWrite)    # check overwrite problem first, then decide new file name
        self.open_button.clicked.connect(self.open)         # request user to choose a file
        self.resume_button.clicked.connect(self.resume)     # activated while macro started
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.open_button)
        self.buttons_layout.addWidget(self.resume_button)

    def __layout(self):
        self.window_layout = QVBoxLayout(self)
        self.window_layout.addWidget(self.editor)
        self.window_layout.addLayout(self.buttons_layout)

    def __checkMode(self):
        self.open_button.setDisabled(self.running)
        self.save_button.setDisabled(self.running)
        self.resume_button.setEnabled(True if (self.editing and self.running) else False)
        self.editor.setReadOnly(not self.editing)
        self.editor.setStyleSheet("color: black; background-color: {}".format("white" if self.editing else "Floralwhite"))
    
    def __readFile(self):
        filelist=[]
        with open(self.current_file,"r") as f:
            for x in f:
                x = x.replace("\n", "")
                filelist.append(x)
        return filelist

    def overWrite(self):
        if self.current_file != None: #if there's a name already, check overwrite
            buttonReply = QMessageBox.question(self, 'Save Macro', "Do you want to overwrite?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if buttonReply == QMessageBox.Yes:
                self.save(os.path.basename(self.current_file))
            else:
                file_name = self.getName()
                self.save(file_name)
        else:
            file_name = self.getName()
            self.save(file_name)

    def save(self, file_name):
        self.editing = False
        if file_name != False:
            text = self.editor.toPlainText()  # transform user_text to plaintext
            txt_file = "{0}{1}".format(self.directory, file_name)
            with open(txt_file, "w") as file:
                file.write(text)
            self.setWindowTitle("Macro Editor - {0}".format(file_name))
        self.__checkMode()

    def getName(self, msg="", file_name = False):
        text, ok = QInputDialog.getText(self, 'Save Macro', 'New macro name:\n'
                                                            '{}'.format(msg))
        if ok:
            if text != "":
                if not os.path.exists('{0}{1}.txt'.format(self.directory,text)):
                    self.macroMsg.emit("macro file saved: {0}.txt".format(text))
                    file_name = str(text)+'.txt'
                else:
                    error_msg = "File name already exist: {0}.".format(text)
            else:
                error_msg = 'file name can\'t be empty'
        else:
            error_msg = 'file not saved.'
        if file_name == False:
            self.errorMsg.emit(error_msg, 'err')
            self.getName(error_msg)
        return (file_name)

    def open(self):
        self.editing = True
        fname = QFileDialog.getOpenFileName(self, 'Open macro file',
                                            directory=self.directory
                                            , filter='Text files (*.txt)'
                                            , options=QFileDialog.ReadOnly)
        if fname != ('', ''):
            file = fname[0]
            self.load(file)

    def load(self, filepath = None):
        if filepath != None:
            with open(filepath, 'r') as f:
                data = f.read()
                self.editor.setText(data)
                title = "Macro Editor - {0}".format(os.path.basename(f.name))
                self.current_file = filepath 
            self.__checkMode()
        else:
            title = "Macro Editor"
        self.setWindowTitle(title)

    def modify(self, current_index):
        self.editing = True
        self.editing_index = current_index+1
        filelist = self.__readFile()
        self.editor.setText('<br>'.join(filelist[self.editing_index:-1]))
        self.__checkMode()

    def resume(self):
        self.editing = False
        filelist = self.__readFile()[:self.editing_index]
        text = self.editor.toPlainText()
        with open(self.current_file, "w") as f:
            f.write('\n'.join(filelist)+'\n'+text)
        self.__checkMode()

    def marcoStart(self, name):
        self.running = True
        self.load(name)

    def macroFinished(self):
        self.running = False
        self.editing = False
        self.load(self.current_file)

    def closeEvent(self, event):
        if self.running == False:
            self.windowclosed.emit()
            event.accept()
        else:
            self.errorMsg.emit('Can\'t close macro editor window while macro is running.', 'err')
            event.ignore()

# test running independently
#app = QApplication(sys.argv)
#macro = MacroEditor("a")
#macro.show()
#sys.exit(app.exec_())