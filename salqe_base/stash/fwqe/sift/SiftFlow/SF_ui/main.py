# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created: Fri Oct 26 15:48:35 2012
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1252, 953)
        MainWindow.setMinimumSize(QtCore.QSize(750, 550))
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(10)
        MainWindow.setFont(font)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter_leftright = QtGui.QSplitter(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter_leftright.sizePolicy().hasHeightForWidth())
        self.splitter_leftright.setSizePolicy(sizePolicy)
        self.splitter_leftright.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_leftright.setChildrenCollapsible(False)
        self.splitter_leftright.setObjectName("splitter_leftright")
        self.frame_left = QtGui.QFrame(self.splitter_leftright)
        self.frame_left.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_left.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_left.setObjectName("frame_left")
        self.gridLayout_3 = QtGui.QGridLayout(self.frame_left)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.tabWidget_treeview = QtGui.QTabWidget(self.frame_left)
        self.tabWidget_treeview.setObjectName("tabWidget_treeview")
        self.tab_proj = QtGui.QWidget()
        self.tab_proj.setObjectName("tab_proj")
        self.gridLayout_5 = QtGui.QGridLayout(self.tab_proj)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.treeWidget_proj = QtGui.QTreeWidget(self.tab_proj)
        self.treeWidget_proj.setItemHidden(self.treeWidget_proj.headerItem(), True)
        self.treeWidget_proj.setObjectName("treeWidget_proj")
        self.treeWidget_proj.headerItem().setText(0, "1")
        self.gridLayout_5.addWidget(self.treeWidget_proj, 0, 0, 1, 1)
        self.tabWidget_treeview.addTab(self.tab_proj, "")
        self.tab_nonProj = QtGui.QWidget()
        self.tab_nonProj.setObjectName("tab_nonProj")
        self.gridLayout_4 = QtGui.QGridLayout(self.tab_nonProj)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.treeWidget_nonProj = QtGui.QTreeWidget(self.tab_nonProj)
        self.treeWidget_nonProj.setItemHidden(self.treeWidget_nonProj.headerItem(), True)
        self.treeWidget_nonProj.setObjectName("treeWidget_nonProj")
        self.treeWidget_nonProj.headerItem().setText(0, "1")
        self.gridLayout_4.addWidget(self.treeWidget_nonProj, 0, 0, 1, 1)
        self.tabWidget_treeview.addTab(self.tab_nonProj, "")
        self.gridLayout_3.addWidget(self.tabWidget_treeview, 0, 0, 1, 1)
        self.frame_right = QtGui.QFrame(self.splitter_leftright)
        self.frame_right.setAutoFillBackground(False)
        self.frame_right.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_right.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_right.setLineWidth(1)
        self.frame_right.setObjectName("frame_right")
        self.gridLayout_2 = QtGui.QGridLayout(self.frame_right)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.tabWidget_viewer = QtGui.QTabWidget(self.frame_right)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_viewer.sizePolicy().hasHeightForWidth())
        self.tabWidget_viewer.setSizePolicy(sizePolicy)
        self.tabWidget_viewer.setObjectName("tabWidget_viewer")
        self.gridLayout_2.addWidget(self.tabWidget_viewer, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.splitter_leftright, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1252, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuBuild = QtGui.QMenu(self.menubar)
        self.menuBuild.setObjectName("menuBuild")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setAutoFillBackground(False)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setOrientation(QtCore.Qt.Horizontal)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.ToolBarArea(QtCore.Qt.TopToolBarArea), self.toolBar)
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionFind = QtGui.QAction(MainWindow)
        self.actionFind.setObjectName("actionFind")
        self.actionManual = QtGui.QAction(MainWindow)
        self.actionManual.setObjectName("actionManual")
        self.actionAbout = QtGui.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionCut = QtGui.QAction(MainWindow)
        self.actionCut.setObjectName("actionCut")
        self.actionCopy = QtGui.QAction(MainWindow)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtGui.QAction(MainWindow)
        self.actionPaste.setObjectName("actionPaste")
        self.actionFindInFiles = QtGui.QAction(MainWindow)
        self.actionFindInFiles.setObjectName("actionFindInFiles")
        self.actionReference = QtGui.QAction(MainWindow)
        self.actionReference.setObjectName("actionReference")
        self.actionUndo = QtGui.QAction(MainWindow)
        self.actionUndo.setObjectName("actionUndo")
        self.actionRedo = QtGui.QAction(MainWindow)
        self.actionRedo.setObjectName("actionRedo")
        self.actionGoto = QtGui.QAction(MainWindow)
        self.actionGoto.setObjectName("actionGoto")
        self.actionIndent = QtGui.QAction(MainWindow)
        self.actionIndent.setObjectName("actionIndent")
        self.actionUnindent = QtGui.QAction(MainWindow)
        self.actionUnindent.setObjectName("actionUnindent")
        self.actionComment = QtGui.QAction(MainWindow)
        self.actionComment.setObjectName("actionComment")
        self.actionUncomment = QtGui.QAction(MainWindow)
        self.actionUncomment.setObjectName("actionUncomment")
        self.actionSave = QtGui.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_All = QtGui.QAction(MainWindow)
        self.actionSave_All.setObjectName("actionSave_All")
        self.actionOpen = QtGui.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionDownload = QtGui.QAction(MainWindow)
        self.actionDownload.setObjectName("actionDownload")
        self.actionReferenceInFiles = QtGui.QAction(MainWindow)
        self.actionReferenceInFiles.setObjectName("actionReferenceInFiles")
        self.menuHelp.addAction(self.actionManual)
        self.menuHelp.addAction(self.actionAbout)
        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionCut)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionIndent)
        self.menuEdit.addAction(self.actionUnindent)
        self.menuEdit.addAction(self.actionComment)
        self.menuEdit.addAction(self.actionUncomment)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionFind)
        self.menuEdit.addAction(self.actionFindInFiles)
        self.menuEdit.addAction(self.actionReference)
        self.menuEdit.addAction(self.actionReferenceInFiles)
        self.menuEdit.addAction(self.actionGoto)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuBuild.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.toolBar.addAction(self.actionOpen)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionUndo)
        self.toolBar.addAction(self.actionRedo)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionIndent)
        self.toolBar.addAction(self.actionUnindent)
        self.toolBar.addAction(self.actionComment)
        self.toolBar.addAction(self.actionUncomment)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionFind)
        self.toolBar.addAction(self.actionReference)
        self.toolBar.addAction(self.actionReferenceInFiles)
        self.toolBar.addAction(self.actionGoto)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionDownload)

        self.retranslateUi(MainWindow)
        self.tabWidget_treeview.setCurrentIndex(0)
        self.tabWidget_viewer.setCurrentIndex(-1)
        QtCore.QObject.connect(self.actionExit, QtCore.SIGNAL("activated()"), MainWindow.close)
        QtCore.QObject.connect(self.treeWidget_proj, QtCore.SIGNAL("itemSelectionChanged()"), MainWindow.update)
        QtCore.QObject.connect(self.treeWidget_nonProj, QtCore.SIGNAL("itemSelectionChanged()"), MainWindow.update)
        QtCore.QObject.connect(self.splitter_leftright, QtCore.SIGNAL("splitterMoved(int,int)"), MainWindow.update)
        QtCore.QObject.connect(self.actionCut, QtCore.SIGNAL("activated()"), MainWindow.update)
        QtCore.QObject.connect(self.actionCopy, QtCore.SIGNAL("activated()"), MainWindow.update)
        QtCore.QObject.connect(self.actionPaste, QtCore.SIGNAL("activated()"), MainWindow.update)
        QtCore.QObject.connect(self.actionFindInFiles, QtCore.SIGNAL("activated()"), MainWindow.update)
        QtCore.QObject.connect(self.tabWidget_viewer, QtCore.SIGNAL("tabCloseRequested(int)"), MainWindow.update)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.treeWidget_proj, self.treeWidget_nonProj)
        MainWindow.setTabOrder(self.treeWidget_nonProj, self.tabWidget_treeview)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Sift Flow", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget_treeview.setTabText(self.tabWidget_treeview.indexOf(self.tab_proj), QtGui.QApplication.translate("MainWindow", "Project", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget_treeview.setTabText(self.tabWidget_treeview.indexOf(self.tab_nonProj), QtGui.QApplication.translate("MainWindow", "Non Project", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFile.setTitle(QtGui.QApplication.translate("MainWindow", "File", None, QtGui.QApplication.UnicodeUTF8))
        self.menuHelp.setTitle(QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.menuEdit.setTitle(QtGui.QApplication.translate("MainWindow", "Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.menuBuild.setTitle(QtGui.QApplication.translate("MainWindow", "Build", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setText(QtGui.QApplication.translate("MainWindow", "Exit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionFind.setText(QtGui.QApplication.translate("MainWindow", "Find", None, QtGui.QApplication.UnicodeUTF8))
        self.actionManual.setText(QtGui.QApplication.translate("MainWindow", "Manual", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout.setText(QtGui.QApplication.translate("MainWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCut.setText(QtGui.QApplication.translate("MainWindow", "Cut", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCut.setToolTip(QtGui.QApplication.translate("MainWindow", "Copys the selected text to the clipboard, then removes it from the editor.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCut.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+X", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCopy.setText(QtGui.QApplication.translate("MainWindow", "Copy", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCopy.setToolTip(QtGui.QApplication.translate("MainWindow", "Copys selected text to the clipboard.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCopy.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+C", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPaste.setText(QtGui.QApplication.translate("MainWindow", "Paste", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPaste.setToolTip(QtGui.QApplication.translate("MainWindow", "Pastes the text in the clipboard, to the cursors location in the editor.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPaste.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+V", None, QtGui.QApplication.UnicodeUTF8))
        self.actionFindInFiles.setText(QtGui.QApplication.translate("MainWindow", "Find in Files", None, QtGui.QApplication.UnicodeUTF8))
        self.actionFindInFiles.setToolTip(QtGui.QApplication.translate("MainWindow", "Open the selected text in the Find dialog, with all .fmls that contain a match opened in new tabs within the editor.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReference.setText(QtGui.QApplication.translate("MainWindow", "Find References", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReference.setToolTip(QtGui.QApplication.translate("MainWindow", "Find the selected text\'s references in the current file.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUndo.setText(QtGui.QApplication.translate("MainWindow", "Undo", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUndo.setToolTip(QtGui.QApplication.translate("MainWindow", "Undo last change.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUndo.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Z", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRedo.setText(QtGui.QApplication.translate("MainWindow", "Redo", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRedo.setToolTip(QtGui.QApplication.translate("MainWindow", "Redo a change that you just undid.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRedo.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Shift+Z", None, QtGui.QApplication.UnicodeUTF8))
        self.actionGoto.setText(QtGui.QApplication.translate("MainWindow", "Go to...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionGoto.setToolTip(QtGui.QApplication.translate("MainWindow", "Go to a specified line in the current viewer tab.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionGoto.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+G", None, QtGui.QApplication.UnicodeUTF8))
        self.actionIndent.setText(QtGui.QApplication.translate("MainWindow", "Indent", None, QtGui.QApplication.UnicodeUTF8))
        self.actionIndent.setToolTip(QtGui.QApplication.translate("MainWindow", "Move a selected block of code right one tab", None, QtGui.QApplication.UnicodeUTF8))
        self.actionIndent.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Tab", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUnindent.setText(QtGui.QApplication.translate("MainWindow", "Unindent", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUnindent.setToolTip(QtGui.QApplication.translate("MainWindow", "Moves a selected block of text left one tab", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUnindent.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Shift+Backtab", None, QtGui.QApplication.UnicodeUTF8))
        self.actionComment.setText(QtGui.QApplication.translate("MainWindow", "Comment", None, QtGui.QApplication.UnicodeUTF8))
        self.actionComment.setToolTip(QtGui.QApplication.translate("MainWindow", "Comments out a selected block of text", None, QtGui.QApplication.UnicodeUTF8))
        self.actionComment.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUncomment.setText(QtGui.QApplication.translate("MainWindow", "Uncomment", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUncomment.setToolTip(QtGui.QApplication.translate("MainWindow", "Removes all comments from a block of code", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUncomment.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Shift+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave.setText(QtGui.QApplication.translate("MainWindow", "Save", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave_All.setText(QtGui.QApplication.translate("MainWindow", "Save &All", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOpen.setText(QtGui.QApplication.translate("MainWindow", "Open", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOpen.setToolTip(QtGui.QApplication.translate("MainWindow", "Open more .fmls", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOpen.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+O", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDownload.setText(QtGui.QApplication.translate("MainWindow", "Download", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDownload.setToolTip(QtGui.QApplication.translate("MainWindow", "Download changed files to the printer. If the project is fml, it is compiled first.", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDownload.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+D", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReferenceInFiles.setText(QtGui.QApplication.translate("MainWindow", "Find References in Files", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReferenceInFiles.setToolTip(QtGui.QApplication.translate("MainWindow", "Find the text by reference in all project files.", None, QtGui.QApplication.UnicodeUTF8))

