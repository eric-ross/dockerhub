# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'find.ui'
#
# Created: Tue Mar 27 15:35:19 2012
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Find(object):
    def setupUi(self, Find):
        Find.setObjectName(_fromUtf8("Find"))
        Find.setWindowModality(QtCore.Qt.NonModal)
        Find.resize(475, 210)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Find.sizePolicy().hasHeightForWidth())
        Find.setSizePolicy(sizePolicy)
        Find.setMinimumSize(QtCore.QSize(475, 210))
        Find.setMaximumSize(QtCore.QSize(475, 210))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("DejaVu Sans"))
        font.setPointSize(10)
        Find.setFont(font)
        Find.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("images/SIFTTeal.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Find.setWindowIcon(icon)
        self.layoutWidget = QtGui.QWidget(Find)
        self.layoutWidget.setGeometry(QtCore.QRect(370, 10, 101, 140))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.vboxlayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.pushButton_findnext = QtGui.QPushButton(self.layoutWidget)
        self.pushButton_findnext.setAutoDefault(False)
        self.pushButton_findnext.setDefault(True)
        self.pushButton_findnext.setObjectName(_fromUtf8("pushButton_findnext"))
        self.vboxlayout.addWidget(self.pushButton_findnext)
        self.pushButton_findprev = QtGui.QPushButton(self.layoutWidget)
        self.pushButton_findprev.setAutoDefault(False)
        self.pushButton_findprev.setObjectName(_fromUtf8("pushButton_findprev"))
        self.vboxlayout.addWidget(self.pushButton_findprev)
        self.pushButton_count = QtGui.QPushButton(self.layoutWidget)
        self.pushButton_count.setAutoDefault(False)
        self.pushButton_count.setObjectName(_fromUtf8("pushButton_count"))
        self.vboxlayout.addWidget(self.pushButton_count)
        self.pushButton_findinfiles = QtGui.QPushButton(self.layoutWidget)
        self.pushButton_findinfiles.setObjectName(_fromUtf8("pushButton_findinfiles"))
        self.vboxlayout.addWidget(self.pushButton_findinfiles)
        self.groupBox_findops = QtGui.QGroupBox(Find)
        self.groupBox_findops.setGeometry(QtCore.QRect(140, 50, 121, 81))
        self.groupBox_findops.setObjectName(_fromUtf8("groupBox_findops"))
        self.radioButton_current = QtGui.QRadioButton(self.groupBox_findops)
        self.radioButton_current.setGeometry(QtCore.QRect(10, 20, 111, 23))
        self.radioButton_current.setChecked(True)
        self.radioButton_current.setObjectName(_fromUtf8("radioButton_current"))
        self.radioButton_selection = QtGui.QRadioButton(self.groupBox_findops)
        self.radioButton_selection.setGeometry(QtCore.QRect(10, 50, 93, 23))
        self.radioButton_selection.setObjectName(_fromUtf8("radioButton_selection"))
        self.groupBox_startpos = QtGui.QGroupBox(Find)
        self.groupBox_startpos.setGeometry(QtCore.QRect(270, 50, 91, 80))
        self.groupBox_startpos.setObjectName(_fromUtf8("groupBox_startpos"))
        self.radioButton_top = QtGui.QRadioButton(self.groupBox_startpos)
        self.radioButton_top.setGeometry(QtCore.QRect(10, 20, 61, 23))
        self.radioButton_top.setChecked(True)
        self.radioButton_top.setObjectName(_fromUtf8("radioButton_top"))
        self.radioButton_bottom = QtGui.QRadioButton(self.groupBox_startpos)
        self.radioButton_bottom.setGeometry(QtCore.QRect(10, 50, 81, 23))
        self.radioButton_bottom.setObjectName(_fromUtf8("radioButton_bottom"))
        self.groupBox_options = QtGui.QGroupBox(Find)
        self.groupBox_options.setGeometry(QtCore.QRect(50, 150, 371, 51))
        self.groupBox_options.setObjectName(_fromUtf8("groupBox_options"))
        self.checkBox_verbatim = QtGui.QCheckBox(self.groupBox_options)
        self.checkBox_verbatim.setGeometry(QtCore.QRect(10, 20, 91, 23))
        self.checkBox_verbatim.setObjectName(_fromUtf8("checkBox_verbatim"))
        self.checkBox_case = QtGui.QCheckBox(self.groupBox_options)
        self.checkBox_case.setGeometry(QtCore.QRect(200, 20, 61, 23))
        self.checkBox_case.setObjectName(_fromUtf8("checkBox_case"))
        self.checkBox_wrap = QtGui.QCheckBox(self.groupBox_options)
        self.checkBox_wrap.setGeometry(QtCore.QRect(120, 20, 71, 23))
        self.checkBox_wrap.setObjectName(_fromUtf8("checkBox_wrap"))
        self.checkBox_re = QtGui.QCheckBox(self.groupBox_options)
        self.checkBox_re.setGeometry(QtCore.QRect(280, 20, 91, 20))
        self.checkBox_re.setObjectName(_fromUtf8("checkBox_re"))
        self.label_find = QtGui.QLabel(Find)
        self.label_find.setGeometry(QtCore.QRect(12, 11, 32, 26))
        self.label_find.setObjectName(_fromUtf8("label_find"))
        self.groupBox_mode = QtGui.QGroupBox(Find)
        self.groupBox_mode.setGeometry(QtCore.QRect(10, 50, 121, 81))
        self.groupBox_mode.setObjectName(_fromUtf8("groupBox_mode"))
        self.radioButton_normal = QtGui.QRadioButton(self.groupBox_mode)
        self.radioButton_normal.setGeometry(QtCore.QRect(10, 20, 81, 23))
        self.radioButton_normal.setChecked(True)
        self.radioButton_normal.setObjectName(_fromUtf8("radioButton_normal"))
        self.radioButton_reference = QtGui.QRadioButton(self.groupBox_mode)
        self.radioButton_reference.setGeometry(QtCore.QRect(10, 50, 111, 23))
        self.radioButton_reference.setObjectName(_fromUtf8("radioButton_reference"))
        self.comboBox_find = QtGui.QComboBox(Find)
        self.comboBox_find.setGeometry(QtCore.QRect(50, 10, 271, 29))
        self.comboBox_find.setEditable(True)
        self.comboBox_find.setMaxVisibleItems(10)
        self.comboBox_find.setInsertPolicy(QtGui.QComboBox.InsertAtCurrent)
        self.comboBox_find.setDuplicatesEnabled(True)
        self.comboBox_find.setObjectName(_fromUtf8("comboBox_find"))

        self.retranslateUi(Find)
        QtCore.QObject.connect(self.pushButton_findnext, QtCore.SIGNAL(_fromUtf8("clicked()")), Find.update)
        QtCore.QObject.connect(self.pushButton_findprev, QtCore.SIGNAL(_fromUtf8("clicked()")), Find.update)
        QtCore.QObject.connect(self.pushButton_count, QtCore.SIGNAL(_fromUtf8("clicked()")), Find.update)
        QtCore.QObject.connect(self.radioButton_current, QtCore.SIGNAL(_fromUtf8("clicked()")), Find.update)
        QtCore.QObject.connect(self.radioButton_selection, QtCore.SIGNAL(_fromUtf8("clicked()")), Find.update)
        QtCore.QObject.connect(self.pushButton_findinfiles, QtCore.SIGNAL(_fromUtf8("clicked()")), Find.update)
        QtCore.QMetaObject.connectSlotsByName(Find)

    def retranslateUi(self, Find):
        Find.setWindowTitle(QtGui.QApplication.translate("Find", "Find", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findnext.setToolTip(QtGui.QApplication.translate("Find", "Go to the next item found [F3].", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findnext.setText(QtGui.QApplication.translate("Find", "Find Next", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findnext.setShortcut(QtGui.QApplication.translate("Find", "F3", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findprev.setToolTip(QtGui.QApplication.translate("Find", "Go to the previous match [F4].", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findprev.setText(QtGui.QApplication.translate("Find", "Find Prev", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findprev.setShortcut(QtGui.QApplication.translate("Find", "F4", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_count.setToolTip(QtGui.QApplication.translate("Find", "Displays how many items where found.", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_count.setText(QtGui.QApplication.translate("Find", "Count", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findinfiles.setToolTip(QtGui.QApplication.translate("Find", "Display .fmls that contain an occurance of the text in a new tab.", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_findinfiles.setText(QtGui.QApplication.translate("Find", "Find in Files", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_findops.setTitle(QtGui.QApplication.translate("Find", "Find In", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_current.setToolTip(QtGui.QApplication.translate("Find", "Find the text in the file currently selected and displayed in the main tab of the viewer.", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_current.setText(QtGui.QApplication.translate("Find", "Current File", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_selection.setToolTip(QtGui.QApplication.translate("Find", "Search the currently selected text in the viewer.", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_selection.setText(QtGui.QApplication.translate("Find", "Selection", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_startpos.setTitle(QtGui.QApplication.translate("Find", "Start From", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_top.setToolTip(QtGui.QApplication.translate("Find", "Start search from top of the file or selection.", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_top.setText(QtGui.QApplication.translate("Find", "Top", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_bottom.setToolTip(QtGui.QApplication.translate("Find", "Start search from the bottom of the file or selection.", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_bottom.setText(QtGui.QApplication.translate("Find", "Bottom", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_options.setTitle(QtGui.QApplication.translate("Find", "Search Options", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_verbatim.setToolTip(QtGui.QApplication.translate("Find", "Search for exactly what is in the Find text box. Matches that are inside a word or otherwise partial finds are ignored.", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_verbatim.setText(QtGui.QApplication.translate("Find", "Verbatim", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_case.setToolTip(QtGui.QApplication.translate("Find", "Case sensitive search.", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_case.setText(QtGui.QApplication.translate("Find", "Case", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_wrap.setText(QtGui.QApplication.translate("Find", "Wrap", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_re.setText(QtGui.QApplication.translate("Find", "RegExp", None, QtGui.QApplication.UnicodeUTF8))
        self.label_find.setText(QtGui.QApplication.translate("Find", "Find: ", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_mode.setTitle(QtGui.QApplication.translate("Find", "Search Mode", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_normal.setToolTip(QtGui.QApplication.translate("Find", "Search for a word or phrase.", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_normal.setText(QtGui.QApplication.translate("Find", "Normal", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_reference.setToolTip(QtGui.QApplication.translate("Find", "Search for references of the text. This will display the lines it occurs on in the output box, rather than select each match in the main viewer.", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_reference.setText(QtGui.QApplication.translate("Find", "References", None, QtGui.QApplication.UnicodeUTF8))
