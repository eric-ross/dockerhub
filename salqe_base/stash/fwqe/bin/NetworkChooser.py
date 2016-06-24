#!/bin/env python
################################################################################
#
#
# (C) Copyright 2013 Hewlett-Packard Development Company, L.P.
#
#
# File Name :  NetworkChooser.py
#
# Purpose:
# - choose and configure the network proxy config for the SALQE VM
#
#
################################################################################
# Release Notes:
#
# ----- May/23/2013 - Eric Ross  ------------------------------------------
#
################################################################################
#
#  Add the 'network.zone' configuration to the .salqeconfig file
#
#  This config will be used to drive any network dependent scripts (such as proxy configuration)

import sys, os, json
from PyQt4 import QtGui
from PyQt4 import QtCore

class MessageBoxClass(QtGui.QWidget):
    """Basic class for pop up a message box, now supports 3 types of message box:
        - Information:  Ok button
        - Question:     Yes/No buttons
        - Critical      Abort/Retry/Ignore buttons
        Args:
            txtMsg:   Text message displays in the pop-up window
            titleMsg: Window title
    """
    def __init__(self, txtMsg='', titleMsg='', parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.returnVal = {QtGui.QMessageBox.Ok:     'Ok',
                          QtGui.QMessageBox.Cancel: 'Cancel',
                          QtGui.QMessageBox.Yes:    'Yes',
                          QtGui.QMessageBox.No:     'No',
                          QtGui.QMessageBox.Abort:  'Abort',
                          QtGui.QMessageBox.Retry:  'Retry',
                          QtGui.QMessageBox.Ignore: 'Ignore'}

    def information(self,txtMsg, titleMsg):
        reply= QtGui.QMessageBox.information(self,titleMsg, txtMsg)
        return self.returnVal[reply]

    def question(self,txtMsg, titleMsg):
        reply= QtGui.QMessageBox.question(self,titleMsg, txtMsg, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        return self.returnVal[reply]

    def critical(self,txtMsg, titleMsg):
        reply= QtGui.QMessageBox.critical(self,titleMsg, txtMsg, QtGui.QMessageBox.Abort |QtGui.QMessageBox.Retry |QtGui.QMessageBox.Ignore)
        return self.returnVal[reply]


def messageBox(txtMsg, titleMsg='Information'):
    """Pop up an information message box with Ok button.
       Args:
            txtMsg:   Text message displays in the pop-up window
            titleMsg: Window title
       Return:
            String value of selected button name
    """
    app = QtGui.QApplication(sys.argv)
    return MessageBoxClass().information(txtMsg, titleMsg)

class ListBoxClass(QtGui.QDialog):
    """Class to build up a dialog with a list box.
        Args:
            list:         Option list would display in list box.
            listBoxTitle: List box title on top of list box
            windowTitle:  Window title
            width:        Dialog width
            height:       Dialog height
    """
    def __init__(self,list, listBoxTitle ='',windowTitle = '', width = 180, height = 270, parent=None):
        super(ListBoxClass,self).__init__(parent)
        self.setWindowTitle(windowTitle)
        self.resize(width,height)
        self.selected = None

        self.txtSelect  = QtGui.QLabel(listBoxTitle, self)
        self.btnOK      = QtGui.QPushButton('OK',    self)
        self.btnCancel  = QtGui.QPushButton('Cancel',self)
        self.listWidget = QtGui.QListWidget()

        self.listWidget.addItems(list)
        #self.listWidget.setCurrentRow(0)
        #self.selected =  self.listWidget.item(self.listWidget.currentRow()).text()

        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(self.txtSelect,  0, 0, 1, 2)
        self.layout.addWidget(self.listWidget, 1, 0, 1, 2)
        self.layout.addWidget(self.btnOK,      2, 0, 1, 1)
        self.layout.addWidget(self.btnCancel,  2, 1, 1, 1)

        self.connect(self.btnOK,     QtCore.SIGNAL("clicked()"), self.getSelectedItem)
        self.connect(self.btnCancel, QtCore.SIGNAL("clicked()"), self.close)

        self.show()

    def getSelectedItem(self):
        try:
            self.selected = self.listWidget.item(self.listWidget.currentRow()).text()
        except:
            self.selected = None
        self.close()

def listBox(list,listBoxTitle ='Select:',windowTitle = 'List Box', width = 180, height = 270):
    """Pop up a list box dialog and get the selected item string.
        Args:
            list:         Option list would display in list box.
            listBoxTitle: List box title on top of list box
            windowTitle:  Window title
            width:        Dialog width
            height:       Dialog height
        Return:
            Selected item string in list box. Return None if nothing selected or Cancel button pressed.
    """
    app = QtGui.QApplication(sys.argv)
    ls  = ListBoxClass(list, listBoxTitle, windowTitle, width, height)
    app.exec_()

    return ls.selected


if __name__ == '__main__':

    zones = {'HP Vancouver':'vancouver','HP outside Vancouver':'hp','Non HP':'external'}
    #Example of list box
    exitcode = -1 
    returnVal = listBox(zones.keys(),listBoxTitle='Select your network:',windowTitle='Select Network')
    if returnVal is not None:
        ret = str(returnVal)
        if ret in zones:
            try:
                with open(os.environ['HOME']+'/.salqeconfig','rw+') as f:
                    config = json.load(f)
                    config['network.zone']=zones[ret]
                    f.seek(0)
                    json.dump(config,f)
                    f.truncate()
                    messageBox('Logoff and logon to refresh the configuration.')
                    exitcode = 0 
            except IOError:
                with open(os.environ['HOME']+'/.salqeconfig','w') as f:
                    config={'network.zone':zones[ret]}
                    json.dump(config,f)
                    f.truncate()
                    messageBox('Logoff and logon to refresh the configuration.')
                    exitcode = 0
            except ValueError:
                print "ERROR:  ~/.salqeconfig:  syntax error"
        else:
            exitcode = -1
    
    sys.exit(exitcode)          


