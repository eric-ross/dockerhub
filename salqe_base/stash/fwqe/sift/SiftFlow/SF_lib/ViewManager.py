#!/usr/bin/python -d
 
import sys, os
from PyQt4 import QtCore, QtGui
from SFLibManager import *
from SiftScintilla import *
from FileManager import *

class ViewManager():
    def __init__(self, libMgr, tabWidget):
        self.libMgr = libMgr
        self.tabWidget = tabWidget
        self.fileMgr = ''
        self.commentChars = {
            'fml': '//',
            'lua': '--'
        }

        #Add Main tab
        self.addTab('Main')  

        #Set up tab bar right click menu
        self.tabWidget.tabBar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tabWidget.tabBar().customContextMenuRequested.connect(self.tabMenu)

    #--- Display Methods ---#
    
    # - - - - - - - - - - - - - - - - 
    # - Name: __displayFml() 
    # - Parameters: fmlName - name of an fml file
    # - Description: displays the whole fml file into the viewer. Handles the tabs.
    def displayFml(self, fileName, pathOrProj, tabIndex='new'):
        #If it is already displayed, switch to it and skip loading all the data
        if(self.isDisplayed(fileName, pathOrProj, setCurrent=True)):
            return

        #If the user has clicked to display a new flow in main, switch to it
        if((isinstance(tabIndex, int) and tabIndex == 0) or
                                      tabIndex == 'Main' or
                                      self.tabWidget.tabText(0) == 'Main'):
            #If main tab is unsaved, create new main tab, otherwise highjack main
            if self.doesTabHaveStatus('unsaved', 0):
                self.addTab(fileName, index=0)
            else:
                self.recycleTab(0, fileName, pathOrProj)  
        else:
            #Add a tab for new flow, if it already exists switch to it instead
            self.addTab(fileName, pathOrProj)

        fmlDat = self.fileMgr.getFmlText(fileName, pathOrProj)

        if(not fmlDat): #no fml text error
            return

        #Drop data into the code widget
        self.__getCodeWidget(fileName).setEditorText(fmlDat, fileName, pathOrProj)
        self.__getCodeWidget(fileName).setLineNumberOffset(1)

        #We now know the file on disk will be synced with the file displayed and 
        #if there was a conflict, there isn't anymore
        self.removeStatus('conflict', fileName)

        #store data for open recent menu in config file
        self.libMgr.addRecentPath(fileName, pathOrProj)
        self.removeStatus('unsaved')

        #Change syntax highlighting of code widget
        if(self.fileMgr.getFileType(fileName, pathOrProj) == ".lua"):
            self.__getCodeWidget(fileName).setLuaSyntax()
        else:
            self.__getCodeWidget(fileName).setFmlSyntax()

        #if displayed out of projectd, add status
        if(self.fileMgr.isFileInProj(fileName, pathOrProj)):
            self.removeStatus('outofproj')
        else:
            self.addStatus('outofproj')

        self.resetTabTitle()

    # - - - - - - - - - - - - - - - - 
    # - Name: __displayFlow() 
    # - Parameters: fileName - name of file, pathOrProj - if proj projName, if out of proj, path
    # -             flowName - name of a flow in the fml
    # -             tabIndex - the index (int or name) of the tab to display on
    # -             dIndex - If there are duplicate flows in an fml, the index of which copy this is
    # - Description: Find the flow/func in the file and display it in the viewer. Handles the tabs.
    def displayFlow(self, fileName, pathOrProj, flowName, tabIndex='new', dIndex=None):
        #If it is already displayed, switch to it and skip loading all the data
        if(self.isDisplayed(fileName, pathOrProj, funcName=flowName, setCurrent=True, duplicateIndex=dIndex)):
            return

        #If the user has clicked to display a new flow in main, switch to it
        if((isinstance(tabIndex, int) and tabIndex == 0) or
                                    tabIndex == 'Main' or
                                    self.tabWidget.tabText(0) == 'Main'):
            #If main tab is unsaved, create new main tab, otherwise highjack main
            if self.doesTabHaveStatus('unsaved', 0):
                self.addTab(fileName, pathOrProj, flowName, index=0, dIndex=dIndex)
            else:
                self.recycleTab(0, fileName, pathOrProj, flowName, dIndex=dIndex)
        else:
            #Add a tab for new flow, if it already exists switch to it instead
            self.addTab(fileName, pathOrProj, flowName, dIndex=dIndex)

        flowDat = self.fileMgr.getFlowText(fileName, pathOrProj, flowName, dIndex)#return [flow, start line num]

        if(not flowDat):
            return

        #Drop data into the code widget
        self.__getCodeWidget(flowName, pathOrProj, dIndex).setEditorText(flowDat[0], fileName, pathOrProj, flowName, dIndex)
        self.__getCodeWidget(flowName, pathOrProj, dIndex).setLineNumberOffset(flowDat[1])

        #We now know the file on disk will be synced with the file displayed and 
        #if there was a conflict, there isn't anymore
        self.removeStatus('conflict', flowName, pathOrProj, dIndex)

        #store data for open recent menu in config file
        self.libMgr.addRecentPath(fileName, pathOrProj, flowName, dIndex)
        self.removeStatus('unsaved', flowName, pathOrProj, dIndex)

        #Change syntax highlighting of code widget
        if(self.fileMgr.getFileType(fileName, pathOrProj) == ".lua"):
            self.__getCodeWidget(flowName, pathOrProj, dIndex).setLuaSyntax()
        else:
            self.__getCodeWidget(flowName, pathOrProj, dIndex).setFmlSyntax()

        #if displayed out of projectd, add status
        if(self.fileMgr.isFileInProj(fileName, pathOrProj)):
            self.removeStatus('outofproj', flowName, pathOrProj, dIndex)
        else:
            self.addStatus('outofproj', flowName, pathOrProj, dIndex)

        self.resetTabTitle(dIndex=dIndex)

    # - - - - - - - - - - - - - - - - 
    # - Name: __displayMotd() 
    # - Description: Gets the Motd to display on the main viewer at startup
    def displayMotd(self):
        self.__getCodeWidget(0).setEditorText(self.fileMgr.getMotd(), 'Main', None)

    #--- Tab Operations ---#

    # - - - - - - - - - - - - - - - - 
    # - Name: resetMainViewer() 
    # - Description: On project load, close all tabs but main, remove its tab tags, display motd
    def resetMainViewer(self):
        #Close all tabs but main
        for x in range(self.tabWidget.tabBar().count(), -1, -1):
            if(x > 0):
                self.tabWidget.removeTab(x)

        self.unsetSearchArea()
        self.removeStatus('all')
        self.tabWidget.setTabText(0, 'Main')
        self.displayMotd()

    # - - - - - - - - - - - - - - - - 
    # - Name: addTab(tabName) 
    # - Description: adds a tab to the main viewer tab widget with name stored in tabName
    def addTab(self, fileName, pathOrProj=None, flowName=None, index=None, dIndex=None):
        #Create the tab
        tab = QtGui.QWidget()

        #Create the code editor widget
        codeWidget = Editor(tab, self)

        #Must set data here, so the first time we getCodeWidget by name, the name is correct
        codeWidget.setEditorData(fileName, pathOrProj, flowName, dIndex=dIndex)

        layout = QtGui.QHBoxLayout()  
        layout.setMargin(0)      
        layout.addWidget(codeWidget)

        tab.setLayout(layout)

        #Add the tab to the tab widget
        if isinstance(index, int):
            self.tabWidget.insertTab(index, tab, flowName or fileName)
        else:
            self.tabWidget.addTab(tab, flowName or fileName) 

        self.tabWidget.setCurrentWidget(tab) #switch to it

        return True

    def recycleTab(self, index, fileName, pathOrProj, flowName=None, dIndex=None):
        #Instead of createing a new tab, reuse an unneeded one that is already opened
        #Typically this is used to reuse the first 'main' tab
        self.tabWidget.setCurrentIndex(index)
        self.tabWidget.setTabText(index, flowName or fileName)

        #Must set data here, so the first time we getCodeWidget by name, the name is correct
        self.__getCodeWidget(index).setEditorData(fileName, pathOrProj, flowName, dIndex)

    def reloadTab(self, index='current'):
        fileName = self.__getCodeWidget(index).getLoadedFileName()
        pathOrProj = self.__getCodeWidget(index).getLoadedPathOrProj()
        dIndex = self.__getCodeWidget(index).getLoadedDuplicateIndex()
        loadFml = False

        #if we're reloading a flow
        if(self.__getCodeWidget(index).isFunctionLoaded()):
            funcName = self.__getCodeWidget(index).getLoadedFuncName()
                #return [flow, start line num]
            flowDat = self.fileMgr.getFlowText(fileName, pathOrProj, funcName, dIndex)

            if(not flowDat):
                return

            #If the flow has been removed, remove tab or display parent
            if(flowDat[0] == '' and self.tabWidget.count() == 1):
                loadFml = True
            elif(flowDat[0] == '' and self.tabWidget.count() > 1):
                self.tabWidget.removeTab(index)
            else:
                #Drop data into the code widget
                self.__getCodeWidget(index).setEditorText(flowDat[0], fileName, pathOrProj, funcName, dIndex)
                self.__getCodeWidget(index).setLineNumberOffset(flowDat[1])

        #if we're reloading the file
        if(not self.__getCodeWidget(index).isFunctionLoaded() or loadFml):
            fmlDat = self.fileMgr.getFmlText(fileName, pathOrProj)

            if(not fmlDat): #no fml text error
                return

            #Drop data into the code widget
            self.__getCodeWidget(index).setEditorText(fmlDat, fileName, pathOrProj)
            self.__getCodeWidget(index).setLineNumberOffset(1)

        #We now know the file on disk will be synced with the file displayed and 
        #if there was a conflict, there isn't anymore
        self.removeStatus('conflict', index)

        #Since we have merely reloaded the file, take off unsaved status
        self.removeStatus('unsaved', index)

    def reloadAllFileAndFuncs(self, fileName, pathOrProj):
        #Reload any tab that is displaying something from fileName pathOrProj
        for x in range(self.tabWidget.tabBar().count()):
            if(self.__getCodeWidget(x).getLoadedFileName() == fileName and
               self.__getCodeWidget(x).getLoadedPathOrProj() == pathOrProj):
              self.reloadTab(x)

    def tabMenu(self, pos):
        save = False #For use in unsaved changes warning

        #Select Tab that was right clicked, this is messy since our version of qt was originally written by copernicus
        index = 0
        for x in range(self.tabWidget.tabBar().count()):
            if(self.tabWidget.tabBar().tabRect(x).contains(pos)):
                self.tabWidget.setCurrentIndex(x)
                index = x
                break

        menu = QtGui.QMenu()

        closeTab = menu.addAction('Close Tab')
        closeAll = menu.addAction('Close All Tabs')
        closeAllBut = menu.addAction('Close All But This')
        menu.addSeparator()
        reloadTab = menu.addAction('Reload Tab')
        reloadFileAndFuncs = menu.addAction('Reload All Associated')

        action = menu.exec_(QtGui.QCursor.pos())

        if(action == closeTab):
            if(index > 0 or self.tabWidget.tabBar().count() > 1):
                #If there are any unsaved changes, ask user what they want to do
                if(self.doesTabHaveStatus('unsaved', index)):
                    msg = "There are unsaved changes. Quitting will discharges these changes."

                    reply = QtGui.QMessageBox.question(self.libMgr.parent, "Warning", msg, QtGui.QMessageBox.Save, 
                                                        QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)

                    if reply == QtGui.QMessageBox.Save:
                        self.saveTab(index)
                    elif reply == QtGui.QMessageBox.Cancel:
                        return

                self.tabWidget.removeTab(index)

        elif(action == closeAll):
            #If there are any unsaved changes, ask user what they want to do
            if(self.anyUnsavedChanges(0)):
                msg = "There are unsaved changes. Quitting will discharges these changes."

                reply = QtGui.QMessageBox.question(self.libMgr.parent, "Warning", msg, QtGui.QMessageBox.Save, 
                                                    QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)

                if reply == QtGui.QMessageBox.Save:
                    save = True
                elif reply == QtGui.QMessageBox.Cancel:
                    return

            #If we're all set, remove the correct tabs
            for x in range(self.tabWidget.tabBar().count() - 1, -1, -1):
                if(x > 0):
                    if (save):
                        self.saveTab(x)

                    self.tabWidget.removeTab(x)

        elif(action == closeAllBut): 
            #If there are any unsaved changes, ask user what they want to do
            if(self.anyUnsavedChanges(index)):
                msg = "There are unsaved changes. Quitting will discharges these changes."

                reply = QtGui.QMessageBox.question(self.libMgr.parent, "Warning", msg, QtGui.QMessageBox.Save, 
                                                    QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)

                if reply == QtGui.QMessageBox.Save:
                    save = True
                elif reply == QtGui.QMessageBox.Cancel:
                    return

            #If we're all set, remove the correct tabs
            for x in range(self.tabWidget.tabBar().count() -1, -1, -1):
                if(x != index):
                    if(save):
                        self.saveTab(x)

                    self.tabWidget.removeTab(x)
        elif(action == reloadTab):
            self.reloadTab(index)
        elif(action == reloadFileAndFuncs):
            #Get filename and pathorproj
            fileName = self.__getCodeWidget(index).getLoadedFileName() 
            pathOrProj = self.__getCodeWidget(index).getLoadedPathOrProj()
            self.reloadAllFileAndFuncs(fileName, pathOrProj)

    # - - - - - - - - - - - - - - - - 
    # - Name: tabAlreadyExists(tabName)
    # - Parameters: tabName - string/Qstring - the name of the tab to look for
    # - Description: Check all current tab to see if a func/flow is currently displayed
    def tabAlreadyExists(self, tabName, setCurrent=False):
        #Look at all tabs, if one already exists, return True
        for x in range(self.tabWidget.count()):
            if(self.tabWidget.tabText(x) == tabName):
                if setCurrent:
                    self.tabWidget.setCurrentIndex(x)
                return True

        #If there are no matches return false
        return False

    # - - - - - - - - - - - - - - - - 
    # - Name: isFileDisplayed(fileName, pathOrProj)
    # - Description: Check all current tab to see if a func/flow is currently displayed
    def isDisplayed(self, fileName, pathOrProj, funcName=None, setCurrent=False, duplicateIndex=None):
        #Look at all tabs, if one already exists, return True
        for x in range(self.tabWidget.count()):
            if(self.__getCodeWidget(x).getLoadedFileName() == fileName and 
               self.__getCodeWidget(x).getLoadedFuncName() == funcName and 
               self.__getCodeWidget(x).getLoadedPathOrProj() == pathOrProj and
               self.__getCodeWidget(x).getLoadedDuplicateIndex() == duplicateIndex):
                if setCurrent:
                    self.tabWidget.setCurrentIndex(x)

                return True

        #If there are no matches return false
        return False

    # - - - - - - - - - - - - - - - - 
    # - Name: getDisplayedFileIndexsList(fileName, pathOrProj)
    # - Description: get a list of all the indexes of tabs that display anything from fileName pathOrProj
    def getDisplayedFileIndexsList(self,fileName, pathOrProj):
        indexs = []
        #Look at all tabs, if one is displaying something from fileName, add it to the list
        for x in range(self.tabWidget.count()):
            if(self.__getCodeWidget(x).getLoadedFileName() == fileName and 
               self.__getCodeWidget(x).getLoadedPathOrProj() == pathOrProj):
                indexs.append(x)

        return indexs

    # - - - - - - - - - - - - - - - - 
    # - Name: addStatus(statusName)
    # - Parameters: statusName - string/Qstring - which status to add to the display associated with a viewer tab
    # - Description: add a status to the display associated with a viewer tab
    def addStatus(self, statusName, index='current', pathOrProj=None, dIndex=None):
       #Remove the status item from the display associated with a viewer tab
        self.__getCodeWidget(index, pathOrProj, dIndex).addStatus(statusName)

        #Reset the title
        self.resetTabTitle(index, pathOrProj, dIndex)

    # - - - - - - - - - - - - - - - - 
    # - Name: removeStatus
    # - Description: Remove a status from the tab
    def removeStatus(self, statusName, index='current', pathOrProj=None, dIndex=None):
        #Remove the status item from the display associated with a viewer tab
        self.__getCodeWidget(index, pathOrProj, dIndex).removeStatus(statusName)

        #Reset the title
        self.resetTabTitle(index, pathOrProj, dIndex)

    # - - - - - - - - - - - - - - - - 
    # - Name: removeAllstatus(statusName)
    # - Parameters: statusName - string/Qstring - which status to remove
    # - Description: Remove all status' from the current tab
    def removeAllStatus(self, statusName='all'):
        #If no status is provided remove them all
        for x in range(self.tabWidget.count()):
            self.removeStatus(statusName, x)

    def resetTabTitle(self, index='current', pathOrProj=None, dIndex=None):
        displayText = self.__getCodeWidget(index, pathOrProj, dIndex).getStatusMarkers() + \
                      self.__getCodeWidget(index, pathOrProj, dIndex).getDisplayName() + \
                      self.__getCodeWidget(index, pathOrProj, dIndex).getDisplayDuplicate()
        widgetIndex = self.tabWidget.indexOf(self.__getCodeWidget(index, pathOrProj, dIndex).parent())
        pathOrProj = self.__getCodeWidget(index, pathOrProj, dIndex).getLoadedPathOrProj()
        fileName = self.__getCodeWidget(index, pathOrProj, dIndex).getLoadedFileName()

        #Construct tooltip text
        if(not pathOrProj):
            ttText = 'Welcome Tab'
        else:
            ttText = "File: " + str(fileName) + '\n'
            ttText += "Proj or Filepath: " + str(pathOrProj)

        self.tabWidget.setTabText(widgetIndex, displayText)
        self.tabWidget.setTabToolTip(widgetIndex, ttText)

    # - - - - - - - - - - - - - - - - 
    # - Name: doesTabHaveStatus(statusName)
    # - Parameters: statusName - string/Qstring - which tag to check
    # - Description: returns true if the displayed tab has the status
    def doesTabHaveStatus(self, statusName, index='current'):
        return self.__getCodeWidget(index).isStatus(statusName)

    def tabContainsPos(self, pos):
        #If the mouse is on the tab when its clicked
        return self.tabWidget.tabBar().tabRect(self.tabWidget.currentIndex()).contains(pos)

    #--- Find and Replace Methods ---#
    def findTextCurrent(self, text, flags, flip):
        #If find previous, must set find to reverse, then call findNext, qscintilla oddity
        if(not flags['forward']):
            toRet = self.__getCodeWidget('current').findFirst(text,
                                                         flags['re'],
                                                         flags['cs'],
                                                         flags['wo'],
                                                         flags['wrap'],
                                                         flags['forward'],
                                                         flags['line'],
                                                         flags['index'])

            #If this is the first search, we don't want to findNext or it'll skip the first find at the bottom
            if(self.doesTabHaveStatus('search') and not flip):
                return self.__getCodeWidget('current').findNext()
            else:
                return toRet

        #Find Next search
        return self.__getCodeWidget('current').findFirst(text,
                                                         flags['re'],
                                                         flags['cs'],
                                                         flags['wo'],
                                                         flags['wrap'],
                                                         flags['forward'],
                                                         flags['line'],
                                                         flags['index'])


    #---- Text Widget Cursor Operations ----#
    def setCursorToReference(self, line, pos):
        #Since line number on bar is only visual, must recalculate real line number to select right line
        lineNum = line - self.__getCodeWidget('current').lineNumberOffset() + 1
        lineEnd = self.__getCodeWidget('current').lineLength(lineNum)
        self.__getCodeWidget('current').setSelection(lineNum, pos, lineNum, lineEnd)

    def getCursorBeginning(self):
        return self.__getCodeWidget('current').getCursorBeginning()

    def getCursorEnd(self):
        return self.__getCodeWidget('current').getCursorEnd()

    def getSearchAreaBeginning(self):
        return self.__getCodeWidget('current').getSearchAreaBeginning()

    def getSearchAreaEnd(self):
        return self.__getCodeWidget('current').getSearchAreaEnd()

    def setSearchArea(self):
        return self.__getCodeWidget('current').setSearchArea()

    def reselectSearchArea(self):
        self.__getCodeWidget('current').reselectSearchArea()

    def unsetSearchArea(self):
        self.__getCodeWidget('current').clearSearchArea()

    def unsetAllSearchAreas(self):
        for x in range(self.tabWidget.count()):
            self.__getCodeWidget(x).clearSearchArea()

    #--- Reference Display ---#
    def getCurrentReferences(self, reg, flag):
        refs = []
        currentFlow = 'n/a'

        funcName = self.__getCodeWidget('current').getLoadedFuncName()
        fileName = self.__getCodeWidget('current').getLoadedFileName()
        pathOrProj = self.__getCodeWidget('current').getLoadedPathOrProj()

        #Determine if search if from func or file
        if(funcName):
            sType = 'func'
            refs.append([sType, fileName + '?' + pathOrProj + '?' + funcName + '?' 
                        + self.__getCodeWidget('current').getDisplayDuplicate()])
        else:
            sType = 'file'
            refs.append([sType, fileName, pathOrProj])

        for lineNum in range(self.__getCodeWidget('current').lines()):
            line = self.__getCodeWidget('current').text(lineNum)

            if(sType == 'file'):
                #Store flows as we go so we can display which flow the match is in
                matches = re.findall(str("^flow\s+flow_.*\s?\("), line, re.I) 
                if(len(matches) > 0):
                    currentFlow = matches[0][5:] #chop off flow 

                #Mark end of flow in case match is in space between flows or not in flows at all (global.fml)
                matches = re.findall(str("^\s*endflow"), line, re.I) 
                if(len(matches) > 0):
                    currentFlow = 'n/a'

            finds = re.findall(reg, line, flag)
            if(len(finds) > 0):
                for match in finds:
                    offset = self.getLineNumberOffset()

                    if(sType == 'file'):
                        toOut = [str(lineNum + offset), str(currentFlow).strip('\n ('), str(line).strip('\n ')]
                    else:
                        toOut = [str(lineNum + offset), str(line).strip('\n ')]

                    refs.append(toOut)

        return refs

    def getSelectionReferences(self, reg, flag):
        refs = []
        fileName = self.__getCodeWidget('current').getLoadedFileName()
        pathOrProj = self.__getCodeWidget('current').getLoadedPathOrProj()

        #If no text is selected
        if(self.__getCodeWidget('current').selectedText().isEmpty()):
            return 'noselection'

        begPos = self.getCursorBeginning()
        endPos = self.getCursorEnd()

        currentFlow = 'n/a'

        #Determine if search if from func or file
        if(re.search('flow_.*', self.tabWidget.tabText(self.tabWidget.currentIndex()))):
            sType = 'func'
            refs.append([sType, fileName + '?' + pathOrProj])
        else:
            sType = 'file'
            refs.append([sType, fileName, pathOrProj])

        text = self.getSelectionText()

        textLines = text.split('\n')

        for x,line in enumerate(textLines):
            lineNum = begPos[0] + x + 1

            if(sType == 'file'):
                #Store flows as we go so we can display which flow the match is in
                matches = re.findall(str("^flow\s+flow_.*\s?\("), line, re.I) 
                if(len(matches) > 0):
                    currentFlow = matches[0][5:] #chop off flow 
    
                #Mark end of flow in case match is in space between flows or not in flows at all (global.fml)
                matches = re.findall(str("^\s*endflow"), line, re.I) 
                if(len(matches) > 0):
                    currentFlow = 'n/a'

            finds = re.findall(reg, line, flag)
            if(len(finds) > 0):
                for match in finds:
                    offset = self.getLineNumberOffset()

                    if(sType == 'file'):
                        toOut = [str(lineNum + offset), str(currentFlow).strip('\n ('), str(line).strip('\n ')]
                    else:
                        toOut = [str(lineNum + offset), str(line).strip('\n ')]

                    # Tack on fileName and pathorproj to use when displaying
                    refs.append(toOut)

        return refs

    def getCountSelection(self, reg, flag):
        begPos = self.getCursorBeginning()
        endPos = self.getCursorEnd()
        count = 0
        text = self.getSelectionText()

        textLines = text.split('\n')

        for line in textLines:
            finds = re.findall(reg, line, flag)

            count += len(finds)
        return count

    def getCountCurrent(self, reg, flag):
        count = 0

        for lineNum in range(self.__getCodeWidget('current').lines()):
            line = self.__getCodeWidget('current').text(lineNum)
            finds = re.findall(reg, line, flag)
            count += len(finds)
        return count

    #--- Edit Related Methods ---#
    def cut(self):
        self.__getCodeWidget('current').cut()

    def copy(self):
        self.__getCodeWidget('current').copy()

    def paste(self):
        self.__getCodeWidget('current').paste()

    def undo(self):
        self.__getCodeWidget('current').undo()

    def redo(self):
        self.__getCodeWidget('current').redo()

    def indent(self):
        sBeg = self.getCursorBeginning()[0]
        sEnd = self.getCursorEnd()[0]

        self.beginUndoAction()
        while sBeg != sEnd + 1:
            self.__getCodeWidget('current').indent(sBeg)
            sBeg += 1

        self.endUndoAction()

    def unindent(self):
        sBeg = self.getCursorBeginning()[0]
        sEnd = self.getCursorEnd()[0]


        self.beginUndoAction()
        while sBeg != sEnd + 1:
            self.__getCodeWidget('current').unindent(sBeg)
            sBeg += 1

        self.endUndoAction()

    def comment(self):
        sBeg = self.getCursorBeginning()[0]
        sEnd = self.getCursorEnd()[0]

        #select comment chars that are in the current editor
        comChars = self.commentChars[self.__getCodeWidget('current').getLoadedFileType()]

        if(not self.__getCodeWidget('current').selectedText().isEmpty()): #if there is no selection, skip

            self.beginUndoAction()
            while sBeg != sEnd + 1:
                index = self.__getCodeWidget('current').text(sBeg).indexOf(QtCore.QRegExp('[^\s\t]'))

                #if the line contains no text, don't comment it out
                if(index > -1):
                    self.__getCodeWidget('current').insertAt(comChars, sBeg, index)
                sBeg += 1

            self.endUndoAction()

    def uncomment(self):
        #Get the selected text, go line by line and remove first comment chars, use replace to 
        #replace the selected text with the new altered text
        text = self.__getCodeWidget('current').selectedText().split('\n')

        #select comment chars that are in the current editor
        comChars = self.commentChars[self.__getCodeWidget('current').getLoadedFileType()]

        for x in range(len(text)):
            index = text[x].indexOf(QtCore.QRegExp('[^\s\t]'))

            #If line is not long enough, empty, then skip it to avoid array out of bounds
            if(len(text[x]) > len(self.commentChars) and text[x].contains(QtCore.QRegExp('^[\s\t]*' + re.escape(comChars)))):
                text[x] = text[x].remove(index, len(comChars))

        #reassemble text into one block
        text = text.join('\n')

        #replace old with new
        self.__getCodeWidget('current').replaceSelectedText(text)

    def replace(self, text):
        #Only replace if there is something selected
        if(self.getSelectionText() != ''):
            self.__getCodeWidget('current').replaceSelectedText(text)

    def beginUndoAction(self):
        self.__getCodeWidget('current').beginUndoAction()

    def endUndoAction(self):
        self.__getCodeWidget('current').endUndoAction()

    # - - - - - - - - - - - - - - - - 
    # - Name: saveTab() 
    # - Description: Saves the current tab to the .fml file. If the tab contains a whole fml
    # - just save it. If the tab contains a flow, cut into the correct fml and save
    def saveTab(self, index='current'):
        #Setup needed variables
        text = str(self.__getCodeWidget(index).text())
        fileName = self.__getCodeWidget(index).getLoadedFileName()
        funcName = self.__getCodeWidget(index).getLoadedFuncName()
        pathOrProj = self.__getCodeWidget(index).getLoadedPathOrProj()
        dIndex = self.__getCodeWidget(index).getLoadedDuplicateIndex()
        resultList = []

        #Only save if we're not saving the main tab or something that isn't unsaved
        if(fileName == 'Main'):
            #If the user has tried to save the main tab, just ignore it and let them know
            self.libMgr.out("Can't save Main tab.", 5)

        elif(self.doesTabHaveStatus('unsaved', index)):
            #if flow, reset starting line number incase something have been saved previously that changes it in the .fml file
            if(funcName):
                offset = self.fileMgr.getLineNumberOffset(fileName, pathOrProj, funcName, dIndex)
                self.__getCodeWidget(index).setLineNumberOffset(offset)

            #Don't allow the file to be reloaded on file change for this save (causes time and the viewer to reset)
            self.fileMgr.ignoreFileChange(fileName, pathOrProj, skipOnce=True)

            #If save was succesful
            if(self.fileMgr.save(text, fileName, pathOrProj, funcName, self.__getCodeWidget(index).lineNumberOffset() - 1)):
                self.libMgr.out(fileName + ' saved successfully', 6)

                #We now know the file on disk will be synced with the file displayed and 
                #if there was a conflict, there isn't anymore
                self.removeStatus('conflict', index)
                self.removeStatus('unsaved', index)

                #Reload the files treeview entry in case the save has added/removed a flow
                self.libMgr.reloadFileTreeview(fileName, pathOrProj)

            else: #save failed
                resultList.append(fileName)

        return resultList #If save success, empty list (no failures), if save failed, one element with fileName

    # - - - - - - - - - - - - - - - - 
    # - Name: saveAllTabs() 
    # - Description: Saves all tabs that have not been saved (ie not tagged as unsaved)
    # - In case there is a .fml and a flow from that fml open, save the .fmls first so they
    # - flows will overwrite there contents in the .fml file
    def saveAllTabs(self):
        resultList = []

        #save all files first
        for x in range(self.tabWidget.count()):
            #Only save if the tab is tagged as unsaved and is a .fml
            if(self.doesTabHaveStatus('unsaved', x) and self.__getCodeWidget(x).isFileLoaded()):
                result = self.saveTab(x)
                if(len(result) > 0):
                    resultList.append(result)

        #Save all funcs next, so they would overwrite in the .fml if there was a conflict
        for x in range(self.tabWidget.count()):
            #Only save if the tab is tagged as unsaved and is a func
            if(self.doesTabHaveStatus('unsaved', x) and self.__getCodeWidget(x).isFunctionLoaded()):
                result = self.saveTab(x)
                if(len(result) > 0):
                    resultList.append(result)

        return resultList

    # - - - - - - - - - - - - - - - - 
    # - Name: anyUnsavedChanges() 
    # - Description: If any tabs are unsaved return true. Index is tab to skip
    def anyUnsavedChanges(self, index=-1):
        for x in range(self.tabWidget.count()):
            if(x != index and self.doesTabHaveStatus('unsaved', x)):
                return True

        return False

    def saveAnyUnsavedChanges(self):
        for x in range(self.tabWidget.count()):
            if(self.doesTabHaveStatus('unsaved', x)):
                self.saveTab(x)

    def getLoadDataCurrent(self):
        fileName = self.__getCodeWidget('current').getLoadedFileName()
        pathOrProj = self.__getCodeWidget('current').getLoadedPathOrProj()
        time = self.__getCodeWidget('current').getLoadTime()

        return [fileName, pathOrProj, time]

    def getLoadDataAll(self):
        dataList = []
        for x in range(self.tabWidget.count()):
            fileName = self.__getCodeWidget(x).getLoadedFileName()
            pathOrProj = self.__getCodeWidget(x).getLoadedPathOrProj()
            time = self.__getCodeWidget(x).getLoadTime()
            dataList.append([fileName, pathOrProj, time])

        return dataList

    #--- Setters, Getters, Helpers ---#
    def setFileManager(self, fileMgr):
        self.fileMgr = fileMgr

    def getCurrentTabText(self):
        return self.tabWidget.tabText(self.tabWidget.currentIndex())

    def getSelectionText(self):
        return str(self.__getCodeWidget('current').selectedText())

    def getLineNumberOffset(self):
        return self.__getCodeWidget('current').lineNumberOffset()

    def __getCodeWidget(self, index, pathOrProj=None, dIndex=None):
        #If Index is an int, return the text at that index, mainly used to get main tab
        if(isinstance(index, int)):
            return self.tabWidget.widget(index).layout().itemAt(0).widget()

        #If index is a string or a qstring
        else:
            #Return the current tab
            if(index == 'current'):
                return self.tabWidget.currentWidget().layout().itemAt(0).widget()

            #Return by the tab title text
            for x in range(self.tabWidget.count()):
                widg = self.tabWidget.widget(x).layout().itemAt(0).widget()

                if(str(index) == str(widg.getDisplayName()) and
                    dIndex == widg.getLoadedDuplicateIndex() and
                    (not pathOrProj or pathOrProj==widg.getLoadedPathOrProj())):
                    return widg

