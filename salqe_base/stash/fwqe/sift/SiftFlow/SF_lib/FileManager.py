#!/usr/bin/python -d
 
import sys, os, re, glob, subprocess
import datetime, time, threading
from PyQt4 import QtCore, QtGui
from SFLibManager import *

class FileManager():
    def __init__(self, libMgr):
        self.libMgr = libMgr
        self.fileList = []
        self.fileDirs = None
        self.regexs = self.initRegexs()
        self.ignoreFileChanged = {} #key/value is explained in ignoreFileChanged
        
        #Setup the file watcher related stuff
        self.rTimer = QtCore.QObject()
        self.rTimerSignal = QtCore.pyqtSignal()

        self.fWatcher = QtCore.QFileSystemWatcher()
        QtCore.QObject.connect(self.fWatcher, QtCore.SIGNAL("fileChanged(const QString&)"), self.__fileChanged)
        QtCore.QObject.connect(self.rTimer, QtCore.SIGNAL("reloadFile(const QString&)"), self.__reloadFile)
        QtCore.QObject.connect(self.rTimer, QtCore.SIGNAL("skipReloadFile(const QString&)"), self.__skipReloadFile)
        QtCore.QObject.connect(self.fWatcher, QtCore.SIGNAL("directoryChanged(const QString&)"), self.__directoryChanged)

    #--- Public Methods ---#

    # - - - - - - - - - - - - - - - - 
    # - Name: loadProject()
    # - Parameters: none
    # - Description: Loads a project from a .all file. First it clears the temp data directory. Then
    # - creates an list of the .fml names in memory. For each fml it goes through and pulls the actual 
    # - data from the .all and places them in temp .fml files. Lastly it creates a file, fml_list.ini
    # - that contains all .fml names and flow names contained in them
    def loadProject(self, fileDirs): 
        self.fileDirs = fileDirs

        #Repopulate internal filelist object
        self.fileList = self.__createFileList()

        #If fileList is empty then project wasn't loaded successfully
        if(self.fileList == [] or self.fileList == None):
            return False

        return True

    # - - - - - - - - - - - - - - - - 
    # - Name: addFiles()
    # - Description: add files to already loaded standalone files
    # - if any were already loaded in proj files warn the user, return
    # - a list of the files tossed out, if any
    def addFiles(self, filepaths):
        filesNotAdded = []

        for fp in filepaths:
            #If a file is already loaded, skip
            filePath, fileName = os.path.split(fp)
            if(self.isFileLoaded(fileName, filePath)):
                filesNotAdded.append(fp)
                continue

            #Add file to be watched for modifications
            self.fWatcher.addPath(fp)

            #add file to the fileMgr
            newFile = File(fp, self.regexs, self.libMgr)
            self.fileList.append(newFile)
            
        return filesNotAdded

    # - - - - - - - - - - - - - - - - 
    # - Name: fileChanged()
    # - Description: is run when ever a watched file is altered externally
    def __fileChanged(self, path):
        #On linux, this signal is called for each flush, which means there will be many
        #calls for each file change, In order to keep this from reloading a viewer many times
        #We will spin a timered thread to skip the extra signals with a flag, then do the reload

        #if we are ignoring the file and we want to skipOnce (skip this signal, but process ones after this)
        ignoring, skipOnce = self.ignoringFile(path)
        if(ignoring and skipOnce):
            self.setSkipped(path)

            t = threading.Timer(.3, self.__skipReloadTimer, [path]).start()

        elif(not ignoring):
            self.ignoreFileChange(fullPath=path)

            #pass in the path as a param
            t = threading.Timer(.3, self.__reloadTimer, [path]).start()

    def __reloadTimer(self, path):
        #This function is kinda of a hack to just run after the thread timer has gone off
        #and then call the reload function back in the main thread so we're not doin all
        #that in a different thread, which causes issues with Qfont and other things
        self.rTimer.emit(QtCore.SIGNAL("reloadFile(const QString&)"), path)

    def __skipReloadTimer(self, path):
        #This function allows us to skip one signal for path, this is needed for linux so
        #we can get around the multiple signals for one file change shinanigans
        self.rTimer.emit(QtCore.SIGNAL("skipReloadFile(const QString&)"), path)

    def __reloadFile(self, path):
        #Get the files name and pathOrProj
        filePath, fileName = os.path.split(str(path))
        fileProj = self.getFileProj(fileName, filePath)

        #Make sure its actually None since getFileProj will only return strings
        if(fileProj == "None"):
            fileProj = None
        
        #Reload the file if its being displayed and the treeview
        self.libMgr.reloadFile(fileName, fileProj or filePath)
        self.libMgr.reloadFileTreeview(fileName, fileProj or filePath)

        #Reset flag so we don't skip the next file change
        self.allowFileChange(fullPath=path)

    def __skipReloadFile(self, path):
        #Get the files name and pathOrProj
        filePath, fileName = os.path.split(str(path))
        fileProj = self.getFileProj(fileName, filePath)

        #Make sure its actually None since getFileProj will only return strings
        if(fileProj == "None"):
            fileProj = None

        #Reset flag so we don't skip the next file change
        self.allowFileChange(fullPath=path)

    # - - - - - - - - - - - - - - - - 
    # - Name: setSkipped()
    # - Description: set the ignore files entry to False to say we have skipped this once
    def setSkipped(self, path):
        #Only escape special chars for windows since it used backspaces in its paths
        if(sys.platform.startswith('win')):
            escPath = re.escape(str(path))
        else:
            escPath = str(path)

        self.ignoreFileChanged[escPath] = False

    # - - - - - - - - - - - - - - - - 
    # - Name: ignoringFile()
    # - Description: if we're ignoring a file's changed signals, return true and if we skip once
    # - Path must be a full path including file name
    def ignoringFile(self, path):
        #Only escape special chars for windows since it used backspaces in its paths
        if(sys.platform.startswith('win')):
            escPath = re.escape(str(path))
        else:
            escPath = str(path)

        if escPath in self.ignoreFileChanged:
            return [True, self.ignoreFileChanged[escPath]]

        return[False, False]

    # - - - - - - - - - - - - - - - - 
    # - Name: ignoreFileChange()
    # - Description: if a signal comes in that the file in path has change, ignore it        
    def ignoreFileChange(self, fileName=None, pathOrProj=None, fullPath=None, skipOnce=False):
        if(fileName and pathOrProj):
            path = self.getFilePathFull(fileName, pathOrProj)
        elif (fullPath):
            path = fullPath

        #Only escape special chars for windows since it used backspaces in its paths
        if(sys.platform.startswith('win')):
            path = re.escape(str(path))

        #Just add path to the dictionay, the value tells us we are not removing this entry manually with
        #the allowFileChange, but instead want to remove it after the next signal for this path comes
        #in and is skipped once, False = don't remove, we'll use allow, True = remove after next time it's skiped
        self.ignoreFileChanged[str(path)] = skipOnce

    # - - - - - - - - - - - - - - - - 
    # - Name: ignoreFileChange()
    # - Description: stop ignoring the signals for the file in path
    def allowFileChange(self, fileName=None, pathOrProj=None, fullPath=None):
        if(fileName and pathOrProj):
            path = self.getFilePathFull(fileName, pathOrProj)
        elif (fullPath):
            path = fullPath

        #We need to reload the file in the watcher, if the file was deleted and reloaded (git checkout) it for
        #some reason is no longer watched
        if(not self.fWatcher.files().contains(path)):
            self.fWatcher.addPath(path)

        #Only escape special chars for windows since it used backspaces in its paths
        if(sys.platform.startswith('win')):
            path = re.escape(str(path))

        #If this causes an assert, someone is trying to allow something that was not first ignored
        del(self.ignoreFileChanged[str(path)])

    # - - - - - - - - - - - - - - - - 
    # - Name: directoryChanged()
    # - Description: is run when ever a watched directoy is altered externally
    def __directoryChanged(self, path):
        #We really don't care if a dir is changed, but its here just in case we
        #need it in the future
        pass

    # - - - - - - - - - - - - - - - - 
    # - Name: getFmlText()
    # - Parameters: fmlName - string - Name of the file to process
    # - Description: Gets the entire text for a given file.
    def getFmlText(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getFileTextString()

    # - - - - - - - - - - - - - - - - 
    # - Name: getFlowText()
    # - Parameters: fileName, funcName 
    # - Description: This functions gets text of a function from a file
    def getFlowText(self, fileName, pathOrProj, funcName, duplicateIndex=None):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getFunctionText(funcName, duplicateIndex)

    #--- Private Members and Helpers ---#
    def initRegexs(self):
        #fml regex
        regexFML = {
            "functionLine":     re.compile("^flow\s+flow_\w*\s?\("),
            "functionName":     re.compile("(flow_\w*)"),
            "functionEnd":      re.compile("^endflow"),
            "headerTop":        re.compile("^(endflow|endconstants|REQUIRED_FLOWS_|@endif)")
        }
        #lua regexs
        regexLUA = {
            "functionLine":     re.compile("^(local\s*)?function\s+(\w+:?\.?\w+)\s?\("),
            "functionName":     re.compile("\s*function\s+(\w+:?.?\w+)(?:[\s|\(])"),
            "functionEnd":      re.compile("^end"),
            "headerTop":        re.compile("^[^-]")
        }
        regexs = {
            "fml":      regexFML,
            "lua":      regexLUA
        }
        return regexs

    # - - - - - - - - - - - - - - - - 
    # - Name: createFileListFile()
    # - Description: This method opens the .all file and finds the list of .fml files that is after
    # - the actual flows. It then creates an array  fmlList that contains a list of all .fml
    # - file names and the READ_ONLY|WRITE tag.
    def __createFileList(self):
        files = []
        projType = self.libMgr.getLoadedProjType()
        projName = self.libMgr.getLoadedProjName()
        projPath = self.libMgr.getLoadedProjPath()

        #If any of the data is strange, do not continue
        if(not projPath or not projName or not projType):
            return files

        #if sift is using the users .sift dir to chop and get the project from
        if(re.search('homes', projPath) or re.search('Users', projPath) ):
            for infile in glob.glob(os.path.join(projPath, '*' + projType)):
                #Add file to be watched for modifications
                self.fWatcher.addPath(infile)

                #Add file to the fileMgr
                newFile = File(infile, self.regexs, self.libMgr, projName)
                files.append(newFile)

        #if sift is using a git repo
        elif(re.search('work', projPath)):
            if(projType == 'fml'):
                files = self.__processFmlFileList(projName, projPath, projType)
            if(projType == 'lua'):
                files = self.__processLuaFileList(projName, projPath, projType)

        return files

    def __processFmlFileList(self, projName, projPath, projType):
        files = []
        listFileName = 'fml_file.list'

        try:
            listFile = open(os.path.join(projPath, listFileName))
        except IOError:
            self.libMgr.printError('Could not open ' + listFileName, 'File Error', 10)
            return []

        str = listFile.read()
        fmls = str.split(' ')

        #For every entry, make sure it exists, then add it
        for fml in fmls:
            #Quick safety check to make sure the file exists
            if os.path.exists(fml):
                #Add file to be watched for modifications
                self.fWatcher.addPath(fml)

                #Add file to the fileMgr
                newFile = File(fml, self.regexs, self.libMgr, projName)
                files.append(newFile)

        return files

    def __processLuaFileList(self, projName, projPath, projType):
        files = []
        for infile in glob.glob(os.path.join(projPath, '*.' + projType)):
                #Add file to be watched for modifications
                self.fWatcher.addPath(os.path.join(dir, filename))

                #Add file to fileMgr
                newFile = File(infile, self.regexs, self.libMgr, projName)
                files.append(newFile)

        return files

    #--- Find things in files ---#

    # - Name: findAllInFmls(text)
    # - Parameters: text - string - text to look in the file for
    # - Description: Loop through all files, if the text is found in it, add the file name and 
    # - pathOrProj to the list
    def findAllInFiles(self, text, flags):
        foundList = []
        reg = str(text)
        flag = re.I

        if(flags['wo']):
            reg = '^' + text + '$|'             #text by itself
            reg += '^' + text + '(?=[\s\n])|'       #text at start of line
            reg += '[\s]' + text + '(?=[\s\n])|'    #text in a line
            reg += '[\s]' + text + '$'          #text at the end

        if(flags['cs']):
            flag = 0

        for fl in self.fileList:
            result = fl.findInFile(reg, flag)

            #If the tab already exists, don't look in the file (optimization)
            if(result and not self.libMgr.tabAlreadyExists(result[0])):
                foundList.append(result)

        return foundList

    def findReferences(self, text, flags):
        refs = [['all']]
        reg = str(text)
        flag = re.I

        if(flags['wo']):
            reg = '^' + text + '$|'             #text by itself
            reg += '^' + text + '(?=[\s\n])|'       #text at start of line
            reg += '[\s]' + text + '(?=[\s\n])|'    #text in a line
            reg += '[\s]' + text + '$'          #text at the end

        if(flags['cs']):
            flag = 0

        for fl in self.fileList:
            refs.extend(fl.getReferences(reg, flag))

        return refs

    #--- Saving ---#
    def save(self, text, fileName, pathOrProj, funcName, startingLineNum):
        #Get Text ready to save to file
        if(funcName == None):
            toSave = text
        elif(fileName == 'Main'): #user is accidentally saving Main tab, bail
            return False
        elif(funcName != None):
            fileText = self.fileList[self.getFileIndex(fileName, pathOrProj)].getFileTextList()

            #Cut the function text into the file's text
            flow = text.split('\n')

            bText = aText = ''
            grabAfter = False
            for x, line in enumerate(fileText):
                #get text before the change
                if(x < startingLineNum):
                    bText += line

                #get all file text after the changed flow, starting at the line after the old flows endflow in the file
                if(grabAfter):
                    aText += line

                if(x > startingLineNum and not grabAfter and 
                  (self.regexs['fml']['functionEnd'].search(line) or self.regexs['lua']['functionEnd'].search(line))):
                    grabAfter = True

            #assemble the three parts
            toSave = bText + text + aText
        else:
            self.libMgr.printError('File type not recognized.', 'Save Failed', 10)
            return False

        #Refresh the files function list since a function could have been added/renamed
        self.fileList[self.getFileIndex(fileName, pathOrProj)].refreshFunctions()

        #Save to file
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].save(toSave)

    def getLineNumberOffset(self, fileName, pathOrProj, flowName, duplicateIndex=None):
        return self.getFlowText(fileName, pathOrProj, flowName, duplicateIndex)[1]

    def getRepo(self):
        parts = []
        projPath = self.libMgr.getLoadedProjPath()

        if(projPath and sys.platform.startswith('win')):
            parts = projPath.split('\\') 
        elif(projPath and
            (sys.platform.startswith('linux') or sys.platform.startswith('darwin'))):
            parts = projPath.split('/')

        for x in range(len(parts)):
            if(parts[x] == 'work' and re.search("^obj_\w+_\w+$", parts[x+1])): #if in a repo
                return parts[x+1].split('_')[1]

        #temp dir in linux or windows, none
        return 'None'

    # - Name: getMotd()
    # - Description: Get the text for motd from the motd.txt file in SiftFlow/docs
    def getMotd(self):
        try:
            file = open(os.path.join(self.libMgr.getDocDir(), 'motd.txt'))
        except IOError:
            self.libMgr.printError('Could not open motd.txt', 'File Error', 10)
            return

        #get all the text from the motd file and return it
        toRet = ''
        for line in file:
            toRet += line

        return toRet

    # - Name: getAboutText()
    # - Description: Get the text for about dialog from the about.txt file in SiftFlow/docs
    def getAboutText(self):
        try:
            file = open(os.path.join(self.libMgr.getDocDir(), 'about.txt'))
        except IOError:
            self.libMgr.printError('Could not open about.txt', 'File Error', 10)
            return

        #get all the text from the motd file and return it
        toRet = ''
        for line in file:
            toRet += line

        return toRet

    #--- Getters ---#
    def getFileIndex(self, fileName, pathOrProj):
        #Get the correct file object from the list
        for x, lFile in enumerate(self.fileList):
            #If pathOrProj is a proj name
            if(not os.sep in str(pathOrProj)):
                if(fileName == lFile.getName() and lFile.isInProject(pathOrProj)):
                    return x
            #if pathOrProj is a path
            else:
                if(fileName == lFile.getName() and pathOrProj == lFile.getPath()):
                    return x

        #If file was not found in list
        raise Exception("FileNotFound")

    def getFileAndProjNames(self):
        fileList = []

        #resort the file list just incase things have been added or taken away
        self.fileList.sort()

        for fl in self.fileList:
            if(fl.isInProject()):
                fileList.append([fl.getName(), fl.getProjName()])

        #Alphabetize file list so treeview is organized
        return fileList

    def getFullPathsNonProj(self):
        fileList = []
        for fl in self.fileList:
            if(not fl.isInProject()):
                fileList.append(fl.getFullPath())
        return fileList

    def getFunctionNames(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getFunctions()

    def isFunctionDuplicate(self, fileName, pathOrProj, funcName):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].isFunctionDuplicate(funcName)

    def getFilePath(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getPath()

    def getFullPath(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getFullPath()

    def getFileProj(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getProjName()

    def getFilePathFull(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getFullPath()

    def isFileInProj(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].isInProject()

    def getFuncParent(self, pathOrProj, funcName):
        for fl in self.fileList:
            if(fl.doesFunctionExist(funcName) and fl.isInProject(pathOrProj)):
                return fl.getName()

        return False

    def getFileType(self, fileName, pathOrProj):
        return self.fileList[self.getFileIndex(fileName, pathOrProj)].getType()

    def isFileLoaded(self, fileName, path):
        for fl in self.fileList:
            if(fl.getName() == fileName and fl.getPath() == path):
                return True

        return False

    def getDownloadFileList(self, proj, projPath):
        filenames = []

        #Get the modded time of the hlg or all file, whichever exists
        allFullPath = os.path.join(projPath, proj)
        if os.path.exists(allFullPath + '.hlg'):
            allFullPath = allFullPath + '.hlg'
        elif os.path.exists(allFullPath + '.all'):
            allFullPath = allFullPath + '.all'

        allModTime = datetime.datetime.fromtimestamp(os.path.getmtime(allFullPath))

        for fl in self.fileList:
            if(fl.isInProject(proj) and fl.isFileModified(allModTime)):
                filenames.append(fl.getName())

        return filenames

class File():
    def __init__(self, path, regexs, libMgr, projName=None):
        self.libMgr = libMgr
        self.fullPath = str(path)
        self.path, self.name = os.path.split(self.fullPath)
        self.type = os.path.splitext(self.fullPath)[1]

        if(self.type != '.lua' and self.type != '.fml'):
            raise Exception('IOError')

        if(self.type == '.lua'):
            self.regexs = regexs["lua"]
        else:
            self.regexs = regexs["fml"]

        self.projName = projName
        if(self.projName != None): #Make sure its not a QString
            self.projName = str(self.projName)

        self.functions = self.getFunctionNamesFromFile()

    def getFileTextString(self):
        text = '' 

        #Open the correct fml file
        try:
            file = open(self.fullPath, 'r')
        except IOError:
            self.libMgr.printError('File load failed: ' + self.name)
            return False

        for line in file:
            text = text + line

        return text

    def getFileTextList(self):
        #Open the correct fml file
        try:
            file = open(self.fullPath, 'r')
        except IOError:
            self.libMgr.printError('File load failed: ' + self.name)
            return False

        text = file.readlines()
        file.close()

        return text

    # - Name: getFunctionText()
    # - Parameters: funcName - Name of a flow that is in the fml
    # -             duplicateIndex - which copy of the flow to get 
    # - Description: This functions takes the name of a function and gets
    # - the text from the file, returning it as a string
    def getFunctionText(self, funcName, duplicateIndex):
        text = ''
        fHeader = []
        dIndex = duplicateIndex or 0 #if None, set to 0

        #Open the correct fml file
        try:
            file = open(self.fullPath, 'r')
        except IOError:
            self.libMgr.printError('File load failed: ' + self.name)
            return False

        grabbing = False
        beforeFunc = True
        lineStart = 1

        #Set up line regex since we need to cut in funcName
        if(self.type == ".lua"):
            funcReg = "^\s*(local)?\s*function\s+" + funcName + "\s?\("
        else:
            funcReg = "^flow\s+" + funcName + "\s?\("

        for x, line in enumerate(file):  
            if(re.search(str(funcReg), line, re.I)):
                #If there are duplicates, deincrement and continue
                if(dIndex > 1):
                    dIndex -= 1
                    continue

                #If there are no duplicates, or we've arrived at zero (the flow copy we want)
                lineStart += x
                grabbing = True
                beforeFunc = False

            if(grabbing and self.regexs["functionEnd"].search(line)):
                text = text + line
                break

            if(grabbing):
                text = text + line

            if(beforeFunc):
                fHeader.append(line)

        file.close()

        headerDat = self.__getFuncHeader(fHeader)
        toRet = [headerDat[0] + text, lineStart - headerDat[1] + 1]
        return toRet

    # - - - - - - - - - - - - - - - - 
    # - Name: getFuncHeader()
    # - Parameters: fHeader - list of lines above the flow
    # - Description: Gets the comment block above a flow
    def __getFuncHeader(self, fHeader):
        text = ''
        grabbing = True
        headerLen = 0
        for x in range(len(fHeader)):
            line = fHeader[(len(fHeader) - 1) - x]
            headerLen += 1
            #If bottom of the flow above is encountered, stop and return the header
            if(self.regexs["headerTop"].search(line)):
                del fHeader[:(len(fHeader)) - x]
                break

        return ["".join(fHeader), headerLen]

    # - - - - - - - - - - - - - - - - 
    # - Name: getFunctionNamesFromFile()
    # - Parameters: fmlName - string - Name of the .fml file to process
    # - Description: This functions takes the name of a flow file and gets
    # - all the flows from it, returning them as a list
    def getFunctionNamesFromFile(self):
        funcs = []
        try:
            file = open(self.fullPath, 'r')
        except IOError:
            self.libMgr.printError('File load failed: ' + self.name)
            return funcs

        for line in file:
            if(self.regexs["functionLine"].search(line)):
                m = self.regexs["functionName"].search(line)
                func = m.group(1)
                funcs.append(func)

        file.close()
        
        #Sort the names alphebetically
        funcs.sort()
        return funcs

    # -- Find Related Methods -- #
    def getReferences(self, reg, flag):
        refs = []
        funcRefs = []
        currentFunc = 'n/a'
        isDuplicate = False
        duplicate = {}
        dupString = ''

        try:
            file = open(self.fullPath, 'r')
        except IOError:
            self.libMgr.printError('Could not open ' + self.name, 'File Error', 10)
            return

        for x, line in enumerate(file):
            #Store flows as we go so we can display which flow the match is in
            if(self.regexs["functionLine"].search(line)):
                m = self.regexs["functionName"].search(line)
                currentFunc = m.group(1)
                currentFunc.strip(' (')

                #Need to determine if this is a duplicate, store which duplicate it is and add it to funcName
                isDuplicate = self.isFunctionDuplicate(currentFunc)
                    
                if(isDuplicate and (not currentFunc in duplicate)):
                    duplicate[currentFunc] = 1
                    dupString = "(" + str(duplicate[currentFunc]) + ")"
                elif(isDuplicate and (currentFunc in duplicate)):
                    duplicate[currentFunc] += 1
                    dupString = "(" + str(duplicate[currentFunc]) + ")"
                else:
                    dupString = ""

            #Empty the dupstring if we are displaying a line with an n/a flow
            if(currentFunc == "n/a"):
                dupString = ""

            if(re.search(reg, line, flag)):
                toOut = [str(x + 1), currentFunc + dupString, self.name, str(line[:-1]).strip('\n '), self.getPathOrProj()]
                refs.append(toOut)

            #Set flow to n/a if we've just out put the 'endflow' or end function
            #Do it here so the flow still shows up for it rather then displaying it as n/a
            if(self.regexs["functionEnd"].search(line)):
                currentFunc = "n/a"

        file.close()
        return refs

    # - - - - - - - - - - - - - - - - 
    # - Name: findInFile()
    # - Parameters: reg - regex to search for, flag - search flag, typical case sensitive
    # - Description: Searchs each line in the file, if regex is found, returns the file 
    # - and pathOrProj. Mainly used for find in all files
    def findInFile(self, reg, flag):
        try:
            file = open(self.fullPath, 'r')
        except IOError:
            self.libMgr.printError('Could not open ' + self.name, 'File Error', 10)
            return

        for line in file:
            if(re.search(reg, line, flag)):
                file.close()
                return[self.name, self.getPathOrProj()]

    #--- Saving ---#
    def save(self, text):
        #Open the correct fml file
        try:
            file = open(self.fullPath, 'w')
        except IOError:
            self.libMgr.printError('File load failed: ' + self.name)
            return False

        #overwrite the entire contents with the new contents
        file.write(text)
        file.close()
        return True

    # -- Getter -- #
    def doesFunctionExist(self, funcName):
        #Do the search ignoring case since sift likes un unppercase flow names in trace
        for func in self.functions:
            if(func == funcName):
                return True
        return False

    def isInProject(self, inProjName=None):
        result = False

        #If we want to know its in a specific project
        if(inProjName != None and self.projName == inProjName):
            result = True
        #We just want to know its in any project
        elif(inProjName == None and self.projName != None):
            result = True

        return result

    def isFunctionDuplicate(self, funcName):
        dups = False
        occurances = 0

        #does funcName have any duplicates in this file, True False
        for item in self.functions:
            if (item == funcName):
                occurances += 1

        if (occurances > 1):
            dups = True

        return dups

    def refreshFunctions(self):
        self.functions = self.getFunctionNamesFromFile()

    def getName(self):
        return self.name

    def getProjName(self):
        return str(self.projName)

    def getPath(self):
        return self.path

    def getFullPath(self):
        return self.fullPath

    def getFunctions(self, refresh=False):
        #Refresh the files function list since a function could have been added/renamed
        self.refreshFunctions()
        return self.functions

    def getPathOrProj(self):
        if(self.projName):
            return self.projName

        return self.path

    def getType(self):
        return self.type
