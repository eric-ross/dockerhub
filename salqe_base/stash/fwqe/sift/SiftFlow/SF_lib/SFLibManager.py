#!/usr/bin/python -d
#############################################
# SiftFlow Lib Manager
#
# Manages all the lower level component managers so 
# Gui windows only need to interact with this.
#
############################################# 
import sys, os, re
from PyQt4 import QtCore, QtGui
from TreeviewManager import *
from FileManager import *
from ViewManager import *
from MessageManager import *
from ConfigManager import *

class SFLibManager():
    def __init__(self, parent, uiObj):
        #Declare Project Variables
        self.__configFile = os.path.join(os.path.expanduser(os.path.join('~',".sift")),'sf_config.ini')
        self.loadedProjName = ''
        self.loadedProjPath = ''
        self.loadedProjType = ''

        #Determine the path to sift.py
        self.baseDir = self.initBaseDir()

        #Declare all Managers
        self.uiObj = uiObj
        self.parent = parent
        self.treeViewMgr = TreeviewManager(self, 
                                           self.uiObj.treeWidget_proj, 
                                           self.uiObj.treeWidget_nonProj,
                                           self.uiObj.tabWidget_treeview)
        self.fileMgr = FileManager(self)
        self.viewMgr = ViewManager(self, self.uiObj.tabWidget_viewer)
        self.messageMgr = MessageManager(self, self.uiObj.statusbar)
        self.configMgr = ConfigManager(self)        

        #Pass Managers to other Managers that need them
        #(Basically this simulates the Singleton pattern since python can't do it natively)
        self.viewMgr.setFileManager(self.fileMgr) 
        self.treeViewMgr.setFileManager(self.fileMgr)
        self.treeViewMgr.setViewManager(self.viewMgr)

        #Load up things needed to happen at start up, but after the managers are all loaded
        self.viewMgr.resetMainViewer()

    # - - - - - - - - - - - - - - - - 
    # - Name: loadProject()
    # - Parameters: file_dirs, projPath - provided by sift
    # - Description: Loads the project from the .all by creating a list of all .fml + paths.
    # - Lastly the treeview is populate to allow the user to navigate through the flows
    def loadProject(self, fileDirs, projPath, projName, projType):
        #Reset the main viewer back the welcome tab in case we're opening a project while already opened
        self.viewMgr.resetMainViewer()

        #Make sure fileDirs is a list
        if(not isinstance(fileDirs, list)):
            fileDirs = [fileDirs]

        #Make sure fileDirs is a correct form
        if((len(fileDirs) == 0) or
           (not isinstance(fileDirs[0], QtCore.QString) and not isinstance(fileDirs[0], str)) or
           fileDirs[0] == ''):
            self.printError("Project path is incorrect or not a string",
                                       "Project NOT loaded successfully!", 10)
            return

        #Get data from the .all
        self.loadedProjName = projName
        self.loadedProjPath = projPath
        self.loadedProjType = projType

        #Load project into file manager and populate the treeview, if they fail, tell the user
        if (self.fileMgr.loadProject(fileDirs) and self.treeViewMgr.loadTreeviewProject()):
            self.uiObj.tabWidget_treeview.setCurrentIndex(0)
            self.out("Project loaded successfully", 6) 
        else:
            msg =  "Project data incorrect, try loading project in sift using the open button.\n"
            msg +=  "\tIf this is a Lua project, loading lua files on windows is not yet implemented."
            self.printError(msg, "Project NOT loaded successfully", 10) 

    # - - - - - - - - - - - - - - - - 
    # - Name: loadFiles()
    # - Parameters: fileList
    # - Description: Loads individual files given by the user that are not associated with a .all/project
    def loadFiles(self, fileList):
        #Pass to fileMgr to load, if any are already loaded in proj, remove and warn user
        filesNotAdded = self.fileMgr.addFiles(fileList)

        #If any files were tossed, tell the user
        if(len(filesNotAdded) > 0):
            self.messageMgr.loadedFilesTossedBox(filesNotAdded)

        #If any files were actually loaded, update and switch to nonproj treeview
        if(len(filesNotAdded) < len(fileList)):
            #Populate the treeview
            self.treeViewMgr.loadTreeviewNonProject()
            self.uiObj.tabWidget_treeview.setCurrentIndex(1)

            #Tell user project is loaded
            self.out(str(len(fileList) - len(filesNotAdded)) + " of " + str(len(fileList)) + " file(s) loaded successfully", 6)
                

    # - - - - - - - - - - - - - - - - 
    # - Name: reloadFile()
    # - Parameters: path
    # - Description: Reloads a file if it is currently being viewed. If there are unsaved changes
    # - prompt the user for what they want to do
    def reloadFile(self, fileName, pathOrProj):
        #Get List of all tabs displaying something from the file
        displayedIndexs = self.viewMgr.getDisplayedFileIndexsList(fileName, pathOrProj)
        unsavedChanges = []

        #For every item being displayed that doesn't have unsaved changes, just reload them without bothering user
        #But if there are one or more with changes give the user a warning.
        for index in displayedIndexs:
            if(not self.viewMgr.doesTabHaveStatus("unsaved", index)):
                self.viewMgr.reloadTab(index)

            #If there are unsaved changes, we need to know what the user wants since just saving over
            #their changes may cause unwanted fury.
            else:
                unsavedChanges.append(index)

        #If any tab had unsaved changes, tell the user and see what they want to do
        if (len(unsavedChanges) > 0):
            result = self.messageMgr.conflictMessageBox(fileName)
            #User wants to discard their changes, and reload the viewer with the external changes
            if result == 'discard':
                for index in unsavedChanges:
                    self.viewMgr.reloadTab(index)

            #User wants to Ignore the external changes and overwrite them with whats in the viewer
            #Add the conflict status so they can see that the viewer and file are out of sync
            elif result == 'ignore':
                for index in unsavedChanges:
                    self.viewMgr.addStatus('conflict', index)

    # - - - - - - - - - - - - - - - - 
    # - Name: reloadFileTreeview()
    # - Parameters: path
    # - Description: Reloads a file entry in the treeview, if it exists
    def reloadFileTreeview(self, fileName, pathOrProj):
        self.treeViewMgr.reloadFileTreeview(fileName, pathOrProj)

    # - - - - - - - - - - - - - - - - 
    # - Name: *Update() 
    # - Parameters: None
    # - Description: update the flow that is being viewed in the main viewer. When
    # - a new selection is made in the treeview an event calls these functions, which
    # - are passed to the treeview where it then calls the view manager, giving it the 
    # - name of the flow that needs to be displayed in the view
    def tvProjUpdate(self):
        self.treeViewMgr.projUpdate()

    def tvNonProjUpdate(self):
        self.treeViewMgr.nonProjUpdate()

    # - - - - - - - - - - - - - - - - 
    # - Name: resizeTreeview() 
    # - Parameters: None
    # - Description: When something on the window is moved, resize the tree widgets
    # - so they always match the tab widgets size.
    def resizeTreeview(self):
        #First resize the tab widget to the containing frames size, then
        #use that to resize the treeviews that reside in the tab widget
        self.treeViewMgr.resizeTreeviews(self.uiObj.tabWidget_treeview.size())

    # - - - - - - - - - - - - - - - - 
    # - Name: out 
    # - Parameters: 
    # - Description: Print normal messages to the user in the appropriate fields depending on 
    # - the arguments passed in.
    # - Usage: out("Message to the output box"), out("Message to the status bar",  10 [time to show message in seconds])
    # -        out("Message to output box", "Message to status bar", 10 [time to show message in seconds])
    def out(self, text, *args):
        self.messageMgr.out(text, args)

    # - - - - - - - - - - - - - - - - 
    # - Name: printError
    # - Parameters: 
    # - Description: Similar to out, but for error messages
    def printError(self, text, *args):
        self.messageMgr.printError(text, args)

    # - - - - - - - - - - - - - - - - 
    # - Name: displayFlow
    # - Parameters: dIndex - If there are duplicate flows in an fml, the index of 
    # - which copy this is
    # - Description: Calls viewmgr to display the flow in an appropriate veiwer tab
    def displayFlow(self, fileName, pathOrProj, flowName, dIndex=None):
        self.viewMgr.displayFlow(fileName, pathOrProj, flowName, dIndex=dIndex)

    # - - - - - - - - - - - - - - - - 
    # - Name: displayFml
    # - Parameters:  
    # - Description: Calls the view manager to display the fml in an appropriate tab
    def displayFml(self, fileName, pathOrProj):
        self.viewMgr.displayFml(fileName, pathOrProj)

    # - - - - - - - - - - - - - - - - 
    # - Name: addFindHistoryEntry(combobox)
    # - Parameters: combobox - the combobox ui element to add the text from
    # - Description: adds the current text in the combobox to the config history
    def addFindHistoryEntry(self, combobox):
        self.configMgr.addFindHistoryEntry(combobox)

    # - - - - - - - - - - - - - - - - 
    # - Name: addReplaceHistoryEntry(combobox)
    # - Parameters: combobox - the combobox ui element to add the text from
    # - Description: adds the current text in the combobox to the config history
    def addReplaceHistoryEntry(self, combobox):
        self.configMgr.addReplaceHistoryEntry(combobox)

    # - - - - - - - - - - - - - - - - 
    # - Name: addRecentPath(flowName, fmlPath)
    # - Description: adds a flowname and fml path to the config history for the recent menu
    def addRecentPath(self, fileName, pathOrProj, flowName=None, dIndex=None):
        #Need to store both path and proj in the config file
        path = self.fileMgr.getFilePath(fileName, pathOrProj)
        proj = self.fileMgr.getFileProj(fileName, pathOrProj)
        self.configMgr.addRecentPath(fileName, path, proj, flowName, dIndex)

    def getRecentList(self):
        return self.configMgr.getRecentList()

    # - - - - - - - - - - - - - - - - 
    # - Name: updateComboHistoryEntry(text)
    # - Parameters: combobox - the combobox ui element to add the text from
    # - Description: moves the current text in the combobox to the top of the config history (technically bottom
    # - of the xml nodes since it can only be appended to. String list is flipped in loadCombo())
    def updateComboHistoryEntry(self, combobox):
        self.configMgr.updateComboHistoryEntry(combobox)

    # - - - - - - - - - - - - - - - - 
    # - Name: updateFindOptions(text)
    # - Parameters: ops_d - a dictionary of all the options checked in the dialog
    # - Description: saves all the options in config.ini, updates if they already exist
    def updateConfigOptions(self, ops_d, comp):
        self.configMgr.updateConfigOptions(ops_d, comp)

    # - - - - - - - - - - - - - - - - 
    # - Name: loadCombo(combobox)
    # - Parameters: combobox - the combobox ui element to add the text from
    # - Description: Fills the combo box with the items in the config file
    def loadCombo(self, combobox):
        self.configMgr.loadCombo(combobox)

    # - - - - - - - - - - - - - - - - 
    # - Name: getFindConfigDict()
    # - Description: Get the dictionary of the windows radio and check states
    def getConfigDict(self, comp):
        return self.configMgr.getConfigDict(comp)

    # - - - - - - - - - - - - - - - - 
    # - Name: findTextCurrent()
    # - Description: Get the next occurrence of text in the currently selected tab of main viewer
    def findTextCurrent(self, text, flags, flip=False):
        return self.viewMgr.findTextCurrent(text, flags, flip)

    #-- Return True if the newly found match is within the search area boundaries
    def isCursorInSearchArea(self):
        saBeg = self.viewMgr.getSearchAreaBeginning()
        saEnd = self.viewMgr.getSearchAreaEnd()
        cEnd = self.viewMgr.getCursorEnd()

        if(self.docCoordIsGreater(cEnd, saBeg) and self.docCoordIsLess(cEnd, saEnd)):
            return True
        else:
            return False

    def docCoordIsGreater(self, coord1, coord2):
        #is coord1 greater than (its position is passed) coord2
        if((coord1[0] == coord2[0] and coord1[1] > coord2[1]) or
            (coord1[0] > coord2[0])):
            return True

        return False

    def docCoordIsLess(self, coord1, coord2):
        #is coor1 less than (its position is before) coord2
        if((coord1[0] == coord2[0] and coord1[1] < coord2[1]) or
            (coord1[0] < coord2[0])):
            return True

        return False

    def setCursorToReference(self, line, pos):
        self.viewMgr.setCursorToReference(line, pos)

    def getCursorBeginning(self):
        return self.viewMgr.getCursorBeginning()

    def getCursorEnd(self):
        return self.viewMgr.getCursorEnd()

    def getSearchAreaBeginning(self):
        return self.viewMgr.getSearchAreaBeginning()

    def getSearchAreaEnd(self):
        return self.viewMgr.getSearchAreaEnd()

    def setSearchArea(self):
        return self.viewMgr.setSearchArea()

    def unsetSearchArea(self):
        self.viewMgr.unsetSearchArea()

    def reselectSearchArea(self):
        self.viewMgr.reselectSearchArea()

    def getSelectionText(self):
        return self.viewMgr.getSelectionText()

    def isDisplayed(self, fileName, pathOrProj):
        return self.viewMgr.isDisplayed(fileName, pathOrProj)

    # - - - - - - - - - - - - - - - - 
    # - Name: findAllOpenFmls()
    # - Description: Find every file with a reference of text and open them in a new tab
    def findAllOpenFmls(self, text, flags):
        #Get list of [fileNames, pathorProj] the text occurs in
        findList = self.fileMgr.findAllInFiles(text, flags)

        #Open every member of list in a new tab, if tab already exists don't create a new one
        for item in findList:
            self.viewMgr.displayFml(item[0], item[1]) #display item in tab named item

    # - - - - - - - - - - - - - - - - 
    # - Name: findReferences()
    # - Parameters: text - string - text for which to search
    # -             flags - search flags
    # -             isCurrent - bool - is the user searching the current page, False if searching selection
    # - Description: If there is a match for text then return a list of all line numbers and lines the match
    # - occurs in. Handle searching in a selection.
    def findReferences(self, text, flags, isCurrent):
        #Search all lines
        reg = text = re.escape(str(text))
        flag = re.I

        if(flags['wo']):
            reg = '^' + text + '$|'             #text by itself
            reg += '^' + text + '(?=[\s\n])|'       #text at start of line
            reg += '[\s]' + text + '(?=[\s\n])|'    #text in a line
            reg += '[\s]' + text + '$'          #text at the end

        if(flags['cs']):
            flag = 0        

        if(isCurrent):
            return self.viewMgr.getCurrentReferences(reg, flag)
        else:
            return self.viewMgr.getSelectionReferences(reg, flag)

    # - - - - - - - - - - - - - - - - 
    # - Name: findReferencesInFiles()
    # - Parameters: text - string - text for which to search
    # -             flags - search flags
    # - Description: If there is a match for text then display the line number and line in
    # - the output box. Searches all fml files.
    def findReferencesInFiles(self, text, flags):
        return self.fileMgr.findReferences(text, flags)

    # - - - - - - - - - - - - - - - - 
    # - Name: getCount()
    # - Description: Returns the number of matches for a given search
    def getCount(self, text, flags, isCurrent):
        #Search all lines
        reg = text = str(text)
        flag = re.I

        if(flags['wo']):
            reg = '^' + text + '$|'             #text by itself
            reg += '^' + text + '(?=[\s\n])|'       #text at start of line
            reg += '[\s]' + text + '(?=[\s\n])|'    #text in a line
            reg += '[\s]' + text + '$'          #text at the end
            

        if(flags['cs']):
            flag = 0        

        if(isCurrent):
            count = self.viewMgr.getCountCurrent(reg, flag)
        else:
            count = self.viewMgr.getCountSelection(reg, flag)
        return count

    def isFileLoaded(self, fileName, path):
        return self.fileMgr.isFileLoaded(fileName, path)

    def isProjLoaded(self, proj=None):
        if(proj and self.loadedProjName == proj):
            return True
        elif(not proj and self.loadedProjName != ''):
            return True

        return False

    def getDownloadFileList(self):
        return self.fileMgr.getDownloadFileList(self.loadedProjName, self.loadedProjPath)

    def tabAlreadyExists(self, tabName):
        return self.viewMgr.tabAlreadyExists(tabName)

    def tabContainsPos(self, pos):
        return self.viewMgr.tabContainsPos(pos)

    def getCurrentTabText(self):
        return self.viewMgr.getCurrentTabText()

    def isFirstSearch(self):
        #If the search tag is in the tab title, then its not the first search
        if(self.viewMgr.doesTabHaveStatus('search')):
            return False
        return True

    def finishSearch(self):
        self.viewMgr.removeStatus('search')
        self.viewMgr.unsetSearchArea()

    def finishAllSearchs(self):
        self.viewMgr.removeAllStatus('search')
        self.viewMgr.unsetAllSearchAreas()

    def startSearch(self):
        self.viewMgr.addStatus('search')

    def addStatus(self, status):
        self.viewMgr.addStatus(status)

    def selectionToFill(self, selection):
        #Determine if selection is ok to post in the find textbox when find dialog opens
        selection = selection.strip(' \n(') #strip leading/trailing spaces and new lines
        
        #If its empty, just return it
        if(selection == ''):
            return selection

        #If its a flow or keyword (ie has letters numbers or underscores uninterrupted)
        if(re.search('^(flow|cmd)?[_\w\d]+$', selection)):
            return selection

        #If what remains isn't a consecutive group of letters, numbers, underscores
        return ''

    # --- Config Save/Load Methods --- #
    def saveWindowState(self, width, height, tvWidth):
        self.configMgr.addWindowSize(width, height)
        self.configMgr.addTreeviewWidth(tvWidth)
        self.configMgr.save()

    def getWindowSize(self):
        return self.configMgr.getWindowSize()

    def getTreeviewWidth(self):
        return self.configMgr.getTreeviewWidth()
        
    def setLastOpenDir(self, path):
        self.configMgr.addLastOpenDir(path)

    def getLastOpenDir(self):
        return self.configMgr.getLastOpenDir()

    #--- Edit Related Methods ---#

    def cut(self):
        self.viewMgr.cut()

    def copy(self):
        self.viewMgr.copy()

    def paste(self):
        self.viewMgr.paste()

    def undo(self):
        self.viewMgr.undo()

    def redo(self):
        self.viewMgr.redo()

    def indent(self):
        self.viewMgr.indent()

    def unindent(self):
        self.viewMgr.unindent()

    def comment(self):
        self.viewMgr.comment()

    def uncomment(self):
        self.viewMgr.uncomment()

    def replace(self, text):
        self.viewMgr.replace(text)

    def beginUndoAction(self):
        self.viewMgr.beginUndoAction()

    def endUndoAction(self):
        self.viewMgr.endUndoAction()

    #--- Saving ---#
    def saveCurrentTab(self):
        result = self.viewMgr.saveTab()

        #If the tab failed to save, let the user know
        if (len(result) > 0):
            self.messageMgr.failedSaveBox(result)
            return False

        return True

    def saveAllTabs(self):
        #result will be the fileNames of what failed to save, if empty nothing failed
        result = self.viewMgr.saveAllTabs()

        if(len(result) > 0):
            self.messageMgr.failedSaveBox(result)
            return False

        return True

    def anyUnsavedChanges(self):
        return self.viewMgr.anyUnsavedChanges()

    def saveAnyUnsavedChanges(self):
        self.viewMgr.saveAnyUnsavedChanges()

    def getRepo(self):
        return self.fileMgr.getRepo()

    def initBaseDir(self):
        dir = sys.path[0]

        #If there is a file on the end (cause of randals windows bug) remove it
        parts = os.path.split(dir)
        if(re.search('.*\..*', parts[1])):
            dir = parts[0]

        return dir

    #--- Getters ---#
    def getFileNameFromFuncName(self, projName, funcName):
        return self.fileMgr.getFuncParent(projName, funcName)

    def getBaseDir(self):
        return self.baseDir

    def getAboutText(self):
        return self.fileMgr.getAboutText()

    def getDocDir(self):
        dir = self.getBaseDir()

        if(os.path.exists(os.path.join(dir, 'SiftFlow'))):
            return os.path.join(dir, 'SiftFlow', 'docs')

        #if all else fails, return str to avoid None type cat error
        return dir

    def getIconDir(self):
        #Find the resource path that has SiftFlow, add the images folder to it
        dir = self.getBaseDir()       

        if(os.path.exists(os.path.join(dir, 'SiftFlow'))):
            return os.path.join(dir, 'SiftFlow', 'images')

        #If all else fails, return a string to get around a None type str cat error
        return dir

    def getConfigFile(self):
        return self.__configFile

    def getLineNumberOffset(self):
        return self.viewMgr.getLineNumberOffset()

    def getLoadedProjName(self):
        return self.loadedProjName

    def getLoadedProjType(self):
        return self.loadedProjType

    def getLoadedProjPath(self):
        return self.loadedProjPath

    def getMainUiActions(self):
        #Return all the menu actions from the main window ui
        actions = {
            'cut':          self.uiObj.actionCut,
            'copy':         self.uiObj.actionCopy,
            'paste':        self.uiObj.actionPaste,
            'find':         self.uiObj.actionFind,
            'findinfiles':  self.uiObj.actionFindInFiles,
            'currentReferences': self.uiObj.actionReference,
            'referenceInFiles': self.uiObj.actionReferenceInFiles
        }
        return actions
