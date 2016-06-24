from PyQt4 import QtCore, QtGui
import Qsci
import os, sys, re, datetime

if sys.platform == 'darwin':
    BASE_FONT = QtGui.QFont('Menlo', 12)
elif os.name == 'nt':
    BASE_FONT = QtGui.QFont('Courier New', 10)
else:
    BASE_FONT = QtGui.QFont('Monospace', 10)

# QScintilla's lexer defaults can be a bit crazy
# This class also gives the possibility to add custom highlighting
# for a Sirius-specific set of core functions / constants / modules
# (Either by replacing / amending one of the normal keyword sets, or
# by using one of Scintilla's 4 reserved "user" keyword sets)
class LexerLua(Qsci.QsciLexerLua):
    def __init__(self, parent):
        Qsci.QsciLexerLua.__init__(self, parent)

        self.setDefaultFont(BASE_FONT)
        self.setAutoIndentStyle(Qsci.QsciScintilla.AiMaintain)
        self.setFoldCompact(False)

    def defaultColor(self, style):
        if style in [Qsci.QsciLexerLua.Comment, Qsci.QsciLexerLua.LineComment]:
            return QtGui.QColor(0x7f, 0x7f, 0x7f)
        elif style == Qsci.QsciLexerLua.Number:
            return QtGui.QColor(0x00, 0x00, 0xff)
        elif style == Qsci.QsciLexerLua.Keyword:
            return QtGui.QColor(0x00, 0x00, 0x00)
        elif style in [Qsci.QsciLexerLua.BasicFunctions,
                       Qsci.QsciLexerLua.StringTableMathsFunctions,
                       Qsci.QsciLexerLua.CoroutinesIOSystemFacilities]:
            return QtGui.QColor(0x7f, 0x00, 0x7f)
        elif style in [Qsci.QsciLexerLua.String,
                       Qsci.QsciLexerLua.Character,
                       Qsci.QsciLexerLua.LiteralString,
                       Qsci.QsciLexerLua.UnclosedString]:
            return QtGui.QColor(0x7f, 0x00, 0x00)
        elif style == Qsci.QsciLexerLua.Preprocessor:
            return QtGui.QColor(0x00, 0x7f, 0x00)
        return Qsci.QsciLexerLua.defaultColor(self, style)

    def defaultPaper(self, style):
        if style == Qsci.QsciLexerLua.UnclosedString:
            return QtGui.QColor(0xf0, 0xe0, 0xe0)
        return Qsci.QsciLexer.defaultPaper(self, style)

    def defaultFont(self, style):
        font = Qsci.QsciLexer.defaultFont(self, style)
        if style == Qsci.QsciLexerLua.Keyword:
            font.setBold(True)
        elif style in [Qsci.QsciLexerLua.Comment, Qsci.QsciLexerLua.LineComment]:
            font.setItalic(True)
        return font

class LexerFml(Qsci.QsciLexerFml):
    def __init__(self, parent = None):
        Qsci.QsciLexerFml.__init__(self, parent)

        self.setDefaultFont(BASE_FONT)
        self.setAutoIndentStyle(Qsci.QsciScintilla.AiMaintain)
        self.setFoldCompact(False)

class Editor(Qsci.QsciScintilla):
    breakpointAdded = QtCore.pyqtSignal(int)
    breakpointRemoved = QtCore.pyqtSignal(int)

    def __init__(self, parent, viewMgr):
        Qsci.QsciScintilla.__init__(self, parent)
        self.viewMgr = viewMgr

        self.loadedFileName = None
        self.loadedFileType = None
        self.loadedFuncName = None
        self.loadedPathOrProj = None
        self.loadedDuplicateIndex = None #None means there is no duplicates

        #tells textchanged handler not to add unsaved status (when displaying new data)
        self.textChangeLock = False 

        self.status = []
        self.statusMarkers_d = {
            'search':       '^',
            'unsaved':      '*',
            'outofproj':    '@',
            'conflict':     '!',
        }

        self.setFont(BASE_FONT)
        self.setUtf8(True)
        self.setMarginsBackgroundColor(self.palette().color(QtGui.QPalette.Window))
        self.setMarginsForegroundColor(self.palette().color(QtGui.QPalette.WindowText))
        self.setMarginType(0, Qsci.QsciScintilla.SymbolMargin)
        self.setMarginSensitivity(0, True)
        self.setMarginLineNumbers(1, True)
        self.setFolding(Qsci.QsciScintilla.BoxedTreeFoldStyle, 2)
        self.setMarginWidth(0, 14)
        self.setMarginWidth(1, ' 0')
        self.setMarginWidth(2, 12)

        self.SendScintilla(Qsci.QsciScintillaBase.SCI_SETENDATLASTLINE, 0)
        self.SendScintilla(Qsci.QsciScintillaBase.SCI_SETSCROLLWIDTHTRACKING, 1)
        self.SendScintilla(Qsci.QsciScintillaBase.SCI_SETSCROLLWIDTH, 240)

        # Use breakpoint symbols in margin 0
        break_pixmap = QtGui.QPixmap(os.path.join(self.viewMgr.libMgr.getIconDir(), "break.png"))
        self.breakMarker = self.markerDefine(break_pixmap)
        self.breaks = set()
        self.setMarginMarkerMask(0, 1 << self.breakMarker)
        self.setMarginMarkerMask(1, 0)

        # This kind of stuff should be configurable from the GUI
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setTabIndents(True)
        self.setBackspaceUnindents(True)
        self.setWhitespaceVisibility(Qsci.QsciScintilla.WsVisible)
        self.setWhitespaceForegroundColor(QtGui.QColor(0xA0, 0xA0, 0xA0))
        self.setEdgeMode(Qsci.QsciScintilla.EdgeLine)
        self.setEdgeColumn(80)
        self.setEdgeColor(QtGui.QColor(0xE8, 0xE8, 0xE8))
        self.setAutoIndent(True)

        self.linesChanged.connect(self.onLinesChanged)
        self.marginClicked.connect(self.onMarginClicked)
        self.textChanged.connect(self.onTextChanged)

        #Find/Search members
        self.searchArea = [0, 0, 0, 0]

    def setEditorText(self, text, fileName, pathOrProj, funcName=None, dIndex=None):
        self.setEditorData(fileName, pathOrProj, funcName, dIndex)

        self.textChangeLock = True
        self.setText(text)
        self.textChangeLock = False

    #For Times when we must set the data before we can set the text
    def setEditorData(self, fileName, pathOrProj, funcName=None, dIndex=None):
        self.loadedFileName = fileName
        self.loadedDuplicateIndex = dIndex

        #setup fileType
        self.loadedFileType = 'fml' #default to fml in case its Main tab
        if '.' in fileName:
            self.loadedFileType = fileName.split('.')[1]

        self.loadedFuncName = funcName
        self.loadedPathOrProj = pathOrProj

    def updateSyntax(self):
        # Ensure settings which might get overridden by lexers get
        # set properly (should be called after setLexer() calls)
        self.setBraceMatching(Qsci.QsciScintilla.SloppyBraceMatch)
        self.setMatchedBraceForegroundColor(QtGui.QColor(0, 0, 0xFF))
        self.setUnmatchedBraceForegroundColor(QtGui.QColor(0xFF, 0, 0))
        self.SendScintilla(Qsci.QsciScintillaBase.SCI_STYLESETBOLD,
                           Qsci.QsciScintillaBase.STYLE_BRACELIGHT, True)
        self.SendScintilla(Qsci.QsciScintillaBase.SCI_STYLESETBOLD,
                           Qsci.QsciScintillaBase.STYLE_BRACEBAD, True)

    def onLinesChanged(self):
        # Adjust the line number margin width
        self.setMarginWidth(1, ' %d' % (self.lines() + self.lineNumberOffset() - 1))

    def onMarginClicked(self, margin, line, state):
        if margin == 0:
            # Toggle a breakpoint
            if line in self.breaks:
                self.markerDelete(line, self.breakMarker)
                self.breaks.remove(line)
                self.breakpointRemoved.emit(line + 1)
            else:
                self.markerAdd(line, self.breakMarker)
                self.breaks.add(line)
                self.breakpointAdded.emit(line + 1)

    def onTextChanged(self):
        if not self.textChangeLock:
            self.viewMgr.addStatus('unsaved')

    def contextMenuEvent(self, e):
        menu = QtGui.QMenu()

        mainActions = self.viewMgr.libMgr.getMainUiActions()

        #Setup all menu items/actions

        #If a flow name is selected, add an options to open it in new tab
        openAction = None
        if(self.__isFlowName(self.viewMgr.getSelectionText()) and not self.isStatus('outofproj')):
            openAction = menu.addAction('Open in New Tab')
            menu.addSeparator()

        cutAction = menu.addAction(mainActions['cut'])
        copyAction = menu.addAction(mainActions['copy'])
        pasteAction = menu.addAction(mainActions['paste'])
        menu.addSeparator()
        findAction = menu.addAction(mainActions['find'])
        findInFilesAction = menu.addAction(mainActions['findinfiles'])
        currentReferences = menu.addAction(mainActions['currentReferences'])
        referenceInFiles = menu.addAction(mainActions['referenceInFiles'])

        action = menu.exec_(QtGui.QCursor.pos())

        if(action == findAction or action == findInFilesAction):
            self.contextUsed = True
        elif(action == openAction):
            text = self.viewMgr.getSelectionText()
            fileName = self.viewMgr.fileMgr.getFuncParent(self.loadedPathOrProj, text)
            self.viewMgr.displayFlow(fileName, self.loadedPathOrProj, text)

    def __isFlowName(self, text):
        text = text.strip(' ')

        if(re.search('^flow_\w+', text)):
            return True

        return False

    def setSearchArea(self):
        #Set the beginning and end points of the selection area, so we can use find in those boundaries
        self.searchArea = self.getSelection()

        #If there is no selection (ie beginning and end points are the same) return false
        if(self.searchArea[0] == -1):
            return False

        #Set a secondary background color (behind selection) so the user can see what it was as they continue

        return True

    def reselectSearchArea(self):
        self.setSelection(self.searchArea[0], self.searchArea[1], self.searchArea[2], self.searchArea[3])

    def clearSearchArea(self):
        self.searchArea = [0, 0, 0, 0]

        #Set secondary background color back to normal

    def getSearchAreaBeginning(self):
        #[linenum, index in line]
        return [self.searchArea[0], self.searchArea[1]]

    def getSearchAreaEnd(self):
        #[linenum, index in line]
        return [self.searchArea[2], self.searchArea[3]]

    def getCursorBeginning(self):
        #Return the start of the cursor, even if its a selection
        cursor = self.getSelection()

        if(cursor[0] == -1 and cursor[1] == -1):
            return self.getCursorPosition()
        else:
            return [cursor[0], cursor[1]]

    def getCursorEnd(self):
        #Return the end of the cursor, even if its a selection
        cursor = self.getSelection()

        if(cursor[2] == -1 and cursor[3] == -1):
            return self.getCursorPosition()
        else:
            return [cursor[2], cursor[3]]

    def setLuaSyntax(self):
        lex = LexerLua(self)
        self.setLexer(lex)
        self.updateSyntax()

    def setFmlSyntax(self):
        lex = LexerFml(self)
        self.setLexer(lex)
        self.updateSyntax()

    def getLoadTime(self):
        return self.loadTime

    def getLoadedFileName(self):
        return self.loadedFileName

    def getLoadedFileType(self):
        return str(self.loadedFileType)

    def getLoadedFuncName(self):
        return self.loadedFuncName

    def getLoadedPathOrProj(self):
        return self.loadedPathOrProj

    def getLoadedDuplicateIndex(self):
        return self.loadedDuplicateIndex

    def getDisplayDuplicate(self):
        text = ""
        if self.loadedDuplicateIndex:
            text = "(" + str(self.loadedDuplicateIndex) + ")"

        return text

    def getDisplayName(self):
        if(self.loadedFuncName):
            return self.loadedFuncName
        elif(self.loadedFileName):
            return self.loadedFileName

        return ''

    def isFunctionLoaded(self):
        if(self.loadedFuncName):
            return True

        return False

    def isFileLoaded(self):
        if(not self.loadedFuncName):
            return True

        return False

    # -- Status Methods -- #
    def addStatus(self, statusName):
        if self.statusMarkers_d[statusName] and not statusName in self.status:
            self.status.append(statusName)

    def removeStatus(self, statusName):
        #If statusName = all remove all status
        if(statusName == 'all'):
            del self.status[:]
            return

        if statusName in self.status:
            self.status.remove(statusName)

    def isStatus(self, statusName):
        for x in range(len(self.status)):
            if(self.status[x] == statusName):
                return True

        return False

    def getStatusMarkers(self):
        markers = []
        for s in self.status:
            markers.append(self.statusMarkers_d[s])

        return "".join(markers)