from PyQt5 import QtGui, QtCore, QtWidgets
from pyqtgraph import PlotWidget

class CustomWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(CustomWidget, self).__init__(parent=parent)
        self.ui = Plot_engine()
        self.ui.setupUi(CustomWidget)
        self.ui.plotWidget.plot(x=[0.0, 1.0, 2.0, 3.0],
                                y=[4.4, 2.5, 2.1, 2.2])
# OPTIONAL
# //Simple demonstration of pure Qt widgets interacting with pyqtgraph//
#        self.ui.checkBox.stateChanged.connect(self.toggleMouse)
#    def toggleMouse(self, state):
#        if state == QtCore.Qt.Checked:
#            enabled = True
#        else:
#            enabled = False
#
#        self.ui.plotWidget.setMouseEnabled(x=enabled, y=enabled)

class Plot_engine(object):

    def setupUi(self, CustomWidget):

        CustomWidget.resize(800, 600)

        self.gridLayout = QtWidgets.QGridLayout(CustomWidget)
        self.plotWidget = PlotWidget(CustomWidget)
        self.gridLayout.addWidget(self.plotWidget, 0, 0, 1, 1)

        self.checkBox = QtWidgets.QCheckBox(CustomWidget)
        self.gridLayout.addWidget(self.checkBox, 1, 0, 1, 1)

if __name__ == '__main__':
    app = QtGui.QApplication([])
    widget = CustomWidget()
    widget.show()
    app.exec_()
