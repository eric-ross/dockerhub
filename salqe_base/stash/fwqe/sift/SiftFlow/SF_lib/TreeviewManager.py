#!/usr/bin/python -d
 
import sys, os
from PyQt4 import QtCore, QtGui
from SFLibManager import *
from FileManager import *
from ViewManager import *

class TreeviewManager():

    #Parameters: SFLibManager, treeview widget flows, treeview wiget all, treeview widget constants
    def __init__(self, libMgr, proj_widget, nonProj_widget, tabWidget):
        self.libMgr = libMgr
        self.fileMgr = ''
        self.viewMgr = ''

        #UI Widgets to directly manipulate
        self.proj_widget = proj_widget
        self.nonProj_widget = nonProj_widget
        self.tabWidget = tabWidget

        #Do we want to skip displaying in treeview if selection is changed
        #Usually used when we programmatically change selection (reloadTreeview ie)
        self.displayLock = False

    #--- Public Methods ---#

    # - - - - - - - - - - - - - - - - 
    # - Name: loadTreeviewProj()
    # - Description: Loads the project treeview, getting correct files from file mgr
    def loadTreeviewProject(self):
        #Clear the current treeviews
        self.proj_widget.clear()

        #Load each Treeview widget if there are no errors. TODO intigrate with messager later
        result = self.__loadProj()
        if(not result):
            self.libMgr.printError('Project Widgets not loaded!', 'Load failed', 10)

        return result

    # - - - - - - - - - - - - - - - - 
    # - Name: loadTreeviewNonProj()
    # - Description: Loads the nonproject treeview, getting correct files from file mgr
    def loadTreeviewNonProject(self):
        self.nonProj_widget.clear()

        #Load each Treeview widget if there are no errors. TODO intigrate with messager later
        if(not self.__loadNonProj()):
            self.libMgr.printError('Non Project Widgets not loaded!', 'Load failed', 10)

    # - - - - - - - - - - - - - - - - 
    # - Name: *Update() 
    # - Parameters: None
    # - Description: update the flow that is being viewed in the main viewer.
    def projUpdate(self):
        #If we don't want to update this in the viewer, bail
        if(self.displayLock):
            return


        #If item is the parent node (.fml .lua), open it
        if(len(self.proj_widget.selectedItems()) > 0 and not self.proj_widget.selectedItems()[0].parent()):
            fileName = self.proj_widget.selectedItems()[0].text(0)
            self.viewMgr.displayFml(fileName, self.libMgr.getLoadedProjName(), 0)

        #If the item is a child, open as a function
        if(len(self.proj_widget.selectedItems()) > 0 and self.proj_widget.selectedItems()[0].parent()):
            #Determine the correct flow and fml name
            funcName = self.proj_widget.selectedItems()[0].text(0)
            fileName = self.proj_widget.selectedItems()[0].parent().text(0)
            pathOrProj = self.libMgr.getLoadedProjName()

            #Handle case of duplicate flows in an fml, look above and get the number of duplicates, use that as an offset
            #to pass to the file manager in order to get the correct version of the duplicate flow
            funcDuplicateIndex = self.__getDuplicateIndex(fileName, pathOrProj, funcName)

            self.viewMgr.displayFlow(fileName, pathOrProj, funcName, tabIndex=0, dIndex=funcDuplicateIndex)

    def nonProjUpdate(self):
        #If we don't want to update this in the viewer, bail
        if(self.displayLock):
            return

        #If item is the parent node (.fml .lua), open it
        if(len(self.nonProj_widget.selectedItems()) > 0 and not self.nonProj_widget.selectedItems()[0].parent()):
            fileName = self.nonProj_widget.selectedItems()[0].text(0)
            self.viewMgr.displayFml(fileName, self.nonProj_widget.selectedItems()[0].toolTip(0), 0)

        #If the item is a child, open as a function
        if(len(self.nonProj_widget.selectedItems()) > 0 and self.nonProj_widget.selectedItems()[0].parent()):
            #Determine the correct flow and fml name
            funcName = self.nonProj_widget.selectedItems()[0].text(0)
            fileName = self.nonProj_widget.selectedItems()[0].parent().text(0)
            pathOrProj = self.nonProj_widget.selectedItems()[0].parent().toolTip(0)

            #Handle case of duplicate flows in an fml, look above and get the number of duplicates, use that as an offset
            #to pass to the file manager in order to get the correct version of the duplicate flow
            funcDuplicateIndex = self.__getDuplicateIndex(fileName, pathOrProj, funcName)

            self.viewMgr.displayFlow(fileName, pathOrProj, funcName,  tabIndex=0, dIndex=funcDuplicateIndex)

    # - - - - - - - - - - - - - - - - 
    # - Name: __getDuplicateIndex() 
    # - Parameters: None
    # - Description: This looks above the current item and counts duplicate flows, returns the current items
    # - index in the duplicate flows. ie the second flow_paper_load returns 2. if no duplicates, return None
    def __getDuplicateIndex(self, fileName, pathOrProj, funcName):
        #If there are no duplicates just return None
        if(not self.fileMgr.isFunctionDuplicate(fileName, pathOrProj, funcName)):
            return None

        #Use current selected table widget
        widget = self.tabWidget.currentWidget().layout().itemAt(0).widget()
        item = widget.selectedItems()[0]
        name = item.text(0)

        #Look at item above selected item, if its a duplicate, count it, do this until there aren't duplicates
        qindex = widget.indexFromItem(item).sibling(widget.indexFromItem(item).row() - 1, 0)

        #if there is no item above, don't look
        dIndex = 1
        while (qindex.isValid() and widget.itemFromIndex(qindex).text(0) == name):
            dIndex += 1
            qindex = qindex.sibling(qindex.row() - 1, 0) #Point at item above

        return dIndex

    # - - - - - - - - - - - - - - - - 
    # - Name: resizeTreeview() 
    # - Parameters: None
    # - Description: When something on the window is moved, resize the tree widgets
    # - so they always match the tab widgets size.
    def resizeTreeviews(self, size):
        self.proj_widget.resize(size)
        self.nonProj_widget.resize(size)


    # - - - - - - - - - - - - - - - - 
    # - Name: reloadFileTreeview()
    # - Parameters: path
    # - Description: Reloads a file entry in the treeview, if it exists
    def reloadFileTreeview(self, fileName, pathOrProj):
        dIndex = 0
        #Reload the file in the correct widget
        if(pathOrProj == self.libMgr.getLoadedProjName()):
            widget = self.proj_widget
        else:
            widget = self.nonProj_widget

        #Do not update the viewer
        self.displayLock = True

        #Need to unselect, then reselect at the end, we only care if its a flow
        #get the dIndex also, a flow copy may be selected
        needReselect = False
        if(widget.currentItem().parent()):
            parentToExpand = widget.currentItem().parent()
            selectedName = widget.currentItem().text(0)
            dIndex = self.__getDuplicateIndexFromTreeview(widget)
            needReselect = True

        #Find any occurances of the file
        finds = widget.findItems(fileName, QtCore.Qt.MatchFlags(), 0)

        #For every find, reload it, re expand it if needed
        for x in range(len(finds)):
            #Is the entry expanded?
            expand = widget.isItemExpanded(finds[x])

            #Remove the nodes children
            finds[x].takeChildren()

            #Get all the funcs from the file
            funcs = self.fileMgr.getFunctionNames(fileName, pathOrProj)

            for func in funcs:
                child = QtGui.QTreeWidgetItem(finds[x])
                child.setText(0, func)
                finds[x].addChild(child)

                if(needReselect and func == selectedName and finds[x] == parentToExpand):
                    if(dIndex > 1):
                        dIndex -= 1
                        continue

                    widget.setCurrentItem(child)

                    #We did it, if its true below that means we need to reload
                    needReselect = False 

            #expand if needed
            widget.setItemExpanded(finds[x], expand)

        #Update the viewer, if we are selecting a different thing, force and update
        self.displayLock = False

    # - - - - - - - - - - - - - - - - 
    # - Name: __getDuplicateIndexFromTreeview() 
    # - Parameters: None
    # - Description: If the selected node has duplicates, return its index among them 
    def __getDuplicateIndexFromTreeview(self, widget):
        selectedItem = widget.selectedIndexes()[0]
        selectedName = widget.currentItem().text(0)

        #Start at the item above selection and keep getting duplicates
        index = widget.indexAbove(selectedItem)
        x = 1
        while(widget.itemFromIndex(index).text(0) == selectedName):
            x += 1
            index = widget.indexAbove(index)
        return x

    #--- Private Methods and Helpers ---#

    # - - - - - - - - - - - - - - - - 
    # - Name: __loadProj() 
    # - Parameters: None
    # - Description: load proj treeview widget
    def __loadProj(self):
        if(self.proj_widget == ''):
            return False

        #Make the tab tooltip the proj name
        loadedProjName = self.libMgr.getLoadedProjName()
        self.tabWidget.setTabToolTip(0, loadedProjName)

        #Loop through all files
        for fileName, projName in self.fileMgr.getFileAndProjNames():
            #Get an array of all the functions in the file
            funcs = self.fileMgr.getFunctionNames(fileName, projName)

            item = QtGui.QTreeWidgetItem(self.proj_widget)
            item.setText(0, fileName) 
            item.setToolTip(0, self.fileMgr.getFilePath(fileName, projName))

            for func in funcs:
                child = QtGui.QTreeWidgetItem(item)
                child.setText(0, func)
                item.addChild(child)

            self.proj_widget.addTopLevelItem(item)

        return True

    # - - - - - - - - - - - - - - - - 
    # - Name: __loadNonProj() 
    # - Parameters: None
    # - Description: load Non proj treeview widget
    def __loadNonProj(self):
        if(self.nonProj_widget == ''):
            return False

        #Loop through all fml files
        for element in self.fileMgr.getFullPathsNonProj():
            filePath, fileName = os.path.split(element)

            #Get an array of all the functions in the file
            funcs = self.fileMgr.getFunctionNames(fileName, filePath)

                       
            item = QtGui.QTreeWidgetItem(self.nonProj_widget)
            item.setText(0, fileName) 
            item.setToolTip(0, filePath)                   

            for func in funcs:
                child = QtGui.QTreeWidgetItem(item)
                child.setText(0, func)
                item.addChild(child)

            self.nonProj_widget.addTopLevelItem(item)

        return True
    #--- Setters ---#
    def setFileManager(self, fileMgr):
        self.fileMgr = fileMgr

    def setViewManager(self, viewMgr):
        self.viewMgr = viewMgr
