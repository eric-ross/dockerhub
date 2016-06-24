#!/usr/bin/python -d
 
import sys, os, re
from PyQt4 import QtCore, QtGui, QtXml
from SFLibManager import *

class ConfigManager():
    def __init__(self, libMgr):
        self.libMgr = libMgr
        self.config = None #Dom obj, built in load
        self.maxHistorys = 15
        self.load()

    def addWindowSize(self, width, height):
        #add windowsize tag in main tag if it doesn't exist
        if(self.config.elementsByTagName('windowsize').isEmpty()):
            node = self.config.createElement('windowsize')
            widthNode = self.config.createElement('winwidth')
            heightNode = self.config.createElement('winheight')
            node.appendChild(widthNode)
            node.appendChild(heightNode)
            self.config.elementsByTagName("main").item(0).appendChild(node)

        #update the text of width and height
        winwidth = self.config.elementsByTagName('winwidth').item(0)
        winwidth.removeChild(winwidth.firstChild())
        winwidth.appendChild(self.config.createTextNode(str(width)))

        winheight = self.config.elementsByTagName('winheight').item(0)
        winheight.removeChild(winheight.firstChild())
        winheight.appendChild(self.config.createTextNode(str(height)))

    def addTreeviewWidth(self, width):
        #add windowsize tag in main tag if it doesn't exist
        if(self.config.elementsByTagName('treeview_width').isEmpty()):
            node = self.config.createElement('treeview_width')
            self.config.elementsByTagName("main").item(0).appendChild(node)

        #update the text of width and height
        treeWidth = self.config.elementsByTagName('treeview_width').item(0)
        treeWidth.removeChild(treeWidth.firstChild())
        treeWidth.appendChild(self.config.createTextNode(str(width)))

    def addLastOpenDir(self, path):
        #add windowsize tag in main tag if it doesn't exist
        if(self.config.elementsByTagName('last_open_dir').isEmpty()):
            node = self.config.createElement('last_open_dir')
            self.config.elementsByTagName("main").item(0).appendChild(node)

        #update the text of width and height
        loDir = self.config.elementsByTagName('last_open_dir').item(0)
        loDir.removeChild(loDir.firstChild())
        loDir.appendChild(self.config.createTextNode(str(path)))

    #--- Add element to combobox historys ---#
    def addFindHistoryEntry(self, combobox):
        #Determine if the history has already been made, if not, add the node
        if(self.config.elementsByTagName(combobox.objectName()).isEmpty()):
            node = self.config.createElement(combobox.objectName())
            self.config.elementsByTagName("find").item(0).appendChild(node)

        existingNode = self.config.elementsByTagName(combobox.objectName()).item(0)

        #If the find combobox(either window, find or replace) and the node doesn't already exist
        if(combobox.objectName() == "comboBox_find" and existingNode.parentNode().nodeName() == 'find'):
            #Check to see if we are under the history limit, if not, remove the oldest entry
            node = self.config.elementsByTagName(combobox.objectName()).item(0)
            if(node.childNodes().length() >= 15):
                node.removeChild(node.firstChild())

            node = self.config.createElement(combobox.currentText())
            self.config.elementsByTagName(combobox.objectName()).item(0).appendChild(node)

        self.save()

    def addReplaceHistoryEntry(self, combobox):
        #Determine if the history has already been made, if not, add the node
        if(self.config.elementsByTagName(combobox.objectName()).isEmpty()):
            node = self.config.createElement(combobox.objectName())
            self.config.elementsByTagName("replace").item(0).appendChild(node)

        existingNode = self.config.elementsByTagName(combobox.objectName()).item(0)

        #If it's the replace combobox and the node doesn't already exist
        if(combobox.objectName() == "comboBox_replace" and existingNode.parentNode().nodeName() == 'replace'):
            #Check to see if we are under the history limit, if not, remove the oldest entry
            node = self.config.elementsByTagName(combobox.objectName()).item(0)
            if(node.childNodes().length() >= 15):
                node.removeChild(node.firstChild())

            node = self.config.createElement(combobox.currentText())
            self.config.elementsByTagName(combobox.objectName()).item(0).appendChild(node)

        self.save()

    #--- Move an entry to the top of the history ---#
    def updateComboHistoryEntry(self, combobox):
        text = combobox.currentText()
        name = combobox.objectName()

        #Get the appropriate nodes from the config tree
        node = self.config.elementsByTagName(name).item(0)
        children = node.childNodes()

        #See if there is already a history entry for the current combo text
        for x in range(children.length()):
            child = children.item(x)
            if(child.nodeName() == text):
                #Delete the node
                node.removeChild(child)

                #Reappend it to the parent node
                node.appendChild(child)
                break

        self.save()

    def addRecentPath(self, fileName, path, proj, funcName, dIndex):
        #Determine if the history has already been made, if not, add the node
        node = self.config.elementsByTagName('recent').item(0)

        if(node.childNodes().length() >= 20):
            node.removeChild(node.firstChild())

        #Create a node named after func or file if its not a func, take into
        #accout the dIndex and tack it on so we can store duplicate flows simultaneously
        if funcName and dIndex:
            newName = funcName + str(dIndex)
        else:
            newName = funcName or fileName

        #The text for the node will be a concat of the pathOrProj and the funcName
        newText = fileName + '|' + path + '|' + proj + '|' + str(funcName) +'|' + str(dIndex)

        #if the node already exists, delete it so the new one moves to the most recent
        if(not self.config.elementsByTagName(newName).isEmpty()):
            node.removeChild(self.config.elementsByTagName(newName).item(0))

        newNode = self.config.createElement(newName)
        nodeText = self.config.createTextNode(newText)
        newNode.appendChild(nodeText)       
        node.appendChild(newNode)

        self.save()

    #--- Put search options into the config ---#
    def updateConfigOptions(self, ops_d, comp):
        if(comp == 'find'):
            look = self.config.elementsByTagName('find_options')
        elif(comp == 'replace'):
            look = self.config.elementsByTagName('replace_options')
        else:
            self.libMgr.printError("Component name in updateFindOptions call incorrect", "Config save error", 10)
            return

        #If there is previous find options, delete it
        if(not look.isEmpty()):
            parent = look.item(0).parentNode()
            parent.removeChild(look.item(0))

        #otherwise make a new node and append it to the find node
        node = self.config.createElement(comp + '_options')
        self.config.elementsByTagName(comp).item(0).appendChild(node)

        #Add search mode
        text = self.config.createTextNode(ops_d['search_mode'])
        child = self.config.createElement('search_mode')
        child.appendChild(text)
        node.appendChild(child)

        #Add find in
        text = self.config.createTextNode(ops_d['find_in'])
        child = self.config.createElement('find_in')
        child.appendChild(text)
        node.appendChild(child)

        #Add start from
        text = self.config.createTextNode(ops_d['start_from'])
        child = self.config.createElement('start_from')
        child.appendChild(text)
        node.appendChild(child)

        #Add verbatim
        text = self.config.createTextNode(ops_d['verbatim'])
        child = self.config.createElement('verbatim')
        child.appendChild(text)
        node.appendChild(child)

        #Add wrap
        text = self.config.createTextNode(ops_d['wrap'])
        child = self.config.createElement('wrap')
        child.appendChild(text)
        node.appendChild(child)

        #Add case
        text = self.config.createTextNode(ops_d['case'])
        child = self.config.createElement('case')
        child.appendChild(text)
        node.appendChild(child)

        self.save()

    #--- Load history into combobox ---#
    def loadCombo(self, combobox):
        eList = QtCore.QStringList()

        combobox.clear()

        #Get all the children of the combobox node
        children = self.config.elementsByTagName(combobox.objectName()).item(0).childNodes()

        #Add all the children to the string list in reverse order so the most recent added is first
        for x in range(children.length()):
            eList.insert(0, children.item(x).nodeName())
        
        #Add the list to the combobox
        combobox.addItems(eList)

    #--- Load Find Config Data ---#
    def getConfigDict(self, comp):
        ops_d = {
            'search_mode':      'normal',
            'find_in':          'current',
            'start_from':       'top',
            'verbatim':         'False',
            'wrap':             'False',
            'case':             'wrap'
        }

        if(comp == 'find'):
            look = self.config.elementsByTagName('find_options')
        elif(comp == 'replace'):
            look = self.config.elementsByTagName('replace_options')
        else:
            self.libMgr.printError("Component name in getConfigDict() call incorrect", "Config load error", 10)
            return

        children = look.item(0).childNodes()

        #If there is no node for the config options, use defaults(first time start)
        if(children.isEmpty()):
            return ops_d

        #If the nod is there, use stored values
        for x in range(children.length()):
            if(children.item(x).nodeName() == 'search_mode'):
                ops_d['search_mode'] = children.item(x).childNodes().item(0).nodeValue()
            elif(children.item(x).nodeName() == 'find_in'):
                ops_d['find_in'] = children.item(x).childNodes().item(0).nodeValue()
            elif(children.item(x).nodeName() == 'start_from'):
                ops_d['start_from'] = children.item(x).childNodes().item(0).nodeValue()
            elif(children.item(x).nodeName() == 'verbatim'):
                ops_d['verbatim'] = children.item(x).childNodes().item(0).nodeValue()
            elif(children.item(x).nodeName() == 'wrap'):
                ops_d['wrap'] = children.item(x).childNodes().item(0).nodeValue()
            elif(children.item(x).nodeName() == 'case'):
                ops_d['case'] = children.item(x).childNodes().item(0).nodeValue()

        return ops_d

    def getWindowSize(self):
        #Start with defaults
        width = 1000
        height = 600

        #if the node exists (it will, but just in case the user deletes it from file manually)
        if(not self.config.elementsByTagName('windowsize').isEmpty()):
            widthNode = self.config.elementsByTagName('winwidth').item(0).firstChild()
            heightNode = self.config.elementsByTagName('winheight').item(0).firstChild()

            width = int(widthNode.nodeValue().toAscii())
            height = int(heightNode.nodeValue().toAscii())

        return QtCore.QSize(width, height)

    def getTreeviewWidth(self):
        width = 200

        if(not self.config.elementsByTagName('treeview_width').isEmpty()):
            node = self.config.elementsByTagName('treeview_width').item(0).firstChild()
            width = int(node.nodeValue().toAscii())

        return width

    def getRecentList(self):
        paths = []

        #if Something is missing, bail
        node = self.config.elementsByTagName('recent')
        if(not node.isEmpty() and node.item(0).hasChildNodes()):
            nodes = self.config.elementsByTagName('recent').item(0).childNodes()
    
            #Build an element [fileName, pathOrProj, funcName] from the xml node
            for x in range(nodes.length()):
                try:
                    fileName, path, proj, funcName, dIndex = str(nodes.item(x).firstChild().nodeValue()).split('|')
                except: #If there is a problem with the node, just erase it and skip
                    node.item(0).removeChild(nodes.item(x))
                    self.save()
                    continue

                #if the file no longer exists, remove it
                if(not os.path.exists(os.path.join(path, fileName))):
                    node.item(0).removeChild(nodes.item(x))
                    self.save()
                    continue

                #Convert func name to None for easier display calling later
                if(funcName == 'None'):
                    funcName = None

                #Fix up dIndex for use, None if its None, an actual int otherwise
                if(dIndex == 'None'):
                    dIndex = None
                else:
                    dIndex = int(dIndex)

                paths.append([fileName, path, proj, funcName, dIndex])

        return paths

    def getLastOpenDir(self):
        #Just grab the newest entry in the recent open node
        path = '/work'
        
        if(not self.config.elementsByTagName('last_open_dir').isEmpty()):
            node = self.config.elementsByTagName('last_open_dir').item(0).firstChild()
            path = str(node.nodeValue().toAscii())

        return path

    #--- Save All Config Data ---#
    def save(self):
        file = QtCore.QFile(self.libMgr.getConfigFile())

        #Load data into config, if file doesn't exist, create one
        if(not file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Truncate | QtCore.QIODevice.Text)):
            self.libMgr.printError('config.ini could not be opened', "Config save failed", 10)
            return

        fileStr = str(self.config.toString())
        file.writeData(fileStr)
        file.close()

    #--- Load Config Data ---#
    def load(self):
        file = QtCore.QFile(self.libMgr.getConfigFile())

        #Load data into config, if file doesn't exist, create one
        if(not file.open(QtCore.QIODevice.ReadWrite | QtCore.QIODevice.Text)):
            print 'config.ini could not be opened'
            return

        self.config = QtXml.QDomDocument("ConfigFile")

        #Validate file xml
        if(not self.config.setContent(file)):
            self.libMgr.printError('config.ini could not be parsed', "Config load failed", 10)
            return
        file.close()

        root = self.config.documentElement()
        
        #If there was wierdness as the root node, error
        if(root.tagName() != 'config' and root.tagName() != ''):
            self.libMgr.printError('config.ini invalid xml', "Config load failed", 10)
            return
        #If there was no root, empty file, start one
        elif(root.tagName() == ''):
            self.__initDefaults()
        #If its good, make sure all the base nodes have not been manually deleted
        else:
            self.__validateDefaults(root)

        self.save()

    def __initDefaults(self):
        #Create root config node
        root = self.config.createElement("config")

        #Create chilidren of root
        main = self.config.createElement("main")
        find = self.config.createElement("find")
        replace = self.config.createElement("replace")
        recent = self.config.createElement("recent")

        #Add children to root
        root.appendChild(main)
        root.appendChild(find)
        root.appendChild(replace)
        root.appendChild(recent)

        #Add root to doc
        self.config.appendChild(root)

    def __validateDefaults(self, root):
        #Check for main, add if its gone
        if(self.config.elementsByTagName('main').isEmpty()):
            main = self.config.createElement("main")
            root.appendChild(main)

        #Check for find, add if its gone
        if(self.config.elementsByTagName('find').isEmpty()):
            main = self.config.createElement("find")
            root.appendChild(main)

        #Check for replace, add if its gone
        if(self.config.elementsByTagName('replace').isEmpty()):
            main = self.config.createElement("replace")
            root.appendChild(main)

        #Check for file_recent, add if its gone
        if(self.config.elementsByTagName('recent').isEmpty()):
            main = self.config.createElement("recent")
            root.appendChild(main)
