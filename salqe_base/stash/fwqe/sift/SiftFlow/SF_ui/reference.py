# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'reference.ui'
#
# Created: Tue Mar 27 15:49:23 2012
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Reference(object):
    def setupUi(self, Reference):
        Reference.setObjectName(_fromUtf8("Reference"))
        Reference.setWindowModality(QtCore.Qt.NonModal)
        Reference.resize(490, 347)
        Reference.setMinimumSize(QtCore.QSize(250, 100))
        self.gridLayout = QtGui.QGridLayout(Reference)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tabWidget_reference = QtGui.QTabWidget(Reference)
        self.tabWidget_reference.setObjectName(_fromUtf8("tabWidget_reference"))
        self.tab_main = QtGui.QWidget()
        self.tab_main.setObjectName(_fromUtf8("tab_main"))
        self.tabWidget_reference.addTab(self.tab_main, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget_reference, 0, 0, 1, 1)

        self.retranslateUi(Reference)
        QtCore.QMetaObject.connectSlotsByName(Reference)

    def retranslateUi(self, Reference):
        Reference.setWindowTitle(QtGui.QApplication.translate("Reference", "References", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget_reference.setTabText(self.tabWidget_reference.indexOf(self.tab_main), QtGui.QApplication.translate("Reference", "Tab 1", None, QtGui.QApplication.UnicodeUTF8))

