import PyQt5
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys, os

class MacroWindow(QWidget):
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

    def __mainwindow__(self):
        self.setWindowTitle("Macro Editor")
        self.resize(300, 500)
        self.setWindowFlags(self.windowFlags() & Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)

    def __statusbar__(self):
        self.status_bar = QLineEdit(self)
        self.status_bar.setReadOnly(True)
        self.show_bar()

    def __editor__(self):
        self.editor = QTextEdit(self)
        self.editor.setFocusPolicy(Qt.StrongFocus)
        self.editor.setFocus()

    def __buttons__(self):
        self.save_button = QPushButton("save", self)
        self.open_button = QPushButton("open", self)
        self.edit_button = QPushButton("edit", self)
        self.save_button.clicked.connect(self.save)
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



    def save(self):
        file_name = self.getName()
        text = self.editor.toPlainText() # transform user_text to plaintext
        txt_file = "{0}{1}.txt".format(self.directory, file_name)
        file = open(txt_file, "w")
        file.write(text)
        file.close()
        self.editor.setDisabled(True)

    def getName(self):
        text, ok = QInputDialog.getText(self, 'Save Macro', 'New macro name:')
        if ok:
            if os.path.exists(self.directory + text):
                self.show_bar("File already exist: {0} file not saved.".format(text), False)
                pass
            else:
                file_name = str(text)
                self.show_bar(str(text))
                self.macroMsg.emit("macro file saved: {0}.txt".format(file_name))
        return (file_name)

    def open(self):
        fname = QFileDialog.getOpenFileName(self, 'Open macro file',
                                    directory =self.directory
                                    ,filter = 'Text files (*.txt)'
                                    ,options=QFileDialog.ReadOnly)

        if fname[0]:
            f = open(fname[0], 'r')

            with f:
                data = f.read()
                self.editor.setText(data)

    def edit(self):
        pass

    def show_bar(self, name=" ", flag=True):
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