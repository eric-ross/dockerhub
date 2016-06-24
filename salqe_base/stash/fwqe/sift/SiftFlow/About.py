#!/usr/bin/python -d
 
import sys, os
from PyQt4 import QtCore, QtGui
from SF_ui.about import Ui_About

class About(QtGui.QDialog):
    def __init__(self, parent, libMgr):
        QtGui.QDialog.__init__(self)
        self.mainWin = parent
        self.libMgr = libMgr
        self.ui = Ui_About()
        self.ui.setupUi(self)
        pic = QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), 'SiftTeal.png'))
        self.ui.label.setPixmap(pic.scaled(self.ui.label.width(), self.ui.label.width()))
        self.ui.text.setText(self.libMgr.getAboutText())
