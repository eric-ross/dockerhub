#!/usr/bin/python -d
 
import sys, os
from PyQt4 import QtCore, QtGui
from SFLibManager import *

class MessageManager():
    def __init__(self, libMgr,statusbarWidget):
        self.parentWindow = libMgr.parent
        self.statusbarWidget = statusbarWidget

    # - - - - - - - - - - - - - - - - 
    # - Name: out 
    # - Parameters: 
    # - Description: Print normal messages to the user in the appropriate fields depending on 
    # - the arguments passed in.
    # - Usage: out("Message to the output box"), out("Message to the status bar",  10 [time to show message in seconds])
    # -        out("Message to output box", "Message to status bar", 10 [time to show message in seconds])
    def out(self, text, args):
        argCount = len(args)

        #If there are an invalid number of args, throw exception
        if(argCount > 2):
            raise IOError("Invalid number of arguments")

        #text only, just goes to outputbox
        if(argCount == 0):
            print text
        #args exist, 1 means text/number for status bar, 2 is text/text/number for output and statusbar
        elif(argCount == 1):
            self.statusbarWidget.showMessage(text, args[0] * 1000)
        elif(argCount == 2):
            print text
            self.statusbarWidget.showMessage(args[0], args[1] * 1000)

    # - - - - - - - - - - - - - - - - 
    # - Name: statusbarClear()  
    # - Description: If a 0 is passed into out, as the time to display a status bar message 
    # - this then can be called to clear that message
    def statusbarClear(self):
        self.statusbarWidget.clearMessage()

    # - - - - - - - - - - - - - - - - 
    # - Name: printError
    # - Parameters: 
    # - Description: Similar to out, but for error messages
    def printError(self, text, args):
        argCount = len(args)

        #If there are an invalid number of args, throw exception
        if(argCount > 2):
            raise IOError("Invalid number of arguments")

        # 1 arg = output box only
        if(argCount == 0):
            print "SiftFlow Error: " + text
        # 2 arg = Status bar only with delay in seconds
        elif(argCount == 1):
            self.statusbarWidget.showMessage(text, args[0] * 1000)
        # 3 arg = both output and status bar with delay in seconds
        elif(argCount == 2):
            print "SiftFlow Error: " + text
            self.statusbarWidget.showMessage(args[0], args[1] * 1000)

    def conflictMessageBox(self, fileName):
        #Display dialog with options of what the user can do
        msg = "There is a conflict with " + str(fileName) + " or one if it's flows.\n\nYour options are:\n\n"
        msg += "1. Press Discard. Discard your changes and reload the tabs displaying the changed file and/or flows.\n"
        msg += "2. Press Ignore. Handle the conflict(s) manually. Tabs with possible conflicts are marked with an !\n\n"

        detailMsg = "An external application has made changes to " + str(fileName)
        detailMsg += " and you have unsaved changes for that file and/or containing functions.\n\n"
        detailMsg += "If you want to have the external changes and apply your changes too, "
        detailMsg += " copy your changes somewhere, press Discard to reload the file, then reapply your"
        detailMsg += " changes from where you copied them."

        msgBox = QtGui.QMessageBox(self.parentWindow)
        msgBox.setWindowTitle("File Conflict!")
        discardButton = msgBox.addButton("Discard", QtGui.QMessageBox.AcceptRole)
        ignoreButton = msgBox.addButton(QtGui.QMessageBox.Ignore)
        msgBox.setText(msg)
        msgBox.setDetailedText(detailMsg)

        reply = msgBox.exec_()

        #User wants to discard their changes, and reload the viewer with the external changes
        if msgBox.clickedButton() == discardButton:
            return 'discard'

        #User wants to Ignore the external changes and overwrite them with whats in the viewer
        #Add the conflict status so they can see that the viewer and file are out of sync
        elif msgBox.clickedButton() == ignoreButton:
            return 'ignore'

    def failedSaveBox(self, failedFilesList):
        msg = "The following file(s) failed to save:\n"

        for item in failedFilesList:
            msg += item + '\n'

        QtGui.QMessageBox.about(self.parentWindow, "Save Failed", msg)

    def loadedFilesTossedBox(self, filesNotAdded):
        msg = "The following file(s) are already loaded in the project and will not be loaded a second time:\n"

        for item in filesNotAdded:
            msg += item + '\n'

        QtGui.QMessageBox.about(self.parentWindow, "Load File Warning", msg)