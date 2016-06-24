#!/usr/bin/python -d
###############################################################################
# SiftFlow
#
# An FML IDE for Sift.
#
# Documentation:
# To Do
#
# Platforms:
# Linux
#
# Contact:
# tad.eug.harris@hp.com
#
# Requirements:
# Sift
# Pyqt4
###############################################################################

import sys, os, traceback
from PyQt4 import QtCore, QtGui
from SF_ui.main import Ui_MainWindow
from SF_lib.SFLibManager import *

from About import *
from Find import *
from Reference import *

class SiftFlow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        #If we were opened from the base sift (not the gui) setup the app internaly
        if (parent == None):
            self.app = QtGui.QApplication(sys.argv)
            self.app.setOrganizationName("Hewlett-Packard")
            self.app.setOrganizationDomain("hp.com")
            self.app.setApplicationName("SiftFlow")
    
            if (sys.platform.startswith("darwin")):
                self.app.setStyle("Cleanlooks")

        #Setup the window
        QtGui.QMainWindow.__init__(self)
        self.parent = parent

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Declare interface object with backend
        self.libMgr = SFLibManager(self, self.ui)

        #Do additional Window setup
        self.__initMainWindow()

        #Only want one reference window at a time
        self.refWin = None
        self.aboutWin = None
        self.findWin = None
        self.repWin = None

        #Set up actions and signals
        QtCore.QObject.connect(self.ui.actionAbout, QtCore.SIGNAL("triggered()"), self.__about)
        QtCore.QObject.connect(self.ui.actionFind, QtCore.SIGNAL("triggered()"), self.__find)
        QtCore.QObject.connect(self.ui.actionFindInFiles, QtCore.SIGNAL("triggered()"), self.__findInFiles)
        QtCore.QObject.connect(self.ui.actionReference, QtCore.SIGNAL("triggered()"), self.reference)
        QtCore.QObject.connect(self.ui.actionReferenceInFiles, QtCore.SIGNAL("triggered()"), self.referenceInFiles)
        QtCore.QObject.connect(self.ui.actionCut, QtCore.SIGNAL("triggered()"), self.__cut)
        QtCore.QObject.connect(self.ui.actionCopy, QtCore.SIGNAL("triggered()"), self.__copy)
        QtCore.QObject.connect(self.ui.actionUndo, QtCore.SIGNAL("triggered()"), self.__undo)
        QtCore.QObject.connect(self.ui.actionRedo, QtCore.SIGNAL("triggered()"), self.__redo)
        QtCore.QObject.connect(self.ui.actionGoto, QtCore.SIGNAL("triggered()"), self.__goto)
        QtCore.QObject.connect(self.ui.actionIndent, QtCore.SIGNAL("triggered()"), self.__indent)
        QtCore.QObject.connect(self.ui.actionUnindent, QtCore.SIGNAL("triggered()"), self.__unindent)
        QtCore.QObject.connect(self.ui.actionComment, QtCore.SIGNAL("triggered()"), self.__comment)
        QtCore.QObject.connect(self.ui.actionUncomment, QtCore.SIGNAL("triggered()"), self.__uncomment)
        QtCore.QObject.connect(self.ui.actionPaste, QtCore.SIGNAL("triggered()"), self.__paste)
        QtCore.QObject.connect(self.ui.actionDownload, QtCore.SIGNAL("triggered()"), self.__download)

        QtCore.QObject.connect(self.ui.treeWidget_proj, QtCore.SIGNAL("itemSelectionChanged()"), self.__projSelectionChanged)
        QtCore.QObject.connect(self.ui.treeWidget_nonProj, QtCore.SIGNAL("itemSelectionChanged()"), self.__nonProjSelectionChanged)
        QtCore.QObject.connect(self.ui.splitter_leftright, QtCore.SIGNAL("splitterMoved(int, int)"), self.__resizeAll)

        #QtCore.QObject.connect(self.ui.actionNewFlow, QtCore.SIGNAL("triggered()"), self.__newFlow)
        QtCore.QObject.connect(self.ui.actionOpen, QtCore.SIGNAL("triggered()"), self.__open)
        QtCore.QObject.connect(self.ui.actionSave, QtCore.SIGNAL("triggered()"), self.__save)
        #QtCore.QObject.connect(self.ui.actionSave_All, QtCore.SIGNAL("triggered()"), self.__saveAll)
        QtCore.QObject.connect(self.ui.menuRecent, QtCore.SIGNAL("aboutToShow()"), self.__fillMenuRecent)
        QtCore.QObject.connect(self.ui.menuBuild, QtCore.SIGNAL("aboutToShow()"), self.__fillMenuBuild)

        #SiftFlow, show thyself!!
        if(parent == None): self.show()

    def run(self):
        """Run the main QT event loop"""
        self.app.exec_()

    #--- Child Windows ---#
    def __about(self):
        if(self.aboutWin == None or self.aboutWin.isHidden()):
            self.aboutWin = About(self, self.libMgr)
            self.aboutWin.exec_()

    def __find(self):
        if(self.findWin == None or self.findWin.isHidden()):
            self.findWin = Find(self, self.libMgr)
            self.findWin.show()

    def reference(self, text='none', flags=None, isCurrent=True):
        if(self.refWin == None or not self.refWin.isVisible()):
            self.refWin = Reference(self, self.libMgr)
            result = self.refWin.addSearch(text, flags, isCurrent)
            if(isinstance(result, str) and result == 'noselection'):
                QtGui.QMessageBox.about(self, "Selection Status", "There is no text selected.")
            elif(result):
                self.refWin.show()
            else:
                QtGui.QMessageBox.about(self, "Match Status", "There are no more matches.")
        elif(self.refWin.isVisible()): #the window is open, reset
            if(not self.refWin.addSearch(text, flags, isCurrent)):
                QtGui.QMessageBox.about(self, "Match Status", "There are no more matches.")

    def referenceInFiles(self):
        self.reference(isCurrent='all')

    #--- Signal Handlers ---#
    def __projSelectionChanged(self):
        self.libMgr.tvProjUpdate()

    def __nonProjSelectionChanged(self):
        self.libMgr.tvNonProjUpdate()

    def __cut(self):
        self.libMgr.cut()

    def __copy(self):
        self.libMgr.copy()

    def __paste(self):
        self.libMgr.paste()

    def __findInFiles(self):
        findWin = Find(self, self.libMgr)
        findWin.findInFiles()
        findWin.exec_()

    def __undo(self):
        self.libMgr.undo()

    def __redo(self):
        self.libMgr.redo()

    def __goto(self):
        lineNum, ok = QtGui.QInputDialog.getText(self, 'Go to..', 'Go To Line: ')
        if ok:
            self.libMgr.setCursorToReference(int(lineNum) - 1, 0)

    def __indent(self):
        self.libMgr.indent()

    def __unindent(self):
        self.libMgr.unindent()

    def __comment(self):
        self.libMgr.comment()

    def __uncomment(self):
        self.libMgr.uncomment()

    def __newFlow(self):
        print 'new flow'

    def __save(self):
        result = self.libMgr.saveCurrentTab()

        #Reset the reference window if it is open, to reflect any changes in the files after saving
        if(self.refWin and self.refWin.isVisible()): #the window is open
            self.refWin.resetTabs()

    #def __saveAll(self):
        #For now I am removing save all from the ui, but will leave the functionality in.
        #Save All would rarely be used and caused a few hard to solve cunundrums with file conflicts
        #when a user had unsaved changes in both fmls and flows from those fmls. If in the future, this 
        #feature is demanded, then all that needs to be done is to reattach the action to the toolbar and
        #uncomment this function, the signal and file menu entry near the bottom of this file
        
        #result = self.libMgr.saveAllTabs()

        #Reset the reference window if it is open, to reflect any changes in the files after saving
        #if(self.refWin and self.refWin.isVisible()): #the window is open
            #self.refWin.resetTabs()

    def __download(self):
        #Cannot download if there is no project loaded
        if(not self.libMgr.isProjLoaded()):
            self.libMgr.printError("Download failed!", 10)
            QtGui.QMessageBox.about(self, "Download Failed", "No Project Loaded.")
            return

        #Get a list of all files changed since .all was build
        dList = self.libMgr.getDownloadFileList()

        #If files have changed since the .all was built, download them to printer
        if(len(dList) > 0):
            #Turn that list into the command string
            cmd = "download " + " ".join(dList)

            #Send command to sift
            self.parent.parse(cmd)

        #If no files have changed, tell user and do nothing
        else:
            self.libMgr.out("No changed files to download", 6)

    #--- Event Handlers ---#
    def showEvent(self, se):
        self.__resizeAll(0, 0)

    def __resizeAll(self, index, pos):
        self.libMgr.resizeTreeview()

    def closeEvent(self, e):
        #If there are any unsaved changes, ask user what they want to do
        if(self.libMgr.anyUnsavedChanges()):
            msg = "There are unsaved changes. Quitting will discharges these changes."

            reply = QtGui.QMessageBox.question(self, "Warning", msg, QtGui.QMessageBox.Save, 
                                                QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)
    
            if reply == QtGui.QMessageBox.Save:
                self.libMgr.saveAnyUnsavedChanges()
            elif reply == QtGui.QMessageBox.Cancel:
                e.ignore()
                return

        #Save window size, treeview width, output box height
        self.libMgr.saveWindowState(self.width(), self.height(), 
                                    self.ui.splitter_leftright.widget(0).width())

        #Close any open dialogs
        if(self.aboutWin != None and not self.aboutWin.isHidden()):
            self.aboutWin.close()
        if(self.findWin != None and not self.findWin.isHidden()):
            self.findWin.close()
        if(self.repWin != None and not self.repWin.isHidden()):
            self.repWin.close()
        if(self.refWin != None and not self.refWin.isHidden()):
            self.refWin.close()

        if (self.parent != None):
            self.parent.ui.edit.setEnabled(True)

    #--- Opening Files ---#
    # Signal handler for open file action
    def __open(self):
        #Get the last dir opened by the user (from config file)
        lastDir = self.libMgr.getLastOpenDir()
        
        #Use file dialog to allow user to select one or more .fmls
        ofDialog = QtGui.QFileDialog(self)
        files = ofDialog.getOpenFileNames(caption='Open file(s)', 
                                          directory=lastDir, 
                                          filter='Files (*.fml *.lua)')

        #Only load files if the user select any
        if not files.isEmpty():
            #Place the chosen directory in the config file
            self.libMgr.setLastOpenDir(os.path.split(str(files[0]))[0])

            #Load the files
            self.loadFiles(files)

    #Loads a project file provided by sift
    def loadProject(self, fileDirs, projPath, projName, projType):
        #If not in linux or project_dir is not pointed to a build directory (ie bound to repo) or file_dirs is empty
        #Use the project_dir as the file_dirs since the project files will be with the .hlg
        if(not sys.platform.startswith('linux') or 
           not re.search("obj_\w+_\w+", projPath) or
           len(fileDirs) == 0):
            fileDirs = projPath

        try:
            self.libMgr.loadProject(fileDirs, projPath, projName, projType)
        except:
            print "SiftFlow Load Error: "
            print "file_dirs: " + str(fileDirs)
            print "project_dir: " + str(projPath)
            print "project_name: " + str(projName)
            print "project_type: " + str(projType)
            print "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
            return

        #Add the .all name and the repo name (None if not in repo) to the window title
        self.setWindowTitle('SiftFlow (' + (projName or "None") + ') (Repo: ' + self.libMgr.getRepo() + ')')

    #Loads files not associated with a project file
    def loadFiles(self, args):
        #If no loaded project, set window title
        if(self.libMgr.getLoadedProjName() == ''):
            self.setWindowTitle('SiftFlow (No Project)') 

        fileList = []
        #Load files the user has specified from command line args rather than a project from sift
        if(len(args) == 0):
            #If no args were given, check cwd for any .fmls and open them
            cwd = os.getcwd()
            for infile in glob.glob(os.path.join(cwd, '*.fml')):
                fileList.append(infile)

        elif(len(args) > 0):
            #Loop through the args and open files if they exist
            for x in range(len(args)):
                arg = str(args[x]) 
                if ((arg.endswith('.fml') or arg.endswith('.lua')) and 
                     os.path.exists(arg)):
                    fileList.append(arg)
                else:
                    print arg + ' is not an fml or does not exist'

        #If there are files, open them
        if(len(fileList) > 0):
            try:
                self.libMgr.loadFiles(fileList)
            except:
                print "SiftFlow Load Error: "
                print "file list: " + str(fileList)
                print "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
                return

    def displayFlowFromSift(self, funcName, projName):
        #Use project name to get the correct filename for the function
        fileName = self.libMgr.getFileNameFromFuncName(projName, funcName)

        if not fileName:
            print "There was an error displaying the flow."
            return

        self.libMgr.displayFlow(fileName, projName, funcName)

    def __displayFromRecent(self, todisplay):
        fileName = todisplay[0] 
        path = todisplay[1]
        proj = todisplay[2]
        funcName = todisplay[3]
        dIndex = todisplay[4]

        #If file is not in the loaded file list, add it
        if(not self.libMgr.isFileLoaded(fileName, path)):
            self.libMgr.loadFiles([os.path.join(path,fileName)])

        #Set up pathOrProj
        if(self.libMgr.isProjLoaded(proj)):
            pathOrProj = proj
        else:
            pathOrProj = path

        #Display the thing
        if(not funcName):
            self.libMgr.displayFml(fileName, pathOrProj)
        else:
            self.libMgr.displayFlow(fileName, pathOrProj, funcName, dIndex=dIndex)

    #--- Setup Functions ---#
    def __initMainWindow(self):
        #Set Main Window starting size
        self.resize(self.libMgr.getWindowSize())

        #Treeview (navigation) Tab Control Init
        self.ui.tabWidget_treeview.setCurrentIndex(0)

        #Set all layout margins to zero
        self.ui.gridLayout.setMargin(0)
        self.ui.gridLayout_2.setMargin(0)
        self.ui.gridLayout_3.setMargin(0)
        self.ui.gridLayout_4.setMargin(0)
        self.ui.gridLayout_5.setMargin(0)

        #Set stretch factors so the resize widgets know what ratio each side can be
        self.ui.splitter_leftright.setStretchFactor(1, 2)

        #Set Left frame contents sizes
        self.ui.splitter_leftright.widget(0).setMinimumWidth(125)
        self.ui.splitter_leftright.setSizes([self.libMgr.getTreeviewWidth(), self.ui.splitter_leftright.widget(1).width()])

        #setup main icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "SiftTeal.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        #setup find icon
        iconF = QtGui.QIcon()
        iconF.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "find.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionFind.setIcon(iconF)

        #setup reference icon
        iconRef = QtGui.QIcon()
        iconRef.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "findreference.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionReference.setIcon(iconRef)

        #setup reference icon
        iconRefInFiles = QtGui.QIcon()
        iconRefInFiles.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "findreferenceinfiles.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionReferenceInFiles.setIcon(iconRefInFiles)

        #setup undo icon
        iconU = QtGui.QIcon()
        iconU.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "undo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionUndo.setIcon(iconU)

        #setup redo icon
        iconRed = QtGui.QIcon()
        iconRed.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "redo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionRedo.setIcon(iconRed)

        #setup comment icon
        iconCom = QtGui.QIcon()
        iconCom.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "comment.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionComment.setIcon(iconCom)

        #setup uncomment icon
        iconUncom = QtGui.QIcon()
        iconUncom.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "uncomment.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionUncomment.setIcon(iconUncom)

        #setup indent icon
        iconIn = QtGui.QIcon()
        iconIn.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "indent.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionIndent.setIcon(iconIn)

        #setup unindent icon
        iconUnin = QtGui.QIcon()
        iconUnin.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "unindent.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionUnindent.setIcon(iconUnin)

        #setup goto icon
        iconGoto = QtGui.QIcon()
        iconGoto.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "goto.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionGoto.setIcon(iconGoto)

        #setup open icon
        iconO = QtGui.QIcon()
        iconO.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "open.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionOpen.setIcon(iconO)

        #setup save icon
        iconSave = QtGui.QIcon()
        iconSave.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "save.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionSave.setIcon(iconSave)

        #setup saveall icon
        iconSaveAll = QtGui.QIcon()
        iconSaveAll.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "saveall.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionSave_All.setIcon(iconSaveAll)

        #setup download icon
        iconDownload = QtGui.QIcon()
        iconDownload.addPixmap(QtGui.QPixmap(os.path.join(self.libMgr.getIconDir(), "download.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.actionDownload.setIcon(iconDownload)

        #Create File menu
        #self.ui.menuNew = QtGui.QMenu('New')
        #self.ui.actionNewFlow = QtGui.QAction(self.ui.menuNew)
        #self.ui.actionNewFlow.setObjectName('actionNewFlow')
        #self.ui.actionNewFlow.setText('Flow')
        #self.ui.menuNew.addAction(self.ui.actionNewFlow)
        #self.ui.menuFile.addMenu(self.ui.menuNew)

        #self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionOpen)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionSave)
        #self.ui.menuFile.addAction(self.ui.actionSave_All) 
        self.ui.menuFile.addSeparator()

        #build recent menu
        self.ui.menuRecent = QtGui.QMenu(self.ui.menuFile)
        self.ui.menuRecent.setTitle('Recent')
        self.ui.menuFile.addMenu(self.ui.menuRecent)

        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionExit)

        #build...build menu
        self.ui.menuBuild.addAction(self.ui.actionDownload)

    def __fillMenuRecent(self):
        list = self.libMgr.getRecentList()
        self.ui.menuRecent.clear()

        for item in reversed(list):
            action = QtGui.QAction(self.ui.menuRecent)

            #Display the flow name, or .fml if that all there is, tack on dIndex if there
            dIndex = ''
            if item[4]:
                dIndex = '(' + str(item[4]) + ')'

            action.setText((item[3] or item[0]) + dIndex)

            #Pass in path:flow to the display function when the action is clicked for easy displaying
            receiver = lambda todisplay=item: self.__displayFromRecent(todisplay)
            action.connect(action, QtCore.SIGNAL("triggered()"), receiver)
            self.ui.menuRecent.addAction(action)

    def __fillMenuBuild(self):
        #build...build menu
        self.ui.menuBuild.addAction(self.ui.actionDownload)
        
