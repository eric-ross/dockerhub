#!/usr/bin/python -d
 
import sys
from PyQt4 import QtCore, QtGui
from SF_ui.replace import Ui_Replace
from SF_lib.SFLibManager import *

class Replace(QtGui.QDialog):
    def __init__(self, parent, libMgr):
        QtGui.QDialog.__init__(self, parent)
        self.libMgr = libMgr
        self.mainWin = parent

        self.ui = Ui_Replace()
        self.ui.setupUi(self)

        #Init config options
        self.libMgr.loadCombo(self.ui.comboBox_find)
        self.libMgr.loadCombo(self.ui.comboBox_replace)
        self.__loadConfigOps(self.libMgr.getConfigDict('replace'))

        #If there is a selection in the current viewer, set the combo text to it if it meets criteria
        selection = self.libMgr.getSelectionText()
        self.ui.comboBox_find.setEditText(self.libMgr.selectionToFill(selection))

        self.ui.comboBox_replace.setEditText('')

        #Set autocompleter to case sensitive so that current item is on whats in the text field
        #rather the being switched to a match that only differs by case
        self.ui.comboBox_find.setAutoCompletionCaseSensitivity(QtCore.Qt.CaseSensitive)

        #set up icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "findreplace.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        #Set up actions and signals
        QtCore.QObject.connect(self.ui.pushButton_findnext, QtCore.SIGNAL("clicked()"), self.__findNext)
        QtCore.QObject.connect(self.ui.pushButton_findprev, QtCore.SIGNAL("clicked()"), self.__findPrev)
        QtCore.QObject.connect(self.ui.pushButton_replace, QtCore.SIGNAL("clicked()"), self.__replace)
        QtCore.QObject.connect(self.ui.pushButton_replaceall, QtCore.SIGNAL("clicked()"), self.__replaceAll)
        QtCore.QObject.connect(self.ui.pushButton_count, QtCore.SIGNAL("clicked()"), self.__count)
        QtCore.QObject.connect(self.ui.pushButton_findinfiles, QtCore.SIGNAL("clicked()"), self.__findInFiles)
        QtCore.QObject.connect(self.ui.radioButton_current, QtCore.SIGNAL("clicked()"), self.__finishSearch)
        QtCore.QObject.connect(self.ui.radioButton_selection, QtCore.SIGNAL("clicked()"), self.__finishSearch)

        #Disable find and replace actions so only one can be opened at a time
        self.mainWin.setFindReplaceEnabled(False)

    #--- Button Handlers ---#
    def __findNext(self):
        #Set the Find Next button as the default button if it wasn't already
        self.ui.pushButton_findnext.setDefault(True)

        #If find is empty, don't process, inform user
        if(self.ui.comboBox_find.currentText().isEmpty()):
            self.libMgr.out("Find field is empty", 5)
            return

        #Update history for the combo box to include new text
        self.__updateFindHistory()

        #Get find flags depending on the search options, start search forward
        flags = self.__getFlags(True)

        #Do the search, depending on which 'find in' option is checked
        if(self.ui.radioButton_current.isChecked()): #Search current file
            #If the references option is used, display the finds line number and line in output
            if(self.ui.radioButton_reference.isChecked()):
                self.mainWin.reference(self.ui.comboBox_find.currentText(), flags, True)
                return

            #If match, note to skip cursor setting
            if(self.libMgr.findTextCurrent(self.ui.comboBox_find.currentText(), flags)):
                self.libMgr.startSearch()
            #No match, if wrapping, reset cursor to start over, it not tell user its over
            else:
                self.__noMatch('next', flags)

        elif(self.ui.radioButton_selection.isChecked()):
            #If the references option is used, display the finds line number and line in output
            if(self.ui.radioButton_reference.isChecked()):
                self.mainWin.reference(self.ui.comboBox_find.currentText(), flags, False)
                return

            #Set beginning and end select point, if its first search
            if(self.libMgr.isFirstSearch()):
                #if the search area beg and end is same (ie jut the cursor and no selection) tell user, return
                if(not self.libMgr.setSearchArea()):
                    QtGui.QMessageBox.about(self, "Selection Status", "There is no text selected.")
                    return

                #Set search to the start of the selection, or end if bottom is checked
                if(self.ui.radioButton_selection.isChecked() and not self.ui.radioButton_bottom.isChecked()):
                    flags['line'], flags['index'] = self.libMgr.getCursorBeginning()
                elif(self.ui.radioButton_selection.isChecked() and self.ui.radioButton_bottom.isChecked()):
                    flags['line'], flags['index'] = self.libMgr.getCursorEnd()

            if(self.libMgr.findTextCurrent(self.ui.comboBox_find.currentText(), flags)):
                #If theres a match and its not passed the selection, success
                if(self.libMgr.isCursorInSearchArea()):
                    self.libMgr.startSearch()
                #If theres a match, but its passed the end of the selection, tell user no matches
                else:
                    self.__noMatch('next', flags)
                    
            #No match, if wrapping, reset cursor to start over, it not tell user its over
            else:
                self.__noMatch('next', flags)

    def __findPrev(self):
        #Set the Find Prev button as the default button if it wasn't already
        self.ui.pushButton_findprev.setDefault(True)

        #If find is empty, don't process, inform user
        if(self.ui.comboBox_find.currentText().isEmpty()):
            self.libMgr.out("Find field is empty", 5)
            return

        #Update history for the combo box to include new text
        self.__updateFindHistory()

        #Get find flags depending on the search options, start search backwards
        flags = self.__getFlags(False)

        #Do the search, depending on which 'find in' option is checked
        if(self.ui.radioButton_current.isChecked()): #Search current file
            #If the references option is used, display the finds line number and line in output
            if(self.ui.radioButton_reference.isChecked()):
                self.mainWin.reference(self.ui.comboBox_find.currentText(), flags, True)
                return

            #If match, note to skip cursor setting
            if(self.libMgr.findTextCurrent(self.ui.comboBox_find.currentText(), flags)):
                self.libMgr.startSearch()
            #No match, if wrapping, reset cursor to start over, it not tell user its over
            else:
                self.__noMatch('prev', flags)

        elif(self.ui.radioButton_selection.isChecked()):
            #If the references option is used, display the finds line number and line in output
            if(self.ui.radioButton_reference.isChecked()):
                self.mainWin.reference(self.ui.comboBox_find.currentText(), flags, False)
                return

            #Set beginning and end select point, if its first search
            if(self.libMgr.isFirstSearch()):
                #if the search area beg and end is same (ie jut the cursor and no selection) tell user, return
                if(not self.libMgr.setSearchArea()):
                    QtGui.QMessageBox.about(self, "Selection Status", "There is no text selected.")
                    return

                #Set search to the start of the selection, or end if bottom is checked
                if(not self.ui.radioButton_bottom.isChecked()):
                    flags['line'], flags['index'] = self.libMgr.getCursorBeginning()
                elif(self.ui.radioButton_bottom.isChecked()):
                    flags['line'], flags['index'] = self.libMgr.getCursorEnd()

            if(self.libMgr.findTextCurrent(self.ui.comboBox_find.currentText(), flags)):
                #If theres a match and its not passed the selection, success
                if(self.libMgr.isCursorInSearchArea()):
                    self.libMgr.startSearch()
                #If theres a match, but its passed the end of the selection, tell user no matches
                else:
                    self.__noMatch('prev', flags)
                    
            #No match, if wrapping, reset cursor to start over, it not tell user its over
            else:
                self.__noMatch('prev', flags)

    def __count(self):
        count = 0
        cs = ''

        #Get find flags depending on the search options
        flags = self.__getFlags(True)

        #Current
        if(self.ui.radioButton_current.isChecked()):
            count = self.libMgr.getCount(self.ui.comboBox_find.currentText(), flags, True)
            cs = " current file."

        #Selection
        elif(self.ui.radioButton_selection.isChecked()):
            count = self.libMgr.getCount(self.ui.comboBox_find.currentText(), flags, False)
            cs = " selection."

        QtGui.QMessageBox.about(self, "Count", str(count) + " matches in the " + cs)

    def __findInFiles(self):
        #If find is empty, don't process, inform user
        if(self.ui.comboBox_find.currentText().isEmpty()):
            self.libMgr.out("Find field is empty", 5)
            return

        #Update history for the combo box to include new text
        self.__updateFindHistory()

        #Get find flags depending on the search options
        flags = self.__getFlags(True)

        #If the references option is used, display the finds line number and line in output
        if(self.ui.radioButton_reference.isChecked()):
            self.mainWin.reference(self.ui.comboBox_find.currentText(), flags, 'all')
            return

        #Find any .fml with a match and display it in a new tab
        self.libMgr.findAllOpenFmls(self.ui.comboBox_find.currentText(), flags)

    def __replace(self):
        #Update history for the combo box to include new text
        self.__updateFindHistory()
        self.__updateReplaceHistory()

        #If find is empty, don't process, inform user
        if(self.ui.comboBox_find.currentText().isEmpty()):
            self.libMgr.out("Find field is empty", 5)
            return

        self.__findNext()
        self.libMgr.replace(self.ui.comboBox_replace.currentText())

    def __replaceAll(self):
        #Update history for the combo box to include new text
        self.__updateFindHistory()
        self.__updateReplaceHistory()

        #If find is empty, don't process, inform user
        if(self.ui.comboBox_find.currentText().isEmpty()):
            self.libMgr.out("Find field is empty", 5)
            return

        flags = self.__getFlags(True)
        flags['wrap'] = False #never wrap with this, would be infinite loop in libMgr

        #Set the search area to reselect after the replace
        saResult = self.libMgr.setSearchArea()
        self.libMgr.beginUndoAction()

        if(self.ui.radioButton_current.isChecked()): #Search current file
            #Always start from the beginning of the page
            flags['line'] = 0
            flags['index'] = 0

            #If the selected text and find text match, then selected text was autofilled, replace it
            if(self.ui.comboBox_find.currentText() == self.libMgr.getSelectionText()):
                self.libMgr.replace(self.ui.comboBox_replace.currentText())

            while (self.libMgr.findTextCurrent(self.ui.comboBox_find.currentText(), flags)):
                self.libMgr.replace(self.ui.comboBox_replace.currentText())


        elif(self.ui.radioButton_selection.isChecked()):
            #if the search area beg and end is same (ie jut the cursor and no selection) tell user, return
            if(not saResult):
                QtGui.QMessageBox.about(self, "Selection Status", "There is no text selected.")
                return

            flags['line'], flags['index'] = self.libMgr.getCursorBeginning()

            while(self.libMgr.findTextCurrent(self.ui.comboBox_find.currentText(), flags) and self.libMgr.isCursorInSearchArea()):
                self.libMgr.replace(self.ui.comboBox_replace.currentText())


        self.libMgr.reselectSearchArea()
        self.libMgr.unsetSearchArea()
        self.libMgr.endUndoAction()

    #--- Event Handlers ---#
    def closeEvent(self, re):
         #Remove all search selections
        self.libMgr.finishAllSearchs()

        #Gather all the options to store and pass them to the config manager
        self.libMgr.updateConfigOptions(self.__gatherOptions(), 'replace')

        #Renable dialog actions
        self.mainWin.setFindReplaceEnabled(True)

    def reject(self):
        self.close()

    #--- Private and Helper Methods ---#
    def __finishSearch(self):
        self.libMgr.finishSearch()

    def __getFlags(self, startForward):
        flags = {
            're':        self.ui.checkBox_re.isChecked(), 
            'cs':        self.ui.checkBox_case.isChecked(),
            'wo':        self.ui.checkBox_verbatim.isChecked(),
            'wrap':      self.ui.checkBox_wrap.isChecked(),
            'forward':   startForward,
            'line':      -1,
            'index':     -1
        }

        return flags

    def __noMatch(self, caller, flags):
         #If Not wrapping reselect the original area and reset the search
        if(not self.ui.checkBox_wrap.isChecked()):
            if(self.ui.radioButton_selection.isChecked()):
                self.libMgr.reselectSearchArea()

            self.libMgr.finishSearch()
            QtGui.QMessageBox.about(self, "Match Status", "There are no more matches in the selection.")
        #If wrapping, just move the cursor back to the selection beginning
        else:
            #Smartly set the 'start from' radio depending on what the user has pushed
            if(caller == 'next'): # findNext has called
                #tell cursor to circle to the top
                flags['line'], flags['index'] = self.libMgr.getSearchAreaBeginning()
                self.ui.radioButton_top.setChecked(True)
            else: #If findPrev has called
                #tell cursor to circle around to the bottom
                flags['line'], flags['index'] = self.libMgr.getSearchAreaEnd()
                self.ui.radioButton_bottom.setChecked(True)

            self.libMgr.findTextCurrent(self.ui.comboBox_find.currentText(), flags, True)

    #--- Private and Helper Methods ---#
    def __updateFindHistory(self):
        #If that item is not in the combobox, add it to the history
        text = self.ui.comboBox_find.currentText()
        index = self.ui.comboBox_find.findText(text)

        if(not text.isEmpty()):
            if(index == -1):
                self.libMgr.addFindHistoryEntry(self.ui.comboBox_find)
            else:
                #If it already exists, move it to the top of the history and remove its old duplicate from the combo
                self.libMgr.updateComboHistoryEntry(self.ui.comboBox_find)

            self.libMgr.loadCombo(self.ui.comboBox_find)

    def __updateReplaceHistory(self):
        #If that item is not in the combobox, add it to the history
        text = self.ui.comboBox_replace.currentText()
        index = self.ui.comboBox_replace.findText(text)

        if(not text.isEmpty()):
            if(index == -1):
                self.libMgr.addReplaceHistoryEntry(self.ui.comboBox_replace)
            else:
                #If it already exists, move it to the top of the history and remove its old duplicate from the combo
                self.libMgr.updateComboHistoryEntry(self.ui.comboBox_replace)

            self.libMgr.loadCombo(self.ui.comboBox_replace)

    def __loadConfigOps(self, ops_d):
        #Set all the radio and check widgets using what was stored in config.ini
        if(ops_d['search_mode'] == 'reference'):
            self.ui.radioButton_reference.setChecked(True)

        if(ops_d['find_in'] == 'selection'):
            self.ui.radioButton_selection.setChecked(True)

        if(ops_d['start_from'] == 'bottom'):
            self.ui.radioButton_bottom.setChecked(True)

        if(ops_d['verbatim'] == 'True'):
            self.ui.checkBox_verbatim.setChecked(True)
        if(ops_d['wrap'] == 'True'):
            self.ui.checkBox_wrap.setChecked(True)
        if(ops_d['case'] == 'True'):
            self.ui.checkBox_case.setChecked(True)
            
    def __gatherOptions(self):
        ops_d = {}

        #Search Mode
        if(self.ui.radioButton_normal.isChecked()):
            ops_d['search_mode'] = 'normal'
        else:
            ops_d['search_mode'] = 'reference'

        #Find in
        if(self.ui.radioButton_current.isChecked()):
            ops_d['find_in'] = 'current'
        else:
            ops_d['find_in'] = 'selection'

        #Start From
        if(self.ui.radioButton_top.isChecked()):
            ops_d['start_from'] = 'top'
        else:
            ops_d['start_from'] = 'bottom'

        #Search ops - verbatim
        if(self.ui.checkBox_verbatim.isChecked()):
            ops_d['verbatim'] = 'True'
        else:
            ops_d['verbatim'] = 'False'

        #Search ops - wrap
        if(self.ui.checkBox_wrap.isChecked()):
            ops_d['wrap'] = 'True'
        else:
            ops_d['wrap'] = 'False'

        #Search ops - case
        if(self.ui.checkBox_case.isChecked()):
            ops_d['case'] = 'True'
        else:
            ops_d['case'] = 'False'

        return ops_d

