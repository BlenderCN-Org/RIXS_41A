import PyQt5
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys, os

class MacroWindow(QWidget):
    errorMsg = pyqtSignal(str,str)
    macroMsg = pyqtSignal(str)
    def __init__(self, directory):
        super().__init__()
        self.__mainwindow__()
        self.__statusbar__()
        self.__editor__()
        self.__buttons__()
        self.__layout__()
        self.directory = directory # inherited by Mainwindow
        self.macro_running = False
        self.current_file = None

    def __mainwindow__(self):
        self.setWindowTitle("Macro Editor")
        self.resize(400, 600)
        self.setWindowFlags(self.windowFlags() & Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)

    def __statusbar__(self):
        self.status_bar = QLineEdit(self)
        self.status_bar.setReadOnly(True)
        self.status_bar.setDisabled(True)
        self.show_bar('New File',False)

    def __editor__(self):
        self.editor = QTextEdit(self)
        self.editor.setFocusPolicy(Qt.StrongFocus)
        self.editor.setFocus()

    def __buttons__(self):
        self.save_button = QPushButton("save", self)
        self.open_button = QPushButton("open", self)
        self.edit_button = QPushButton("edit", self)
        self.save_button.clicked.connect(self.overWrite)
        self.open_button.clicked.connect(self.open)
        self.edit_button.clicked.connect(self.edit)
        self.edit_button.setDisabled(True)

    def __layout__(self):
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.open_button)
        self.buttons_layout.addWidget(self.edit_button)
        self.window_layout = QVBoxLayout(self)
        self.window_layout.addWidget(self.status_bar)
        self.window_layout.addWidget(self.editor)
        self.window_layout.addLayout(self.buttons_layout)

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
            txt_file = "{0}{1}.txt".format(self.directory, file_name)
            with open(txt_file, "w") as file:
                file.write(text)
            self.editor.setDisabled(True)

    def getName(self, msg=""):
        text, ok = QInputDialog.getText(self, 'Save Macro', 'New macro name:\n'
                                                            '{}'.format(msg))
        if ok:
            if text != "":
                if os.path.exists('{0}{1}.txt'.format(self.directory,text)):
                    file_name = False
                    error_msg = "File name already exist: {0}.".format(text)
                    self.show_bar(error_msg, False)
                    self.errorMsg.emit(error_msg, 'err')
                    self.getName(error_msg)
                else:
                    file_name = str(text)
                    self.show_bar(str(text))
                    self.macroMsg.emit("macro file saved: {0}.txt".format(file_name))
            else:
                file_name = False
                error_msg = 'file name can\'t be empty'
                self.show_bar(error_msg, False)
                self.errorMsg.emit(error_msg, 'err')
                self.getName(error_msg)
        else:
            file_name = False

        return (file_name)


    def open(self):
        fname = QFileDialog.getOpenFileName(self, 'Open macro file',
                                    directory =self.directory
                                    ,filter = 'Text files (*.txt)'
                                    ,options=QFileDialog.ReadOnly)

        self.current_file = fname[0]
        print('current file = ', self.current_file)
        with open(fname[0], 'r') as f:
            data = f.read()
            self.editor.setText(data)
            self.show_bar(os.path.basename(fname[0]))

    def edit(self):
        with open(self.current_file, 'r') as f: #load text to editor
            data = f.read()
            self.editor.setText(data)
            self.show_bar(os.path.basename(self.current_file))

        with open(self.current_file, "a") as f:
            f.write("\n###MacroPause###")

        self.editor.setEnabled(True)

    def editButton(self, name):
        self.current_file = name
        self.edit_button.setEnabled(True)

    def show_bar(self, name, flag=True):
        if flag:
            string = "File Name: {0}".format(name)
        else:
            string = name
        self.status_bar.setText(string)

    def running(self, bool):
        self.macro_running = bool


# test running independently
# app = QApplication(sys.argv)
# macro = MacroWindow("a")
# macro.show()
# sys.exit(app.exec_())