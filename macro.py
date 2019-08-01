import PyQt5
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys, os

class MacroWindow(QWidget):
    errorMsg = pyqtSignal(str,str)
    macroMsg = pyqtSignal(str)
    windowclosed = pyqtSignal()

    def __init__(self, directory):
        super().__init__()
        self.macro_running = False
        self.current_file = None
        self.__mainwindow__()
        self.__statusbar__()
        self.__jobdone__()
        self.__buttons__()
        self.__editor__()
        self.__layout__()
        self.directory = directory # inherited by Mainwindow

    def __mainwindow__(self):
        self.setWindowTitle("Macro Editor")
        self.resize(400, 600)
        self.setWindowFlags(self.windowFlags() & Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)

    def __statusbar__(self):
        self.status_bar = QLineEdit(self)
        self.status_bar.setReadOnly(True)
        self.status_bar.setDisabled(True)
        self.showBar('New File',False)

    def __jobdone__(self):
        self.jobdonela = QLabel('Job done')
        self.jobdone = QTextEdit(self)
        self.jobdone.setFixedHeight(100)
        self.jobdone.setReadOnly(True)
        self.donetext = []

    def __editor__(self):
        self.editorla = QLabel('Editor')
        self.editor = QTextEdit(self)
        self.editor.setFocusPolicy(Qt.StrongFocus)
        self.editor.setFocus()

    def __buttons__(self):
        self.save_button = QPushButton("save", self)
        self.open_button = QPushButton("open", self)
        self.edit_button = QPushButton("edit", self)
        self.save_button.clicked.connect(self.overWrite)# check overwrite problem first, then decide new file name
        self.open_button.clicked.connect(self.open)     # request user to choose a file
        self.edit_button.clicked.connect(self.edit)     # activated while macro started
        self.edit_button.setDisabled(True)
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.open_button)
        self.buttons_layout.addWidget(self.edit_button)

    def __layout__(self):
        self.window_layout = QVBoxLayout(self)
        self.window_layout.addWidget(self.status_bar)
        self.window_layout.addWidget(self.editorla)
        self.window_layout.addWidget(self.editor)
        self.window_layout.addLayout(self.buttons_layout)
        self.window_layout.addWidget(self.jobdonela)
        self.window_layout.addWidget(self.jobdone)

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
        if file_name != False:
            text = self.editor.toPlainText()  # transform user_text to plaintext
            txt_file = "{0}{1}".format(self.directory, file_name)
            with open(txt_file, "w") as file:
                file.write(text)
            self.enableEditor(False)
            if self.macro_running == True: 
                self.edit_button.setEnabled(True)

    def getName(self, msg="", file_name = False):
        text, ok = QInputDialog.getText(self, 'Save Macro', 'New macro name:\n'
                                                            '{}'.format(msg))
        if ok:
            if text != "":
                if not os.path.exists('{0}{1}.txt'.format(self.directory,text)):
                    self.showBar(str(text))
                    file_name = str(text) + '.txt'
                    self.macroMsg.emit("macro file saved: {0}".format(file_name))
                else:
                    error_msg = "File name already exist: {0}.".format(text)
            else:
                error_msg = 'file name can\'t be empty'
        else:
            error_msg = 'file not saved.'
        if file_name == False:
            self.showBar(error_msg, False)
            self.errorMsg.emit(error_msg, 'err')
            self.getName(error_msg)
        return (file_name)

    def open(self):
        fname = QFileDialog.getOpenFileName(self, 'Open macro file',
                                            directory=self.directory
                                            , filter='Text files (*.txt)'
                                            , options=QFileDialog.ReadOnly)
        if fname != ('', ''):
            file = fname[0]
            self.load(file)

    def load(self, file = None, i = None):
        if file != None:
            with open(file, 'r') as f:
                if i == None:
                    data = f.read()
                self.editor.setText(data)
                self.showBar(f.name)
                title = "Macro Editor - {0}".format(os.path.basename(f.name))
                self.current_file = file
        else:
            title = "Macro Editor"
        self.setWindowTitle(title)

    def edit(self):
        with open(self.current_file, 'r') as f: # load text to editor
            data = f.read()
            self.editor.setText(data)
            self.showBar(os.path.basename(self.current_file))

        with open(self.current_file, "a") as f:
            f.write("\n###MacroPause###")       # for MainWindow to check pause, will be overwrited when new file is saved
        self.enableEditor(True)
        self.open_button.setDisabled(True)

    def marcoStart(self, name):
        self.macro_running = True
        self.enableEditor(False)
        self.load(name)

    def macroFinished(self):
        self.macro_running = False
        self.load(self.current_file)
        self.enableEditor(True)
        self.donetext = []
        self.jobdone.clear()

    def showBar(self, name, flag=True):
        if flag:
            string = "File path: {0}".format(name)
        else:
            string = name
        self.status_bar.setText(string)

    def readFile(self):
        filelist=[]
        with open(self.current_file,"r") as f:
            for x in f:
                x = x.replace("\n", "")
                filelist.append(x)
        return filelist

    def macroNum(self, macro_index):
        filelist = self.readFile()
        if macro_index < len(filelist): # macro_index = running line
            self.jobdone.setText('\n'.join(self.donetext) if macro_index != 0 else '')
            self.donetext.append(filelist[macro_index])
            if self.macro_running: # mark running macro
                line = filelist[macro_index]
                filelist[macro_index] = '<font color = blue> {} </font>'.format(line)
                self.editor.setText('<br>'.join(filelist))
    
    def enableEditor(self, bool):
        self.open_button.setEnabled(bool)
        self.edit_button.setDisabled(True)
        self.editor.setReadOnly(not bool)
        self.editor.setStyleSheet("color: black; background-color: {}".format("white" if bool else "Floralwhite"))

    def closeEvent(self, event):
        if self.macro_running == False:
            self.windowclosed.emit()
            event.accept()
        else:
            self.errorMsg.emit('Can\'t close macro window while macro is running.', 'err')
            event.ignore()

# test running independently
# app = QApplication(sys.argv)
# macro = MacroWindow("a")
# macro.show()
# sys.exit(app.exec_())