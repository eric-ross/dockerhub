#!/usr/bin/python -d
 
import sys
from PyQt4 import QtCore, QtGui
from SF_ui.reference import Ui_Reference
from SF_lib.SFLibManager import *

class Reference(QtGui.QDialog):
    def __init__(self, parent, libMgr):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Reference()
        self.libMgr = libMgr
        self.mainWin = parent
        self.ui.setupUi(self)
        self.tabWidget = self.ui.tabWidget_reference
        self.searchFlags = {}

        #Set up icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "findreference.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        #Set up tab bar right click menu
        self.tabWidget.tabBar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tabWidget.tabBar().customContextMenuRequested.connect(self.tabMenu)

    def addSearch(self, text, flags, isCurrent):
        #If search is from viewer, get text from selection
        if(text == 'none'):
            sText = self.libMgr.getSelectionText()

            #If there is no selection tell user and bail
            if(sText == ''):
                self.libMgr.out('Find unsuccessful. No text Selected', 6)
                return
        else:
            sText = text

        #get flags if none are provided
        if(flags == None):
            fFlags = self.__getFlags()
        else:
            fFlags = flags

        #If user is searching all files for references
        if(isCurrent == 'all'):
            entries = self.libMgr.findReferencesInFiles(sText, fFlags)
        else: #If searching for either current file or selection
            entries = self.libMgr.findReferences(sText, fFlags, isCurrent)

        #If entries is empty, then nothing was found
        if(len(entries) < 1):
            return False
        #If tab is already opened, just refresh it and make it current
        elif(self.tabAlreadyExists(sText)):
            self.resetTab(sText, fFlags, isCurrent)
            return True
        elif(isinstance(entries, str)): #if error code (string)
            return entries

        #If the window has just been opened
        title = re.sub(r'\\(.)', r'\1', str(sText)) #unescape so the title doestn' look wierd
        if(self.tabWidget.tabText(0) == 'Tab 1'):
            self.addTab(title)
            self.tabWidget.removeTab(0)
        else:
            self.addTab(title)

        #Store data in a dictionary in case we need to reset the tabs results
        self.searchFlags[title] = fFlags

        self.fillTable(self.__getTableWidget('current'), entries)
        return True

    def fillTable(self, table, entries):
        #Set up Header
        headers = ['Line']
        if(entries[0][0] == 'func'): #From Flow only
            headers += ['Text']
        elif(entries[0][0] == 'file'): #from file
            headers += ['Flow', 'Text']
        elif(entries[0][0] == 'all'): #from all files
            headers += ['Flow', 'File', 'Text', 'File Source']

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setColumnWidth(0, 45)

        for x,line in enumerate(entries):
            table.insertRow(x)

            for y, item in enumerate(line):
                new = QtGui.QTableWidgetItem(item)
                table.setItem(x, y, new)

        # Hide first row since it is just table config data
        table.hideRow(0)
        table.verticalHeader().setVisible(False)

    # - - - - - - - - - - - - - - - - 
    # - Name: addTab(tabName) 
    # - Parameters: tabName - string - the desired name of the tab
    # - Description: adds a tab to the main viewer tab widget with name stored in tabName
    def addTab(self, tabName, index=-1):
        #If the tab already exists, don't create a new one
        if(self.tabAlreadyExists(tabName)):
            return False #tab not created

        #Create the tab
        tab = QtGui.QWidget()

        headers = ['Line']

        #Create the table editor widget
        tableWidget = QtGui.QTableWidget(self)
        tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        tableWidget.horizontalHeader().setStretchLastSection(True)
        QtCore.QObject.connect(tableWidget, QtCore.SIGNAL("cellDoubleClicked(int, int)"), self.cellDoubleClicked)

        layout = QtGui.QHBoxLayout()  
        layout.setMargin(0)      
        layout.addWidget(tableWidget)

        tab.setLayout(layout)

        #Add the tab to the tab widget
        if(index == -1):
            self.tabWidget.addTab(tab, tabName)
        else:
            self.tabWidget.insertTab(index, tab, tabName)
        self.tabWidget.setCurrentWidget(tab)

        return True

    def resetTab(self, sText, fFlags, sType):
        #If tab is a search all files
        if(sType == 'all'):
            entries = self.libMgr.findReferencesInFiles(sText, fFlags)
        else: #If searching for either current file or selection
            entries = self.libMgr.findReferences(sText, fFlags, sType)

        #Clear current rows and start over
        self.__getTableWidget(sText).clear()
        self.__getTableWidget(sText).setRowCount(0)

        self.fillTable(self.__getTableWidget(sText), entries)

        self.setCurrentWidgetByTitle(sText)

    def resetTabs(self):
        #For each tab, reset its contents in case a save has changed the results
        for x in range(self.tabWidget.count()):
            sText = self.tabWidget.tabText(x)
            fFlags = self.searchFlags[str(sText)]
            sType = str(self.__getTableWidget(x).item(0, 0).text())

            #If tab is a search all files
            if(sType == 'all'):
                entries = self.libMgr.findReferencesInFiles(sText, fFlags)
            else: #If searching for either current file or selection
                entries = self.libMgr.findReferences(sText, fFlags, sType)

            #Clear current rows and start over
            self.__getTableWidget(x).clear()
            self.__getTableWidget(x).setRowCount(0)

            self.fillTable(self.__getTableWidget(x), entries)

    def removeSearchTab(self, index):
        #remove the entry from the search tags directory
        del(self.searchFlags[str(self.tabWidget.tabText(index))])

        #remove the actual tab
        self.tabWidget.removeTab(index)

    def setCurrentWidgetByTitle(self, title):
        for x in range(self.tabWidget.count()):
            if(title == self.tabWidget.tabText(x)):
                self.tabWidget.setCurrentIndex(x)

    def tabMenu(self, pos):
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

        action = menu.exec_(QtGui.QCursor.pos())

        if(action == closeTab):
            self.removeSearchTab(index)
        elif(action == closeAll):
            for x in range(self.tabWidget.tabBar().count(), -1, -1):
                if(x > 0):
                    self.removeSearchTab(x)
        elif(action == closeAllBut):
            for x in range(self.tabWidget.tabBar().count(), -1, -1):
                if(x != index):
                    self.removeSearchTab(x)

    # - - - - - - - - - - - - - - - - 
    # - Name: tabAlreadyExists(tabName)
    # - Parameters: tabName - string/Qstring - the name of the tab to look for
    # - Description: Check all current tab to see if a tab with that name already exists
    def tabAlreadyExists(self, tabName):
        #Look at all tabs, if one already exists, return True
        for x in range(self.tabWidget.count()):
            if(self.tabWidget.tabText(x) == tabName):
                return True

        #If there are no matches return false
        return False

    def __getFlags(self):
        flags = {
            're':        False, 
            'cs':        False,
            'wo':        False
        }

        return flags

    def __getTableWidget(self, index):
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
                if(self.tabWidget.tabText(x) == index):
                    return self.tabWidget.widget(x).layout().itemAt(0).widget()

    def getDuplicateIndexFromFuncName(self, funcName):
        index = None
        retFunc = funcName
        if(funcName.contains('(')):
            index = funcName.split('(')[1].remove(')').toInt()[0]
            retFunc = funcName.split('(')[0]

        return retFunc, index

    def cellDoubleClicked(self, x, y):
        columnText = self.__getTableWidget('current').horizontalHeaderItem(y).text()
        lineNum = self.__getTableWidget('current').item(x, 0).text()
        cellText = self.__getTableWidget('current').item(x, y).text()
        sType = self.__getTableWidget('current').item(0, 0).text()

        #If there is an error, lineNum == n/a for no find in current tab, bail
        if(lineNum == 'n/a' or columnText == 'File Source'):
            return

        if(sType == 'func'): #need to upack from 0,1 cell(so we didn't have to create new column)
            fileName , pathOrProj, funcName, dIndex = self.__getTableWidget('current').item(0, 1).text().split('?')
            strippedFunc, dIndex = self.getDuplicateIndexFromFuncName(funcName+dIndex)

            self.libMgr.displayFlow(fileName, pathOrProj, strippedFunc, dIndex=dIndex)

        elif(sType == 'file'):
            funcName = self.__getTableWidget('current').item(x, 1).text()
            fileName = self.__getTableWidget('current').item(0, 1).text()
            pathOrProj = self.__getTableWidget('current').item(0, 2).text()

            if(columnText == 'Flow' and funcName != 'n/a'):
                self.libMgr.displayFlow(fileName, pathOrProj, funcName)
            elif(self.libMgr.isDisplayed(fileName, pathOrProj) or funcName == 'n/a'):
                self.libMgr.displayFml(fileName, pathOrProj)
            else:
                self.libMgr.displayFlow(fileName, pathOrProj, funcName)

        elif(sType == 'all'):
            funcName = self.__getTableWidget('current').item(x, 1).text()
            fileName = self.__getTableWidget('current').item(x, 2).text()
            pathOrProj = self.__getTableWidget('current').item(x, 4).text()

            #If neither fml or flow is listed, bail (should never happen)
            if(funcName == 'n/a' and fileName == 'n/a'):
                return

            #if the file isn't already open and the function is not n/a, just open file
            if(self.libMgr.isDisplayed(fileName, pathOrProj) or 
               funcName == 'n/a' or 
               columnText == 'File'):
                self.libMgr.displayFml(fileName, pathOrProj)
            else:
                strippedFunc, dIndex = self.getDuplicateIndexFromFuncName(funcName)
                self.libMgr.displayFlow(fileName, pathOrProj, strippedFunc, dIndex)

        #Move the viewer to the line number
        self.libMgr.setCursorToReference(int(str(lineNum)) - 1, 0)