#!/usr/bin/env python
from __future__ import with_statement 

REV="13.1.9"  # Update manually to the date this file is last edited.
###############################################################################
# Sift
#
# Text or GUI based tool to trace and debug mech flows. Runs either real time
# or takes a -f file of raw trace data. Displays flows, arguments, global
# variables, and local variables in readable form, similar to what you see
# in source code. Also provides for basic debugging with breakpoints, step,
# next, finish, and backtrace features. Finally it can set and get DSIDs
# and global variables.
#
# Documentation:
# http://hpedia.hp.com/wiki/Sift
#
# Platforms:
# Linux, Windows, Mac
#
# Contact:
# erik.kilk@hp.com
#
# Requirements:
# Python 2.5 or 2.7
# http://www.python.org/
#
# pyserial 2.5
# http://pyserial.sourceforge.net/
###############################################################################

from optparse import OptionParser, SUPPRESS_HELP
import sys
import os
import time
import subprocess
import signal
import optparse
import ConfigParser
import string
import unicodedata
import collections
import re
import pdb
import Queue
import glob
import threading
import select
import socket
import SocketServer
import shutil
import shelve
import struct
import datetime
import platform
try:                    # Optional if you don't use serial
    import serial       # From http://pyserial.sourceforge.net
    pyserial = True
except ImportError:
    pyserial = None
import subprocess
import shlex
import uu
import traceback
import webbrowser
import ctypes
import errno
import urllib
import urllib2

try:
    import fcntl
    import termios
except ImportError:
    fcntl = None

try:                    # For Android SL4A support
    import android
except ImportError: pass

try:                    # Optional, graphical front end
    from PyQt4 import QtCore, QtGui
except ImportError:
    QtGui = None

try:
    import SiftWidget
except ImportError:
    SiftWidget = None

#If qtgui is imported, then import SiftFlow to avoid module errors
siftflow = None
if QtGui:
    try:
        from SiftFlow.SiftFlow import *
        siftflow = True
    except ImportError:
        siftflow = None

# User Options
DEFAULT_USER_OPTIONS         = {'gui': False,
                                'autoupdate': True,
                               }

# Files created by Sift
DEFAULT_LOGFILE              = "trace.sift"             # Human readable trace
DEFAULT_HTML_FILE            = "trace.html"             # Browser readable trace
BACKUP_DEFAULT_LOGFILE       = "trace.bak"              # Backup of last "trace.sift"
RAW_OUTPUT_FILE              = "trace.raw"              # Original raw trace file
DEFAULT_OUTPUT_FILE_SIZE     = 209715200                # Limit trace file size
MAX_HTML_SIZE                = 10000000                 # Limit HTML to this size

# Config files in user's $HOME/.sift directory
SIFT_CONFIG_DIR              = os.path.expanduser(os.path.join('~',".sift"))
SIFT_ICON                    = "sift.png"               # Icon file
SIFT_INI                     = "sift.ini"               # Default settings
STARTUP_FILE                 = "sift.rc"                # Initial commands to sent to printer
HISTORY_FILE                 = "sift.hist"              # Users's history of commands
FAVORITE_FILE                = "sift.fav"               # User's favorites on GUI
HIGHLIGHT_FILE               = "sift.highlight"         # User's saved highlights
ONDBUG_FILE                  = "sift.dbug"              # on_dbug comonent names
IPADDRESS_FILE               = "sift.ip"                # ip addresses
LASTPORT_FILE                = "sift.lastport"          # last port used
LAST_FILE                    = "sift.lastfile"          # last file used
ALL_DIRECTORY                = "compile"                #
SHELF_FILE                   = "sift.persist"           # persistent things to remember
SETTINGS_FILE                = "sift.settings"          # persistent settings
USAGE_FILE                   = "sift.usage"             # usage transmissions
SIFT_SERVER                  = "http://sift.vcd.hp.com/"
USAGE_SCRIPT                 = "postusage.php"
N_STRINGS                    = ['create_fiber']

# Port numbers for network services
PCS_PORT                     = 8779
SHELL_PORT                   = 7435
SDV_PORT                     = 8080
UDW_PORT                     = 6839
SS_PORT                      = 7777
SIFT_PORT                    = 9999
PORT_NAMES_TO_NUMBER         = {"pcs":PCS_PORT, "shell":SHELL_PORT, "udw":UDW_PORT,
                                        "ss":SS_PORT, "sift":SIFT_PORT}

# Various constants
ERROR_PREFIX                 = "\nSIFT: "
PROJ_DIR_INFO                = "proj_dir_info.spd"
PROMPT                       = "-> "
ECHO_PROMPT                  = ';udw.echo "' + PROMPT + '";'
TAB_COMPLETION_ASK_USER      = 10
# EOLN                         = "\r\n"
EOLN                         = '\n'
COMMENT                      = '#'
GOODBYE                      = "Press <ENTER> to quit"
PJL_ENTER_UDW                = "@PJL ENTER LANGUAGE=UDW\n"
PJL_EXIT_UDW                 = "exit;\x1B%-12345X"
PJL_UDW_TIMEOUT              = 60*5
SYNC_STRING                  = "sync"
FLOWC                        = "flowc"
FLOWCEXE                     = "flowc.exe"
DEFAULT_PORT                 = "0"
RESOURCE_PATH                = [SIFT_CONFIG_DIR, os.sys.path[0],
                                r"/sirius/tools/sift", os.getcwd()]
SEARCH_PATH                  = [(r"~\Documents\HP\FlexFlow\Compile", True),
                                (r"~\Documents\HP\FlexScript\Compile", True),
                                (r"C:\Program Files\HP\FlexTool\Compile", False), 
                                (r"C:\Program Files (x86)\HP\FlexTool\Compile", False), 
                                (r"/sirius/work", True), (r"~", False),
                                (os.path.join(SIFT_CONFIG_DIR, ALL_DIRECTORY), True)]
SDV_LIST                     = [r"C:\Program Files (x86)\HP\SDV\sdv.appref-ms",
                                r"C:\Program Files\HP\SDV\sdv.appref-ms"]

SIRIUS_BUILD_DIR             = "/sirius/work"

SIFT_COMMANDS = ["pwd","b","break","port","trace","level","tick","tock",
                 "sdv","browse","sweep","nosweep","depth","door","power","tap",
                 "vtap","serial_number","dot4","flash","lp","compile","download","cad",
                 "rev","exit","assert","crash","print","info","exec","save","reload",
                 "ok","options","watch","help","quit","q", "edit"]
                
# Array of internal sift commands used for unpausing
internal_cmd = ["pwd", "calls", "bt", "backtrace", "where", "w", "l", "l+",
    "l-", "l.", "print", "help"]

# Trace command bitfield
TRACE_FLUSH     = 0x01
TRACE_FLOWS     = 0x02
TRACE_GLOBALS   = 0x04
TRACE_LOCALS    = 0x08
TRACE_KEYWORDS  = 0x10
TRACE_ARRAYS    = 0x80


######################################################################
#
# Configurable defaults
#
# Users may adjust defaults in .sift/sift_init.py
#
######################################################################

sys.path.append(SIFT_CONFIG_DIR)
try:
    # Users con configure their own stuff here
    from sift_init.py import *
except ImportError: pass


######################################################################
#
# Adjustments for Android
#
# FUTURE: Some of this should be moved where SIFT_CONFIG_DIR
# is defined and some maybe into main() and/or process_options().
#
######################################################################

if 'android' in globals():
    # SL4A's home directory is incorrect
    SIFT_CONFIG_DIR = '/sdcard/.sift'

    # Get an IP address from the user (hack)
    droid = android.Android()
    DEFAULT_PORT = droid.dialogGetInput("Address", "Enter printer IP address").result


#####################################################################
#
# Common error mechanism
#
#####################################################################

class ErrCode:
    def __init__(self, code, die, string):
        self.code = code
        self.string = string
        self.die = die

# Keep list of possible errors here:
err_codes = {}
err_codes["PCS_PRINT_FAIL"]      = ErrCode(10, False, "PCS didn't connect printer. Is printer in use?")
err_codes["PCS_DEBUG_FAIL"]      = ErrCode(11, False, "PCS didn't connect printer. Is printer in use? FlexCIO installed? DOT4 enabled?")
err_codes["LOST_CONNECTION"]     = ErrCode(12, False, "Lost connection to printer.")
err_codes["NO_PCS_SERVICE"]      = ErrCode(13, True,  "Couldn't connect to PCS. Is pcs.exe running on the PC (pcs on Linux)?")
err_codes["NO_SS_SERVICE"]       = ErrCode(14, False, "Is ss.exe running on the PC?")
err_codes["PCS_INIT_FAILURE"]    = ErrCode(15, True,  "PCS isn't talking. Suggest killing and restarting pcs.exe (pcs on Linux).")
err_codes["SERIAL_ERROR"]        = ErrCode(16, False, "Serial port error, is some other program using it?")
err_codes["NETWORK_CONNECTION"]  = ErrCode(17, False, "Host wouldn't accept network connection.")
err_codes["QT4_NOT_INSTALLED"]   = ErrCode(18, False, "GUI requires PyQt4 from http://www.riverbankcomputing.co.uk/software/pyqt/download")
err_codes["PYSERIAL_ERROR"]      = ErrCode(19, False, "Install pySerial to user the serial port.")
err_codes["RESET_EXIT"]          = ErrCode(20, True,  "Settings reset. Restart Sift.")
err_codes["USER_EXIT"]           = ErrCode(99, False, "User exit.")

# Call when one of the above errors, call this:
def exit(error):
    global gui
    if error in err_codes:
        output_str(EOLN + " " + err_codes[error].string + "  (" + error + ")" + EOLN, "warning")
        if (not gui) and err_codes[error].die:
            if (os.name == "nt"): raw_input(GOODBYE)
            quit_event.set()
            if error in err_codes:
                sys.exit(err_codes[error].code)
    else:
        sys.exit(0)

# List the error codes for Sift Launch Pad
def errcodes():
    for error in err_codes:
        print str(err_codes[error].code) + "-" + err_codes[error].string + " (" + error + ")"


##############################################################
#
# Output Formatting Tables
#
# Data used to format trace output for various devices. Handles
# colorizing, Linux terminal escape sequences, TkTalk codes,
# and special HTML generation for browsers and Sift Data Viewer.
#
##############################################################

# winbase.h
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12

# wincon.h
FOREGROUND_BLACK     = 0x0000
FOREGROUND_BLUE      = 0x0001
FOREGROUND_GREEN     = 0x0002
FOREGROUND_CYAN      = 0x0003
FOREGROUND_RED       = 0x0004
FOREGROUND_MAGENTA   = 0x0005
FOREGROUND_YELLOW    = 0x0006
FOREGROUND_GREY      = 0x0007
FOREGROUND_INTENSITY = 0x0008 # foreground color is intensified.

BACKGROUND_BLACK     = 0x0000
BACKGROUND_BLUE      = 0x0010
BACKGROUND_GREEN     = 0x0020
BACKGROUND_CYAN      = 0x0030
BACKGROUND_RED       = 0x0040
BACKGROUND_MAGENTA   = 0x0050
BACKGROUND_YELLOW    = 0x0060
BACKGROUND_GREY      = 0x0070
BACKGROUND_INTENSITY = 0x0080 # background color is intensified

# WinSift aka sdv colors
sdv_color_dictionary = {
        "default": '', "line": '', "popline": EOLN,
        "F": '<b>', "popF": '</b>',
        "r": '<font color="#595959">', "popr": '</font>',
        "args": '<font color="#008144">', "popargs": '</font>',
        "comment": '<font color="#595959">', "popcomment": '</font>',
        "raw": '<font color="#595959">', "popraw": '</font>',
        "K": '<font color="blue">', "popK": '</font>',
        "number": '<font color="red">', "popnumber": '</font>',
        "G": '<font color="green">', "popG": '</font>',
        "L": '<font color="#595959">', "popL": '</font>',
        "named": '<font color="magenta">', "popnamed": '</font>',
        "error": '<font color="red">', "poperror": '</font>',
        "warning": '<font color="red">', "popwarning": '</font>',
        }

tktalk_color_dictionary = {'default': chr(222),'indent': chr(200+FOREGROUND_RED),
        'F': chr(200+FOREGROUND_BLACK),
        'r': chr(200+FOREGROUND_GREY), 'args': chr(200+FOREGROUND_CYAN),"comment": chr(200+FOREGROUND_GREY),
        "time": chr(200+FOREGROUND_GREY), "raw": chr(200+FOREGROUND_GREY), 'K': chr(200+FOREGROUND_BLUE),
        'number': chr(200+FOREGROUND_RED), 'G': chr(200+FOREGROUND_GREEN), 'L': chr(200+FOREGROUND_GREY),
        'named': chr(200+FOREGROUND_MAGENTA), 'error': chr(200+FOREGROUND_RED),
        'warning': chr(200+FOREGROUND_RED)}

xterm_color_dictionary = {"default": "\033[0m", "indent": "\033[31m", "F": "\033[1;30m", "r": "\033[30m",
        "args": "\033[0;34m", "comment": "\033[90m", "raw": "\033[90m", "time": "\033[90m",
        "K": "\033[1;34m", "number": "\033[31m", "G": "\033[32m", "L": "\033[90m", "named": "\033[0;35m",
        "error": "\033[31m", "warning": "\033[1;31m"}

html_color_dictionary = {
        "default":    '<span class=%s>', "popdefault": '</span>',
        "text":       '<div class=text>', "poptext":    '</div>\n',
        "line":       '<div class="%s" level=%d onmousedown="toggle(event)">', "popline":    '</div>\n',
        "clear":      ''}

qt_color_dictionary = {
        "default": '\033R0', "indent": '\033N1', "F": '\033B0', "r": '\033N8', "args": '\033N4',
        "comment": '\033N8', "raw": '\033N8', "K": '\033B4', "number": '\033N1', "G": '\033N2',
        "L": '\033N8', "named": '\033N5', "info": '\033N4', "error": '\033N1', "warning": '\033B1',
        }

debug_color_dictionary = {"default":"[%s]"}
no_color_dictionary = {"default":""}

color_dictionary = {"none":    no_color_dictionary,
        "tktalk":  tktalk_color_dictionary,
        "sdv":     sdv_color_dictionary,
        "qt":      qt_color_dictionary,
        "html":    html_color_dictionary,
        "debug":   debug_color_dictionary,
        "xterm":   xterm_color_dictionary}


###############################################################################
#
# uni2str()
#
# Convert unicode strings to underware friendly strings. Replace all unicode
# quotes with most sensible " or ' character.
#
###############################################################################

unitranslate = {0x2018:39,0x2019:39,0x201A:39,0x201B:39,0x2032:39,0x2035:39,
                0x201C:34,0x201D:34,0x201E:34,0x201F:34,0x2033:34,0x2036:34}

def uni2str(u):                         # often u will be a QString
    try:
        return str(u)                   # try easy conversion first
    except UnicodeEncodeError:
        print "handling unicode"
        s = ""                          # need to do this manually
        for c in u:
            try:                            # translate if we can
                s += chr(unitranslate[ord(unicode(c))])
            except KeyError:
                try:                        # otherwise normal conversion
                    s += chr(ord(unicode(c)))
                except ValueError:
                    pass                    # otherwise remove the unknown char
        return s


###############################################################################
#
# Printer Data
#
# Contains all the printer data used to transform raw trace data into human
# readable data. Contains the results of reading the .i and .hlg symbol files
# that have been created by the flow compiler and firmware build process.
#
###############################################################################


headers = {}

def init_arrays_and_dict_for_hlg():
    global dsids
    global dsids_by_id
    global dsids_by_name
    global everything_hlg

    dsids                  = []
    dsids_by_id            = {}    # key=ID, value=name
    dsids_by_name          = {}    # key=name, value=ID
    everything_hlg         = []     # list of everything read in from .hlg

def init_arrays_and_dictionaries():
    global flows
    global flows_by_id
    global flows_by_name
    global frames
    global keywords
    global keywords_by_id
    global keywords_by_name
    global global_ids
    global global_names
    global constant_ids
    global constant_names
    global constant_values
    global constant_name2value
    global values_for
    global statement_by_offset
    global statement_by_file_line
    global filenames
    global everything
    global everything_dictionary
    global fml_path_by_file_name
    global underware
    global lua_file

    flows                  = []
    flows_by_id            = {}    # Flows by id
    flows_by_name          = {}    # Flows by name
    frames                 = {}    # Keeps track of flows for break point backtrace print out
    keywords               = []
    keywords_by_id         = {}
    keywords_by_name       = {}    # Keyword objects by ID
    global_ids             = {}    # key=ID, value=name
    global_names           = {}    # key=name, value=ID
    constant_ids           = {}    # key=id, value=name
    constant_names         = {}    # key=name, value=id
    constant_values        = {}    # key=value, value=(list of names)
    constant_name2value    = {}    # key=name, value=value
    values_for             = {}
    statement_by_offset    = {}     # key=offset, value=statement
    statement_by_file_line = {}     # key=filename,line, value=statement
    filenames              = []     # list of filenames
    everything             = []     # list of everything (for keyword completion)
    everything_dictionary  = {}     # alphabetized dictionary of everything used for tab completion
    fml_path_by_file_name  = {}     # Keeps track or fml file locations
    underware              = []     # list of underware commands
    lua_file               = {}     # lua trace file names, indexed by "indent" field

    for i in range(8):
        lua_file[i] = {'file':"", 'func':""}  # set some defaults for first "indent" level

    # If in a Sirius build directory append XM lua directories to our search path for getline().
    try:
        f = open(os.getcwd() + "/subdirs_xm", 'r')
        xm_dirs = f.read().split()
        for i in xm_dirs:
           sys.path.append(i)
    except (IOError, OSError): pass


# Runtime data
flow_stack             = {}    # key=indent, value=flow
conn2color             = {}    # key=socket connection, value = clue to which color code to use


# Machine state names are hardcoded since they are not available in the .i and .hlg files.

machine_states  = [ "INITIALIZING", "OFF", "MFG_OFF", "GOING_ON", "IDS_STARTUP_REQUIRED", "IDS_STARTUP",
    "IDLE", "IO_PRINTING", "REPORTS_PRINTING", "CANCELING_PRINTING", "IO_STALL", "DRY_TIME_WAIT",
    "PEN_CHANGE", "OUT_OF_PAPER", "BANNER_EJECTED_NEEDED", "BANNER_MISMATCH", "PHOTO_MISMATCH",
    "DUPLEX_MISMATCH", "MEDIA_TOO_NARROW", "MEDIA_UPSIDE_DOWN", "MEDIA_JAM", "CARRIAGE_STALL", "PAPER_STALL",
    "SERVICE_STALL", "PICK_MOTOR_STALL", "PUMP_MOTOR_STALL", "MOTOR_STALL", "PEN_FAILURE",
    "INK_SUPPLY_FAILURE", "HARD_ERROR", "IDS_HW_FAILURE", "POWERING_DOWN", "FP_TEST", "HYDE_MISSING",
    "OUTPUT_TRAY_CLOSED", "DUPLEXER_MISSING", "DUPLEXER_INVALID", "OUT_OF_INK", "MEDIA_SIZE_MISMATCH",
    "ASSERT", "LANG_MENU", "DC_PRINTING", "DC_PRINTING_ABORT_ERROR", "DC_SAVING", "DC_CANCELING_SAVING",
    "DC_SAVING_ABORT_ERROR", "DC_DELETING", "DC_CANCELING_DELETING", "DC_DELETING_ABORT_ERROR",
    "DC_EMAILING", "DC_EMAIL_ABORT_ERROR", "DC_CANCELING_EMAILING", "DC_CARD_SHORT_ERROR",
    "DC_CARD_REMOVED_ERROR", "DC_BUBBLES_SCANNING", "DC_BUBBLES_SCAN_DONE", "DC_CANCELING_BUBBLES",
    "DC_BUBBLES_ABORT_ERROR", "DC_USBHOST_OVERCURRENT_ERROR", "DC_VIDEO_ENHANCE_PROCESSING",
    "DC_CANCELING_VIDEO_ENHANCE", "DC_VIDEO_ENHANCE_ABORT_ERROR", "DC_VIDEO_ENHANCE_DELETE",
    "DC_VIDEO_ENHANCE_ZOOM", "DC_VIDEO_ENHANCE_PLAYBACK", "DC_REDEYE_PROCESSING", "DC_CANCELING_REDEYE",
    "DC_REDEYE_ABORT_ERROR", "MEDIA_TOO_WIDE", "MEDIA_WRONG", "MEDIA_TYPE_WRONG", "DOOR_OPEN",
    "PEN_NOT_LATCHED", "INK_SUPPLY_CHANGE", "GENERIC_ERROR", "IDS_STARTUP_BLOCKED_LOI","VLOI",
    "ATTENTION_NEEDED", "(NUM_STATES)" ]


############### Helper fuctions for arrays

def is_constant(str):
    if str         in constant_names: return True
    if str.upper() in constant_names: return True
    if str.lower() in constant_names: return True
    return False

def constant_id_and_value(str):
    if str         in constant_names:
        return constant_names[str], constant_name2value[str]
    if str.upper() in constant_names:
        return constant_names[str.upper()], constant_name2value[str.upper()]
    if str.lower() in constant_names:
        return constant_names[str.lower()], constant_name2value[str.lower()]
    raise KeyError


##############################################################################################
#
# Port and Connection Classes 
#
##############################################################################################

class PortError(Exception):
    def __init__(self, msg):
        self.msg = str(msg)
    def __str__(self):
        return self.msg

class NoService(PortError): pass
class LostService(PortError): pass
class TryAgain(PortError): pass

##############################################################################################

class BasePort(object):
    """Base port to assure all ports have minimal set of features."""
    def __init__(self, printer_is_open_event=None):
        debug("BasePort._init_", printer_is_open_event)
        self.name = ""                      # name displayed to user of the connection
        self.model = ""                     # printer model number if available
        self.serial = ""                    # printer serial number if available
        self.running_shell = False          # shell connection (prompt and needs 'udws ""')
        self.running_udw = False            # udw connection (no prompt and pure udw) 
        self.running_PJL = False            # PJL based connection, needs PJL_ENTER_UDW
        self.terminator = '\n'              # udw terminator
        self.loss_expected = False          # port purposely closed, may see LostService
        self.base_port_open = False
        self.data_seen_event = threading.Event()
        if printer_is_open_event:
            self.printer_is_open_event = printer_is_open_event
        else:
            self.printer_is_open_event = threading.Event()
        self.printer_is_open_event.clear()

    def open(self):
        """Derived port should set self.printer_is_open_event.set() when ready"""
        debug("BasePort.open", self.base_port_open)
        self.base_port_open = True
        return self

    def close(self, loss_expected=True):
        debug("BasePort.close", loss_expected, self.base_port_open)
        if self.base_port_open:
            self.base_port_open = False
            self.loss_expected = loss_expected
            self.printer_is_open_event.clear()

    # read and write methods must be written by derived classes

    
##############################################################################################
#
# No Connection Port 
#
# A port for testing and letting us operate without necessarily a good connection. 
#
##############################################################################################

class NoConnectionPort(BasePort):
    """Echo whatever was written"""

    def __init__(self, printer_is_open_event):
        debug("NoConnectionPort.__init__", printer_is_open_event)
        super(NoConnectionPort, self).__init__(printer_is_open_event)
        self.no_connection_port_open = False
        self.queue = Queue.Queue()

    def open(self):
        debug("NoConnectionPort.open", self.no_connection_port_open)
        super(NoConnectionPort, self).open()
        self.name = "No Connection"
        self.no_connection_port_open = True 
        self.printer_is_open_event.set()    # derived ports must set when ready
        if options.debug: debug("NoConnectionPort.open return", self.no_connection_port_open)
        return self                         # derived ports must return self

    def close(self, loss_expected=True):
        debug("NoConnectionPort.close", loss_expected, self.no_connection_port_open)
        super(NoConnectionPort, self).close(loss_expected)
        if self.no_connection_port_open:
            self.no_connection_port_open = False
        debug("NoConnectionPort.close return", self.no_connection_port_open)

    def read(self, size=None):
        debug("NoConnectionPort.read", size, self.no_connection_port_open)

        data = ""
        while self.no_connection_port_open and not data:
            try:
                data = self.queue.get(timeout=.2)
            except Queue.Empty:
                pass

        if not self.no_connection_port_open:
            raise LostService("NoConnection port closed")

        self.data_seen_event.set()
        debug("NoConnectionPort.read return ", len(data), self.no_connection_port_open) 
        return data
             
    def write(self, data):
        debug("NoConnectionPort.write", len(data), self.no_connection_port_open)
        if self.no_connection_port_open:
            self.queue.put(data)
            self.queue.put(".\n")


##############################################################################################
#
# Serial Class 
#
# Serial wrapper class
#
##############################################################################################

class SerialPort(BasePort):
    BAUD_RATE = 115200

    def __init__(self, printer_is_open_event=None):
        debug("SerialPort.__init__", printer_is_open_event)
        super(SerialPort, self).__init__(printer_is_open_event)
        self.serial_port_open = False

    def open(self, device=0):
        debug("SerialPort.open", device, self.serial_port_open)
        super(SerialPort, self).open()
        try:
            self.serial = serial.Serial(device, SerialPort.BAUD_RATE, timeout=.3)
            self.serial.flushInput()
        except NameError:
            output_str(" pySerial isn't installed in " + sys.exec_prefix + EOLN, "warning");
            output_str(" Install pySerial-2.5.win32.exe from http://pyserial.sourceforge.net"+EOLN,
                 "warning");
            if not gui and os.name == "nt":
                raw_input(GOODBYE)
            debug("SerialPort.open RAISE NoService(pySerial not installed)", device, 
                self.serial_port_open)
            raise NoService("pySerial not installed")
        except serial.SerialException, m:
            debug("SerialPort.open RAISE NoService(m)", m, self.serial_port_open)
            raise NoService(str(m))
        self.running_shell = True
        self.name = str(device)
        self.serial_port_open = True
        self.printer_is_open_event.set()        # derived ports must set when ready
        debug("SerialPort.open return")
        return self

    def close(self, loss_expected=True):
        """Close the serial port"""
        debug("Serialport.close", loss_expected, self.serial_port_open)
        super(SerialPort, self).close(loss_expected)
        if self.serial_port_open:
            self.serial_port_open = False
            try:
                self.serial.close() 
            except serial.SerialException, m:
                debug("Serialport.close with SerialException", self.serial_port_open)
                pass 
        debug("Serialport.close return", self.serial_port_open)
    
    def read(self, size=None):
        """Read a block of characters"""
        # if options.debug: debug("Serialport.read", size, self.serial_port_open)
        try:
            if self.serial_port_open:
                if not size:
                    try:
                        size = self.serial.inWaiting()
                    except serial.SerialException, m:
                        debug("Serialport.read RAISE LostService1", m, self.serial_port_open)
                        raise LostService(str(m))
                    except IOError:
                        raise LostService(str(sys.exc_info()[0]))
                    if size < 1:
                        size = 1
                try:
                    data = self.serial.read(size)
                except serial.SerialException, m:
                    debug("Serialport.read RAISE LostService2", m, self.serial_port_open)
                    raise LostService(str(m))
                except select.error:
                    debug("Serialport.read RAISE LostService3", sys.exc_info()[0], self.serial_port_open)
                    raise LostService(str(sys.exc_info()[0]))
                except:
                    debug("Serialport.read RAISE LostService4", sys.exc_info()[0], self.serial_port_open)
                    raise LostService(str(sys.exc_info()[0]))
                if not data:
                    time.sleep(.2)
                    # debug("Serialport.read RAISE TryAgain(No serial data)", self.serial_port_open)
                    raise TryAgain("No serial data") 
            else:
                debug("Serialport.read RAISE LostService4(No serial data)", self.serial_port_open)
                raise LostService("Serial port not open")
        except LostService, e:
            debug("Serialport.read RAISE LostService5", self.serial_port_open)
            raise LostService(e)
        self.data_seen_event.set()
        return data

    def write(self, data):
        """Write data to serial port. Ignore errors."""
        debug("Serialport.write write", self.serial_port_open)
        if self.serial_port_open:
            try:
                debug("Serialport.write data", self.serial_port_open)
                self.serial.write(data)
            except serial.SerialException, m:
                debug("Serialport.write SerialException", self.serial_port_open)
                self.close(loss_expected=False)
        debug("Serialport.write return", self.serial_port_open)



##############################################################################################
#
# Socket Class 
#
# Socket wrapper class
#
##############################################################################################

class SocketPort(BasePort):
    def __init__(self, printer_is_open_event):
        """Create our socket"""
        debug("SocketPort.__init__", printer_is_open_event)
        super(SocketPort, self).__init__(printer_is_open_event)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_port_open = False

    def open(self, hostname=None, port=None, mark_printer_open=True):
        """Open our socket"""
        debug("SocketPort.open", hostname, port, self.socket_port_open)
        super(SocketPort, self).open()
        if not hostname:
            self.hostname = "localhost"
        else:
            self.hostname = hostname

        # Try to connect to the requested host
        self.socket.settimeout(3)
        try:
            self.socket.connect((self.hostname, port))
        except socket.error, message:
            debug("SocketPort.open socket.error1 RAISE NoService(m)", message, self.socket_port_open)
            raise NoService(str(message))
        except socket.error, (value, message):
            if value == errno.ECONNREFUSED or value == errno.WSAECONNREFUSED:
                debug("SocketPort.open socket.error2 RAISE NoService(m)", value, message, 
                        self.socket_port_open)
                raise NoService(str(message))
            else:
                debug("SocketPort.open socket.error3 RAISE", value, message, self.socket_port_open)
                raise           # catch error response I'm not aware of

        # Try turning on KEEPALIVE. Some OSs apparently will then detect
        # sudden socket shutdowns (as occurs during asserts and power offs).
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except:
            debug("SocketPort.open KEEPALIVE failed")

        # Assure we actually connected. Printers without NetShell will connect
        # but then subsequently disconnect on the first read.
        try:
            self.socket.settimeout(.1)
            debug("SocketPort.open test connection")
            num_sent = self.socket.send(" ")    # space seems to be safe
        except socket.timeout:
            debug("SocketPort.open TIMEOUT", self.socket_port_open)
            pass
        except socket.error, message:
            debug("SocketPort exception RAISE NoService(m)", message, self.socket_port_open)
            raise NoService(str(message))
        else:
            if num_sent != 1:
                debug("SocketPort RAISE NoService(Printer closed connection)", self.socket_port_open)
                raise NoService("Printer closed connection")
        self.socket_port_open = True
        self.running_shell = True
        self.name = self.hostname
        if mark_printer_open: 
            self.printer_is_open_event.set()    # derived ports must set when read
        debug("SocketPort.open return", self.hostname, port, self.socket_port_open)
        return self
            
    def close(self, loss_expected=True):
        """Close our socket"""
        debug("SocketPort.close", self.socket_port_open)
        super(SocketPort, self).close(loss_expected)
        if self.socket_port_open:
            self.socket_port_open = False
            try:
                self.socket.close()
            except socket.error, message:
                debug("SocketPort.close socket.error", message, self.socket_port_open)
                pass
        # time.sleep(1)           # for some reason needed
        debug("SocketPort.return", self.socket_port_open)

    def read(self, size=None):
        """Read a block of characters"""
        if options.debug: debug("SocketPort.read", size, self.socket_port_open)
        if not self.socket_port_open:
            raise LostService("Socket closed")

        begin = 0 
        last = 0 
        total_data=[]
        self.socket.settimeout(.3)
        try:
            while self.socket_port_open and (size==None or size>0):
                # If no size, read a max of .3s or until idle for .05s 
                now = time.time()
                #                                gather data for     max quiet time 
                if not size and total_data and (now-begin > 0.05 or now-last > 0.02):
                    if options.debug: debug("SocketPort.read got data")
                    break

                # otherwise keep trying to read data
                try:
                    if size:
                        data = self.socket.recv(size)
                    else:
                        data = self.socket.recv(8192)
                    if data:
                        if size: 
                            size -= len(data)
                        else:
                            now = time.time()
                            last = now
                            if len(total_data) == 0:    # data has begin arriving
                                begin = now
                                self.socket.settimeout(.02)
                            if options.debug: debug("SocketPort.read data", len(data), now-last, now-begin) 
                        total_data.append(data)
                    else:
                        if options.debug: debug("SocketPort.read RAISE LostService(Host disconnected)")
                        raise LostService("Host disconnected")

                # Socket timeout occured, okay, loop around again 
                except socket.timeout:
                    now = time.time()
                    if options.debug: debug("SocketPort.read timeout", now-last, now-begin)
                    pass
                
                # Some other failure
                except socket.error, message:
                    raise LostService("Connection reset")

                # During shutdown, we might loose our socket
                except AttributeError:
                    raise LostService("Socket went bad")

            if not self.socket_port_open:
                raise LostService("Socket port closed")

        except LostService:
            debug("SocketPort.read RAISE LostService")
            self.close(loss_expected=False)
            raise

        data_received = "".join(total_data)
        self.data_seen_event.set()
        if options.debug: 
            debug("SocketPort.read returns", len(total_data), "blocks as", len(data_received), "bytes")
        return data_received

    def readline(self, size=-1):
        """Read until a LF"""
        line = ""
        while size != 0:
            ch = self.read(1)
            line += ch
            if ch == '\n':
                break
            size -= 1
        return line

    def write(self, data):
        """Write data to the socket"""
        if options.debug: debug("SocketPort.write", len(data), self.socket_port_open)
        bytes_sent = 0
        try:
            # try:
                while self.socket_port_open and bytes_sent < len(data):
                    bytes_sent += self.socket.send(data[bytes_sent:])
            # except:
            #    debug("SocketPort.write exception RAISE LostService(Lost connection to printer)")
            #    raise LostService("Lost connection to printer (write)")
        except LostService:
            debug("SocketPort.write RAISE LostService end")
            self.close(loss_expected=False)
        except NoService:
            debug("SocketPort.write PASS LostService end")
            pass


##############################################################################################
#
# PCS Class  --  Interface to Printer Connection Services 
#
# PCS is a network service that provides an interface to printers (initially USB printers)
#
##############################################################################################

class PCSPort(SocketPort):
    PORT_NUMBER = 8779 
    LIST_CMD = "l"
    DEVICE_ID_CMD = "i"
    CONNECT_CMD = "c"

    def __init__(self, is_open=None, start_pcs=False):
        """Init the object, doesn't do anything significant yet."""
        debug("PCSPort.__init__", is_open, start_pcs)
        super(PCSPort, self).__init__(is_open)
        self.start_pcs = start_pcs
        self.pcs_socket_open = False
        self.pcs_port_open = False
        self.last_write_time = 0

    def open_pcs_socket_if_needed(self, hostname=None):
        """If not already open, open underlying socket to printer"""
        debug("PCSPort.open_socket", self.pcs_socket_open)
        if self.pcs_socket_open:
            return False                        # already open
        else:
            try:
                super(PCSPort, self).open(hostname, PCSPort.PORT_NUMBER, mark_printer_open=False)
            except NoService:
                debug("No PCS service found on", hostname, PCSPort.PORT_NUMBER)
                if self.start_pcs:
                    self.start_server()
                    super(PCSPort, self).open(hostname, PCSPort.PORT_NUMBER, mark_printer_open=False)
                else:
                    raise
            self.pcs_socket_open = True
            return True                         # opened

    def close_socket(self):
        """Close underlying socket to printer"""
        debug("PCSPort.close_socket")
        if self.pcs_socket_open:
            super(PCSPort, self).close()
            self.pcs_socket_open = False

    def list(self):
        """Get list of PCS devices (assumes socket opened)"""
        super(PCSPort, self).write(PCSPort.LIST_CMD+'\n')
        string_of_printers = super(PCSPort, self).readline()
        return string_of_printers.split() 

    def device_id(self, device):
        """Get the device ID of a particular device (assumes socket opened)"""
        super(PCSPort, self).write(PCSPort.DEVICE_ID_CMD+' '+device+'\n')
        device_id = super(PCSPort, self).readline().strip()
        # Careful, device IDs themselves and the PCS results both end in LF
        # In future might send a benign cmd to suredly know if extra LF exists
        super(PCSPort, self).readline()
        try:
            model = re.search("MDL:(.*?)( series)*;", device_id).group(1)
        except AttributeError:
            model = ""
        try:
            serial = re.search("SN:(.*?);", device_id).group(1)
        except AttributeError:
            serial = ""
        return device_id, model, serial

    def connect(self, device, channel="print"):
        """Connect to a specific selected printer (assumes socket opened)"""
        debug("PCSPort.connect", device, channel)
        super(PCSPort, self).write(PCSPort.CONNECT_CMD+' '+device+' '+channel+'\n')
        result = super(PCSPort, self).readline().strip()
        if len(result) == 0:                            # I don't know why we need this
            result = super(PCSPort, self).readline().strip()
        if result != "ok":
            raise NoService("PCS connect to printer failed")
        self.terminator = ';'
        return result

    def printers(self, specifier=None, hostname=None):
        """Get a list of all the printers available, filtering by an optional specifier.
           Doesn't require socket to have been opened yet so that we can query printers
           before opening a connection."""
        debug("PCSPort.printers", specifier)
        we_opened_socket = self.open_pcs_socket_if_needed(hostname)
        result = []
        for device in self.list():
            device_id, model, serial = self.device_id(device)
            debug("PCSPort.printers", device_id, model, serial)
            if not specifier or ((specifier in device) or (specifier in device_id)):
                output_str(" Found printer: "+model+" "+serial+EOLN)
                result.append((device, model, serial))
        if we_opened_socket:               # If socket wasn't open, close it 
            self.close_socket()
        debug("PCSPort.printers =", result)
        return result 

    def open(self, specifier=None, channel="print", hostname=None):
        """Open a PCS connection to a printer given an optional search pattern.
           Assumes the GUI has already had the user select a unique printer.
           If more than one printer matches, asks user to pick (non-GUI only)."""
        global quit_event
        debug("PCSPort.open", specifier, channel, hostname)
        try:
            self.open_pcs_socket_if_needed(hostname)
            while not quit_event.isSet():
                printers = self.printers(specifier)
                if len(printers) == 0:
                    if specifier:
                        output_str("  Waiting for PCS "+specifier+EOLN, "info")
                        time.sleep(3)           # Wait until printer found
                    else:
                        raise NoService("Printer not found")
                elif gui or len(printers) == 1:
                    device, self.model, self.serial = printers[0]
                    break
                else:
                    choice = 0
                    output_str("Printers found:"+EOLN, "info")
                    for device, model, serial in printers:
                        output_str (" %2d. %-15s %s%s" % (choice, serial, model, EOLN), "args")
                    user_choice = raw_input("Select Printer (ENTER to update): ")
                    if user_choice in ['q', 'quit']:
                        raise NoService("User didn't pick a printer")
                    try:
                        user_choice = int(user_choice)
                    except ValueError:
                        pass
                    else:
                        if user_choice >= 0 and user_choice < len(printers):
                            device, model, serial = printers[user_choice]
                            break
            if quit_event.isSet():
                raise NoService("User quitting")

            if channel == "shell":                      # Remove when shell channel implemented
                self.connect(device, "debug")
            else:
                self.connect(device, channel)

        except NoService:
            self.close()
            raise
        self.running_shell = (channel == "shell")
        self.running_udw   = (channel == "debug" or channel == "print")
        self.running_PJL   = (channel == "print")
        if ("reflash" in self.model) or ("coredump" in self.model):
            self.name = "pcs#" + self.model
            self.running_shell = False
            self.running_udw = False
            self.running_PJL = False
            output_str(" Printer in %s mode%s" % (self.model,EOLN), "info")
        else:
            self.name = "pcs#"+self.serial+"/"+channel
        time.sleep(1)
        self.pcs_port_open = True
        self.printer_is_open_event.set()        # must be set by derived classes
        debug("PCSPort.open return", self.printer_is_open_event.isSet())
        return self

    def close(self, loss_expected=True):
        debug("PCSPort.close", self.pcs_port_open)
        super(PCSPort, self).close(loss_expected)
        self.pcs_port_open = False

    def write(self, data):
        """Write data to the socket, don't return errors"""
        if options.debug: debug("PCSPort.write", len(data))
        if self.pcs_port_open:
            if self.running_PJL:
                current_time = time.time()
                if current_time - self.last_write_time > PJL_UDW_TIMEOUT:
                    super(PCSPort, self).write(PJL_ENTER_UDW)
                    time.sleep(1)
                self.last_write_time = current_time
            super(PCSPort, self).write(data)

    def start_server(self):
        """Start the PCS server on the local host"""
        try:
          subprocess.Popen("pcs", shell=False, 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError, message:
          output_str(EOLN+"PCS failed to start: "+str(message)+EOLN, "error")
          if os.name == "nt":
            output_str("Install PCS in C:\Program Files."+EOLN, "info")
            output_str(" 1) http://teams8.sharepoint.hp.com/teams/Mech_FW/"+EOLN, "info")
            output_str(" 2) Go into 'Tools'"+EOLN, "info")
            output_str(" 3) Right click 'pcs' and Save Target As... into C:\Program Files"+EOLN, 
                "info")
          raise NoService("Couldn't start PCS")


##############################################################################################
#
# Connection Class  --  Establish connections to various ports. (Port Factory) 
#
# This class works as a factory. You open a connection with open() and a port_str (same string
# as used by the --port option).  Then one of several open Port objects might be returned. From 
# then on all further IO (read, write, close, open) is done throught the returned Port object.
#
##############################################################################################

class Connection():
    global quit_event

    # Initializer when a Connection is instantiated
    def __init__(self, is_open_event=None):
        """Init a new Connection object. is_open should be a theading.Event() which
           will be used to track the connetion's open state."""
        if not is_open_event: 
            self.is_open_event = threading.Event()
        else:
            self.is_open_event = is_open_event
        self.hostname = None                    # hostname if using socket

        # REVISIT -- These need to be reviewed -- most replaced with new classes
        self.serial_port = None                 # serial IO file descriptor
        self.socket_port = None                 # network IO file descriptor
        self.using_serial = False               # flag indicating we're using serial
        self.using_socket = False               # flag indicating we're using socket
        self.using_pcs = False                  # flag indicating we're using the PCS protocol
        self.pcs_specifier = None               # indicate which printer to choose
        self.serial_number = None               # save serial number
        self.model = None                       # save model
        self.serial_port_name = None            #
        self.simulating = False                 # simulating off as default
        self.size_int = ctypes.c_int()          # integer for icntl results
        self.port_name = None                   # port name

    # Parse the --port argument given by the user
    def parse_port_str(self, port_str=DEFAULT_PORT):
        m = port_re.match(port_str)             # parse the --port argument
        if m:
            self.port_name = port_str
            if m.group("serialport"):
                self.using_serial = True
                try:
                    self.serial_port_name = int(m.group("serialport"))
                except ValueError:
                    self.serial_port_name = m.group("serialport")
            else:
                self.using_socket = True
                if m.group("hostname"):
                    self.hostname = m.group("hostname")
                    if (self.hostname == "none"):
                        self.simulating = True
                    elif ((self.hostname == "pcs") or (self.hostname == "cs")):
                        self.hostname = "localhost"
                    elif (not "." in self.hostname) and (self.hostname != "localhost"):
                        if ("lnx" in self.hostname):
                            self.hostname += ".vcd.hp.com"
                        else:
                            self.hostname += ".americas.hpqcorp.net"
                else:
                    self.hostname = "localhost"

                if m.group("port"):
                    self.socket_port_number = m.group("port")
                    try:
                        self.socket_port_number = int(self.socket_port_number)
                    except ValueError:
                        self.socket_port_number = PORT_NAMES_TO_NUMBER[self.socket_port_number]
                else:
                    if ((self.hostname == "localhost") or
                           ("lnx" in self.hostname) or
                           (".americas" in self.hostname)):
                        self.socket_port_number = PCS_PORT
                    else:
                        self.socket_port_number = SHELL_PORT

                if m.group("channel"):
                    self.pcs_channel = m.group("channel")
                else:
                    self.pcs_channel = "print"                   # default PCS channel

                self.pcs_specifier = m.group("specifier")

    def open(self, port_str=None, start_server=False):
        """Open a connection to the printer. port_str is the exact same
           format as the --port argument."""
        output_str(' '+'-'*80+EOLN)
        if port_str:                                    # Otherwise assume already opened before
            self.__init__(self.is_open_event)           # Re-init our instance variables
            self.port_str = port_str                    # Save for next time
            self.parse_port_str(port_str)               # Parse out the constituents
            try:                                        # Save in LASTPORT_FILE
                if r"#reflash" not in self.port_str:
                    with open(os.path.join(SIFT_CONFIG_DIR, LASTPORT_FILE), 'w') as f:
                        f.write(self.port_str+'\n')
            except IOError: pass
        else:
            self.pcs_specifier = self.serial_number     # Assure we connect to same printer

        output_str(" Connecting to " + self.port_str + EOLN)
        if gui: gui.process_events()

        # Open the proper port
        try:
            if self.simulating:
                self.port = NoConnectionPort(self.is_open_event).open()
            elif self.using_socket and self.socket_port_number == PCS_PORT:
                self.port = PCSPort(self.is_open_event, start_server)
                self.port.open(specifier=self.pcs_specifier, channel=self.pcs_channel)
            elif self.using_socket:
                self.port = SocketPort(self.is_open_event).open(hostname=self.hostname, 
                        port=self.socket_port_number)
            else:
                self.port = SerialPort(self.is_open_event).open(self.serial_port_name)
        except (NoService, LostService), e:
            output_str(" Failed to connect to %s.  %s.%s" % (self.port_str, e, EOLN), "error")
            self.port = NoConnectionPort(self.is_open_event).open()
        else:
            output_str(" Success connecting to " + self.port.name + EOLN, "G")

        output_str(' '+'-'*80+EOLN)
        if gui: gui.process_events()
        return self.port


#############################################################################
#
# Printer Class
#
# Beginnings of a printer class. The plan is to migrate all printer functionality
# to this class. Note that as flows and globals are interpreted from the .i
# file, they are added to this class.
#
# Send underware to printer:            printer.udw("bio.base_dir")
# Flash printer:                        printer.flash("threadx.fhx")
#
############################################################################

class Printer():
    def __init__(self):
        self.is_open_event = threading.Event()              # event if printer open/closed
        self.port = NoConnectionPort(self.is_open_event)    # default no connection

    def open(self, port_str=None):
        if port_str:                            # if no new port_str, keep old
            self.port_str = port_str
        if self.is_open_event:
            self.close()
        self.port = Connection(self.is_open_event).open(self.port_str)
        debug("Printer.open return", self.is_open_event.isSet(), self.is_open_event)
        if gui: gui.io_ready()

    def close(self):
        debug("Printer.close")
        self.port.close()
        self.is_open_event.clear()

    def udw(self, line):
        """Send an underware command to the printer"""
        line = line.strip()
        if self.port.running_shell:
            if not line.startswith("udws"):
                line = "udws '" + line + "'"
        elif self.port.running_udw:
            if not line.endswith(';'):
                line += ';'
            output_str(line + EOLN, "comment")
        self.port.write(line + "\n")

    def flash(self, file):
        """Flash the given file to the printer"""

        # Assure we can open the flash file
        output_str("Preparing to flash:"+EOLN, "info")
        flash_file = open(file, "rb")
        output_str("  "+file+EOLN, "info")
        if gui: gui.process_events()

        # Put printer into flash mode (may be already there)
        if "reflash" in self.port.model:
            # We're already in flash mode and we're already the flash device
            flash_device = self.port
        else:
            process_fifo_thread.processing_allowed.set()              # start input fifo processing
            output_str("Putting printer in reflash mode."+EOLN, "info")
            if gui: gui.process_events()
            time.sleep(2)
            self.port.data_seen_event.clear()
            ready_for_flash_file.clear()
            startup_seen.clear()
            # self.udw("ds2.set 65570 0") # Clear 0x2 bit of DSID_POWER_DOWN_STATE, should query/set
            self.udw("udw.srec_download") # Command reflash mode

            # Wait for printer to say it's ready for the flash file
            output_str("Trying to detect reflash mode (max 10 seconds)." +EOLN, "info")
            if gui: gui.process_events()
            time.sleep(3)                           # give command some time to process
            if gui: gui.process_events()

            # Deal with serial port specifics
            if isinstance(self.port, SerialPort):
                if gui: gui.process_events()
                self.port.data_seen_event.wait(10)              # wait a bit for data to be seen
                if gui: gui.process_events()
                if self.port.data_seen_event.isSet():
                    # REVISIT: We could skip this step if flash_device.model == "reflash" already
                    output_str("Printer responded, waiting for reflash mode (max 30 seconds)" +EOLN, "info")
                    if gui: gui.process_events()
                    ready_for_flash_file.wait(30)   # wait for printer to say it's waiting for flash file
                    if gui: gui.process_events()
                    time.sleep(1)
                    if ready_for_flash_file.isSet():
                        output_str("Printer in reflash"+EOLN, "info")
                        if ((not options.flashhost) and (os.name == "posix") and (sys.platform != "darwin")):
                            # Wait for Linux USB device to go away
                            output_str("Wait for reset (max 5 seconds)"+EOLN, "info")
                            attempt = 0
                            while os.path.exists('/dev/usb/lp0') and (attempt < 10):
                                time.sleep(.5)
                                if gui: gui.process_events()
                                attempt += 1
                            if not os.path.exists('/dev/usb/lp0'):
                                output_str("Printer reset"+EOLN, "info")
                    elif startup_seen.isSet():
                        output_str("Printer reset instead of going into reflash mode"+EOLN, "warning")
                        output_str("Try flashing again."+EOLN, "warning")
                        return
                    else:
                        output_str("Printer didn't say it's in reflash, assuming it is."+EOLN, "info")

                    if ((not options.flashhost) and (os.name == "posix") and (sys.platform != "darwin")):
                        # Wait for Linux device to come back
                        attempt = 0
                        output_str("Wait for USB reflash device (max 20 seconds)"+EOLN, "info")
                        if gui: gui.process_events()
                        time.sleep(2)
                        if gui: gui.process_events()
                        while not os.path.exists('/dev/usb/lp0') and (attempt < 40):
                            time.sleep(.5)
                            if gui: gui.process_events()
                            attempt += 1
                        if gui: gui.process_events()
                        time.sleep(2)
                else:
                    output_str("No response from printer, assuming in reflash mode" +EOLN, "info")

            # Close connection to printer
            output_str("Closing printer connection."+EOLN, "info")
            self.close()
            if gui: gui.process_events()
            time.sleep(1)

            # Connect to flash device
            output_str("Connecting to flash device."+EOLN, "info")
            if options.flashhost:
                # a specific flash port has been specified, we already created flash_device above
                flash_device.open(flash_device.port.hostname+":pcs#reflash")
                if gui: gui.process_events()
            elif isinstance(self.port, PCSPort):
                # try:
                flash_device = Connection().open(self.port.hostname+":pcs#reflash")
                if gui: gui.process_events()
                # except:
                #   output_str("Couldn't connect to flash device over PCS"+EOLN, error)
            else:
                try:
                    flash_device = open("/dev/usb/lp0", "wb")               # Linix
                except:
                    if sys.platform == 'darwin':                            # Mac
                        flash_device = Connection().open("none")
                    else:                                                   # Linux/PC
                        output_str("No printer found on /dev/usb/lp0, trying PCS."+EOLN, "info")
                        # try:
                        flash_device = Connection().open(":pcs#reflash", start_server=True)
                        if not isinstance(flash_device, PCSPort):
                            # Failed to open PCS device, now what? We need to clean
                            # up this flash routine to deal with this. For now do this:
                                output_str("Failed to open PCS. Can't flash."+EOLN, "error")
                                if flash_file: flash_file.close()
                        
                                # Reconnect printer
                                output_str("Reconnecting printer."+EOLN, "info")
                                time.sleep(2)
                                if gui: gui.process_events()
                                self.open()
                                return
                        # except:
                        #     output_str("Couldn't find a flash device", "error")

        # Send flash file
        output_str("Sending " + file + EOLN, "info")
        try:
            if sys.platform == 'darwin':
                # Mac OS Reflash: Need to create a reflash printer queue on the Mac first:
                #  lpinfo -v   (should show the printer when it is in reflash mode)
                #  lpadmin -p reflash -L "Reflash" -E -v usb://Hewlett-Packard/reflash?serial=000000000011
                #    -P /System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/
                #       PrintCore.framework/Versions/A/Resources/Generic.ppd
                # If it fails, use "lpinfo -v" and "lpstat -t" to get information
                # If it is disabled, use "cupsenable reflash".
                #
                os.system("lprm -P reflash -")              # clear the printer queue
                os.system("lp -d reflash -o raw "+file)     # send flash file to printer
            else:
                # save_debug = options.debug; options.debug = False
                debug("Writing flash file")
                flash_device.write(flash_file.read())
                # options.debug = save_debug
        except IOError:
            output_str("IOError: Flash file couldn't be sent !!"+EOLN, "error")
        else:
            output_str("Flash file sent."+EOLN, "info")
            time.sleep(2)

        output_str("Finishing up flash process."+EOLN, "info")
        init_arrays_and_dictionaries()
        init_arrays_and_dict_for_hlg()
        if gui: gui.process_events()
        if flash_file: flash_file.close()
        if flash_device: flash_device.close()

        # Reprocess .i and .hlg files
        output_str("Reprocessing symbols."+EOLN, "info")
        find_and_process_i_and_hlg_files()

        # Track
        UsageThread("flash").start()

        # Reconnect printer
        output_str("Reconnecting printer."+EOLN, "info")
        time.sleep(2)
        if gui: gui.process_events()
        self.open()



###############################################################################
#
# Regular Expressions
#
# Sift uses regular expressions to quickly process raw trace data, amoung other
# things. These are quite delicate. There are tools to help create these on the
# web. Sometimes I have test routines embedded here when I'm working on new
# regular expressions.
#
###############################################################################

# Raw trace
start_re_str   = '^\+?'                               # Optional '+'
header_re_str  = '(?P<header>.*:)?'                   # Optional Serial Tool
time_re_str    = '(?P<time>[0-9]*)\s?'                # Optional time 100ths sec
indent_re_str  = '(?P<indent>[A-Z])\s?'               # Indent is 1 char, A-Z
fiber_re_str   = "(?P<fiber>[\x60a-z]?)"              # Optional fiber
type_re_str    = "(?P<type>[FGTKBLAYNCHMIRXrt=])"     # Type is always one char
id_re_str      = "(?P<id>[0-9]+)"                     # Item ID
args_re_str    = '(?P<args>[\[\(][0-9,-]*[\]\)]?)?'   # Optional arguments
result_re_str  = '((=(?P<result>[0-9-]+))?)'          # Optional result
remain_re_str  = '\s*(?P<remain>.*)'                  # Optional remainder

decode_line_re = re.compile(
    start_re_str + header_re_str + time_re_str + indent_re_str + fiber_re_str \
    + type_re_str + id_re_str + args_re_str + result_re_str + remain_re_str)

# lua_func_re_str = '((?P<func>[-a-zA-Z0-9_]+))?'           # Optional function
# lua_args_re_str    = '([\(](?P<args>.*)[\)])?'            # Optional arguments
# lua_file_re_str = '((?P<file>[-a-zA-Z0-9_]+))?'           # Optional filename
# lua_decode_line_re = re.compile(
#     start_re_str + time_re_str + indent_re_str + type_re_str \
#     + id_re_str + lua_func_re_str + lua_args_re_str + lua_file_re_str)

# Hostname
hostname_re = \
    re.compile("(\d+.\d+.\d+.\d+)|([a-zA-Z][a-zA-Z0-9._-]+)|(localhost)",
        re.IGNORECASE)

# LF to CRLF
eoln_re = re.compile("\r?\n")

# Timestamp of a standard DEBUG_printf() serial line
timestamp_re = re.compile("^\w+ +(?P<time>[0-9]+\.[0-9]{2})[0-9] \(")

# Mech started
mech_started_re = re.compile(".* MECH: start.*")

# DSID watches
dsid_trap_re = re.compile("(?P<prefix>^.*udw trap: id )(?P<dsid>[0-9]+)(?P<suffix>,.*$)")
dsid_err_re  = re.compile("(?P<prefix>^.*DS2 error : DSID )(?P<dsid>[0-9]+)(?P<suffix>.*$)")

# Underware results
udws_return_re = re.compile("(?P<result>.*)(?P<suffix>;.*$|udws\(\).*$)")

# Machine state underware return
dsid_machine_state_re = re.compile(".*get_by_name DSID_MACHINE_STATE.*|.*get 65541.*")

# Machine state old and new values
old_new_re = re.compile("(?P<old>.*old_value )(?P<old_value>[0-9]+.*)(?P<new>, new value )(?P<new_value>[0-9]+.*$)")

# Spontaneous machine state old and new values
spont_old_new_re = re.compile("(?P<PSTS>^.*PSTS )(?P<time>[0-9]*.[0-9]+)(?P<str>.*\(tDsdOlsPrdSts\) machine state )(?P<new>.*new:)(?P<new_value>[0-9]+).*(?P<old>.*old:)(?P<old_value>[0-9]+).*$")

# Does user input have an assignment opperator?
assignment_op_re = re.compile("(?P<variable>\w+)(\s*=\s*)(?P<value>-\d+|\d+)")

# Does user input have an array opperator?
array_op_re = re.compile("(?P<variable>\w+)(\s*\[\s*)(?P<index>-\d+|\d+)?(\s*\]\s*)(\s*=\s*(?P<value>-\d+|\d+))?")

# Regular expression to determine if line has file name and size information when processing .all file
all_file_file_name_re = re.compile("(?P<filename>.*)(?P<byte_count> [0-9]+)(?P<left_over>\s;$)")
hlg_fmls_for_i_re = re.compile(".*%.*%"+"(?P<filename>flows_.*fml)"+ "\s=\s" + "(?P<filetype>.*)" + "\]")

# Regular express to detect embedded COLOR informatin
color_re = re.compile("COLOR(?P<new_text_type>\w*)\|(?P<text_type>\w*)COLOR")

on_dbug_re = re.compile("^\s*(on\w+g)?\s*\"?(?P<component>\w{1,4})\"?\s*(?P<level>\d{1,3})?\s*$")

# Sync string
sync_re = re.compile(SYNC_STRING)

# Port argument
serialport_re_str = "(^(?P<serialport>((com|COM)?(\d+))|(\/dev.+)|(\d+))$)"
hostname_re_str   = "^(?P<hostname>(\d+.\d+.\d+.\d+)|([a-zA-Z][a-zA-Z0-9._-]+)|(localhost))?"
port_re_str       = "([:](?P<port>((pcs|ss|shell|udw)|(\d+))))?"
channel_re_str    = "(/(?P<channel>(print|debug|shell)))?"
specifier_re_str  = "(#(?P<specifier>.+))?"

port_re_str       = serialport_re_str+"|("+hostname_re_str+port_re_str+channel_re_str+specifier_re_str+")|last"
port_re = re.compile(port_re_str)

# test port argument regular expression (Remove these when done)
m = port_re.match("2")
assert(m.group("serialport") == "2")
assert(m.group("hostname") == None)

m = port_re.match("com4")
assert(m.group("serialport") == "com4")
assert(m.group("hostname") == None)

m = port_re.match("10.0.0.40")
assert(m.group("serialport") == None)
assert(m.group("hostname") == "10.0.0.40")
assert(m.group("port") == None)

m = port_re.match("1.2.3.4:pcs")
assert(m.group("hostname") == "1.2.3.4")
assert(m.group("port") == "pcs")

m = port_re.match("1.2.3.4:77")
assert(m.group("hostname") == "1.2.3.4")
assert(m.group("port") == "77")

m = port_re.match("1.2.3.4:3322")
assert(m.group("hostname") == "1.2.3.4")
assert(m.group("port") == "3322")

m = port_re.match(":pcs/print")
assert(m.group("serialport") == None)
assert(m.group("hostname") == None)
assert(m.group("port") == "pcs")
assert(m.group("channel") == "print")
assert(m.group("specifier") == None)

m = port_re.match(":pcs#sam")
assert(m.group("hostname") == None)
assert(m.group("port") == "pcs")
assert(m.group("channel") == None)
assert(m.group("specifier") == "sam")


############################################################################################
#
# Main database structures for the flows, globals, keywords, etc. All the stuff read from
#
############################################################################################

# The Flow class. This data structure holds information about each flow. It is
# created when we parse the .i file.
class Flow(object):
  def __init__(self, id=None, name=None, numArgs=None, argList=None, locals=None, value_for=None):
    self.id   = id
    self.name = name
    self.numArgs = numArgs
    self.argList = argList
    self.locals = locals
    self.value_for = value_for
    self.filename = None
    self.lineNum = None

# The Frame class. This data structure holds information about each frame
class Frame(object):
  def __init__(self, flow_call=None, time_highorder = 0, time = 0):
      self.flow_call = flow_call
      self.locals = {}
      self.flow = None
      self.time_highorder = time_highorder
      self.time = time

# The Keyword class. This data structure holds information about each keyword.
class Keyword(object):
  def __init__(self, id=None, name=None, numArgs=None, argList=None):
    self.id   = id
    self.name = name
    self.numArgs = numArgs
    self.argList = argList

# The Statement class. This data structure holds information about each statement.
class Statement(object):
  def __init__(self, offset=None, flow=None, line_number=None, file_name=None):
    self.offset      = offset
    self.flow        = flow
    self.line_number = line_number
    self.file_name   = file_name

# The Header class. This data structure holds information about each header.
class Header(object):
  def __init__(self, id=None, name=None, numArgs=None, argList=None):
    self.id   = id
    self.name = name
    self.numArgs = numArgs
    self.argList = argList

# Class that implements a fifo which blocks waiting for data
class Fifo():
    def __init__(self):
        self.fifo = collections.deque()
        self.semaphore = threading.Semaphore(0)
        self.lines_appended = 0
        self.open = True

    def __len__(self):
        return len(self.fifo)

    def append(self,item):
        self.fifo.appendleft(item)
        self.semaphore.release()
        self.lines_appended += 1
        if gui:
            gui.pace = len(self.fifo) 

    def pop(self, blocking=True):
        if self.open:
            if self.semaphore.acquire(blocking):
                if self.open:
                    if gui:
                        gui.pace = len(self.fifo)
                    return self.fifo.pop()
        raise RuntimeError

    def close(self):
        self.open = False
        self.append("")


#
# When we output results, we need to format the output as per the
# color dictionary for the device. This might be color escape codes for
# a terminal, HTML for a browser, etc.
#
def process_color(color_dictionary, new_text_type, text_type):
    global line_class
    global line_indent

    # If this is a pop format and the terminal supports , use the pop string
    if ("pop" in new_text_type):
        if new_text_type not in color_dictionary:
            new_text_type = "popdefault"

    if new_text_type in color_dictionary:
        text_template  = color_dictionary[new_text_type]
    else:
        text_template  = color_dictionary["default"]

    # Try replacing any string argument in there, otherwise revert
    try:
        replaced_template = (text_template) % (text_type)
    except TypeError:
        try:
            replaced_template = (text_template) % (line_indent)
        except TypeError:
            if line_class == None:  line_class = "text"
            if line_indent == None: line_indent = 99
            try:
                replaced_template = (text_template) % (line_class, line_indent)
            except TypeError:
                replaced_template = text_template
    return(replaced_template)


#################################################################################################
#
# Server Mode
#
# Sift can run as a server and take command input from a remote connection. This allows
# remote running of Sift. For example, if Sift is running, someone could telnet into
# the program and do the usual Sift commands. In addition, other programs such as
# Sift Data Viewer and the old gSift could communicate with Sift and present a more
# graphical user interface.
#
# This works by having a ListenThread thread listen for new socket connections.  Whenever
# we get a connection comes in, a new ConnectionThread is instantiated. The ConnectionThread
# reads lines of text and passes them to the Sift parser.
#
# As of this time, there are no known uses of this capability anymore. But let's not remove
# this code yet.
#
#################################################################################################

#
# Thread to read each socket connection (created and ended dynamically)
#
# class ConnectionThread(threading.Thread):
# 
#     connections = []                            # list of active connections
# 
#     def __init__ (self, conn, parser, quit_event):          # instantiate with connection & parser to use
#         # if options.debug: print "ConnectionThread __init__"
#         threading.Thread.__init__ (self)
#         self.quit_event = quit_event
#         self.setDaemon (True)                   # stop when main ends
#         self.conn = conn
#         self.parser = parser
#         conn2color[self.conn] = no_color_dictionary
# 
#     def send_all (line):                        # send to every connection
#         for conn in ConnectionThread.connections:
#             if not self.quit_event.isSet():
#                 # if options.debug: print "Sending to port", line.strip()
#                 try:
#                     # If using Sift Data Viewer changes carage returns and newlines to paragraphs
#                     if conn2color[conn] == "sdv_color_dictionary":
#                         line = line.replace(EOLN,"\par")
# 
#                     # Set text color based on user (sdv, tktalk or telnet-None)
#                     m = color_re.match(line)
#                     if m:
#                         new_text_type = m.group("new_text_type")
#                         text_type = m.group("text_type")
#                         # if options.debug: print "colorMATCH", line, new_text_type, text_type, "MATCHcolor"
#                         line = process_color(conn2color[conn], new_text_type, text_type)
# 
#                     conn.send(line)
# 
#                 except KeyError: pass
# 
#     send_all = staticmethod(send_all)           # allow method to be called w/o an instance
# 
#     def run (self):
#         # if options.debug: print "ConnectionThread run"
#         ConnectionThread.connections.append(self.conn)  # add connection to list
#         extra = ""
# 
#         while not self.quit_event.isSet():      # read lines until connection closed
#             line = ""
#             while not line.endswith("\n"):      # read bytes until LF or connection closed
#                 try:
#                     data = self.conn.recv(1024)
#                 except socket.error:
#                     # if options.debug: print "ConnectionThread try error"
#                     data = None
#                 if not data:
#                     line = None
#                     # if options.debug: print "connection closed A"
#                     break
#                 line = line + data
#                 # if options.debug: print "ConnectionThread", data
# 
#             if not line:
#                 # if options.debug: print "connection closed B"
#                 break                  # connection closed
# 
#             # if options.debug: print line
# 
#             # Set color for output on socket by socket basis
#             if "format" in line:
#                 temp = string.lower(line.strip("format").strip())
#                 try:    conn2color[self.conn] = color_dictionary[temp]
#                 except: pass
#                 if (temp == "gsift"):
#                     self.parser.put("info")
# 
#             elif "set_conn" in line:
#                 temp = string.lower(line.strip("set_conn").strip())
#                 try:    conn2color[self.conn] = color_dictionary[temp]
#                 except: pass
#
################################# don't need this? #########################################
#
#            elif "GET / HTTP" in line:
#                conn2color[self.conn] = html_color_dictionary
#                try:
#                    for line in open(os.path.join(SIFT_CONFIG_DIR, HTML_HEADER_FILE)):
#                        self.conn.send(line)
#                except: pass
#
#            else:
#                self.parser.put(line.strip())               # put line in queue to be parsed
#
#######################################################################################
#
#        # if options.debug: print "ConnectionThread close"
#        self.conn.close()
#        ConnectionThread.connections.remove(self.conn)  # remove connection from list
#
#
#
# Thread to listen for socket connections and spawn a separate thread for each
#
#class ListenThread(threading.Thread):
#
#    def __init__ (self, parser, port, quit_event):          # listen for connections this port
#        # if options.debug: print "ListenThread __init__", EOLN
#        threading.Thread.__init__ (self)
#        self.quit_event = quit_event
#        self.setDaemon (True)                   # stop when main ends
#        self.parser = parser                    # use this parser for this port
#        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        self.s.bind(("", port))                 # listen on this port
#
#    def run (self):
#        # if options.debug: print "ListenThread run", EOLN
#        while not self.quit_event.isSet():
#            # if options.debug: print "ListenThread listening", EOLN
#            self.s.listen(1)                    # wait for a connection
#            conn, addr = self.s.accept()        # accept connection
#            # if options.debug: print "ListenThread connect", addr, EOLN
#                                                # create a thread for the connection
#            connThread = ConnectionThread(conn, self.parser, self.quit_event)
#            connThread.start()


#################################################################################################
#
# Keyboard Input
#
#################################################################################################
#
# The following code processes keyboard input on both Linux and Windows. It gives Sift
# a similar experience over Linux and Windows. For this purpose, this code also implements
# command completion itself. We don't use the Python command completion code because it
# didn't work well on all Linux and Window's platforms. Therefore we have our own command
# completion code.
#
#################################################################################################

#
# Getch classes based off code at
# http://code.activestate.com/recipes/134892-getch-like-unbuffered-character-reading-from-stdin/
#
class _Getch:
    """Gets a single character form standard input. Does not echo to the screen."""
    def __init__(self):
        if os.name == "nt":
             self.impl = _GetchWindows()
        else:
             self.impl = _GetchUnix()

    def __call__(self):
        return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty

    def __call__(self):
        import tty,termios
        fd = sys.stdin.fileno()
        try:
            old_settings = termios.tcgetattr(fd)
        except:
            old_settings = None
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)

            if ch == '' :                               # Arrow Key
                next_key = sys.stdin.read(1)
                if next_key == "[" or next_key == "O":
                    keys = next_key + sys.stdin.read(1)
                    if keys == '[A':    return "UP"       # Up Arrow
                    elif keys == '[B':  return "DOWN"     # Down Arrow
                    elif keys == '[C':  return "RIGHT"    # Right Arrow
                    elif keys == '[D':  return "LEFT"     # Left Arrow
                    elif keys == 'OH':  return "HOME"
                    elif keys == 'OF':  return "END"
                    else:
                        keys = keys + sys.stdin.read(1)
                        if keys == '[2~': return "INSERT"
                        elif keys == '[3~': return "DELETE"
                        else: return keys
                else:
                    return next_key
        finally:
            if old_settings:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt, unicodedata

    def __call__(self):
        import msvcrt, unicodedata
        ch = msvcrt.getwch()

        if ch == unichr(224):                         # Arrow Key Pressed
            next_key = msvcrt.getwch()
            if next_key == 'H':      return "UP"      # Up Arrow
            elif next_key == 'P':    return "DOWN"    # Down Arrow
            elif next_key == 'M':    return "RIGHT"   # Right Arrow
            elif next_key == 'K':    return "LEFT"    # Left Arrow
            elif next_key == 'R':    return "INSERT"
            elif next_key == 'S':    return "DELETE"
            elif next_key == 'G':    return "HOME"
            elif next_key == 'O':    return "END"
            else:                    return next_key
        return ch


def tab_completion(line, double_tab):
    opts        = []                             # options - possibilities of what the user could want
    wholeLine   = line                           # Everything the user has typed
    line        = line.split(" ")[len(line.split(" "))-1] # Portion of line trying to be tab completed
    prompt      = cur_prompt
    common_chrs = ""                             # Incase len(opts) > 1 track ch all opts have in common
    if line.isupper():
        line = line.lower()

    try:
        # Look up lines first ch in everything_dictionary and pull out all possiblities
        for i in everything_dictionary[line[0].lower()]:
            if i.startswith(line):
                opts.append(i)
                next_chrs = i.replace(line,"",1)
                if len(opts) == 1:
                    common_chrs = next_chrs
                elif len(opts):
                    for x in range(0,len(common_chrs)):
                        if not next_chrs[x] == common_chrs[x]:
                            common_chrs = common_chrs[0:x]
                            break
        if len(opts) == 1:
            # If only one match complete the word
            temp = opts.pop()
            sys.stdout.write(temp[len(line):])
            return wholeLine[0:(len(wholeLine)-len(line))]+temp
        elif len(opts) and double_tab:
            # If more than one possibiliy and user double tabs print out options or prompt user if
            # they would like to see all options
            ok_to_print = True
            sys.stdout.write(EOLN)
            if len(opts) > TAB_COMPLETION_ASK_USER:
                answer = raw_input("Display all "+str(len(opts))+" possibilities? (y or n) ")
                if not ((answer.strip().lower() == "yes") or (answer.strip().lower() == "y")):
                    ok_to_print = False

            if ok_to_print:
                for option in opts:
                    sys.stdout.write(option +EOLN)
            sys.stdout.write(prompt+wholeLine+common_chrs)    # tab completes as much as possible
    except KeyError: pass
    except IndexError: pass
    return wholeLine+common_chrs

def load_history():
    global history
    global history_pointer
    history = []
    history_pointer = 0
    try:
        for file_line in open(os.path.join(SIFT_CONFIG_DIR,HISTORY_FILE)).readlines():
            # Ignore blank lines and lines that start with #
            if len(file_line.strip()) and (not file_line.startswith("#")):
                history.append(file_line.strip())
    except IOError:
        history = []

def save_history():
    global history
    try:
        if history:
            try:
                history_file = open(os.path.join(SIFT_CONFIG_DIR,HISTORY_FILE),'w')
                while len(history) > 200:
                    history.pop(0)
                for i in history:
                    history_file.write(i+"\n")
            except IOError: pass
    except NameError: pass



#
# Thread to read the keyboard
#
class KeyboardThread(threading.Thread):

    def __init__ (self, parser, quit_event):
        global history
        global history_pointer
        # if options.debug: print "Keyboard __init__"
        threading.Thread.__init__ (self)
        self.setDaemon (True)                   # stop when main ends
        self.parser = parser                    # use this parser for keyboard
        self.getch  = _Getch()
        self.quit_event = quit_event
        self.prompt = PROMPT
        history_pointer = len(history)

    # Appends flags to prompt
    def flags(self):
        flags = []
        if at_a_break_point:                     # We're at a breakpoint
            flags.append("BREAKPOINT ACTIVE")

        if compatibility_error:                  # .i file mismatch detected
            flags.append("Symbols Mismatch")

        if not process_fifo_thread.processing_allowed.isSet():    # Output is paused
            flags.append("Output Paused")

        if len(flags) > 0:
            flag_string = "["
            for i in range(len(flags)):
                flag_string = flag_string + flags[i]
                if i < len(flags)-1:
                    flag_string = flag_string + ","
            flag_string = flag_string + "] "
            self.prompt = flag_string + self.prompt

    def run (self):
        global last_lines_output_count
        global cur_prompt
        global history
        global history_pointer

        # if options.debug: print "Keyboard run"
        lengthOfLine    = 0           # Used to clear previous lines of text when using arrow key movements
        temporary_pause = False
        insert          = False

        while not self.quit_event.isSet():
            lcl = 0                                        # Line cursor location

            # if options.debug: print "Keyboard input"
            try:
                line = ""
                count = 0
                previous_count = 0

                # Create Prompt
                last_lines_output_count = 0
                time.sleep(.1)                               # let output fifo empty some
                self.parser.prompt_seen.wait(.5)             # wait up to 1/2 sec for prompt to arrive

                if self.parser.prompt_seen.isSet():      # prompt seen
                    self.prompt = PROMPT
                    self.parser.prompt_seen.clear()
                else:                                    # no prompt seen, so don't show one
                    self.prompt = ""
                self.flags()

                tab_seen = False
                double_tab = False
                if os.name == 'nt':
                    set_text_attr(FOREGROUND_GREY|FOREGROUND_INTENSITY)
                sys.stdout.write(self.prompt)
                cur_prompt = self.prompt      # goes to parser so proper prompt can be writen to output file

                while not self.quit_event.isSet():
                    ch = self.getch()

                    # Double tab will display list of options
                    double_tab = (tab_seen and ch == "\t")
                    tab_seen = False

                    # Pause on text input if trace is flowing
                    if not len(line) and not (ch == "\n" or ch == "\r") and process_fifo_thread.processing_allowed.isSet() \
                                     and (last_lines_output_count > 10) and (time.time()-last_lines_output_time < 3):
                        temporary_pause = True
                        self.parser.unpause_ok = False
                        self.parser.pause()
                        len_of_old_prompt = len(self.prompt)
                        printer.port.write("\n")
                        self.flags()
                        sys.stdout.write("\b"*len_of_old_prompt + "\r"+ self.prompt)
                    elif (ch == "\n" or ch == "\r") and temporary_pause and (line == "" or not (line.split()[0] in internal_cmd)):
                        temporary_pause = False
                        self.parser.unpause_ok = True
                        len_of_old_prompt = len(self.prompt)
                        printer.port.write("\n")
                        self.flags()
                        sys.stdout.write("\b"*len_of_old_prompt + "\r"+self.prompt)


                    if (ch == '+' or ch == "-" or ch == "=") and not len(line):       # use +/-/= to view lists (no need to press enter)
                        if ch == "=":                                                 # Return to Program Counter
                            line = "l."
                        else:
                            line = "l" + ch
                        break
                    elif ch == '.' and not len(line):                                 # Repeat last command
                        if len(history):
                            line = history[history_pointer-1]
                            break
                        else:
                            ch = ""
                    elif ch == '\x03' or ch == '\x04':                                # Cnt-C or Cnt-D
                        sys.stdout.write(EOLN)
                        raise KeyboardInterrupt()
                    elif ch == '\n' or ch == '\r':                                    # New line
                        # Trace is on and user presses enter for an empty line pause fifo output
                        if not len(line) and process_fifo_thread.processing_allowed.isSet() and (last_lines_output_count > 10) and (time.time()-last_lines_output_time < 3):
                            if self.parser.unpause_ok:
                                line = "pause"
                            temporary_pause = True
                        elif not len(line) and not process_fifo_thread.processing_allowed.isSet():
                            line = "unpause"
                        elif not len(line):
                            if printer.port.running_shell:
                                printer.port.write("\n")
                            elif printer.port.running_udw:
                                printer.port.write(ECHO_PROMPT)
                        else:
                            sys.stdout.write(EOLN)
                        break
                    elif ch == "UP":                                                 # UP Arrow - Go back in history
                        if (history_pointer + count) > 0:
                            count -=1
                    elif ch == 'DOWN':                                               # Down Arrow - Go forward in history
                        if count < 0:
                            count +=1
                        if count == 0:
                            lengthOfLine = len(line)
                            line = ""
                            sys.stdout.write('\b'*(lengthOfLine-len(line)) + ' '*(lengthOfLine-len(line)))
                            sys.stdout.write('\r'+self.prompt)
                    elif ch == "RIGHT":                                              # Right Arrow
                        if not lcl == len(line):
                            lcl += 1
                        sys.stdout.write('\r'+self.prompt+line[0:lcl])
                    elif ch == "LEFT":                                               # Left Arrow
                        if lcl:
                            lcl -= 1
                        sys.stdout.write('\r'+self.prompt+line[0:lcl])
                    elif ch == "INSERT":                                             # Insert
                        insert = not insert
                    elif ch == "HOME":                                               # Home
                        lcl = 0
                        sys.stdout.write('\r'+self.prompt)
                    elif ch == "END":                                                # End
                        lcl = len(line)
                        sys.stdout.write('\r'+self.prompt+line)
                    elif ch == "DELETE":                                             # Delete
                        sys.stdout.write("\b  "*(len(line)-lcl))
                        line = line[0:lcl] + line[lcl+1:len(line)]

                        sys.stdout.write('\r'+self.prompt+line)
                        sys.stdout.write('\r'+self.prompt+line[0:lcl])
                        lengthOfLine = len(line)
                    elif ch == '\x7f' or ch == "\b":                                 # Backspace
                        if len(line) == lcl:
                            sys.stdout.write("\b ")
                        else:
                            sys.stdout.write("\b  "*(len(line)-lcl))
                        if lcl > 0:
                            line = line[0:lcl-1] + line[lcl:len(line)]
                            lcl -= 1
                        else:
                            line = ""
                        sys.stdout.write('\r'+self.prompt+line)
                        sys.stdout.write('\r'+self.prompt+line[0:lcl])
                        lengthOfLine = len(line)
                    elif ch == "\t":                                                # Tab Completion
                        tab_seen = True
                        if len(line):
                            line = tab_completion(line, double_tab)
                            lcl = len(line)
                            sys.stdout.write('\r'+self.prompt+line)
                    elif ch:                                                        # Output ch to stdout and append it to line

                        if insert:
                            line = line[0:lcl] + ch + line[lcl+1:]
                        else:
                            line = line[0:lcl] + ch + line[lcl:]

                        lcl += 1
                        lengthOfLine +=1

                        if insert or (lcl == len(line)):
                            sys.stdout.write(ch)
                        else:
                            # If the former line content is greater than the current line, back up that many spaces and replace with blank spaces
                            if len(line) < lengthOfLine:
                                sys.stdout.write('\b'*(lengthOfLine-len(line)) + ' '*(lengthOfLine-len(line)))
                            sys.stdout.write('\r'+self.prompt+line)
                            sys.stdout.write('\r'+self.prompt+line[0:lcl])

                    if not count == 0 and not count == previous_count:  # Update display to history command at count location
                        lengthOfLine = len(line)
                        sys.stdout.write('\r'+self.prompt+line)
                        line = history[history_pointer + count]
                        lcl = len(line)

                        # If the former line content is greater than the current line, back up that many spaces and replace with blank spaces
                        if len(line) < lengthOfLine:
                            sys.stdout.write('\b'*(lengthOfLine-len(line)) + ' '*(lengthOfLine-len(line)))
                        sys.stdout.write('\r'+self.prompt+line)

                    previous_count = count
            except KeyboardInterrupt:
                self.quit_event.set()

            lengthOfLine = len(line)

            if len(line.strip()) and (not len(history) or not (line == history[history_pointer-1])):
                history.append(line)
                history_pointer +=1

            if os.name == 'nt':
                set_text_attr(default_colors)
            self.parser.put (line.strip())      # give line to parser
            self.parser.join ()                 # wait for parser queue to be empty


##########################################################################################
#
# Printer Input
#
##########################################################################################
#
# Data arriving from the printer is handled by two different threads:
#
# PortToFifoThread:  This thread reads data from the printer and stores the data into a 
#                    fifo. This is done so that we can pause the flood of printer data 
#                    arriving enabling the user to type commands on the keyboard.  When 
#                    the user starts typing on the keyboard, output to the screen is paused.
#                    But this thread continues to read the printer and store the data.
#
#                    It is convenient to watch for a few things here before we hold up the 
#                    data in the fifo. For example, we watch for underware return results 
#                    here so we know they have arrived.
#
# ProcessFifoThread: This is the main Sift printer processing thread. It reads lines from 
#                    the fifo and calls process_line(). Process_line() parses the lines 
#                    and outputs them to the screen.
#
########################################################################################

# Thread to read the printer and dump all received data into a Fifo.
# Assumes printer is running the shell with a -> prompt.
class PortToFifoThread(threading.Thread):
    '''Thread to read from serial and fill a fifo.'''
    quitted_event = threading.Event() 
    quitted_event.clear()

    def __init__(self, printer, fifo, prompt_seen, thread_name, startup_seen, quit_event):
        threading.Thread.__init__(self, name=thread_name)
        self.printer = printer
        self.fifo = fifo
        self.setDaemon(True)
        self.read_error_seen = False
        self.prompt_seen = prompt_seen
        self.quit_event = quit_event
        self.startup_seen = startup_seen

    def run(self):
        """Read raw data from the printer, compose lines, and put in fifo"""
        debug("PortToFifoThread.run start")
        global options

        line = ""
        while not self.quit_event.isSet():

            self.printer.is_open_event.wait(1)
            if self.printer.is_open_event.isSet():

                # get the current port (REVISIT: maybe do after LastService exception)
                port = self.printer.port
                terminator = port.terminator
    
                # read a block of characters
                try:
                    data = port.read()      # printer.port.read()
                except TryAgain, e:
                    # REVISIT: Eliminate TryAgain completely 
                    data = ""
                    # if options.debug: debug("PortToFifoThread.run TryAgain")
                    time.sleep(.1) 
                except (NoService, LostService), e:
                    # REVISIT: Eliminage NoService from here
                    data = ""
                    debug("PortToFifoThread.run NoService/LostService")
                    if not port.loss_expected:
                        output_str("%s Lost connection. %s.%s" % (EOLN, e, EOLN), "error")

                if options.debug: 
                    # debug("PortToFifoThread.run read", len(data), "bytes")
                    if len(data) > 0:
                        sys.stderr.write("[ ")
                        for c in data:
                            sys.stderr.write("%02X " % (ord(c)))
                        sys.stderr.write(" ]"+EOLN)

                for c in data:
                    # accept only printables
                    if (c >= ' ') or (c == '\n') or (c == '\t'):
                        line += c

                        # detect prompt
                        if c==' ':
                            if len(line)>=3 and line[-3]=='-' and line[-2]=='>':
                                self.prompt_seen.set()
                                line = line[:-3]
                                if gui: 
                                    self.fifo.append("-> ")

                        # detect end of line
                        if (c == '\n' or c == terminator):

                            # detect mech rebooted
                            if mech_started_re.match(line):
                                # Mech restarted
                                self.startup_seen.set()
                                startup_trace(self.printer)

                            # detect ready for flash (REVISIT: move to ProcessFifoThread?)
                            elif "Waiting for SREC" in line:
                                ready_for_flash_file.set()
    
                            # send line to ProcessFifoThread
                            self.fifo.append(line)
                            line = ""

        PortToFifoThread.quitted_event.set()


# Thread to read the Fifo we have been filling with printer data and process
# each line.
class ProcessFifoThread(threading.Thread):
    '''Thread to process lines from a fifo.'''

    def __init__(self, fifo, processing_allowed, quit_event, sync_seen):
        threading.Thread.__init__(self, name="ProcessFifo")
        self.fifo = fifo
        self.processing_allowed = processing_allowed
        self.quit_event = quit_event
        self.sync_seen = sync_seen
        self.setDaemon(True)

    # def printable(self, input):
    #    return ''.join([char for char in input if ord(char) > 31 or ord(char) == 9])

    def run(self):
        global last_lines_output_count
        global last_lines_output_time
        global raw_output_file
        while not self.quit_event.isSet():

            line = self.fifo.pop()              # wait and take a line out of Fifo
            if options.debug:
                debug("ProcessFifoThread.run read", len(line), "bytes")

            if (sync_re.search(line)):          # is the sync string here?
                self.sync_seen.set()
        
            self.processing_allowed.wait()      # wait if IO is paused

            if line == PROMPT:
                output_str(PROMPT)
            else:
                process_line(line)              # decode the line and display

            last_lines_output_time  = time.time()
            last_lines_output_count = last_lines_output_count + 1
            if (raw_output_file):
                raw_output_file.write(line.rstrip() + '\n')
        

def process_dot_all():
    # Since for now ALL directories are only needed temporarily, delete any existing ones
    if os.path.exists(os.path.join(SIFT_CONFIG_DIR, ALL_DIRECTORY)):
        shutil.rmtree(os.path.join(SIFT_CONFIG_DIR, ALL_DIRECTORY), ignore_errors=True)

    if not os.path.exists(project_dir):
        os.makedirs(project_dir)

    f = open(os.path.join(project_dir,PROJ_DIR_INFO),'wb')
    f.write(project_name)
    f.close()
    # output_str(" Created " + project_dir + " directory " +EOLN)

    try:
        with open(dot_all_file, 'rb') as all:
            curline = all.readline()
            while curline:
                m = all_file_file_name_re.match(curline)
                if m:
                    filename = m.group("filename").strip()
                    (name,suffix) = os.path.splitext(filename)
                    if suffix in ['.fml','.exe', '.hlg', '.i', '.fhx']:
                        f = open(os.path.join(project_dir,filename),'wb')
                        f.write(all.read(int(m.group('byte_count'))))
                        f.close()
                    else:
                        throwaway = all.read(int(m.group('byte_count')))
                curline = all.readline()
        all.close()
    except IOError:
        output_str("IO Error in process_dot_all()" + EOLN, "error")


def compile():
    # Compile .i and .dwn files
    try:
        # using linux but not a dot all file
        if not dot_all_file and not os.name == "nt":
            path_to_exe = os.path.join(os.path.dirname(os.path.dirname(hlg_filename)),"fm",os.path.basename(os.path.dirname(hlg_filename)))
        else:
            path_to_exe = ""

        # need to chmod of exe so that it can execute on linux
        if not os.name == 'nt':
            if dot_all_file and os.path.exists(os.path.join(project_dir, FLOWCEXE)):
                sub = subprocess.call(["chmod", "+x", os.path.join(project_dir, FLOWCEXE)])
            elif os.path.exists(os.path.join(path_to_exe, FLOWCEXE)):
                sub = subprocess.call(["chmod", "+x", os.path.join(path_to_exe, FLOWCEXE)])

        if dot_all_file and not os.name == "nt":
            path = os.path.join(project_dir, FLOWCEXE)+" -G -e -a 'OFFICIAL' -i "+os.path.join(project_dir,project_name)+".i -p "+os.path.join(project_dir,project_name)+".dwn -r "+os.path.join(project_dir,"raw_"+project_name)+".dwn"+fml_filenames_str
        # Linux non exe
        elif os.path.exists(os.path.join(path_to_exe, FLOWC)) and not os.name == "nt":
            path = os.path.join(path_to_exe, FLOWC)+" -G -e -a 'OFFICIAL' -i "+os.path.join(project_dir,project_name)+".i -p "+os.path.join(project_dir,project_name)+".dwn -r "+os.path.join(project_dir,"raw_"+project_name)+".dwn"+fml_filenames_str
        # Linux using windows exe
        elif os.path.exists(os.path.join(path_to_exe, FLOWCEXE)) and not os.name == "nt":
            path = os.path.join(path_to_exe, FLOWCEXE)+" -G -e -a 'OFFICIAL' -i "+os.path.join(project_dir,project_name)+".i -p "+os.path.join(project_dir,project_name)+".dwn -r "+os.path.join(project_dir,"raw_"+project_name)+".dwn"+fml_filenames_str

        winPath = FLOWCEXE + " -G -e -i "+project_name+".i -p "+project_name+".dwn -r raw_"+project_name+".dwn"+winfml_filenames_str
        if os.name == 'nt':
            if not dot_all_file:
                shutil.copyfile(os.path.join(os.getcwd(),FLOWCEXE),os.path.join(project_dir,FLOWCEXE))
                winfml_filenames_array = winfml_filenames_str.split()

                for i in winfml_filenames_array:
                    shutil.copy(os.path.join(os.getcwd(),i),os.path.join(project_dir,i))

            cd = os.getcwd()
            os.chdir(project_dir)
            if options.debug: print "Flow compile: "+winPath+EOLN
            sub = subprocess.call(winPath)
            if dot_all_file:
                os.chdir(cd)
            else:
                for i in winfml_filenames_array:
                    try:
                        os.remove(os.path.join(project_dir,i))
                    except OSError: pass

        else:
            if options.debug: print "Flow compile: "+path+EOLN
            cmd_line_args = shlex.split(path)
            sub = subprocess.call(cmd_line_args)
    except:
        # output_str('   Unable to compile .i and/or .dwn file'+EOLN, 'error')
        # return "failed"
        pass
    else:
        # If compile was successful convert binary data to uu.encode data
        #try:
        #    uu.encode(os.path.join(project_dir, "raw_"+project_name+".dwn"), os.path.join(project_dir, project_name+".uue"))
        #except OSError:
            pass


"""Cache lines from files.

This is intended to read lines from modules imported -- hence if a filename
is not found, it will look down the module search path for a file by
that name.
"""
def getline(filename, lineno, module_globals=None):
    lines = getlines(filename, module_globals)
    n = int(lineno)
    if (1 <= n <= len(lines)):
        return lines[n-1].rstrip()
    else:
        return ''

# The cache
cache = {} # The cache

def clearcache():
    """Clear the cache entirely."""
    global cache
    cache = {}

def getlines(filename, module_globals=None):
    """Get the lines for a file from the cache.
    Update the cache if it doesn't contain an entry for this file already."""
    if filename in cache:
        return cache[filename][2]
    else:
        return updatecache(filename, module_globals)

def checkcache(filename=None):
    """Discard cache entries that are out of date.
    (This is not checked upon each call!)"""

    if filename is None:
        filenames = cache.keys()
    else:
        if filename in cache:
            filenames = [filename]
        else:
            return

    for filename in filenames:
        size, mtime, lines, fullname = cache[filename]
        if mtime is None:
            continue   # no-op for files loaded via a __loader__
        try:
            stat = os.stat(fullname)
        except os.error:
            del cache[filename]
            continue
        if size != stat.st_size or mtime != stat.st_mtime:
            del cache[filename]

def updatecache(filename, module_globals=None):
    """Update a cache entry and return its list of lines.
    If something's wrong, print a message, discard the cache entry,
    and return an empty list."""

    if filename in cache:
        del cache[filename]
    if not filename or filename[0] + filename[-1] == '<>':
        return []

    fullname = filename
    try:
        stat = os.stat(fullname)
    except os.error, msg:
        basename = os.path.split(filename)[1]

        # Try for a __loader__, if available
        if module_globals and '__loader__' in module_globals:
            name = module_globals.get('__name__')
            loader = module_globals['__loader__']
            get_source = getattr(loader, 'get_source', None)

            if name and get_source:
                if basename.startswith(name.split('.')[-1]+'.'):
                    try:
                        data = get_source(name)
                    except (ImportError, IOError):
                        pass
                    else:
                        if data is None:
                            # No luck, the PEP302 loader cannot find the source
                            # for this module.
                            return []
                        cache[filename] = (
                            len(data), None,
                            [line+'\n' for line in data.splitlines()], fullname
                        )
                        return cache[filename][2]

        # Try looking through the module search path.

        for dirname in sys.path:
            # When using imputil, sys.path may contain things other than
            # strings; ignore them when it happens.
            try:
                fullname = os.path.join(dirname, basename)
            except (TypeError, AttributeError):
                # Not sufficiently string-like to do anything useful with.
                pass
            else:
                try:
                    stat = os.stat(fullname)
                    break
                except os.error:
                    pass
        else:
            # No luck
##            print '*** Cannot stat', filename, ':', msg
            return []
    try:
        fp = open(fullname, 'rU')
        lines = fp.readlines()
        fp.close()
    except IOError, msg:
##        print '*** Cannot open', fullname, ':', msg
        return []
    size, mtime = stat.st_size, stat.st_mtime
    cache[filename] = size, mtime, lines, fullname
    return lines


# Used by list commands
def print_fml_source_code (FILE = None , start = 1, stop = 11, PC = None, MATCH = False, EXCEPTION_RETURN = None):
    if start < 1:
        start = 1
        stop = 11

    debug("print_fml_source_code", FILE, start, stop, PC)
    if not os.path.isfile(FILE): 
        FILE = os.path.join(i_file_directory, os.path.basename(FILE))
        debug("print_fml_source_code FILE", FILE)

    for x in range(start,stop+1):
        # look ahead if the next four line are empty ==> EOF
        if not (getline(FILE,x)  == "" and getline(FILE,x+1)=="" and \
                getline(FILE,x+2)  == "" and getline(FILE,x+3)=="" ):
            if x == PC and MATCH:
                output_str('===>')
            else:
                output_str('    ')

            try:
                statement_by_file_line[os.path.basename(FILE).strip()][str(x)].offset
                output_str(".")
            except:
                output_str(" ")

            output_str(str(x).rjust(4) + ": "+ getline(FILE,x).rstrip()+EOLN)
        else:
            output_str("Reached End of File " +EOLN, 'warning')
            if x == start:
                return EXCEPTION_RETURN
            else:
                return stop
            break
    return stop


#
# Thread to queue and parse lines
#
class CommandParserThread(threading.Thread):
    '''Process commands from the keyboard. These are the terminal commands.'''

    # global indent_at_breaking_point     #variable needed to track indent for frame print out
    global frame_iter                   #keeps track of what frame is being printed out during call
    global process_fifo_thread

    def __init__ (self, running_event, prompt_seen, prompt, quit_event, sync_seen):
        global last_lines_output_count
        global last_lines_output_time
        global cur_prompt

        last_lines_output_count          = 0
        last_lines_output_time           = time.time()
        self.running                     = running_event    # python event to start/stop fifo processing
        self.prompt_seen                 = prompt_seen
        cur_prompt                       = PROMPT
        self.unpause()
        self.unpause_ok                  = True
        threading.Thread.__init__ (self)
        self.setDaemon(True)                                # causes thread to stop when main ends
        self.queue                       = Queue.Queue()    # create a queu for commands
        self.quit_event                  = quit_event
        self.last_udws_cmd               = ""               #Variables needed to track Machine State
        self.calling                     = False            #When using process_line to print out frame set calling to True so frame wont be over writen
        self.sync_seen                   = sync_seen

    def put (self, line):                       # everyone submits commands here
        self.queue.put (line)                   # commands are queued up

    def join (self):                            # waits for queue to be empty
        self.queue.join ()

    def do_swap(self, first_word, remainder):
        # do_swap looks at first_word and reaminder and if certain conditions
        # are met it returns true (which means switch) or false (leave alone)
        # Allows user to type # tap
        if (remainder == "tap") or (remainder == "vtap"):
            try:
                int(first_word)
                return True
            except ValueError:
                return False
        #Allows user to type "sift help"
        elif first_word == "sift" and remainder == "help":
                return True
        else:
                return False

    def pause(self):
        global gui
        """Pauses the serial threads."""
        if not gui:
            process_fifo_thread.processing_allowed.clear()            # stop fifo processing

    def unpause(self):
        """Unpauses the serial threads."""
        process_fifo_thread.processing_allowed.set()              # start fifo processing

    def emptyline(self):                                          # currently we dont use
        """Toggle pause/unpause"""
        global last_lines_output_count
        global last_lines_output_time
        if process_fifo_thread.processing_allowed.isSet() and (last_lines_output_count > 10) and (time.time()-last_lines_output_time < 3):
            self.pause()
        else:
            self.unpause()
        printer.port.write("\n")

    def do_function(self, line):
        # If calling a flow or keyword
        function_name = re.split('[() .]', line)[0]
        if (function_name in flows) or (function_name in keywords):
            if not re.search("\(.*\)", line):
                line += "()"
            try:
                exec "printer."+line
            except:
                output_str(str(sys.exc_info()[1])+EOLN, "error")
        else:
            output_str(ERROR_PREFIX+function_name+" isn't a flow or keyword" +EOLN, "error")

    def do_underware(self, line):
        self.last_udws_cmd = line
        printer.udw(line)

    def do_break(self, line):
        try:
            line_num = int(line)
        except ValueError:
            line_num = None

        if line_num and (len(line.split()) == 1):
            args = (os.path.basename(current_fml_file) +" : "+str(line_num)).split("python_issue")
        else:
            args = line.split()

        if len(args) >= 1:
            name = args[0]

            # break on flow name
            if name in flows_by_name:
                self.do_underware("fm.break_flow %d" % flows_by_name[name].id)

            # break on variable write
            elif (name in global_names) or (len(args) == 2):
                if len(args) == 1:
                    self.do_underware("fm.break_variable %s" % global_names[name])
                else:
                    try:
                        value_int = int(eval(args[1]))
                        self.do_underware("fm.break_variable_value %s %d" % (global_names[name], value_int))
                    except:
                        output_str(args[1] + " unknown" +EOLN,"error")
                        self.unpause_ok = False

            # break on file:line
            elif (len(name.split(':')) == 2):
               args = name.split(':')
               partial_name = args[0].strip()
               line         = args[1].strip()

               # get the full filename (because we allow partial name)
               filename = None
               for f in filenames:
                   if partial_name in f:
                       filename = f
                       break

               if filename:
                   if filename in statement_by_file_line:
                       if line in statement_by_file_line[filename]:
                           statement = statement_by_file_line[filename][line]
                           output_str("SETTING BREAK IN  " + statement.flow.name + "()  " + statement.file_name + ":" + statement.line_number +EOLN, "error")
                           self.do_underware("fm.break %d" % int(statement_by_file_line[filename][line].offset))
                       else:
                           output_str(filename + ":" + line + " isn't a statement" +EOLN, "error")
                   else:
                       output_str(filename + " has no statements" +EOLN, "error")
               else:
                   output_str(partial_name + " not recognizable as a file" +EOLN, "error")

            else:
                try:
                    value_int = int(name)
                    self.do_underware("fm.break %d" % value_int)
                except ValueError:
                    output_str(args[0] + " unknown" +EOLN,"error")
                    self.unpause_ok = False

    def do_list(self, line, first_word, remainder):
        global current_fml_file
        global current_fml_line
        global was_l_minus

        if (first_word == "list" or first_word == "l") and (remainder.split(" ")[0] in flows or remainder.split(":")[0] in filenames):
            try:
                if remainder.split(":")[0] in filenames:
                    start = 1
                    stop = 11
                    # Input from user says to go to specific line in file
                    if len(remainder.split(":")) > 1:
                        try:
                            start = int(remainder.split(":")[1])
                            stop = start + 11
                        except:
                            start = 1
                    current_fml_file = fml_path_by_file_name[remainder.split(":")[0]]
                    if os.path.isfile(current_fml_file):
                        print_fml_source_code (current_fml_file, start, stop, None, False, None)
                    else:
                        output_str("Error: Sift can not find fml files" +EOLN, 'error')
                        current_fml_file = None
                else:
                    start = flows_by_name[remainder.split(" ")[0]].lineNum -5
                    stop = flows_by_name[remainder.split(" ")[0]].lineNum + 5

                    current_fml_file = flows_by_name[remainder.split(" ")[0]].filename
                    if len(remainder.split("-")) > 1 and remainder.split("-")[1].strip() == "f":
                        output_str(flows_by_name[remainder.split(" ")[0]].filename+EOLN)

                    print_fml_source_code (current_fml_file, start, stop, None, False, None)

                if not current_fml_file == None:
                    current_fml_line = stop
            except TypeError:
                if os.name == "nt":
                    output_str("Statement info not in symbol files. Put FlexTool in Flow Debugging mode and recompile." +EOLN, 'error')
                else:
                    output_str("TypeError", 'error')
        elif first_word == "list" or first_word == "l" and remainder.isdigit():
            try:
                current_fml_line = int(remainder)
                start = current_fml_line - 5
                stop = current_fml_line + 5
                was_l_minus = False

                if break_or_assert_pc:
                    pc = break_or_assert_pc
                else:
                    pc = None

                if current_fml_file:
                    stop = print_fml_source_code (current_fml_file , start, stop, pc, (current_fml_file == break_or_assert_file), current_fml_line)
                current_fml_line = stop
            except:
                output_str("No break points, asserts or lists have occurred" +EOLN, 'error')
                current_fml_file = None
                printer.port.write("\n")

        elif line.replace(" ","") =="l.":
            try:
                was_l_minus = False

                if break_or_assert_file:
                    stop = print_fml_source_code (break_or_assert_file, (break_or_assert_pc-5), (break_or_assert_pc+5), break_or_assert_pc, break_or_assert_file,  break_or_assert_pc)

                current_fml_line = stop
                current_fml_file = break_or_assert_file
            except:
                output_str("No break points or asserts have occurred" +EOLN, 'error')
                current_fml_file = None

        elif line.strip() =="l" or line.strip() =="l+" or line.strip() =="l-" and not (current_fml_file == None):
            try:
                if was_l_minus and (line.strip() == "l+" or line.strip() =="l"):
                    current_fml_line = current_fml_line + 10
                elif not was_l_minus and line.strip() == "l-":
                    current_fml_line = current_fml_line - 10

                was_l_minus = False

                if line.strip() =="l" or line.strip() =="l+":
                    start = current_fml_line + 1
                    stop = current_fml_line + 11
                elif line.strip() =="l-":
                    start = current_fml_line -11
                    stop = current_fml_line - 1
                    was_l_minus = True

                if break_or_assert_pc:
                    pc = break_or_assert_pc
                else:
                    pc = None

                if current_fml_file:
                    stop = print_fml_source_code (current_fml_file , start, stop, pc, (current_fml_file == break_or_assert_file) , current_fml_line)

                if line =="l-" and start < 1:
                    current_fml_line = 1
                elif line == "l-":
                    current_fml_line = start
                else:
                    current_fml_line = stop
            except:
                output_str("No break points, asserts or lists have occurred" +EOLN, 'error')
                current_fml_file = None
        else:
            output_str("Error: Invalid Selection" +EOLN, 'error')
        printer.port.write("\n")

    def do_sync(self, remainder):
        try:    timeout = int(remainder)
        except: timeout = 5
        self.unpause()
        self.sync_seen.clear()
        printer.port.data_seen_event.clear()
        printer.udw("udw.echo "+SYNC_STRING)
        while True:
            self.sync_seen.wait(timeout)
            if self.sync_seen.isSet():
                break;
            if not printer.port.data_seen_event.isSet():
                break;
            printer.port.data_seen_event.clear()
        if self.sync_seen.isSet():
            # output_str("sync completed"+EOLN, "args")
            pass
        elif not printer.port.data_seen_event.isSet():
            output_str("printer timeout"+EOLN, "warning")
        printer.port.write("\n")

    def do_open(self, files):
        # process symbol files first
        for f in files[:]:
            (root,ext) = os.path.splitext(f)
            if ext in ['.all','.i','.hlg']:
                load_symbols(f)
                files.remove(f)

            if ext in ['.lua', '.luc']:
                self.do_lua(f)
                files.remove(f)

        # process everything else 
        for f in files[:]:
            print "Reading", f
            process_file(f)

        UsageThread("open").start()

    def do_calls(self, indent): #Prints frames, calls is also bt, backtrace, and w(here)
        self.calling = True
        try:
            for self.frame_iter in iter(frames):
                if self.frame_iter <= indent:
                    process_line(frames[self.frame_iter].flow_call)
                    for j in iter(frames[self.frame_iter].locals):
                        process_line(frames[self.frame_iter].locals[j])
        except:
            pass
        finally:
            self.calling = False
            printer.port.write("\n")

    # cmd trace
    def do_trace(self, argline):
        global trace_startup

        # parse the arguments
        sum = 0
        new_argline = ""
        args = argline.split()
        while True:
            if (len(argline) == 0) or (argline == "on"):
                new_argline = "30"
                break

            if argline == "off":
                new_argline = "0"
                break

            if argline == "reset":
                new_argline = "reset";
                if trace_startup > 0:
                    trace_startup = 0
                    printer.udw("ds2.set 75352,0")  # DSID_FM_TRACE
                break

            if argline == "get":
                new_argline = "get"
                # Old XP systems have troubles keeping up with serial 
                if not isinstance(printer.port, SerialPort) or platform.release() != "XP":
                    new_argline += " 0"
                break

            if argline.startswith("startup"):
                try:
                    trace_startup = int(args[1])
                except IndexError:      # argument missing
                    trace_startup = 30
                except ValueError:      # argument not a number
                    output_str(args[1] + " not valid\n", "error")
                    return
                printer.udw("ds2.set 75352,"+str(trace_startup))  # DSID_FM_TRACE
                return
                # Printers since 2010 used the DSID. Underware method came in mid-2011.
                # Some day we can switch to the underware method ourselves.
                # new_argline = "startup " + str(trace_startup)
                # break

            #MAGGIE:
            if argline == "enable":
                key_serial_num = 0
                if underware_result_seen:
                    underware_result_seen.clear()
                    printer.udw("ds2.get_rec_array_str_by_name DSID_SERIAL_NUMBER")
                    underware_result_seen.wait(0.5)
                    if underware_result_seen.isSet():
                        udws_str_result_match = udws_str_result.split(";")[0]
                        if udws_str_result_match != "":
                            list_udws_str_result = list(udws_str_result_match)
                            for i in range(len(list_udws_str_result)):
                                if list_udws_str_result[i].isdigit():
                                    key_serial_num += int(list_udws_str_result[i])
                                elif list_udws_str_result[i].isalpha():
                                    key_serial_num += 100
                                else:
                                    print "\nthis character is neither a number nor a letter!!"
                        send_key_serial_num = "fm.trace enable " + str(key_serial_num)
                        printer.udw(send_key_serial_num)
                break

            if argline == "disable":
                printer.udw("fm.trace disable")
                break

            try:
                sum = int(argline)
                break
            except ValueError:
                pass

            for arg in args:

                try:
                    flow = flows_by_name[arg]
                except:
                    pass
                else:
                    if new_argline == "":
                        new_argline = "flow "
                    new_argline += str(flow.id) + " "
                    continue

                try:
                    keyword = keywords_by_name[arg]
                except:
                    pass
                else:
                    if new_argline == "":
                        new_argline = "keyword "
                    new_argline += str(keyword.id) + " "
                    continue

                if arg in ["slow"]:
                    sum = sum + 1
                elif arg in ["flow","flows"]:
                    sum = sum + 2
                elif arg in ["global","globals"]:
                    sum = sum + 4
                elif arg == ["local","locals"]:
                    sum = sum + 8
                elif arg in ["keyword","keywords","key","keys"]:
                    sum = sum + 16
                else:
                    output_str(arg, "args")
                    output_str(" unknown" + EOLN, "warning")
                    new_argline += arg + " "

            break

        if (new_argline == ""):
            new_argline = str(sum)

        self.do_underware("fm.trace "+new_argline)

    # cmd reload
    def do_reload(self):
        # Reprocess .i and .hlg files
        init_arrays_and_dictionaries()
        find_and_process_i_and_hlg_files()

    # cmd save
    def do_save(self, file):
        if file and len(file) > 0:
            (root,ext) = os.path.splitext(file)
            output_file.save(file)
            html_output_file.save(root)
        else:
            output_str("No filename given" + EOLN, "error")
        
    # cmd info
    def do_info(self):
        if dot_i_filename: output_str (".i file:     " + os.path.abspath(dot_i_filename) + EOLN)
        else:              output_str (".i file:     None" +EOLN)

        if hlg_filename:   output_str (".hlg file:   " + os.path.abspath(hlg_filename) + EOLN)
        else:              output_str (".hlg file:   None" +EOLN)

    # cmd usage
    def do_usage(self):
        UsageThread("usage").start()

    # cmd cad
    def do_cad(self, line):
        passed = ""
        if line == "compile" or line == "cad":
            init_arrays_and_dictionaries()
            if not dot_all_file:
                init_arrays_and_dict_for_hlg()
            passed = compile()
            if  not passed == "failed":
                # Process .i and .hlg files
                find_and_process_i_and_hlg_files()
                # Batch process input file
                if options.file:
                    process_file(options.file)
                printer.port.write("\n")
                try:
                    if os.name == "nt":
                        try:
                            os.remove(os.path.join(project_dir,project_name)+".j")
                        except OSError: pass
                        if not dot_all_file:
                            os.chdir(os.path.dirname(hlg_filename))

                    os.rename(os.path.join(project_dir,project_name)+".i", os.path.join(project_dir,project_name)+".j")
                except OSError:
                    print "Could not rename file please remove "+ project_name +".i from your current directory if you do not want it"


        if (line == "download" or line == "cad") and not passed == "failed" and not at_a_break_point:
            output_str("Sending file to printer " +EOLN,'warning')

            # read uuencoded data and replace the chars ; and " with offsets by a given delta
            uuencode = open(os.path.join(project_dir, project_name+".uue"), 'r')

            try:
                for line in uuencode.readlines():
                    read_data = line.replace("\'",chr(ord('\'')+64))
                    read_data = read_data.replace(";",chr(ord(';')+64))
                    read_data = read_data.replace("\\",chr(ord('\\')-64))
                    self.do_underware("fm.u " + read_data)
                    time.sleep(.2)
            except:
                output_str("Download Failed " +EOLN,'error')
            finally:
                uuencode.close()
        elif (line == "download" or line == "cad") and at_a_break_point:
            output_str("Can not download while at a break point", 'error')


    def do_lua(self, remainder):

        if remainder:
            (file, ext) = os.path.splitext(remainder)
            ext = ext.lower()

            if (ext == ".lua") or (ext == ".luc"):
                if os.path.isfile(remainder):
                    try:
                        uu.encode(remainder, remainder+".uue", os.path.basename(remainder))
                    except uu.Error:
                        output_str("Couldn't encode " +remainder + EOLN, "error")
                        return

                    uuencode = open(remainder+".uue", 'r')
                    output_str("Sending encoded file to printer " +EOLN,'warning')
                    try:
                        for line in uuencode.readlines():
                            if len(line) > 2:
                                read_data = line.replace("\'",chr(ord('\'')+64))
                                read_data = read_data.replace(";",chr(ord(';')+64))
                                read_data = read_data.replace("\\",chr(ord('\\')-64))
                                self.do_underware("fm.u " + read_data)
                                time.sleep(.2)
                    except:
                        output_str("Download Failed " +EOLN,'error')
                    finally:
                        uuencode.close()

                    try: os.remove(os.path.join(remainder+".uue"))
                    except OSError: pass

                else:
                    output_str("No such file: " + remainder + EOLN, "error")
            else:
                self.do_underware("fm.lua " + remainder)
        else:
            output_str("Expected .lua file or Lua statement" + EOLN, "error")

    def do_download(self, line):
        #For now this only handles downloading lua files to the printer
        #In the future I would like to integrate a new solution for fml 
        #Compile and download into this one command.
        #Currently it simply calls ramcp, an external .c on linux, in the future
        #it would be nice to pythonise it here so it can be used on windows as well

        #Setup file names to pass to ramcp
        args = line.split()
        files = " ".join(args[1:]).strip()

        #Get the romfs dir for the loaded proj(this will probably be integreated with an
        #updated process_dot_all for lua as a new global akin to file_dirs, but for now, 
        #we'll hack it
        cwd = os.getcwd()
        pathToCall = cwd

        #If we're not in the build directory, bail, this will be fixed when we update .all
        #processing to work better with .lua projects
        if not "obj_" in cwd:
            print "Must be in the projects build directory or it's romfs to download"
            return

        #If we're not in romfs, ie we're in the .all dir (remember this is lua only so far)
        if not "romfs" in cwd:
            parts = cwd.split("/")
            parts = parts[1:] #chop off empty element from the split
            pathToCall = "/" + os.path.join(parts[0], parts[1], "xm", parts[2], "romfs")

        callText = "ramcp " + files

        #Call ramcp and set cwd back afterwards
        subprocess.Popen(callText, cwd=pathToCall, shell=True)
        os.chdir(cwd)

    def do_flash(self, remainder):
        """Flash the unit"""
        global i_file_directory

        # Find file to reflash
        if remainder:
            # file is specified by user, check if it exists
            if os.path.isfile(remainder):
                file = remainder
            elif os.path.isfile(os.path.join(i_file_directory, remainder)):
                file = os.path.join(i_file_directory,remainder)
            else:
                output_str("No such file" + EOLN, "error");
        else:
            # Find a flash file in the build directory
            flash_files = []
            if i_file_directory:
                files = os.listdir(i_file_directory)
                for f in files:
                    (root,ext) = os.path.splitext(f)
                    if (ext == ".fhx"):
                        flash_files.append(os.path.join(i_file_directory, f))
            if (len(flash_files) == 0):
                try:
                    files = os.listdir(project_dir)
                except OSError: pass
                for f in files:
                    (root,ext) = os.path.splitext(f)
                    if (ext == ".fhx"):
                        flash_files.append(os.path.join(project_dir, f))
            if (len(flash_files) == 0):
                output_str("No .fhx file" + EOLN, "error")
                return
            elif (len(flash_files) == 1):
                file = flash_files[0]
            else:
                output_str("Multiple flash files found, use one of these commands:" + EOLN, "args")
                for f in flash_files:
                    output_str(" flash " + f + EOLN)
                return

        printer.flash(file)

    def do_print(self, path_to_file):
        #if os.name == "nt":
        #    try:
        #        subprocess.call("print /d:LPT1 "+ path_to_file) # option 1
        #        subprocess.call("copy "+path_to_file+"LPT1: /b") # option 2
        #    except:
        #        output_str("Could not write to to d: LP1 " +EOLN, "error")
        if os.path.exists('/dev/usb/lp0'):
            output_str("\nSending " + path_to_file +EOLN)
            try:
                subprocess.Popen(['cp', path_to_file, '/dev/usb/lp0'])
                # shutil.copyfile(path_to_file, '/dev/usb/lp0')
            except OSError:
                output_str("Couldn't write to /dev/usb/lp0" +EOLN, "error")
        else:
            output_str("At this time Send... is only available to Linux boxes"+EOLN, "warning")
            output_str("with a USB cable setup to the printer."+EOLN, "warning")
            output_str("[Could not write to to /dev/usb/lp0]" +EOLN, "error")

    def do_decode(self, first_word, remainder):
        global current_fml_file
        global current_fml_line

        error_code = ""
        if first_word == "decode":
            error_code = remainder.replace("0x","").replace("0X","")
        elif not len(remainder):
            error_code = first_word.replace("0x","").replace("0X","")

        set_path_to_hlg_and_i_files(hlg_filename, dot_i_filename)
        error_decode(error_code)

        printer.port.write("\n")

    def do_grep(self, line):
        reg_exp = re.compile(line, re.IGNORECASE)
        possibles = [name
                     for name in everything
                     if reg_exp.search(name)]
        type_dsid = ""
        type_const = ""
        type_global = ""
        type_other = ""
        for name in possibles:
            if name.upper() in dsids:
                name = name.upper()
                if not name.startswith("DSID_"):
                    name = "DSID_" + name
                try:
                    new_item = name + ' (' + dsids_by_name[name]+')'    # no duplicates
                except KeyError: pass
                if (type_dsid.find(new_item) < 0):
                    type_dsid = type_dsid + "  " + new_item +EOLN
            elif name in constant_names:
                try:
                    type_const =type_const+"  " + name.upper() + ' = ' + constant_name2value[name.lower()] +EOLN
                except KeyError: pass
            elif name in global_names:
                type_global =type_global +"  " + name +EOLN
            else:
                type_other = type_other +"  " + name +EOLN
        if len(type_dsid):
            output_str("  " + "-----------DSIDS---------- " +EOLN)
            output_str(type_dsid, "K")
        if len(type_const):
            output_str("  " + "---------CONSTANTS-------- " +EOLN)
            output_str(type_const, "K")
        if len(type_global):
            output_str("  " + "-----GLOBAL VARIABLES----- " +EOLN)
            output_str(type_global, "K")
        if len(type_other):
            output_str("  " + "-----------OTHER---------- " +EOLN)
            output_str(type_other, "K")
        line = "udw.cmds " + line
        self.do_underware(line)

    def do_help(self, arg):
        if len(arg) > 0:
            if (arg == "sift"):
                interactive_help()
            elif (arg == "trace"):
                help_trace()
            elif (arg == "debug"):
                help_debug()
            else:
                self.do_grep(arg)
        else:
            interactive_help()
            if printer.port.running_shell:
                printer.port.write("help\n")

    def do_txt_parse(self,line):
        if not line.endswith(".txt"):
            line = line+".txt"
        try:
           # path = line
            path = os.path.join(SIFT_CONFIG_DIR,line)
            if os.path.isfile(os.path.expanduser(os.path.join(project_dir,line))):
                path = os.path.expanduser(os.path.join(project_dir,line))
            elif os.path.isfile(line):
                path = line

            for file_line in open(path).readlines():
                # Ignore blank lines and lines that start with #
                if (len(file_line.strip()) and (not file_line.startswith("#")) 
                        and not self.quit_event.isSet()):
                    command_parser.put(file_line.strip())
                time.sleep(0.2)
        except:
            output_str("Could not completly process file: "+ line, "error")
            pass
        output_str(EOLN)

    def do_edit(self, line):
        #If siftflow is not installed, let user know why we bailed
        if not siftflow:
            print "SiftFlow not available"
            return

        if not gui:
            try:
                sf = SiftFlow()
            except:
                print "SiftFlow Launch Error: "
                print "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
                return

            args = line.split(' ')

            #No files specified, open current sift proj, no proj in sift, open blank editor
            if(len(args) == 1):
                sf.loadProject(file_dirs, project_dir, project_name, project_type)

            elif(len(args) > 1):
                sf.loadFiles(args[1:])                

            sf.run()
            UsageThread("edit").start()
        else:
            print "Please use the gui's edit button."

    def parse(self, line = ""):
        global output_file
        global break_or_assert_pc
        global break_or_assert_file
        global at_a_break_point
        global compatibility_error
        global process_fifo_thread

        line = line.strip()

        # Saves commands typed at prompt to output file
        output_file.write(cur_prompt + line + "\n")

        first_word      = re.split('[() ]', line)[0]
        remainder       = line[len(first_word):].strip()

        # switches the string order if certain conditions are met
        if self.do_swap(first_word, remainder):
            temp_first_word = first_word
            first_word = remainder;
            remainder = temp_first_word

        #assignment match - this is an assignment opperation
        assignment_match = assignment_op_re.match(line)
        array_match = array_op_re.match(line)

        # !linux_cmd: execute linux command in shell.
        # !cd PATH does not work.
        # Need to check with Windows to see if everything runs correctly
        if line.startswith('!'):
            linux_cmd = line.lstrip("!")
            if linux_cmd.startswith('cd '):
                try:
                  os.chdir(remainder)
                except:
                  print remainder + " is not a directory"
                printer.port.write("\n")
            else:
                os.system(linux_cmd)
                printer.port.write("\n")

        # comment
        elif line.startswith(COMMENT):
            printer.port.write("\n")

        # cmd unpause
        elif line == "unpause":
            self.unpause_ok = True
            printer.port.write("\n")

        # cmd pause
        elif line == "pause":
            self.unpause_ok = False
            self.pause()
            printer.port.write("\n")

        # blank line
        elif len(line) == 0:
            if gui:
                if printer.port.running_shell:
                    printer.port.write("\n")
                elif printer.port.running_udw: 
                    printer.port.write(ECHO_PROMPT)   # REVISIT PCS PROMPT

        # pwd -which directory is sift running in
        elif line.strip() == "pwd":
            print os.getcwd()
            printer.port.write("\n")

        # ls or dir -what files are in that directory
        # elif (first_word == "ls" and not os.name == "nt") or (first_word == "dir" and os.name == "nt"):
        #     os.system(line)
        #     printer.port.write("\n")

        # cd -change to a different directory
        # elif first_word == "cd":
        #     try:
        #         os.chdir(remainder)
        #     except:
        #         print remainder + " is not a directory"
        #     printer.port.write("\n")

        # cmd b or break
        elif first_word == "b" or first_word == "break":
            self.do_break(remainder)

        # list (l), l+ and l- but compatibility issues
        elif (first_word == "list" or first_word == "l" or line.strip() =="l+" or 
                line.strip() =="l-" or line.replace(" ","") =="l.") and compatibility_error:
            output_str("Symbol file incompatibility." +EOLN)
            printer.port.write("\n")

        # cmd list (l), l+ and l-
        elif (first_word == "list" or first_word == "l" or line.replace(" ","") =="l." or 
                line.strip() =="l+" or line.strip() =="l-"):
            self.do_list(line, first_word, remainder)

        # cmd o or open
        elif line.strip() == 'o' or line.strip() == "open" or first_word == "o" or first_word == "open":
            files = shlex.split(remainder) 
            self.do_open(files)

        # cmd s or step
        elif first_word == "s" or first_word == "step":
            self.do_underware("fm.step")

        # cmd n or next
        elif first_word == "n" or first_word == "next":
            self.do_underware("fm.next")

        # cmd f or finish
        elif first_word == "f" or first_word == "finish":
            self.do_underware("fm.finish")

        # cmd g or go
        elif first_word == "g" or first_word == "go":
            at_a_break_point = False
            self.do_underware("fm.go")

        # cmd c or clear
        elif first_word == "c" or first_word == "clear":
            break_or_assert_pc = None
            break_or_assert_file = None
            self.do_underware("fm.clear")

        # cmd port
        elif first_word =="port":
            printer.close()
            if not remainder:
                remainder = "0"
            printer.open(remainder)
            if printer.is_open_event.isSet():
                if printer.port.running_shell:
                    printer.port.write("\n\n")
                elif printer.port.running_udw:
                    output_str(EOLN)
                    printer.port.write(ECHO_PROMPT)

        # cmd t or trace
        elif first_word == "t" or first_word == "trace":
            self.do_trace(remainder)

        # cmd level
        elif first_word == "level":
            if not remainder:
                remainder = "20"
            self.do_underware("fm.level "+remainder)

        # cmd tick
        elif (first_word == "tick") or (first_word == "ticks"):
            if (not remainder) or (remainder == "on"):
                remainder = "20"
            if remainder == "off":
                remainder = "15"
            self.do_underware("fm.level "+remainder)

        # cmd clearlogs
        elif (first_word == "clearlogs"):
            output_file.clear()
            html_output_file.clear()

        # cmd browse
        elif (first_word == "browse"):
            try:
                file = os.path.abspath(html_output_file.name)
            except AttributeError:
                output_str("Error opening HTML"+EOLN)
                return

            # Attempt specific browsers first...
            FIREFOX_PATH = r"/sirius/tools/firefox/latest/firefox"
            browser_list = [] 
            if os.name == "nt":     # Windows (avoid IE)
                browser_list = [r"~\AppData\Local\Google\Chrome\Application\chrome.exe",
                                r"~\Local Settings\Application Data\Google\Chrome\Application\chrome.exe",
                                r"C:\Program Files (x86)\Safari\Safari.exe",
                                r"C:\Program Files\Safari\Safari.exe",
                                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                                r"C:\Program Files\Mozilla Firefox\firefox.exe"]
            elif os.path.exists(FIREFOX_PATH):
                browser_list = [FIREFOX_PATH]

            for browser in browser_list:
                browser = os.path.expanduser(browser)
                if os.path.exists(browser):
                    try:
                        subprocess.Popen([browser, "file://"+file])
                    except:     # failed opening, continue trying 
                        pass
                    else:       # browser must have opened okay
                        return 

            # Now try the system installed browser
            if os.name == "nt":
                output_str("Sift is only compatible with these browsers:" + EOLN)
                output_str("    Chrome     http://google.com/chrome" + EOLN)
                output_str("    Safari     http://apple.com/safari" + EOLN)
                output_str("    Firefox    http://firefox.com" + EOLN)
                output_str("Please install one of these in their default installation location." + EOLN)
            else:                   # Linux and Mac (try this)
                webbrowser.open_new_tab("file://"+file)
        
        # cmd sdv
        elif (first_word == "sdv"):
            hostname = remainder
            if not hostname and 'sdv_host' in user_options:
                hostname = user_options['sdv_host']
            if not hostname:
                hostname = "localhost"

            # Copy the trace file.
            (trace_filename,ext) = os.path.splitext(output_file.name)
            trace_filename = trace_filename + "_tmp" + ext
            trace_filename = os.path.abspath(trace_filename)
            try:
                output_file.save(trace_filename, quiet=True)
            except IOError:
                output_str("Didn't have permission to copy trace file for SDV."+EOLN, "error")
                return

            # Try sending the trace file to SDV
            class CouldNotSendTrace(Exception): pass
            try:
                try:
                    f = open(trace_filename)
                except IOError:
                    output_str("Couldn't open "+trace_filename+EOLN, "error")
                    return

                try:
                    ip_addr = socket.gethostbyname(hostname)
                except socket.error, message:
                    output_str("Couldn't get the IP address of "+hostname+"."+EOLN, "error")
                    raise CouldNotSendTrace 

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                if options.debug: output_str("Trying to connect to "+ip_addr+"..."+EOLN, "info")
                try:
                    s.connect((ip_addr, SDV_PORT))
                except socket.error, message:
                    if options.debug: output_str("Couldn't connect to SDV at "+hostname+". Is SDV running there?  Firewall?"+EOLN, "error")
                    if options.debug: output_str("  "+str(message)+EOLN, "error")
                    raise CouldNotSendTrace 

                if options.debug: output_str("Connected to SDV."+EOLN, "info")
                s.settimeout(None)
                s.send(f.read()) 
                s.close()
                f.close()
                output_str("Sent trace to SDV."+EOLN, "info")
                return
            except CouldNotSendTrace:
                pass

            # See if SDV is installed locally
            for sdv in SDV_LIST:
                if os.path.exists(sdv):
                    try:
                        subprocess.Popen([sdv, trace_filename], shell=True)
                    except:     # failed opening, continue trying 
                        pass
                    else:       # browser must have opened okay
                        output_str("Started SDV with trace file."+EOLN, "info")
                        return 

            # If we got here, we couldn't run SDV nor connect to it. 
            if (os.name == "nt"):
                output_str(r"Couldn't find SDV.  Please install from:"+EOLN, "error")
                output_str(r"    \\vcslab\root\InkSystems\SPHINKS\Randal Morrison\Sift Data Viewer\ " + EOLN)
            else:
                output_str(r"You need to have SDV running on a Windows machine and set the SDV host in the Options tab."+EOLN, "error")
                output_str(r"On your Windows machine, install SDV from:"+EOLN, "error")
                output_str(r"    \\vcslab\root\InkSystems\SPHINKS\Randal Morrison\Sift Data Viewer\ " + EOLN)
                return

        # cmd tock
        elif (first_word == "tock"):
            self.do_underware("fm.level 15"+remainder)

        # cmd sweep
        elif (first_word == "sweep"):
            self.do_underware("fm.level 15"+remainder)

        # cmd nosweep
        elif (first_word == "nosweep"):
            self.do_underware("fm.level 10"+remainder)

        # cmd depth
        elif first_word == "depth":
            self.do_underware("fm."+line)

        # cmd history
        elif first_word == 'h' or first_word == "history":
            global history
            for h in history:
                output_str(h+EOLN)

        # cmd door
        elif first_word == "door":
            if remainder == "open":
                self.do_underware("pe_digital_sensor.set MAIN_DOOR 1")
            elif remainder == "close":
                self.do_underware("pe_digital_sensor.set MAIN_DOOR 0")
            else:
                self.do_underware("pe_digital_sensor.clr MAIN_DOOR")

        # cmd power
        elif first_word == "power":
            if (remainder == "off"):
                self.do_underware("sm.off")
            else:
                self.do_underware("sm.on")

        # cmd tap
        elif first_word == "tap":
            self.do_underware("smgr_pe.multi_button_push "+remainder)

        # cmd vtap
        elif first_word == "vtap":
            self.do_underware("reports_mgr.virtual_tap_report "+remainder)

        # cmd serial_number
        elif (first_word.upper() in ['SERIAL_NUMBER', 'DSID_SERIAL_NUMBER']):
            self.do_underware("ds2.get_rec_array_str_by_name DSID_SERIAL_NUMBER")

        # cmd dot4
        elif first_word == "dot4":
            if remainder == "off":
                self.do_underware("usb_hs.set_cfg_desc_type 0")
            else:
                self.do_underware("usb_hs.set_cfg_desc_type 4")

        # cmd flash
        elif (first_word == "flash") or (first_word == "reflash"):
            self.do_flash(remainder)

        # cmd lua
        elif (first_word == "lua"):
            self.do_lua(remainder)

        # cmd sync
        elif (first_word == "sync"):
            self.do_sync(remainder)

        # cmd lp print
        elif first_word == "lp":
            # Allows user to use ~ to represent home dir
            if remainder.startswith("~/"):
                remainder = remainder.replace("~/", os.path.expanduser("~") + "/")
            elif remainder.startswith("~"):      # will only work on linux
                homeDirName = remainder.split("/")[0].strip("~")
                homeDirPath = "/homes/"+homeDirName+"/lnx"
                remainder = remainder.replace("~"+homeDirName, homeDirPath)
            # find the file
            if os.path.exists(remainder):
                path_to_file = remainder
            elif os.path.exists(os.path.join(project_dir,remainder)):
                path_to_file = os.path.join(project_dir,remainder)
            elif os.path.join(SIFT_CONFIG_DIR, remainder):
                path_to_file = os.path.join(SIFT_CONFIG_DIR, remainder)
            else:
                path_to_file = None

            if path_to_file:
                self.do_print(path_to_file)
            else:
                output_str("Error: could not find " + remainder, 'error')

        # cmd compile, cmd download, cmd cad
        elif line == "compile" or line == "download" or line == "cad":
            self.do_cad(line)

        elif (first_word == 'download'):
            self.do_download(line)

        # cmd flow or keyword
        elif line.startswith("flow_") or line.startswith("cmd_"):
            self.do_function(line)

        # cmd dsid
        elif (line.upper() in dsids) or ("DSID_"+line.upper() in dsids):
            if line.upper() in dsids:
                id = dsids_by_name[line.upper()]
            elif "DSID_"+line.upper() in dsids:
                id = dsids_by_name["DSID_"+line.upper()]
            self.do_underware("ds2.get "+id)

        # cmd set dsid
        elif assignment_match and ((assignment_match.group("variable").upper() in dsids)
                or ("DSID_" + assignment_match.group("variable").upper() in dsids)):
            first_word = assignment_match.group("variable")
            if not  first_word.upper().startswith("DSID_"):
                first_word = "DSID_" + first_word
            self.do_underware("ds2.set_by_name "+first_word.upper() + "," +  assignment_match.group("value"))

        # array query and set
        elif array_match:
            print "Array query: %s[%s]=%s" % (array_match.group("variable"), array_match.group("index"),
                        array_match.group("value"))
            if array_match.group("value"):
                self.do_function("flow_util_array_set_val(%s,%s,%s)" % (array_match.group("variable"),
                        array_match.group("index"), array_match.group("value")))
            else:
                self.do_function("flow_util_array_get_val(%s,%s)" % (array_match.group("variable"),
                        array_match.group("index")))

        # constant assignment
        elif assignment_match and (is_constant(assignment_match.group("variable"))):
            id, value = constant_id_and_value(assignment_match.group("variable"))
            try:    int_id = int(id)
            except: int_id = -1
            if (int_id >= 0):
                value = assignment_match.group("value")
                self.do_underware("fm.set_constant_direct " + id + ',' + value)
            else:
                output_str("can't change enumerations" + EOLN, "error")
                printer.port.write('\n')

        # constant
        elif (is_constant(line)):
            id, value = constant_id_and_value(line)
            try:    int_id = int(id)
            except: int_id = -1
            if (int_id >= 0):
                output_str(line + "=" + value + " in source code, asking printer..." + EOLN)
                self.do_underware("fm.get_constant_direct " + id)
                self.last_udws_cmd = line #Prevents values from incorrectly being converted to machine states
            else:
                output_str(line + "=" + value + EOLN)
                printer.port.write('\n')

        # globals
        elif line in global_names:
            self.do_underware("fm.get_variable_direct " + global_names[line])
            self.last_udws_cmd = line #Prevents values from incorrectly being converted to machine states

        # cmd set globals
        elif assignment_match and assignment_match.group("variable") in global_names:
            self.do_underware("fm.set_variable_direct " + global_names[assignment_match.group("variable")] + \
                                    ',' + assignment_match.group("value"))
            self.last_udws_cmd = line #Prevents values from incorrectly being converted to machine states

        # cmd rev
        elif first_word == "rev":
            output_str("Sift "+REV+EOLN)
            if dot_i_filename:
                output_str ("  "+os.path.abspath(dot_i_filename)+EOLN, "args")
            else:
                output_str ("  No .i file"+EOLN, "warning")

            if hlg_filename:
                output_str ("  "+os.path.abspath(hlg_filename)+EOLN, "args")
            else:
                output_str ("  No .hlg file"+EOLN, "warning")
            self.do_underware("bio.base_dir")
            self.do_underware("udw.get_verbose_fw_rev")

        # cmd exit
        elif first_word == "exit":
            exit("USER_EXIT")

        # cmd assert
        elif first_word == "assert":
            self.do_underware("udw.assert")

        # cmd crash
        elif first_word == "crash":
            crash_now = crash_now / 0

        # cmd print
        elif first_word == "print":
            try:
                exec line in globals()
            except:
                output_str(str(sys.exc_info()[1])+EOLN, "error")
            printer.port.write("\n")

        # cmd info
        elif first_word == "info":
            self.do_info()

        # cmd usage
        elif first_word == "usage":
            self.do_usage()

        # cmd exec 
        elif (first_word == "exec"):
            try:
                exec remainder in globals()
            except:
                output_str(str(sys.exc_info()[1])+EOLN, "error")

        # cmd save
        elif first_word == "save":
            self.do_save(remainder)

        # cmd reload
        elif first_word == "reload":
            self.do_reload()

        # cmd ok or okay
        elif (first_word == "ok") or (first_word == "okay"):
            self.do_underware("ds2.set_by_name DSID_USER_REQUEST,54")

        # cmd option
        elif (first_word == "options"):
            try:
                exec line
            except:
                output_str(str(sys.exc_info()[1])+EOLN, "error")
            printer.port.write("\n")

        # cmd edit
        elif (first_word == 'edit'):
            self.do_edit(line)

        # cmd underware
        elif '.' in line and not line.endswith(".txt"):
            self.do_underware(line)

        # cmd watch
        elif first_word == "watch":
            try:
                dsid_id = int(remainder)
            except ValueError:
                dsid_name = remainder.upper()
                if not dsid_name.startswith("DSID_"):
                    dsid_name = "DSID_" + dsid_name
                try:
                    self.do_underware("ds2.watch "+dsids_by_name[dsid_name])
                except KeyError:
                    output_str("unknown dsid", "error")
                    printer.port.write("\n")
            else:
                self.do_underware("ds2.watch " + str(dsid_id))

        # cmd decode error codes
        elif first_word.startswith("0x") or first_word.startswith("0X") or first_word == "decode":
            self.do_decode(first_word, remainder)

        # cmd help
        elif (first_word == "help"):
            self.do_help(remainder.strip().strip('/'))
            printer.port.write("\n")

        # cmd search
        elif line[0] == '/':
            self.do_grep(line.strip().strip('/'))

        # cmd quit
        elif (line == "quit") or (line == "q"):
            self.quit_event.set()
            if gui:
                gui.app.exit(0)

        # cmd parse sift command file
        elif os.path.isfile(os.path.join(SIFT_CONFIG_DIR,line)) or os.path.isfile(os.path.join(SIFT_CONFIG_DIR,line+".txt")) \
             or os.path.isfile(os.path.join(project_dir,line))  or os.path.isfile(os.path.join(project_dir,line+".txt")) \
             or os.path.isfile(line) or os.path.isfile(line+".txt"):
            self.do_txt_parse(line)

        # otherwise send line to printer
        else:
            printer.port.write(line + "\n")

        if (self.unpause_ok):
            self.unpause()
        return True

    def run (self):                             # process the queue in thread
        # if options.debug: print "CommandParserThread run"
        while not self.quit_event.isSet():
            line = self.queue.get()
            debug("CommandParserThread", len(line), line)
            self.parse(line)
            self.queue.task_done()              # marks item processed in queue
            time.sleep(0.1); 
            if gui: gui.process_events()
            time.sleep(0.1)


############################ START OF DECODE ERROR CODE CODE #############################
#
# Python version of the get_last_assert.bas file included in the dot all file
#
##########################################################################################
#
# VB functions converted to python
#
def mid(string, start, length = -1):
    if length == -1:
        length = len(string)
    return string[start:start+length]

def left(string, length):
    return string[0:length]

def right(string, length):
    return string[len(string)-length:]

def val(string):
    returnString = ""
    string = string.strip()
    for i in range(0,len(string)):
        if string[i].isdigit():
            returnString += string[i]
        elif not (string[i] == "\W"):
            break
    return returnString

def cstr(string):
    return str(string)

class RankException(Exception): pass

def uBound(a, dimension = 1):
    if dimension == 1:
        try:
            return len(a)
        except TypeError:
            raise RankException
    return uBound(a[0],dimension-1)

def Replace(string,find,replacewith,start = 0,count = -1):
    string = string[start:]
    if count == -1:
        count = len(string)
    return string.replace(find,replacewith,count)

#
# get_last_assert.bas functions
#
def mbValue(valueString, base =10):
    return int(valueString, base)

class ArgumentException(Exception):
    pass

def inStr(string1, string2, compare = 0):
    return InStr(1, string1, string2, compare)

def InStr(start, string1, string2, compare = 0):
    start = start - 1
    if start < 0:
        raise ArgumentException
    if not len(string1):
        return -1
    elif not len(string2):
        return start
    elif string2 in string1[start:]:
        return start + string.find(string1[start:],string2,start)
    return -1

def error_decode(assertStr):
    if len(assertStr) and int(assertStr,16) == 0:
        assertStr = "0"*8
    else:
        assertStr = "0"*(8-len(assertStr.lower().lstrip("0x"))) + assertStr.lower().lstrip("0x")
    #display the asset code
    output_str("ERROR CODE: " + "0x" + assertStr +EOLN, "None")

    #get the first char of assert string which is assert type
    assertType = left(assertStr, 1)

    #branch out depending on the assert type
    if assertType == "0" or assertType == "1":
        line_assert(assertStr)
    elif assertType.upper() == "B":
        mem_assert(assertStr)
    elif assertType.upper() in "89CEF":
        error_code_assert(assertStr)
    elif assertType == "6":
        if mid(assertStr,1,1) == "1":
            flow_named_assert(assertStr)
        elif mid(assertStr,1,1) == "2":
            decode_sequence_failure(assertStr)
        else:
            flow_assert(assertStr)
    elif assertType == "":
        output_str("Try Again"+EOLN, "error")
    else:
        output_str("Invalid Code"+EOLN, "error")

def set_path_to_hlg_and_i_files(path_to_hlg = "", path_to_i =""):
    global path_to_hlgfile
    global path_to_ifile

    path_to_hlgfile = path_to_hlg
    path_to_ifile = path_to_i

#Opens HLG/flows.i file and reads all data and gets it into a variant(Array of string)
def GetFileData(hlgFile = True):
    if hlgFile:
        filename = path_to_hlgfile                       #GetFilePath$(HlgFilename, "hlg", sPathname, "Select File", 0)
    else:
        filename = path_to_ifile                         #GetFilePath$(IFilename, "i", sPathname, "Select File", 0)

    if (filename).strip() == "":
        return                                           #End the script if no files were chosen
    file = open(filename, 'r')
    sFiledata = file.read()
    file.close
    if not hlgFile:
        sFiledata = Replace(sFiledata, EOLN, "\n") #Flows file might have lf&cr as line terminators.
    return sFiledata.split("\n")

#'Searches for a section in file data (which should be array of strings)
def SearchForSection(sectionName, vFileData, offset):
    i = 0
    for i in range(offset, uBound(vFileData)):
        if (sectionName == vFileData[i]):
            break
    offset = i
    return ((i < uBound(vFileData)), offset)
#
# FORMAT "A" ASSERT
# This assert decoding function is called for asserts
# that use format "A" as described in lib_assert.h.
# Format "A" contains the line number and a crc of the file name
#
def line_assert(assertStr):
    i = 0
    offset = 0
    SECTION_NAME = "File Name CRCs"

    vFileData = GetFileData()
    temp = SearchForSection(SECTION_NAME, vFileData, offset)
    if not temp[0]:
        output_str("Failed to find the section:'" + SECTION_NAME + "'" + " Wrong HLG format!"+EOLN, "error")
        return

    offset = temp[1]
    fileCrc = ""
    fileCode = mid(assertStr, 4, 4).upper()
    for i in range(offset+1,uBound(vFileData)):
        currentStr = vFileData[i]
        if mid(currentStr, 4, 4) == fileCode:
            filename = mid(currentStr,9,)
            break
        elif currentStr == "":
            output_str("Filename CRC: ????"+EOLN, "warning")
            output_str("Line Number: ????"+EOLN, "warning")
            output_str("Unidentified Code!"+EOLN, "error")
            return

    output_str("Filename CRC: " + filename+EOLN, "None")

    assertStrLine = mid(assertStr, 0, 4)
    assertStrLineNumber = mbValue(assertStrLine, 16)
    output_str("Line Number: " + str(assertStrLineNumber) +EOLN, "None")

#
# FORMAT "C" ASSERT
# This assert decoding function is called for asserts
# that use format "C" as described in lib_assert.h.
# Format "C" contains 3 elements: type, sub-type,uP address
#
def mem_assert(assertStr):
    i = 0
    offset = 0
    errorName = ""
    SECTION_NAME = "processor_errors_t"

    vFileData = GetFileData()
    temp = SearchForSection(SECTION_NAME, vFileData, offset)
    if not temp[0]:
       output_str("Failed to find the section:'" + SECTION_NAME + "'" + " Wrong HLG format!"+EOLN, "error")
       return

    offset = temp[1]
    fileCode = mid(assertStr, 1, 1)
    address = mid(assertStr, 2, 6)

    output_str("- Memory Assert Type -"+EOLN, "K")
    for i in range(offset+1, uBound(vFileData)):
        currentStr = vFileData[i]
        if right(currentStr, 1) == fileCode:
            errorName = error_parser(currentStr)
            break
        elif currentStr == "":
            break

    if len(errorName):
        output_str(" Error name: " + errorName+EOLN, "None")
        output_str(" Address: 0x" + address+EOLN, "None")
    else:
        output_str(" Error name: ????"+EOLN, "warning")
        output_str(" Address: 0x" + address+EOLN, "warning")
        output_str(" Unidentified Code!"+EOLN, "error")

#
# FORMAT "B" ASSERT
# This assert decoding function is called for asserts
# that use format "B" as described in lib_assert.h.
# Format "B" is made up of 3 elements:  type, component id, and error number.
#

def error_code_assert(assertStr):
    i = 0
    offset = 0
    SECTION_NAME = "Assert Component ID"

    vFileData = GetFileData()
    temp = SearchForSection(SECTION_NAME, vFileData, offset)
    if not temp[0]:
       output_str("Failed to find the section:'" + SECTION_NAME + "'" + " Wrong HLG format!"+EOLN, "None")
       return

    offset = temp[1]
    compID = mid(assertStr, 1, 3)
    errorCode = hex(int(mid(assertStr, 4, 4),16))

    if left(assertStr, 1) == "8":
        output_str("- Manufacturing Assert Type -"+EOLN, "K")
    elif left(assertStr, 1) == "9":
        output_str("- Log Assert Type -"+EOLN, "K")
    elif left(assertStr, 1).upper() == "C":
        output_str("- Hardware Assert Type -"+EOLN, "K")
    elif left(assertStr, 1).upper() == "E":
        output_str("- Firmware Assert Type -"+EOLN, "K")
    elif left(assertStr, 1).upper() == "F":
        output_str("- System Assert Type -"+EOLN, "K")

    #
    # Search for component error code type in
    # "Assert Component ID" section of .all file.
    # The string will end in "_errors_t".
    #
    compName = ""
    for i in range(offset+1,uBound(vFileData)):
        currentStr = vFileData[i]
        if right(currentStr, 3).lower() == compID:
            compName = error_parser(currentStr)
            #outputText"compName = " + compName
            break
        elif currentStr == "":
            output_str("Component Name/ID: ????(??)"+EOLN, "warning")
            output_str("Error name: ????"+EOLN, "warning")
            output_str("Unidentified Code!"+EOLN, "error")
            return

    #
    # Search for section corresponding to the error
    # type in .all files (section headed by compName).
    #
    offset = i
    temp = SearchForSection(compName, vFileData, offset)
    if not temp[0]:
        output_str("Component Name/ID: " + compName + "(0x" + compID + ")"+EOLN, "None")
        output_str("Can't find section.  Error code: " + errorCode+EOLN, "None")
        return
    offset = temp[1] + 1
    #
    # Section "<comp>_errors_t" found.
    # Now search for error number within the section.
    #
    errorName = "Could Not Find"
    for i in range(offset,uBound(vFileData)):
        currentStr = vFileData[i]
        if currentStr == "":
            output_str("Component Name/ID: " + compName + "(0x" + compID + ")"+EOLN, "None")
            output_str("Can't find error number.  Error code: " + errorCode+EOLN, "None")
            return
        else:
            try:
                dataErrorCode = ExtractHexVal(currentStr)
            except ValueError:
                return
            if dataErrorCode == errorCode:
                errorName = error_parser(currentStr)
                break

    output_str("Component Name/ID: " + compName + "(0x" + compID + ")"+EOLN, "None")
    output_str("Error name: " + errorName+EOLN, "None")

#
# FLOW ASSERT DECODING
# The next two functions decode
# a special type of assert called
# flow asserts.  The asert code begins with "6".
#
def flow_named_assert(assertStr):
    i = 0
    offset = 0
    start = False
    SECTION_NAME = "# Constant Info"

    output_str("","None")

    vFileData = GetFileData(False)

    temp = SearchForSection("# Constant Info", vFileData, offset)
    if not temp[0]:
        output_str("Failed to find the start of the named flow assert section, wrong flows format!" +EOLN, "error")
        return

    offset = temp[1]
    strIndex = mid(assertStr, 3, 5)
    lIndex = str(mbValue(strIndex, 16))
    strIndex = str(lIndex)

    output_str("- Named Flow Assert -"+EOLN,"K")
    for i in range(offset + 2,uBound(vFileData)):

        currentStr = (vFileData[i]).strip()
        values = currentStr.split("\t")
        ConstantValue= val(values[1])
        constantName=values[2]

        if (start == True) and (ConstantValue == lIndex):
            output_str("assertStr is a " + constantName +EOLN,"None")
            return

        if constantName == "assert_type_flows_fixed_start":
            start = True

        if constantName == "assert_type_flows_fixed_end":
            output_str("Named flow assert not found in flows.i file."+EOLN,"None")
            return

def flow_assert(assertStr):
    global current_fml_file
    global current_fml_line

    i = 0
    offset = 0
    SECTION_NAME = "# Assert Info"

    vFileData = GetFileData(False)
    temp = SearchForSection(SECTION_NAME, vFileData, offset)
    if not temp[0]:
       output_str("Failed to find the section:'" + SECTION_NAME + "' " + "Wrong Flows format!"+EOLN ,"error")
       return
    offset = temp[1]

    strIndex = mid(assertStr, 4, 4)
    lIndex = mbValue(strIndex, 16)
    strIndex = str(lIndex)
    output_str("- Flow Assert Type -"+EOLN,"K")

    flowFile = ""
    flowLine = 0
    for i in range(offset + 1, uBound(vFileData)):
        currentStr = vFileData[i]
        tempStr = string_parser(currentStr, 2)
        if tempStr == strIndex:
            tabAt = InStr(2, currentStr, "\t")
            flowLine = val(string_parser(currentStr, tabAt + 1))
            tabAt = currentStr.rfind("\t")
            flowFile = mid(currentStr,tabAt,)
            break
        elif currentStr == "":
            output_str("Filename: ????"+EOLN, "warning")
            output_str("Line Number: ????"+EOLN, "warning")
            output_str("Unidentified Code!"+EOLN, "error")
            return
    output_str("Filename: " + flowFile.strip() +EOLN, "None")
    output_str("Line Number: " + str(flowLine) +EOLN, "None")

    filename   = flowFile.strip()
    lineNumber = flowLine
    if filename and lineNumber and os.path.exists(filename):
        try:
            current_fml_file = filename
            current_fml_line = print_fml_source_code (filename, int(lineNumber)-5, int(lineNumber)+6)
        except ValueError: pass

#parses out just the error name and leaves any leading or
#trailing spaces behind
def error_parser(inputLine):
    return string_parser(inputLine, 3, " ")


#
# Parse hex value at the end of a line and return int value
#
def ExtractHexVal(inputLine):
    inputLine = inputLine.replace("0X", "0x",1)  # Incase of typo in hlg file
    Pos = InStr(1, inputLine, "0x")
    if (Pos == 0):
        Pos = len(inputLine)
    else:
        Pos = Pos + 1
    return hex(int(mid(inputLine, Pos-1),16))

def string_parser(parseStr, index, searchChar = "\t"):
    if len(parseStr) < index:
        return parseStr
    pos = InStr(index, parseStr, searchChar)+1
    if pos == -1:
        pos = len(parseStr)
    return mid(parseStr, index-1, pos - index)

def decode_sequence_failure (assertStr):
    masterFlow = mid(assertStr,2,3)
    lIndex = mbValue(masterFlow, 16)
    masterFlow = str(lIndex)
    offset = 0

    lastFlow = mid(assertStr, 5,3)
    lIndex = mbValue(lastFlow, 16)
    lastFlow = str(lIndex)

    output_str("Assert Type: Sequence Failure"+EOLN, "K")

    vFileData = GetFileData(False)

    temp = SearchForSection("# Flow Info", vFileData, offset)

    if not temp[0]:
        output_str("Failed to find the start of flow info section!"+EOLN, "error")
        return

    offset = 0
    for i in range((offset+7),uBound(vFileData)):
        currentStr = (vFileData[i]).strip()
        values = currentStr.split("\t")
        compStr = values[0]
        if  val(compStr) == val(masterFlow):
            masterFlowName = values[3]
            output_str("Master Flow ID: " + masterFlowName+EOLN, "None")
            break
        elif currentStr == "":
            output_str("Master Flow ID:" + masterFlow + " Flow not found!"+EOLN, "warning")
            break

    offset = 0
    for i in range((offset+7), uBound(vFileData)):
        currentStr = (vFileData[i]).strip()
        values = currentStr.split("\t")
        compStr = values[0]

        if  val(compStr) == val(lastFlow):
            lastFlowName = values[3]
            output_str("Last Flow ID: " + lastFlowName+EOLN, "None")
            break
        elif currentStr == "":
            output_str("Last Flow ID:" + lastFlow + " Flow not found!"+EOLN, "warning")
            break

############################ END OF DECODE ERROR CODE CODE #############################



# Sort compare function -- by modification date
def by_modification_date (x, y):
    # x_mod_time = int(os.path.getmtime (x))
    # y_mod_time = int(os.path.getmtime (y))
    try:
        x_mod_time = int(os.lstat(x).st_mtime)
        y_mod_time = int(os.lstat(y).st_mtime)
    except OSError:
        return -1
    if options.debug:
        debug ("sortx", x,x_mod_time)
        debug ("sorty", y,y_mod_time)
    return y_mod_time - x_mod_time


def find_filenames(extension, places):
    debug("Looking for", extension, "in", str(places))
    found_filenames = []

    # search
    for place in places:
        (directory, recurse) = place
        directory = os.path.abspath(os.path.expanduser(directory))
        debug("  Checking", directory, recurse)

        if recurse:
            for root, dirs, filenames in os.walk(directory):
                if extension == ".i": output_str(" Searching in "+root+EOLN, "info")
                for filename in filenames:
                    if filename.endswith(extension):
                        if ((not filename.endswith("scramble"+extension)) and
                            (not filename.endswith("_section"+extension))):

                            # Found a possible file
                            fullpath = os.path.join (root, filename)
                            try:
                                mod_time = time.ctime(os.stat(fullpath).st_atime)
                            except OSError:
                                output_str("     OS error on                         "+fullpath+EOLN, "comment", flush=True)
                            else:
                                if options.debug: output_str("     considering "+mod_time+" "+fullpath+EOLN, "comment", flush=True)
                                found_filenames.append(fullpath)
                for dir in dirs[:]:
                    if recurse:
                        if (os.name == "posix"):
                            if (not (dir.startswith("obj_") or dir.endswith("_all"))) or dir.endswith("obj_programs"):
                                dirs.remove(dir)
                    else:
                        dirs.remove(dir)
        else:
            if extension == ".i": output_str(" Searching in "+directory+EOLN, "info")
            for f in glob.glob(os.path.join(directory, "*" + extension)):
                if ((not f.endswith("scramble"+extension)) and
                    (not f.endswith("_section"+extension))):
                        if options.debug: output_str("     considering "+f+EOLN, "comment", flush=True)
                        found_filenames.append(f)

    debug ("    Found", found_filenames)
    return(found_filenames)


def sirius_root(directory):
    """ Determine Sirius root directory """
    base = os.path.basename(directory)
    while base:
        if (os.path.isdir(os.path.join(directory, "printengine")) and
            os.path.isdir(os.path.join(directory, "datapath")) and
            os.path.isdir(os.path.join(directory, "mech"))):
               return directory
        directory, base = os.path.split(directory)
    return None

def git_branch():
    """ Determine current git branch """
    try:
        result = subprocess.Popen(['git', 'branch'], shell=False,
                stdout=subprocess.PIPE).communicate()[0]
    except OSError: return None
    try:
        branch = re.search("\*\s(\w+)", result).group(1)
    except (IndexError, AttributeError): return None
    return branch

def find_best_filename(extension, possible_places):

    # Are we searching the system? (i.e. nothing was in current dir, nothing in -i, etc.)
    if (possible_places == SEARCH_PATH):

        # Are we in an obj_ directory, if so, just look in here
        if os.path.basename(os.path.abspath(os.curdir)).startswith ("obj_"):
            possible_places = [(os.curdir, True)]

        # Are we in the romfs dir - Quck hack to auto load .all when open in lua romfs
        if os.path.basename(os.path.abspath(os.curdir)).startswith ("romfs"):
            #build path to actual .all for the romfs's build dir
            dirnames = os.getcwd().split("/")
            path = "/" + os.path.join(dirnames[1], dirnames[2], dirnames[4])
            possible_places = [(path, True)]

        # Are we in a Sirius repo, if so, see which obj_ directories to look in
        sirius_root_dir = sirius_root(os.path.normpath(os.path.abspath(os.curdir)))
        if (sirius_root_dir):

            # Calculate the new default obj directory
            # Calculate obj_directory from the repo root
            obj_directory = re.sub("\/", "_", sirius_root_dir)
            obj_directory = re.sub("^(_sirius|_work)", "", obj_directory)
            obj_directory = "obj" + obj_directory
            obj_directory = os.path.join(SIRIUS_BUILD_DIR, obj_directory)
            if options.debug: debug ("Sirius root", obj_directory)

            # Check if the basic "makec" version exists
            new_places = []
            if os.path.isdir(obj_directory):
                if options.debug: debug("Sirius root", obj_directory)
                for d in glob.glob(os.path.join(obj_directory, "obj_*_*")):
                    if options.debug: debug ("  place", d)
                    new_places += [(d, False)]

            # Check if the branch "gitmakec" version exists
            # branch = git_branch()
            # debug ("Git branch", branch)
            # if branch:
            #     obj_directory += "_" + branch
            #     if os.path.isdir(obj_directory):
            #         if options.debug: debug("Sirius root (branch)", obj_directory)
            #         for d in glob.glob(os.path.join(obj_directory, "obj_*_*")):
            #             if options.debug: debug ("  place", d)
            #            new_places += [(d, False)]

            # If we had success finding a Sirius object directory, drop the system search
            if len(new_places):
                possible_places = new_places

    if (possible_places == SEARCH_PATH) and (os.name != "nt"):
        try:                                # lookup the last file used
            with open(os.path.join(SIFT_CONFIG_DIR, LAST_FILE)) as f:
                last_file = f.readline().strip()
                # print "last file =", last_file
        except IOError: pass
        else:
            possible_places = [(os.path.dirname(last_file), False)]

    filenames = find_filenames(extension, possible_places)
    if options.debug:
        for f in filenames:
            debug("    found "+f)

    # select best
    if len(filenames) == 0:
        return None
    elif len(filenames) == 1:
        return filenames[0]
    else:
        filenames.sort(by_modification_date)

        # Prefer .hlg files with "flowc" in the file
        if (extension == ".hlg"):
            # print "Test", filenames, "for flowc"
            if gui: gui.process_events()
            for hlg_name in filenames:
                # print "Testing", hlg_name, "for flowc"
                if gui: gui.process_events()
                try:
                    hlg_file = open(hlg_name)
                    found_flowc = hlg_file.read().find(FLOWC)       # I think this reads whole file
                    hlg_file.close()
                    if found_flowc >= 0:
                        if options.debug: print "Selected special HLG with FLOWC in file", hlg_name
                        # print "Selected HLG with FLOWC in file", hlg_name
                        return hlg_name
                except IOError:
                    pass

        debug ("    selected "+filenames[0])
        return filenames[0]



# Try to find best .hlg or .i file.
def old_find_best_filename(extention, starting_path=None, recurse=False):
    if (starting_path):
        output_str("Looking for " + extention + " in " + starting_path + EOLN)
    else:
        output_str("Looking for " + extention + " in system" + EOLN)
    found_filenames = []

    if starting_path:
        # We were given a specific directory to search
        for root, dirs, filenames in os.walk(starting_path):
            output_str("Searching in " + root + EOLN)

            # grab any .extension files in the directory
            for filename in filenames:
                if filename.endswith(extention):
                    # Erik doesn't know why "scramble" was eliminated, but
                    # eliminating it isn't good for builds that use it. So
                    # I'm changing this and will see what breaks.
                    if ((not filename.endswith("scramble"+extention)) and
                        (not filename.endswith("_section"+extention))):
                        fullpath = os.path.join (root, filename)
                        found_filenames.append(fullpath)
                        if options.debug: output_str("       found "+fullpath+EOLN)

            # eliminate any directories we don't want to recurse down
            for dir in dirs[:]:
                if recurse:
                    if (os.name == "nt"):
                        pass
                    else:
                        if (not dir.startswith("obj_")) or (dir.endswith("obj_programs")):
                            dirs.remove(dir)
                else:
                    dirs.remove(dir)

    else:
        # If not given a specific directory to look in, search these...
        possible_places = ["~\Documents\HP", "C:\Program Files\HP\FlexTool\Compile",
                "C:\Program Files (x86)\HP\FlexTool\Compile", "~"]


        # Now get all the possible files in those places
        for dir in possible_places:
            dir_expanded = os.path.expanduser(dir)
            best_filename = find_best_filename(extention, dir_expanded)  # recursive
            if best_filename:
                found_filenames.append(best_filename)

    # select best
    if len(found_filenames) > 0:
        found_filenames.sort(by_modification_date)

        # Prefer .hlg files with "flowc" in the file
        if (extention == ".hlg"):
            for hlg_name in found_filenames:
                hlg_file = open(hlg_name)
                found_flowc = hlg_file.read().find(FLOWC)
                hlg_file.close()
                return hlg_name
            output_str ("Secure .hlg file, some functionality won't work" +EOLN, "warning")

        return found_filenames[0]
    else:
        return None


# Add a flow or keyword to the interpreter so it can be called
def add_function_item_to_interpreter(item):

    def call_printer_function(self, *args):
        # if argument count is good
        if len(args) == item.numArgs:
            arg_list = []
            for arg in args:
                arg_list.append(arg)
            # arg_list.reverse()   -- I thought it should be reverse
            for arg in arg_list:
                printer.port.write('udws "fm.push_value %d"\n' % (arg))

            # call the item
            if item.name.startswith("flow"):
                printer.port.write('udws "fm.flow %s"\n' % (item.id))
            else:
                printer.port.write('udws "fm.execute_keyword %s"\n' % (item.id))

            # query the stack
            printer.port.write('udws "fm.query_stack"\n')

            # pop the result
            printer.port.write('udws "fm.pop"\n')

        else:
            output_str(ERROR_PREFIX + item.name + "() needs to have " \
                + str(item.numArgs) + " arguments\n", "error")

    call_printer_function.__name__ = item.name
    setattr (Printer, item.name, call_printer_function)


def add_variable_to_interpreter(name, value):
    # Make both the upper and lower cases global variables to Python
    globals()[name.upper()] = int(value)
    globals()[name.lower()] = int(value)


# Process the .i file and build lookup tables
def process_dot_i(dot_i_filename):
    global flows
    global flows_by_id
    global flows_by_name
    global frames
    global keywords
    global keywords_by_id
    global keywords_by_name
    global global_ids
    global global_names
    global constant_ids
    global constant_names
    global constant_values
    global constant_name2value
    global values_for
    global statement_by_offset
    global statement_by_file_line
    global filenames
    global everything
    global track_flow_id
    global fml_path_by_file_name
    global file_dirs
    track_flow_id = 0
    SECTION_NONE = 0
    SECTION_FLOWS = 1
    SECTION_GLOBALS = 2
    SECTION_KEYWORDS = 3
    SECTION_CONSTANTS = 4
    SECTION_VALUES = 5
    SECTION_STATEMENTS = 7
    SECTION_EXCLUDEDLINE_INFO = 8
    current_section = SECTION_NONE
    file_dirs = []

    debug("process_dot_i(%s)" % (dot_i_filename))

    try:
        dot_i_file = open(dot_i_filename, "r")
    except:
        return

    try:
        with open(os.path.join(SIFT_CONFIG_DIR, LAST_FILE), 'w') as f:
            f.write(dot_i_filename+'\n')
    except: pass

    if gui:
        gui.filename = dot_i_filename

    if (dot_i_filename.startswith("./")):
        dot_i_filename = dot_i_filename[2:]

    output_str(" "+ os.path.abspath(dot_i_filename) +EOLN, "G")

    # Loop through each line in the .i file.
    for line in dot_i_file:
        # Look to see if we've entered a section in the .i
        # file that we're interested in
        if line.startswith("# Flow Info"):
            current_section = SECTION_FLOWS
        elif line.startswith("# Keyword Info"):
            current_section = SECTION_KEYWORDS
        elif line.startswith("# Variable Info"):
            current_section = SECTION_GLOBALS
        elif line.startswith("# Array Info"):
            current_section = SECTION_NONE
        elif line.startswith("# Constant Info"):
            current_section = SECTION_CONSTANTS
        elif line.startswith("# Value Info"):
            current_section = SECTION_VALUES
        elif line.startswith("# Assert Info"):
            current_section = SECTION_NONE
        elif line.startswith("# Statement Info"):
            current_section = SECTION_STATEMENTS
        elif line.startswith("# ExcludedLine Info"):
            current_section = SECTION_EXCLUDEDLINE_INFO
        elif line.startswith("# Totals"):
            current_section = SECTION_NONE
        # Ignore blank lines and lines that start with #
        elif len(line) and (not line.startswith("#")):
            # Now that we've determined what section we're in, process it.

            if current_section == SECTION_FLOWS:
                line = line.strip()
                splits = line.split("\t")
                if len(splits) >= 4:
                    # This line contains a flow name
                    id      = int(splits[0])
                    numArgs = int(splits[1])
                    name    = splits[3]

                    # Manually add special flow "value_for" results
                    value_for = None
                    if name == "flow_state_get":
                        value_for = "mech_state_value"

                    flow = Flow(id=id, name=name, numArgs=numArgs, argList=[], locals=[], value_for=value_for)
                    if numArgs == 0:
                        flows.append(name)
                        everything.append(name)
                        flows_by_id[id]     = flow
                        flows_by_name[name] = flow
                        add_function_item_to_interpreter(flow)
                elif len(splits) == 1:
                    # This line contains an argument from the previous flow
                    argName = splits[0]
                    # Add this argument to the list of args
                    flow.argList.append(argName)
                    if flow.numArgs == len(flow.argList):
                        flows.append(name)
                        everything.append(name)
                        flows_by_id[id]     = flow
                        flows_by_name[name] = flow
                        add_function_item_to_interpreter(flow)
                elif len(splits) == 3:
                    type = splits[0]
                    if (type == "local"):
                        localName = splits[1]
                        flow.locals.append(localName)

            elif current_section == SECTION_KEYWORDS:
                line = line.strip()
                splits = line.split("\t")
                if len(splits) > 2:
                    # This line contains a flow name
                    id   = int(splits[0])
                    numArgs = int(splits[1])
                    name = splits[2]
                    keyword = Keyword(id, name, numArgs,[])
                    if numArgs == 0:
                        keywords.append(name)
                        everything.append(name)
                        keywords_by_id[id]     = keyword
                        keywords_by_name[name] = keyword
                        add_function_item_to_interpreter(keyword)
                elif len(splits) == 1:
                     # This line contains an argument from the previous keyword
                     argName = splits[0]
                     # Add this argument to the list of args
                     keyword.argList.append(argName)
                     if keyword.numArgs == len(keyword.argList):
                          keywords.append(name)
                          everything.append(name)
                          keywords_by_id[id]     =  keyword
                          keywords_by_name[name] = keyword
                          add_function_item_to_interpreter(keyword)

            elif current_section == SECTION_GLOBALS:
                line = line.strip()
                splits = line.split("\t")
                if len(splits) >= 2:
                    global_ids[splits[0]] = splits[1]
                    global_names[splits[1]] = splits[0]
                    everything.append(splits[1])

            elif current_section == SECTION_CONSTANTS:
                line = line.strip()
                splits = line.split("\t")
                if len(splits) >= 3:
                    constant_index = splits[0]
                    constant_value = splits[1]
                    constant_name  = splits[2]
                    everything.append(constant_name)
                    add_variable_to_interpreter(constant_name, constant_value)

                    if not constant_name.startswith("ur_"):
                        # Add name to constant_names dictionary with value as key
                        if constant_value not in constant_values:
                            constant_values[constant_value] = []
                        constant_values[constant_value].append(constant_name.upper())

                        # Add value to constant_values dictionary with name as key
                        constant_ids[constant_index]       = constant_name
                        constant_names[constant_name]      = constant_index
                        constant_name2value[constant_name] = constant_value

            elif current_section == SECTION_VALUES:
                if line.startswith("\t\t"):
                    # This line has the value names
                    enum_name  = line.strip()
                    if enum_name in constant_names:
                        enum_value = constant_name2value[enum_name]
                        add_variable_to_interpreter(enum_name, enum_value)
                        if type_name in values_for:
                            values_for[type_name][enum_value] = enum_name.upper()
                elif line.startswith("\t"):
                    # This line has the main values_for name
                    type_name = line.strip()
                    values_for[type_name] = {}
                    everything.append(type_name)

            elif current_section == SECTION_STATEMENTS:
                line = line.strip()
                # print line
                splits = line.split("\t")
                if len(line) > 5 and len(splits) == 4:
                    offset      = splits[0]
                    flow_id     = splits[1]
                    line_number = splits[2]
                    filename   = os.path.basename(splits[3])

                    statement   = Statement(offset, flows_by_id[int(flow_id)], line_number,
                                    filename)

                    # save statement by offset so we can look it up when we hit a breakpoint
                    # print offset + " " + flows_by_id[int(flow_id)].name + " " +  line_number + " " + filename
                    statement_by_offset[offset] = statement

                    # save filenames
                    if filename not in filenames:
                        filenames.append(filename)

                    # save statement by filename and line_number so we can look
                    # it up by filename:linenumber
                    if filename not in statement_by_file_line:
                        statement_by_file_line[filename] = {}
                    statement_by_file_line[filename][line_number] = statement
                    # save filename and line number to flows so we can look them up when
                    if int(flow_id) > track_flow_id:
                        track_flow_id = int(flow_id)
                        flows_by_id[int(flow_id)].filename = splits[3]
                        flows_by_id[int(flow_id)].lineNum = int(line_number)
                        flows_by_name[flows[int(flow_id)]].filename = splits[3]
                        flows_by_name[flows[int(flow_id)]].lineNum = int(line_number)
                        fml_path_by_file_name[filename] = splits[3]
                        if os.path.dirname(splits[3]) not in file_dirs:
                            file_dirs.append(os.path.dirname(splits[3]))

            elif current_section == SECTION_EXCLUDEDLINE_INFO:
                line = line.strip()
                splits = line.split("\t")
                if len(line) > 5 and len(splits) == 3:
                    line      = splits[0]
                    count     = splits[1]
                    file      = splits[2]
                if not os.path.basename(file) in fml_path_by_file_name:
                    fml_path_by_file_name[os.path.basename(file)] = file

# Process .hlg file and build a lookup table.
def process_hlg(hlg_filename):
    global underware
    global fml_filenames_str
    global winfml_filenames_str

    SECTION_NONE = 0
    SECTION_DSIDS = 1
    SECTION_FML = 2
    current_section = SECTION_NONE
    fml_filenames_str = ""
    winfml_filenames_str = ""

    try:
        hlg_file = open(hlg_filename, "r")
    except:
        return

    output_str(" "+ os.path.abspath(hlg_filename) +EOLN, "G")

    have_flow_info  = True
    # Loop through each line in the .hlg file.
    for line in hlg_file:
        line = line.strip()
        # Look to see if we've entered a section in the hlg
        # file that we're interested in

        if line.startswith("~J DSID"):
            current_section = SECTION_DSIDS
        #Auto-complete underware commands
        elif line.startswith("~F") or line.startswith("~~F") or line.startswith("~~~F"):
            line = line.strip()
            splits = line.split()
            if len(splits) >= 2:
                marker = splits[0]
                name = splits[1]
                underware.append(name)
                everything_hlg.append(name)
        elif line.startswith("Flexmech_Properties:"): # and dot_all_file:
            current_section = SECTION_FML
        # Ignore blank lines and lines that start with #
        elif len(line) and (not line.startswith("#")):
            # Now that we've determined what section we're in, process it.
            if current_section == SECTION_DSIDS:
                splits = line.split("\t")
                if len(splits) == 2:
                    # This line contains a DSID name and dsid
                    name = splits[0]
                    dsid = splits[1]

                    dsids.append(name)
                    dsids_by_id[dsid]   = name
                    dsids_by_name[name] = dsid
                   #  everything.append(name)
                    everything_hlg.append(name)
            elif current_section == SECTION_FML:
                m = hlg_fmls_for_i_re.match(line)
                if m:
                    if "FlexTool" in hlg_filename:
                        winfml_filenames_str = winfml_filenames_str + " " + os.path.basename(hlg_filename).replace(".hlg","")+ "_" + m.group("filename").strip()
                    else:
                        winfml_filenames_str = winfml_filenames_str + " " + m.group("filename").strip()
                        # Makes certain files read only
                        # if dot_all_file and os.name == "nt" and m.group("filetype").strip() == "READ_ONLY":
                        #    sub = subprocess.call(["attrib", "+r",os.path.join(project_dir,m.group("filename").strip())])

                    if dot_all_file and not os.name == "nt":
                        fml_filenames_str = fml_filenames_str + " " + os.path.join(project_dir,m.group("filename").strip())
                        # Makes certain files read only
                        # if m.group("filetype").strip() == "READ_ONLY":
                        #    sub = subprocess.call(["chmod", "a-w", os.path.join(project_dir,m.group("filename").strip())])
                    elif not os.name == "nt":
                        if os.path.exists(os.path.join(os.path.join(os.path.dirname(os.path.dirname(hlg_filename)),"fm",os.path.basename(os.path.dirname(hlg_filename))), m.group("filename").strip())):
                            fml_filenames_str = fml_filenames_str + " " +  os.path.join(os.path.join(os.path.dirname(os.path.dirname(hlg_filename)),"fm",os.path.basename(os.path.dirname(hlg_filename))), m.group("filename").strip())
                        else:
                            found = False
                            for i in file_dirs:
                                if os.path.exists(os.path.join(i,m.group("filename").strip())):
                                    fml_filenames_str = fml_filenames_str + " " + os.path.join(i,m.group("filename").strip())
                                    found = True
                            try:
                                if not found and have_flow_info:
                                    fml_filenames_str = fml_filenames_str + " " + fml_path_by_file_name[m.group("filename").strip()]
                            except:
                                # ERIK: Note to self: Don't know what all this is doing. Sort it out. Getting this message:
                                # output_str(" Mismatched .hlg file, some functionality will fail." +EOLN, 'named')
                                have_flow_info = False
                else:
                    current_section = SECTION_NONE
        else:
            current_section = SECTION_NONE

def find_and_process_i_and_hlg_files(ifile=None, hlgfile=None):
    global i_file_directory
    global project_dir
    global project_name
    global project_type
    global hlg_filename
    global everything_dictionary
    global dot_i_filename
    global gui
    global dot_all_file
    project_type = "fml" #assume fml

    debug("find_and_process_i_and_hlg_files(%s, %s)" % (ifile, hlgfile))

    # Find and Process .i file
    if ifile:
        dot_i_filename = ifile
    elif options.ifile:
        dot_i_filename = options.ifile                      # specified
    elif dot_all_file:
        dot_i_filename = find_best_filename(".i", [(project_dir, False)])
    else:
        dot_i_filename = find_best_filename(".i", [(".", False)])      # current directory
        if not dot_i_filename:
            if gui: gui.process_events()
            dot_i_filename = find_best_filename(".i", SEARCH_PATH)       # in system

    process_dot_i(dot_i_filename)

    # Find and Process .hlg file
    hlg_filename = None
    if hlgfile:
        hlg_filename = hlgfile
    if (options.hlg):                                       # specified
        hlg_filename = options.hlg
    elif not dot_all_file:
        if (dot_i_filename):
            hlg_filename = find_best_filename(".hlg",       # same place .i file is
                [(os.path.dirname(os.path.abspath(dot_i_filename)),False)])
        if not hlg_filename:
            hlg_filename = find_best_filename(".hlg", [(".",False)])  # current directory
        if not hlg_filename:
            hlg_filename = find_best_filename(".hlg", SEARCH_PATH)       # in system
    elif dot_all_file:
        hlg_filename = find_best_filename(".hlg", [(project_dir,False)])

    # Only process if you have not processed already
    if not dot_all_file:
        process_hlg(hlg_filename)
        if hlg_filename:
            project_name = os.path.basename(hlg_filename).replace(".hlg","")
        else:
            project_name = "sift_tmp"

    if gui: gui.process_events()
    everything.extend(everything_hlg)
    everything.extend(SIFT_COMMANDS)

    # Sort arrays
    flows.sort()
    keywords.sort()
    dsids.sort()
    everything.sort()

    no_caps_everything = everything
    for i in range(0,len(no_caps_everything)):
        no_caps_everything[i] = no_caps_everything[i].lower()
    no_caps_everything.sort()

    # Put everything into an alphabetized dictionary
    start_from = 0
    for letter in range(ord('a'),ord('z')+1):
        letter = chr(letter)
        temp = []
        for i in no_caps_everything[start_from:]:
            if i.lower().startswith(letter):
                temp.append(i)
                start_from +=1
            else: break
        everything_dictionary[letter] = temp
    del no_caps_everything

    # What did we find in the .i and .hlg files
    output_str (" " + str(len(flows)) + " flows   " + str(len(global_names)) + " globals   " + 
        str(len(keywords)) + " keywords   " + str(len(constant_names)) + " constants   " + 
        str(len(dsids)) + " DSIDS" + EOLN + EOLN, "info")
    if gui: gui.process_events()

    if dot_i_filename:
        i_file_directory = os.path.dirname(dot_i_filename)
        project_dir = i_file_directory

    #If there is no dot i, then see if there is a romfs meaning its a lua proj
    if (not dot_i_filename) or (i_file_directory == ""):
        parts = os.path.split(project_dir)
        path = os.path.join(parts[0], "xm", parts[1], "romfs")

        if(os.path.isdir(path)):
            project_dir = path
            project_type = "lua"
            file_dirs.append(path)

        i_file_directory = os.getcwd()

    # Not sure why this is being done, it doesn't allow siftrc in current directory
    # if dot_all_file or (os.name == "nt" and not (i_file_directory == os.getcwd())):
    #    os.chdir(i_file_directory)


#
# Keep a backup file of the trace output in case someone runs Sift and aftewards
# realizes Sift overwrote an existing file.  Sift overwrites its trace file
#

def backup_file(file):
    global output_file_size
    try:
        f = open(file, "r")
        backup_file = open(BACKUP_DEFAULT_LOGFILE, "w")
        backup_file.write(f.read())
    except (IOError, MemoryError, OverflowError):
        pass
    finally:
        try:
            f.close()
        except: pass
        try:
            backup_file.close()
        except: pass
        output_file_size = 0


############################################################
#
# Code to colorize DOS window text
#
############################################################

"""
Colors text in console mode application (win32).
Uses ctypes and Win32 methods SetConsoleTextAttribute and
GetConsoleScreenBufferInfo.

$Id: color_console.py 534 2009-05-10 04:00:59Z andre $
"""

if os.name == "nt":
    from ctypes import windll, Structure, c_short, c_ushort, byref

    SHORT = c_short
    WORD = c_ushort

    class COORD(Structure):
      """struct in wincon.h."""
      _fields_ = [
        ("X", SHORT),
        ("Y", SHORT)]

    class SMALL_RECT(Structure):
      """struct in wincon.h."""
      _fields_ = [
        ("Left", SHORT),
        ("Top", SHORT),
        ("Right", SHORT),
        ("Bottom", SHORT)]

    class CONSOLE_SCREEN_BUFFER_INFO(Structure):
      """struct in wincon.h."""
      _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD)]

if os.name == "nt":
    stdout_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute
    GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo

    def get_text_attr():
      """Returns the character attributes (colors) of the console screen
      buffer."""
      csbi = CONSOLE_SCREEN_BUFFER_INFO()
      GetConsoleScreenBufferInfo(stdout_handle, byref(csbi))
      return csbi.wAttributes

    def set_text_attr(color):
      """Sets the character attributes (colors) of the console screen
      buffer. Color is a combination of foreground and background color,
      foreground and background intensity."""
      SetConsoleTextAttribute(stdout_handle, color)

    default_colors = get_text_attr()
    default_bg     = default_colors & 0x0070



#########################################################################################
#
# Output Color
#
# Main routine to output color trace output.  You give it a text type.
#
#########################################################################################

# Colorize various types of text (to each output simultaneously)
def output_text_type(new_text_type):
    global text_type
    global text_type_stack
    global html_output_file
    global html_output_size
    global gui

    try:
        if options.nocolor: return
    except:
        return

    # Make our static globals if needed
    try:
        foo = text_type_stack
    except NameError:
        text_type = "default"
        text_type_stack = []

    # push, pop, or clear
    if (new_text_type == "pop"):
        new_text_type = "pop" + text_type
        try:
            text_type = text_type_stack.pop()
        except IndexError:
            text_type = "default"
    elif (new_text_type == "clear"):
        text_type = "default"
        text_type_stack = []
    else:
        text_type_stack.append(text_type)
        text_type = new_text_type

    # try:
    #     # if options.debug: print "COLOR"+new_text_type+"|"+text_type+"COLOR"
    #     ConnectionThread.send_all("COLOR"+new_text_type+"|"+text_type+"COLOR")
    # except socket.error:
    #     pass

    # HTML file
    if (html_output_file):
        # if (options.sdv):
        #     html_output_file.write(process_color(sdv_color_dictionary, new_text_type, text_type))
        # else:
            html_output_file.write(process_color(html_color_dictionary, new_text_type, text_type))
            html_output_size = html_output_size - 1

    # GUI colors
    if options.gui and gui:
        gui.write(process_color(qt_color_dictionary, new_text_type, text_type))

    # Standard out
    if (not options.quiet) and (not options.gui):
        if os.name == 'posix':  # ANSI colors
            # 30 black, 31 red, 32 green, 33 yellow, 34 blue, 35 magenta, 36 cyan (dark)
            # 90 gray,  91 red, 92 green, 93 yellow, 94 blue, 95 magenta, 96 cyan (light)
            # 1; bold   4; underline
            if ((text_type == "default") or (text_type == "none")):     # default
                sys.stdout.write('\033[0m')
            elif (text_type == "indent"):       # red
                sys.stdout.write('\033[31m')
            elif (text_type == 'F'):            # black or white (bold)
                sys.stdout.write('\033[1;30m')
            elif (text_type == 'r'):            # grey
                sys.stdout.write('\033[30m')
            elif (text_type == 'args'):         # blue
                sys.stdout.write('\033[0;34m')
            elif (text_type == "comment"):      # grey
                sys.stdout.write('\033[90m')
            elif (text_type == "raw"):          # grey
                sys.stdout.write('\033[90m')
            elif (text_type == "time"):         # grey
                sys.stdout.write('\033[90m')
            elif (text_type == 'K'):            # blue or cyan (bold)
                sys.stdout.write('\033[1;34m')
            elif (text_type == 'info'):         # blue or cyan (bold)
                sys.stdout.write('\033[0;34m')
            elif (text_type == 'number'):       # red or yellow
                sys.stdout.write('\033[31m')
            elif (text_type == 'G'):            # green
                sys.stdout.write('\033[32m')
            elif (text_type == 'L'):            # grey
                sys.stdout.write('\033[90m')
            elif (text_type == 'named'):        # magenta
                sys.stdout.write('\033[0;35m')
            elif (text_type == 'error'):        # red
                sys.stdout.write('\033[31m')
            elif (text_type == 'warning'):      # red
                sys.stdout.write('\033[1;31m')
            elif (text_type == 'c'):            # green
                sys.stdout.write('\033[32m')
            elif (text_type == 'l'):            # black or white (bold)
                sys.stdout.write('\033[1;30m')
            elif (text_type == 'R'):            # grey
                sys.stdout.write('\033[1;30m')
            elif (text_type == 'I'):            # grey
                sys.stdout.write('\033[30m')

        elif os.name == 'nt':  # DOS command colors
            if ((text_type == "default") or (text_type == "none")):             # default
                set_text_attr(FOREGROUND_GREY)
            elif (text_type == "indent"):       # red
                set_text_attr(FOREGROUND_RED | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'F'):            # black or white (bold)
                set_text_attr(FOREGROUND_GREY | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'r'):            # grey
                set_text_attr(FOREGROUND_GREY | default_bg)
            elif (text_type == 'args'):         # blue
                set_text_attr(FOREGROUND_CYAN | default_bg)
            elif (text_type == "comment"):      # grey
                set_text_attr(FOREGROUND_GREY | default_bg)
            elif (text_type == "raw"):          # grey
                set_text_attr(FOREGROUND_GREY | default_bg)
            elif (text_type == "time"):         # grey
                set_text_attr(FOREGROUND_GREY | default_bg)
            elif (text_type == 'K'):            # blue or cyan (bold)
                set_text_attr(FOREGROUND_CYAN | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'info'):            # blue or cyan (bold)
                set_text_attr(FOREGROUND_CYAN | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'number'):       # red or yellow
                set_text_attr(FOREGROUND_YELLOW | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'G'):            # green
                set_text_attr(FOREGROUND_GREEN | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'L'):            # grey
                set_text_attr(FOREGROUND_GREY | default_bg)
            elif (text_type == 'named'):        # green
                set_text_attr(FOREGROUND_GREY | default_bg)
            elif (text_type == 'error'):        # red
                set_text_attr(FOREGROUND_RED | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'warning'):      # yellow
                set_text_attr(FOREGROUND_YELLOW | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'c'):            # green
                set_text_attr(FOREGROUND_GREEN | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'l'):            # black or white (bold)
                set_text_attr(FOREGROUND_GREY | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'R'):            # grey
                set_text_attr(FOREGROUND_GREY | FOREGROUND_INTENSITY | default_bg)
            elif (text_type == 'I'):            # grey
                set_text_attr(FOREGROUND_GREY | default_bg)

##########################################################################
#
# Output String
#
# Main routine to output a string. Optional text type for colorizing.
# Outputs the string to various places simultaneoulsly and takes care of
# formatting for whatever the output format should be.
#
##########################################################################

output_str_lock = threading.Lock()

# Output a string to various places simultaneously. If given a text type, colorize it
def output_str (str, text_type=None, flush=False):
    global output_file
    global output_file_size
    global html_output_file
    global html_output_size
    global output_str_lock
    global gui
    global time_writing

    if not str: str=""

    t0 = time.clock()
    output_str_lock.acquire()

    if text_type:
        output_text_type(text_type)
    else:
        if (EOLN in str) and (str != EOLN):
            text_type = "text"
            output_text_type(text_type)

    # if not options.quiet:
    if not options.gui and not options.quiet:
        sys.stdout.write(eoln_re.sub("\r\n", str))

    # Using options.gui so we can switch output back to stdout for exceptions
    if options.gui:
        if gui: 
            gui.write(str)
        if (flush) or (text_type == "error") or (text_type == "warning") or (text_type == "info"):
            if gui: gui.process_events()

    if output_file:
        output_file.write(str)

    if html_output_file:
        html_output_file.write(eoln_re.sub("", str))

    # if ConnectionThread and len(ConnectionThread.connections):
    #     try:
    #         ConnectionThread.send_all(str)
    #     except socket.error:
    #         pass

    if text_type:
        output_text_type("pop")

    output_str_lock.release()
    time_writing += time.clock() - t0


####################################################################################
#
# Output Number
#
# Deals with outputting a number and helping to find a human readable name.
#
####################################################################################

# Output a number -- looking up possible names for it
def output_number(number, value_for=None):
    separator = ""
    name_for_number = None
    possible_name_for_number = None

    # "value_for"
    if value_for in values_for:
        if number in values_for[value_for]:
            name_for_number = values_for[value_for][number]
    # DSID
    if len(number) == 5 and (number in dsids_by_id):
        name_for_number = dsids_by_id[number]

    # Array
    if len(number) == 9:
        if number in constant_values and len(constant_values[number]) == 1:
            name_for_number = constant_values[number][0]

    # Likely possibilities
    possible_names_for_number = ""
    if name_for_number is None:
        # Constant matches
        if number in constant_values:
            if len(constant_values[number]) <= 2:   # show maximum of 2 names
                for name in constant_values[number]:
                    possible_names_for_number += " ?" + name
        # Oddball DSID
        if (len(number) > 3) and (number in dsids_by_id):
            # Some DSIDs aren't 5 digits
            possible_names_for_number += " ?" + dsids_by_id[number]

    # Output the number
    if not value_for is None:
        output_str(value_for + "=")
    output_str(number, text_type="number")
    separator = " ";

    # Output the number's name
    if name_for_number:
        output_str(separator + name_for_number, text_type="named")
    elif possible_names_for_number:
        output_str(possible_names_for_number, text_type="named")



# Debug statements

previous_time = time.time()

def debug(*args):
    if options.debug:
        global previous_time
        now = time.time()
        delta_time = now - previous_time
        previous_time = now

        sys.stderr.write("[%7.3f" % delta_time)
        for arg in args:
            sys.stderr.write(' ')
            sys.stderr.write(str(arg))
        sys.stderr.write(' ]\r\n')
        if gui: gui.process_events()


######################################################################
#
# Sift Startup or Mech Startup
#
# Called whenever Sift starts *OR* whenever the mech reboots. This
# allows us to send something to the printer in either case. For example,
# this is a good time to turn on tracing, etc.
#
######################################################################

# Startup serial trace on the mech
def startup_trace(printer):
    global command_parser
    global trace_startup
    global fiber

    if options.debug: debug("startup_trace", printer, printer.port)
    fiber = ""
    if printer:
        # Clear printer's serial port and trigger a prompt to be sent
        if printer.port.running_shell:
            printer.port.write("\n")
        elif printer.port.running_udw:
            printer.port.write(ECHO_PROMPT)   # revisit PCS_PROMPT

        # Sift is being called with single command to run
        if (options.command):
            printer.port.write("\n")
            command_parser.put(options.command)
            if options.command != 'flash':
                command_parser.put("sync")
            command_parser.put("quit")
            return

        # Gui might have some settings to reset at printer startup
        if gui:
            gui.printer_started_up()

        # If we're configured to trace immediately at startup, turn on tracing
        if trace_startup > 0:
            printer.udw("fm.trace "+str(trace_startup))

        # Query the printer's rev and match it with the hlg_filename
        if (hlg_filename and 
                (printer.port.running_shell or printer.port.running_udw)):
            if underware_result_seen:
                underware_result_seen.clear()
                printer.udw("bio.rev_str")
                underware_result_seen.wait(0.5)
                if underware_result_seen.isSet():
                    try:
                        udws_str_result_match = udws_str_result.split(";")[0][:5]
                        hlg_base = os.path.basename(hlg_filename)
                        if udws_str_result_match not in hlg_base:
                            output_str("%s/%s possible symbol mismatch" % 
                                (udws_str_result_match, hlg_base), "warning")
                            output_str(EOLN)
                    except: pass

        # Select which startup files to execute 
        if (options.startup):                       # execute given startup file
            if os.path.isfile(options.startup):
                startup_files = [options.startup]
        else:                                       # execute default startup files
            startup_files = [os.path.join(SIFT_CONFIG_DIR, STARTUP_FILE), STARTUP_FILE]

        # Execute the startup files
        for file in startup_files:
            if os.path.isfile(file):
                for line in open(file).readlines():
                    # Ignore blank lines and lines that start with #
                    if len(line) and (not line.startswith("#")):
                        output_str(line + EOLN, "text", flush=True)
                        command_parser.put(line.strip())
                        time.sleep(0.25)

        if gui: gui.process_events


#############################################################################
#
# Process Line
#
# Decodes a single raw trace line from the printer.
#
# This function decodes a line of text received from the
# printer and pretties it up for human consumption.  This is the
# grandmother of all Sift. This is where Sift began. In fact, the
# design of this function hasn't changed -- only additions and tweaks
# have been made. It is sorely in need of redesign. Alas, it works hard
# and well.
#
#############################################################################

last_time = 0
time_highorder = 0
time_format_determined = False
old_time_format = False

def process_line(line):
    global last_time
    global time_highorder
    global dsid_trap_line  #keeps track of latest trap
    global matches         #boolean used to determine if trap was machine state
    global command_parser
    global current_fml_file
    global current_fml_line
    global break_or_assert_pc
    global break_or_assert_file
    global frames
    global compatibility_error
    global at_a_break_point
    global indent
    global line_class
    global line_indent
    global wrap_count
    global time_format_determined
    global old_time_format
    global udws_str_result
    global lines_processed
    global time_processing
    global fiber

    if options.debug: debug("process_line:", len(line), line.strip())

    lines_processed += 1
    t0 = time.clock()

    # Since imported files go straight to process line and bypass command_parser
    # need to check if command parser has been initialized.
    try:
        temp = command_parser
    except:
        cmd_parser_bool = False
    else:
        cmd_parser_bool = True

    ifile_suspect = False
    want_linefeed = True

    # if options.debug: output_str("[" + str(len(line)), "warning")

    # line = line.replace('\r','')

    if len(line) > 0:

      # Regular expression match for a FML trace line
      m = decode_line_re.match(line)

      type = None
      indent = None

      if m:
          indent = ord(m.group("indent")) - ord('A')

          try:
              newfiber = m.group("fiber")
          except IndexError:
              pass
          else:
              if (len(newfiber)==1) and (newfiber != fiber):
                  fiber = newfiber

          type   = m.group("type")
          id     = m.group("id")

          try:
              id = int(id)
          except:
              id = 0

          if not time_format_determined:
              if (len(m.group("time")) == 3):
                  if (m.group("time")[0] == '0'):
                      old_time_format = True
                      time_format_determined = True
              else:
                  old_time_format = False
                  time_format_determined = True

          if (time_format_determined and old_time_format):
              if (not len(m.group("time")) == 3):
                  # time is really old format
                  old_time_format = False

          if (time_format_determined and old_time_format):
              # Old time format
              if (type == 'M' or type == 't'):
                  # Time sync
                  new_time = int(id) / 10
                  trace_time = new_time % 1000
                  time_highorder = new_time / 1000
              else:
                  # Roll high order of time digits
                  trace_time = int(m.group("time"))
                  if (trace_time < last_time):
                      try:
                          time_highorder = time_highorder + 1
                      except NameError:
                          time_highorder = 1
              last_time = trace_time

          else:
              # New time format
              if (m and len(m.group("time")) > 0):
                  trace_time = int(m.group("time"))
                  last_time = trace_time

          if   (type == 'F'):   items = flows_by_id
          elif (type == 'K'):   items = keywords_by_id
          elif (type == 'G'):   items = global_ids
          elif (type == 'H'):   items = headers
          else:                 items = None

          if (items) and (id > len(items)):
              m = None
              ifile_suspect = True

      if m:
          line_class  = type;
          line_indent = indent;
          output_text_type("line")

          # Format the output

          # Raw display
          if (options.raw):
              output_str("%-15s " % line[0:14].strip(), "raw")

          # Serial Tool header (don't know if we want to show it)
          if m.group("header"):
              output_str(m.group("header"))

          # Timestamp
          if cmd_parser_bool and command_parser and command_parser.calling:
              output_str (" ".rjust(12) , text_type="time")
          else:
              if not options.raw:
                  output_str ("+");
                  output_str (fiber);
              if (time_format_determined and old_time_format):
                  output_str ("%6d.%02ds " %
                    ((time_highorder*1000+trace_time)/100, trace_time%100),
                    text_type="time")
              else:
                  output_str ("%6d.%02ds " % 
                    (last_time/100, last_time%100),
                    text_type="time")

          # Indentation
          output_text_type("indent")
          if indent:
            for i in xrange(indent):
              if (options.indent) and (cmd_parser_bool and not command_parser.calling):
                  output_str(options.indent)
              elif not (cmd_parser_bool and command_parser and command_parser.calling):
                  if ((i % 3) == 0):
                      output_str ('| ')
                  else:
                      output_str ('. ')
              else:
                  output_str ('  ')
          output_text_type("pop") #indent

          # Item name
          output_text_type(type)

          if (type == 'F'):
              try:
                  output_str(flows_by_id[id].name)
                  flow_stack[indent+1] = flows_by_id[id]
                  #tracks flows for break point back trace
                  try:
                      if not (cmd_parser_bool and command_parser.calling):
                          frames[indent+1] = Frame(line, time_highorder, trace_time)
                  except:
                      pass
              except KeyError:
                  output_str(type + str(id))
          elif ((items is global_ids) and (id < len(items))):        # TODO: Cleanup
              output_str(items[str(id)])
          elif (items) and (id < len(items)):
              output_str(items[id].name)                           # Item name
          elif (type == 'R' or type == 'r'):
              output_str("return")
          elif (type == '='):                   # resumed keyword result
              output_str(type)
              output_number(str(id))
          elif (type == "N"):                   # string
              try:
                  output_str(N_STRINGS[id])
              except IndexError:
                  output_str(type+str(id))
          elif (type == 'B'):                   # break
              at_a_break_point = True
              try:
                  s = statement_by_offset[str(id)]
                  output_str(("BREAK IN  %s()  %s:%s"+EOLN)
                        % (s.flow.name, s.file_name, s.line_number), "error")
                  current_fml_file = flows_by_name[s.flow.name].filename

                  pc = int(s.line_number)
                  if pc - 5 > 0:
                      start = pc -5
                      stop = pc + 6
                  else:
                      start = 1
                      stop = 11
                  output_str(EOLN)
                  stop = print_fml_source_code (current_fml_file , start, stop, pc, True, pc)
                  current_fml_line = stop
                  break_or_assert_pc = int(s.line_number)
                  break_or_assert_file = current_fml_file
                  compatibility_error = False
              except KeyError:
                  s = None
                  output_str(("BREAK AT  %s"+EOLN) % (str(id)), "error")
                  compatibility_error = True
                  current_fml_file = None
                  current_fml_line = id

          elif (type == 'A'):                   # assert
              try:
                  s = statement_by_offset[str(id)]
                  output_str(("ASSERT %s IN  %s()  %s:%s"+EOLN)
                        % (m.group("args"), s.flow.name, s.file_name, s.line_number), "error")
                  current_fml_file = flows_by_name[s.flow.name].filename
                  pc = int(s.line_number)
                  if pc - 5 > 0:
                      start = pc -5
                      stop = pc + 6
                  else:
                      start = 1
                      stop = 11
                  output_str(EOLN)
                  stop = print_fml_source_code (current_fml_file , start, stop, pc, True, pc)
                  current_fml_line = stop
                  break_or_assert_pc = int(s.line_number)
                  break_or_assert_file = current_fml_file
                  compatibility_error = False
              except KeyError:
                  s = None
                  output_str(("ASSERT %s AT  %s"+EOLN)
                        % (m.group("args"), str(id)), "error")
                  compatibility_error = True
                  current_fml_file = None
                  current_fml_line = id

          elif (type == 'L'):
              try:
                  flow = flow_stack[indent]
                 # frame = frames[indent]
                  num_locals = len(flow.locals)
                  output_str(flow.locals[num_locals-id])
              except (KeyError, IndexError):
                  output_str(type + str(id))
              try:
                  frames[indent].locals[id] = line
              except KeyError:
                  pass
          elif (type == 'T'):
              output_text_type("args")
              output_str("Tracing ")
              if TRACE_FLUSH & id:
                  output_str(" SLOW FLUSH", "error");
              if TRACE_FLOWS & id:
                  output_str(" FLOWS", "F");
              if TRACE_GLOBALS & id:
                  output_str(" GLOBALS", "G");
              if TRACE_LOCALS & id:
                  output_str(" LOCALS", "L");
              if TRACE_KEYWORDS & id:
                  output_str(" KEYWORDS", "K");
              if TRACE_ARRAYS & id:
                  output_str(" ARRAYS");
              output_text_type("pop") #args

          elif (type == 'M' or type == 't'):    # obsolete 't'
              output_str("Time", "args")

          elif (type == 'C'):
              try:
                  output_str(constant_ids[str(id)].upper())
              except KeyError:
                  output_str(type + str(id))

          else:
              output_str(type + str(id))

          args = m.group("args")
          if args:
              args = args.strip("([])")
              if type == 'Y':
                  output_str('[')
              else:
                  output_str('(')
              args = args.split(",")
              i = 0
              for arg in args:
                if (items and (id < len(items))
                        and (id in items)
                        and (hasattr(items[id],"argList"))
                        and (i < len(items[id].argList))):
                    arg_name = items[id].argList[i]
                else:
                    arg_name = None
                    ifile_suspect = True
                output_text_type("args")
                output_number (arg, arg_name)
                if ((type == 'H') and (arg_name == "wrap_line")):
                    wrap_count = int(arg)
                    if (wrap_count > 0):
                        output_str("[WRAP]")
                i = i + 1
                if (i < len(args)):
                    output_str(", ")
                output_text_type("pop") #args

              if type == 'Y':
                  output_str(']')
              else:
                  output_str(')')
          else:
              if type in 'FK':
                  output_str("()")

          if m.group("result"):                                     # Result value
              if (type == 'R' or type == 'r'):
                  output_str("(")
                  if id in flows_by_id:
                      output_number(m.group("result"), flows_by_id[id].value_for)
                  else:
                      output_number(m.group("result"))
                  output_str(")")
                  if (id < len (flows_by_id)):
                      output_str(" // " + flows_by_id[id].name, text_type="comment")
                      try:   #check to make sure flow being returned is in the frame
                          if len(frames) and frames[len(frames)-1].flow_call == flows_by_id[id].name:
                             del frames[len(frames)-1]  # removes last frame
                      except:
                          pass
              elif (type == 'G'):
                      output_str('=', text_type="comment")
                      output_number(m.group("result"))
                      output_str(" // global", text_type="comment")
              else:
                      output_str('=', text_type="comment")
                      output_number(m.group("result"))

          output_text_type("pop") #type

          if m.group("remain"):
              output_text_type("pop")
              line_class  = None;
              line_indent = None;
              output_text_type("line")
              output_str(EOLN + m.group("remain"))

          want_linefeed = True

      else:
          line_class  = None;
          line_indent = None;
          output_text_type("line")

#          if (using_pcs and (line == PROMPT_PCS)):
#              line = "\n-> "
#              want_linefeed = False
#
#          if (using_pcs and (line != "\n-> ")):
#              output_text_type("args")

          # Not a valid trace statement. Decode other things or output the line

          # Timestamp
          if (not time_format_determined) or old_time_format:
              m = timestamp_re.match(line)
              if m:
                  new_time = int(float(m.group("time"))*100)
                  new_time_highorder = new_time/1000
                  new_last_time = new_time - new_time_highorder*1000
                  if (new_time_highorder != time_highorder):
                      last_time = new_last_time
                      time_highorder = new_time_highorder
                      if (options.debug):
                          print "Time, time_highorder, last_time = ", time, time_highorder, last_time
                      # output_str("Sift time resync:"+EOLN, "warning")

          if ("BEGINNING OF TRACE" in line) or ("END OF TRACE" in line):
              last_time = 0

          # DSID watch and error trap
          #
          # This all needs rewritten and cleaned up. Too many people have been in here.

          m = dsid_trap_re.match(line)
          n = spont_old_new_re.match(line)

          if not m:
              m = dsid_err_re.match(line)

          if m:
              output_str(m.group("prefix"))
              output_number(m.group("dsid"))
              output_str(m.group("suffix"))
              want_linefeed = True
              dsid_trap_line = m.group("prefix") + m.group("dsid") + m.group("suffix")
              if gui: gui.process_events()

          elif n:
              output_text_type("F")
              output_str(n.group("PSTS"))
              output_str(n.group("time"))
              output_str(n.group("str"))
              output_str(" "+n.group("new"))
              new_val = int(n.group("new_value"))
              output_str(n.group("new_value"), "number")
              new_id = machine_states[new_val]
              output_str(" "+new_id + "  ", "named")
              output_str(n.group("old"),"F")
              old_val = int(n.group("old_value"))
              output_str(n.group("old_value"),"F")
              old_id = machine_states[old_val]
              output_str(" "+old_id,"F")
              output_text_type("pop")
              if gui: gui.process_events()


          else:
              # Underware return result
              m = udws_return_re.match(line)
              a = old_new_re.match(line)

              #MAGGIE:
              if m:
                  try:
                      last_underware_cmd = command_parser.last_udws_cmd
                  except (NameError, AttributeError):
                      last_underware_cmd = ""

                  # Checks if last udws cmd was machine state
                  if dsid_machine_state_re.match(last_underware_cmd):
                      try:
                          num = int( m.group("result").strip().split(";")[0])
                          name = m.group("result").replace(str(num), machine_states[num],1).strip()
                          id =  m.group("result").split(";")[0] + ": "
                          output_str(id,"args")
                          output_str(name,"named")
                      except:
                          pass
                  else: # all other underware results

                      if "00001," in line:
                          results = m.group("result").split("00001,",1)
                          output_str(results[0]+"00001,","comment")
                          output_str(results[1],"args")
                      else:
                          output_str(m.group("result"),"args")

                      udws_str_result = m.group("result")  # MAGGIE: if named 'underware_result", others could use
                      output_str(m.group("suffix"),"comment")

                  want_linefeed = True
                  underware_result_seen.set()
                  if gui: gui.process_events()



              ####################### when watch machine_state is called ######################
              ####################### old and new # matches to names ##########################
# This crashes looking up machine_state[] when we get another DSID change
#              elif a:
#                  output_str(a.group("old"))
#                  old_val = int(a.group("old_value"))
#                  output_str(a.group("old_value"), "number")
#                  sys.stdout.write(' ')
#                  old_id2 = machine_states[old_val]
#                  output_str(old_id2, "named")
#                  sys.stdout.write(' ')
#                  output_str(a.group("new"), "none")
#                  new_val = int(a.group("new_value"))
#                  output_str(a.group("new_value"), "number")
#                  new_id2 = machine_states[new_val]
#                  sys.stdout.write(' ')
#                  output_str(new_id2, "named")
#                  if gui: gui.process_events()
#
#
              ################ not sure what this is doing here..........####################
              else:
                  # everything else
                  if line.endswith("\n"):
                      try:
                          matches = (dsids_by_id[dsid_trap_line.split(",")[0].split(" id ")[1]] == "MACHINE_STATE")
                      except:
                          matches = False

                      if matches and old_new_re.match(line):
                          try:
                              line_match = old_new_re.match(line)
                              old_int = int(line_match .group("old_value"))
                              new_int = int(line_match .group("new_value"))
                              old_name = machine_states[old_int]
                              new_name = machine_states[new_int]
                              output_str(line_match .group("old"))
                              output_str(line_match .group("old_value") + ": ","args")
                              output_str(old_name,"named")
                              output_str(line_match .group("new"))
                              output_str(line_match .group("new_value") + ": ","args")
                              output_str(new_name,"named")
                          except:
                              pass
                      else:
                          output_str(line.rstrip())
                      if (ifile_suspect):
                          output_str ("        *****  .i file wrong  *****", "error")
                      want_linefeed = True
                  else:
                      #double udws return..............
                      output_str(line)
                      sys.stdout.flush()

          if printer.port and (not printer.port.running_shell) and (line != PROMPT):
              output_text_type("pop")
      output_text_type("pop") #line

    else:
        # length not > 0
        # if (options.debug): output_str("~", "warning")
        pass

    if (wrap_count == -1):
        output_str ("   [WRAP]", "warning")
        wrap_count = 0

    if want_linefeed:
        output_str(EOLN)

    time_processing += time.clock() - t0


#############################################################################################
#
# HTML Header
#
# All HTML files start with this. It contains the HTML header, dynamic features in
# Javascript, and the CSS styling.
#
#############################################################################################

HTML_HEADER_BLOCK = """<!DOCTYPE HTML>
<html>
<head>
<script type="text/javascript">

// Sift HTML
//
// View with Chrome, Firefox, or Safari. Not compatible with IE.

var element = null;
var starting_element = null;
var sibling = null;
var timeout = null;
var reps_per_cycle = 0;;
var selected_element = null;
var search_for_one;
var search_direction;
var counter = 0;
var history_index = 0;
var MAX_HISTORY_SIZE = 100;

// Indentation level of element
function level(node) {
    var level = null;
    if (node.nodeType == Node.ELEMENT_NODE) {
        if (node.getAttribute) {
            level_str = node.getAttribute("level");
            if (level_str != null) {
                level = +level_str;
            }
        }
    }
    return(level);
}

// Cancel background task
function cancel_timeout() {
    if (timeout != null) {
        clearTimeout(timeout);
        timeout = null;
    }
}

function scroll_to() {
    if (selected_element != null) {
        selected_element.scrollIntoView(true);
        window.scrollBy(0,-300);
    }
}

// position "cursor"
function select(element) {
    if (selected_element != null) {
        selected_element.className = selected_element.className.replace(" select", "");
    }
    selected_element = element;
    if (selected_element.className.indexOf("select") < 0) {
        selected_element.className += " select";
    }
    if (selected_element.className.indexOf("crumb") < 0) {
        selected_element.className += " crumb";
    }
}

// is the flow hidden?
function hidden(flow) {
    var sibling = flow.nextElementSibling;
    while (sibling) {
        if (level(sibling) != null) {
            return(sibling.className.indexOf("show") < 0);
        }
        sibling = sibling.nextElementSibling;
    }
    return(false);
}

// hide the flow
function hide(element) {
    cancel_timeout();
    var element_level = level(element);
    var sibling = element.nextElementSibling;
    var sibling_level;
    while (sibling) {
        sibling_level = level(sibling);
        if (sibling_level != null) {
            if (sibling_level == element_level) {
                break;
            }
            if (sibling_level > element_level) {
                if (sibling.className.indexOf("show") >= 0) {
                   sibling.className = sibling.className.replace(" show", "");
                }
            }
        }
        sibling = sibling.nextElementSibling;
    }
}

// background task to show a flow
var element_level;
var child_level;
var count_element;

var max_counter;
var count_reps_per_cycle;

function get_show_count_continue() {
    var reps = count_reps_per_cycle;
    var progress_element = document.getElementById("progressbar");
    while (count_element) {
        max_counter += 1;
        sibling_level = level(count_element);
        if (sibling_level != null) {
            if (sibling_level <= element_level) {
                break;
            }
        }
        count_element = count_element.nextElementSibling;

        if (--reps <= 0) {
            progress_element.max = max_counter;
            timeout = setTimeout("get_show_count_continue()", 1);
        }
    }
    progress_element.max = max_counter;
}

function show_continue() {
    timeout = null;
    var sibling_level;
    var reps = reps_per_cycle;;
    var progress_element = document.getElementById("progressbar");

    while (sibling) {
        counter += 1;
        sibling_level = level(sibling);
        if (sibling_level != null) {
            if (sibling_level <= element_level) {
                // allow level 0 globals
                if (!((sibling_level == 0) && (sibling.className.indexOf("G") >= 0))) {
                    break;
                }
            }
            if ((sibling_level == child_level) || (sibling_level == 99)) {
                if (sibling.className.indexOf("show") < 0) {
                   sibling.className += " show";
                }
                // sibling.style.display = "block";
            }
        }
        sibling = sibling.nextElementSibling;
        if (--reps <= 0) {
            progress_element.value = counter;
            progress_element.textContent = ((counter/progress_element.max)*100 | 0) + "%";
            reps_per_cycle += 1;
            timeout = setTimeout("show_continue()", 2);
            return;
        }
    }
    progress_element.value = progress_element.max;
    progress_element.textContent = "100%";
}

function show(show_element) {
    cancel_timeout();
    element = show_element;
    sibling = show_element.nextElementSibling;
    element_level = level(element);
    child_level    = element_level + 1;
    var progress_element = document.getElementById("progressbar");
    progress_element.value = 0;
    progress_element.textContent = "0%";

    max_counter = 0;
    count_element = sibling;
    count_reps_per_cycle = 50;
    progress_element.max = 100000;;
    setTimeout("get_show_count_continue()",1);

    counter = 0;
    reps_per_cycle = 1;
    timeout = setTimeout("show_continue()",2);
}


function toggle(event) {
    var element = (event.currentTarget) ? event.currentTarget : event.srcElement;
    var isflow = (element.className.indexOf("F") >= 0);

    select(element);
    if (isflow) {
        if (hidden(element)) {
            show(element);
        } else {
            hide(element);
        }
    }
}

function show_text() {
    var element = document.body.firstElementChild;
    while (element) {
        if (element.className) {
            if (element.className.indexOf("text") >= 0) {
                if (element.className.indexOf("show") < 0) {
                    element.className += " show";
                }
            }
        }
        element = element.nextElementSibling;
    }
}

function hide_text() {
    var element = document.body.firstElementChild;
    while (element) {
        if (element.className) {
            if (element.className.indexOf("text") >= 0) {
                if (element.className.indexOf("show") >= 0) {
                    element.className = element.className.replace(" show","");
                }
                if (element.className.indexOf("hide") < 0) {
                    element.className += " hide";
                }
            }
        }
        element = element.nextElementSibling;
    }
}


function expand_all_continue() {
    var reps = reps_per_cycle;
    var progress_element = document.getElementById("progressbar");
    while (element) {
        counter += 1;
        if (element.className) {
            if (element.className.indexOf("show") < 0) {
                    element.className += " show";
            }
        }
        element = element.previousElementSibling;
        if (--reps == 0) {
            if (progress_element) {
                progress_element.value = counter;
                progress_element.textContent = (counter/document.body.childElementCount*100 | 0) + "%";
            }
            timeout = setTimeout("expand_all_continue()", 5);
            // element.scrollIntoView();
            return;
        }
    }
    if (document.options.autoscroll.checked) {
        scroll_to();
    }
    progress_element.value = progress_element.max;
    progress_element.textContent = "100%";
}

function expand_all() {
    element = document.body.lastElementChild;;

    counter = 0;
    progress_element = document.getElementById("progressbar");
    if (progress_element) {
        progress_element.max = document.body.childElementCount;
        progress_element.value = 0;
    }

    reps_per_cycle = 200;
    setTimeout("expand_all_continue()", 1);
}

function collapse_all() {
    var element = document.body.firstElementChild;
    while (element) {
        if (element.className) {
            if (element.className.indexOf("show") >= 0) {
                if (level(element) > 0) {
                        element.className = element.className.replace(" show", "");
                }
            }
        }
        element = element.nextElementSibling;
    }
}

function clear_highlights() {
    var element = document.body.firstElementChild;
    while (element) {
        if (element.className) {
            if (element.className.indexOf("search") >= 0) {
                element.className = element.className.replace(" search", "");
            }
            if (element.className.indexOf("crumb") >= 0) {
                element.className = element.className.replace(" crumb", "");
            }
        }
        element = element.nextElementSibling;
    }
}

function update_status(value, color) {
    var element = document.getElementById("status");
    element.textContent = value;
    element.style.color = color;
}

function show_parent(me) {
        // find parent
        var my_level = level(me);
        var previous_sibling = me.previousElementSibling;
        while (previous_sibling && (level(previous_sibling) >= my_level)) {
            previous_sibling = previous_sibling.previousElementSibling;
        }
        var parent = previous_sibling;
        if (parent) {
            if (parent.className.indexOf("show") < 0)
                parent.className += " show";
            // show_parent(parent);
        }
}

var found = 0;
var search_text;
var search_regex;

function search_continue() {
    var rep = reps_per_cycle;
    timeout = 0;
    while (element) {
        counter += 1;
        var skip_this_one = false;
        if (element.innerHTML) {
            // if (element.innerHTML.indexOf(search_text) >= 0) {
            if (element.innerHTML.match(search_regex)) {
                if (element.className.indexOf(" r") < 0) {
                    if (search_for_one) {
                        if (element == starting_element) {
                            skip_this_one = true;
                            counter += 1;
                        }
                    }
                    if (!skip_this_one) {
                        found += 1;
                        if (found == 1) {
                            select(element);
                            if (document.options.autoscroll.checked) {
                                scroll_to();
                            }
                        }
                        if (!search_for_one) {
                            if (element.className.indexOf("search") < 0) {
                                element.className += " search";
                            }
                        }
                        show_parent(element);
                        if (search_for_one) {
                            break;
                        }
                    }
                }
            }
        }
        if (search_direction == 1) {
            element = element.nextElementSibling;
            if (element == null) {
                element = document.body.firstElementChild.nextElementSibling;
                need_scroll_to = true;
            }
        } else {
            element = element.previousElementSibling;
            if (element == null) {
                element = document.body.lastElementChild;
                need_scroll_to = true;
            }
        }
        if (element == starting_element) {
            break;
        }
        if (--rep == 0) {
            if (found > 0) {
                update_status (found + " found so far", "brown");
            } else {
                update_status ("0 found so far", "brown");
            }
            progress_element.value = counter;
            progress_element.textContent = (counter/document.body.childElementCount*100 | 0) + "%";
            timeout = setTimeout("search_continue()", 1);
            return;
        }
    }
    progress_element.value = progress_element.max;
    progress_element.textContent = "100%";
    if (found > 0) {
        update_status (found + " found", "green");
    } else {
        update_status ("0 found", "red");
    }
    if (need_scroll_to) {
        scroll_to();
    }
}

function search(text, direction, just_one) {
    found = 0;
    search_text = text;
    counter = 0;
    progress_element = document.getElementById("progressbar");
    progress_element.max = document.body.childElementCount;
    progress_element.value = 0;
    var search_options = "";
    if (!document.options.casesensitive.checked) {
        search_options += "i";
    }
    search_regex = new RegExp(text,search_options);
    need_scroll_to = false;
    search_direction = direction;
    search_for_one = just_one;
    if (selected_element != null) {
        element = selected_element
        if (element == document.body.firstElementChild) {
            element = element.nextElementSibling;
        }
    } else {
        if (direction == 1) {
            element = document.body.firstElementChild.nextElementSibling;
        } else {
            element = document.body.lastElementChild;
        }
    }
    starting_element = element;
    reps_per_cycle = 100;
    timeout = setTimeout("search_continue()", 1);
}

function add_to_history(s) {

   if (s.length > 35) return;

   // determine history size
   var history_size = localStorage["sift.history.size"]
   if (history_size == null) {
       history_size = 0;
   } else {
       history_size = parseInt(history_size)
   }

   // see if duplicate exists near top
   h = 0;
   while (h < 5) {
       if (s == localStorage["sift.history." + h]) {
           return;
       }
       h++;
   }

   // add to storage
   h = history_size;
   while (h > 0) {
       localStorage["sift.history." + h] = localStorage["sift.history." + (h-1)];
       h--;
   }
   localStorage["sift.history.0"] = s;
   if (history_size < MAX_HISTORY_SIZE) {
       localStorage["sift.history.size"] = history_size + 1;
   }

   // add to pull down
   history_elem = document.getElementById("history");
   try {
      history_elem.add(new Option(s,s), history_elem.options[1]);
   }
   catch (e) {  // IE
      history_elem.add(new Option(s,s), 1);
   }
}

function fill_history() {
   var select = document.getElementById("history");

   var history_size = localStorage["sift.history.size"]
   if (history_size == null) {
       history_size = 0;
   } else {
       history_size = parseInt(history_size)
   }

   var i = 0;
   select.options[0] = new Option("        ","        ")
   while (i < history_size) {
       s = localStorage["sift.history." + i]
       select.options[select.options.length] = new Option(s,s)
       i++;
   }
}

function select_history() {
  var history_elem = document.getElementById("history");
  text = history_elem.options[history_elem.selectedIndex].value.replace(/^\s+|\s+$/g,"");
  if (text && (text.length >= 2)) {
      document.getElementById("searchbox").value = text;
      add_to_history(text);
      search(text, 1, false);
  }
}

function search_keypress(e) {
   if (e == 13) {
       key = 13;
   }
   else if (window.event) {  // IE
       key = e.keyCode;
   } else {
       key = e.which;
   }
   if (key == 38) {     // up arrow
       var previous = localStorage["sift.history." + history_index]
       if (previous != null) {
           document.getElementById("searchbox").value = previous;
           history_index += 1;
           e.cancelBubble = true;
           if (e.stopPropagation) e.stopPropagation();
           return false;
       }
   }
   if (key == 40) {     // down arrow
       if (history_index > 0)
           history_index -= 1;
       next = localStorage["sift.history." + history_index]
       if (next != null) {
           document.getElementById("searchbox").value = next;
           e.cancelBubble = true;
           if (e.stopPropagation) e.stopPropagation();
           return false;
       }
   }
   if (key == 13) {
       var text = document.getElementById("searchbox").value.replace(/^\s+|\s+$/g,"");
       if (text && (text.length >= 2)) {
           add_to_history(text);
           history_index = 0;
           document.getElementById("history").selectedIndex = 0;
           search(text, 1, false);
       }
   }
}

function next(direction) {
    var text = document.getElementById("searchbox").value;
    search(text, direction, true);
}

function load() {
    fill_history();
}

</script>

<style>
body  {color:grey; font-family:monospace; font-size:10pt; background-color:Ivory;}
body>div[level] {height:1.2em;margin:0; padding:0; white-space:pre;display:none;}
body>div[level="0"]  {display:block;}
body>span {display:none;}
.i {color:red; font-weight:normal;}
.F {color:black; font-weight:bold; cursor:pointer}
.G {color:green;}
.K {color:MediumBlue;}
.r {color:black;}
.time {color:grey; font-weight:normal;}
.args {color:blue; font-weight:normal;}
.number {color:red;}
.named {color:magenta;}
.comment {font-style:italic;}
body>div[level].text {display:none;}
body>div[level].show {display:block;}
body>div[level].crumb {display:block !important;}
body>div[level].search {display:block; background-color:Aquamarine;}
.select {
    background: Khaki !important;
    display:block !important;
}
.crumb .time {background-color:Khaki;}
.text.crumb {background-color:Khaki;}
#panel #status {
    color: green;
    height: 1em;
    width:100%;
}

#panel {
    float:right;
    text-align: center;
    position:fixed;
    top:0;right:0;
    padding:2px;
    background: rgba(139,119,101,0.1);
    border-left: 1px solid rgba(139,119,101,0.2);
    border-bottom: 1px solid rgba(139,119,101,0.2);
    color: black;
    margin-top: 1px;
}

#searchbox {
   text-align: center;
   background: rgba(255,255,255,0.7);
}

#panel button {
    background-color: rgb(220,220,255);
    opacity: 0.7;
    padding: 0;
    margin-top: 1px;
}
#panel button:hover {
    background-color: rgb(210,210,255);
}
#panel button:active {
    background-color: rgb(150,150,255);
}

#searchcmds button {
   width: 60px;
   border: 1px solid darkblue;
   background: pink;
   margin-top:5px;
}

#history {
   opacity: 0.5;
   font-size: 10px;
   margin-bottom:5px;
}

#collapse button {
   width: 128px;
   border: 1px solid darkgreen;
}

#clear button {
   width: 128px;
   border: 1px solid darkred;
}

#info {
    margin-top:1px;
    color: black;
    font-size: small;
    text-align: right;
    opacity:0.5;
}

meter {
   width: 128px;
   height: 1.2em;
}

#iewarning:first-line {
   color: red;
   font-size: large;
   font-weight: bold;
   border: 1px solid red;
}

</style>
</head>

<body id=mybody onload="load()">

<div id=panel>
 <div id=searchline>
  <input type="text" name="siftsearch" id="searchbox" size=30 onkeydown="search_keypress(event)">
 </div>
 <div id=historyline>
  <select id="history" onChange="select_history()"></select>
 </div>
 <div id=statusline>
   <span id=status>Welcome to Sift</span>
 </div>
 <!--[if IE]>
 <div id=iewarning>
     Not compatible with IE<br/>
     Use <a href="http://www.google.com/chrome">Google Chrome</a>
 </div>
 <![endif]-->
 <div id=searchcmds>
  <button title="Show all matches" onclick="search_keypress(13)">Find All</button>
  <button title="Find next match" onclick="next(1)">Next</button>
  <button title="Find previous match" onclick="next(-1)">Prev</button>
  <button title="Scroll selection onto screen" onclick="scroll_to()">ScrollTo</button>
 </div>
 <div id=collapse>
  <button title="Expand all flows" onclick="expand_all()">Expand All</button>
  <button title="Show all debug text" onclick="show_text()">Show All Text</button>
 </div>
 <div id=clear>
  <button title="Collapse all flows" onclick="collapse_all()">Collapse All</button>
  <button title="Clear searches and bread crumbs" onclick="clear_highlights()">Clear Highlights</button>
 </div>
 <div id=info>
   <meter id="progressbar">0%</meter>
   <form name="options">
     Auto ScrollTo <input title="After search, scroll window" type="checkbox" checked name="autoscroll" value=yes/><br/>
     Case Sensitive <input title="Case sensitive searching" type="checkbox" name="casesensitive" value=yes/>
   </form>
 </div>
</div>
"""


#############################################################################################
#
# Process a raw trace file
#
# Basically we run each line of the file through the process_line() function above just as
# if it came from the printer live.
#
#############################################################################################

# Swap words in the coredump input file
def swap (input_filename, output_filename):
    try:
        input  = open(input_filename, "rb")
    except:
        output_str(EOLN+"Bin file '"+str(input_filename)+"' couldn't be opened"+EOLN,text_type="error")
        raise
    try:
        output = open (output_filename, "wb")
    except:
        output_str(EOLN+"Couldn't write "+str(output_filename)+
                " while processing coredump, maybe need write access."+EOLN,text_type="error")
        exit()

    a = input.read(1)
    while (a):
        b = input.read(1)
        c = input.read(1)
        d = input.read(1)
        output.write(d)
        output.write(c)
        output.write(b)
        output.write(a)
        a = input.read(1)
    input.close()
    output.close()

# Process a data file
def process_file(data_filename):
    global wrap_count
    wrap_count = 0                          # process_line() sets hold_count if data has wrapped

    if (".bin" in data_filename):           # coredump is word swapped, convert to normal raw file
        try:
            swap(data_filename, RAW_OUTPUT_FILE)
        except:
            return

        data_filename = RAW_OUTPUT_FILE
    try:
        f = open(data_filename, "r")
    except:
        try:
            f = open(os.path.join(dir_sift_started_in,data_filename), "r")
        except:
            output_str(EOLN + "Raw file '" + str(data_filename) + "' couldn't be opened" +EOLN, text_type="error")
            return

    hold_queue = collections.deque()        # create fifo to hold wrapped data
    for line in f:
        if (not chr(0) in line):
            if (wrap_count > 0):                # detected data has wrapped, save it for later
                hold_queue.append(line)
                wrap_count = wrap_count - 1
            else:
                process_line(line)
    if (len(hold_queue) > 0):
        wrap_count = -1;
        for line in hold_queue:                 # now process the wrapped data
            process_line(line)
    f.close()


###################################################################################
#
# Revision Updater
#
# Occasionally we want to change startup files, ini files, rc files, etc.
# This gives us a chance to rename old files we used to use to the new
# files.
#
###################################################################################

# Update user's environment from old versions of Sift
def update_old_files():
    from_name = os.path.join(SIFT_CONFIG_DIR, "startup.txt")
    to_name   = os.path.join(SIFT_CONFIG_DIR, STARTUP_FILE)
    if not os.path.exists(to_name):
        try:
            os.rename(from_name, to_name)
            print "Renamed", from_name, "to", to_name
        except OSError: pass

    from_name = "startup.txt"
    to_name   = STARTUP_FILE
    if not os.path.exists(to_name):
        try:
            os.rename(from_name, to_name)
            print "Renamed", from_name, "to", to_name
        except OSError: pass

    from_name = os.path.join(SIFT_CONFIG_DIR,"siftrc")
    to_name   = os.path.join(SIFT_CONFIG_DIR,STARTUP_FILE)
    if not os.path.exists(to_name):
        try:
            os.rename(from_name, to_name)
            print "Renamed", from_name, "to", to_name
        except OSError: pass

    from_name = "siftrc"
    to_name   = STARTUP_FILE
    if not os.path.exists(to_name):
        try:
            os.rename(from_name, to_name)
            print "Renamed", from_name, "to", to_name
        except OSError: pass

    from_name = os.path.join(SIFT_CONFIG_DIR,"sift.history")
    to_name   = os.path.join(SIFT_CONFIG_DIR,HISTORY_FILE)
    if not os.path.exists(to_name):
        try:
            os.rename(from_name, to_name)
            print "Renamed", from_name, "to", to_name
        except OSError: pass

    try: os.remove(os.path.join(SIFT_CONFIG_DIR,"siftout_replay_trace.fml"))
    except OSError: pass

    try: os.remove(os.path.join(SIFT_CONFIG_DIR,"gsift.css"))
    except OSError: pass

    try: os.remove(os.path.join(SIFT_CONFIG_DIR,"sift.html"))
    except OSError: pass

    try:
        os.remove("siftout_replay_trace.fml")
    except OSError: pass


    ##################### don't need anymore ########################
#    try:
#        os.remove(os.path.join(SIFT_CONFIG_DIR, HTML_HEADER_FILE))
#    except OSError: pass
    #################################################################



############################################################################
#
# Initialize .sift directory
#
# Check if the user has a .sift directory, create as needed, and set
# defaults.
#
# MAJOR KLUDGE HERE: The HTML/CSS/Javascript code for HTML files shouldn't
# be here !!  It was here because it happened to be convenient when
# experimenting.
#
############################################################################

def check_for_sift_directory():
    if not os.path.exists(SIFT_CONFIG_DIR):
        try:
            os.mkdir(SIFT_CONFIG_DIR)
        except: pass

    if not os.path.exists(os.path.join(SIFT_CONFIG_DIR,STARTUP_FILE)):
        try:
            f = open(os.path.join(SIFT_CONFIG_DIR,STARTUP_FILE), 'w')
            f.write("# Sift startup commands\n")
            f.close
        except: pass

    if not os.path.exists(os.path.join(SIFT_CONFIG_DIR, SIFT_INI)):
        try:
            f = open(os.path.join(SIFT_CONFIG_DIR, SIFT_INI), 'w')
            f.write( """# Sift defaults
[Arguments]
# serial port (Use 0, 1, 2 or /dev/foo [default: 0])
#port=
# html file
#html=True

[Max_Output_File_Size]
#Default 200MB
#maxSize =
"""
)
            f.close
        except: pass


##################################################################################################
##################################################################################################
##                                                                                              ##
## Sift GUI                                                                                     ##
##                                                                                              ##
## PyQt (Qt4) GUI code to provide two types of graphical user interfaces to the user.           ##
## --qt is a basic control panel that compliments the textual trace output, giving the user     ##
## common commands and programmable favorites. --QT extends this to include the live            ##
## trace data.                                                                                  ##
##                                                                                              ##
## Both of these are automagically dependent and only used if PyQt4 has been installed with     ##
## Qt4. PyQt4 is support on Windows, Linux, and Mac.
##                                                                                              ##
##################################################################################################
##################################################################################################

def X_is_running():
    from subprocess import Popen, PIPE
    p = Popen(["xset", "-q"], stdout=PIPE, stderr=PIPE)
    p.communicate()
    return p.returncode == 0

if (not QtGui) or (not SiftWidget):
    class Gui():
      def __init__ (self):
        raise ImportError
else:

  ###################################
  ## BufferView Widget             ##
  ###################################

  # This number may be larger than that defined below, since the C++ widget
  # gets much better performance regardless of buffer size
  GUI_DEFAULT_LINES = 100000

  class BufferView(SiftWidget.BufferView):
      def __init__(self, maxLines = GUI_DEFAULT_LINES, parent = None):
          SiftWidget.BufferView.__init__(self, maxLines, parent)

          self.forwardKeyEvent.connect(self.forwardedKeyPressEvent)
          self.forwardPasteEvent.connect(self.forwardedPasteEvent)
          self.editFlow.connect(self.forwardedEditFlow)

      def paintEvent(self, event):
          global time_painting
          global paint_count
          t0 = time.clock()
          SiftWidget.BufferView.paintEvent(self, event)
          paint_count += 1
          time_painting += time.clock() - t0

      def forwardedKeyPressEvent(self, event):
          gui.ui.input.lineEdit().setFocus()
          QtGui.QApplication.sendEvent(gui.ui.input.lineEdit(), event)

      def forwardedPasteEvent(self, text):
          gui.ui.input.lineEdit().paste()
          gui.ui.input.lineEdit().setFocus()

      def forwardedEditFlow(self, text):
          gui.sf_displayFlow(text)

      def insertPlainText(self, text):
          global line_indent
          indent = line_indent
          if indent == 99 or indent is None:
              indent = -1
          self.addText(text, indent)

  class ColorFrame(QtGui.QFrame):
    colorChanged = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, parent):
        QtGui.QFrame.__init__(self, parent)

        # Qt automatically calculates the right highlights and shadows
        # when constructing a palette with a single base color
        self.setAutoFillBackground(True)
        self.setFrameShape(QtGui.QFrame.StyledPanel)

        self.inClick = False

    def setColor(self, color):
        self.setPalette(QtGui.QPalette(color))
        self.colorChanged.emit(color)

    def color(self):
        return self.palette().color(QtGui.QPalette.Button)

    def _pickColor(self):
        color = QtGui.QColorDialog.getColor(self.color())
        if color.isValid():
            self.setColor(color)

    def mousePressEvent(self, event):
        self.inClick = (event.button() == QtCore.Qt.LeftButton and \
                        self.rect().contains(event.pos()))

    def mouseReleaseEvent(self, event):
        if not self.inClick:
            return
        self.inClick = False;

        if event.button() == QtCore.Qt.LeftButton and self.rect().contains(event.pos()):
            self._pickColor()



  ########################################
  ## Qt Designer Results                ##
  ##                                    ##
  ## AUTO GENERATED - DO NOT EDIT       ##
  ########################################


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'connect.ui'
#
# Created: Tue Nov  1 15:58:36 2011
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

  try:
    _fromUtf8 = QtCore.QString.fromUtf8
  except AttributeError:
    _fromUtf8 = lambda s: s

  class Ui_ConnectDialog(object):
    def setupUi(self, ConnectDialog):
        ConnectDialog.setObjectName(_fromUtf8("ConnectDialog"))
        ConnectDialog.resize(567, 207)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ConnectDialog.sizePolicy().hasHeightForWidth())
        ConnectDialog.setSizePolicy(sizePolicy)
        ConnectDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(ConnectDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(ConnectDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.serial_radio = QtGui.QRadioButton(ConnectDialog)
        self.serial_radio.setChecked(True)
        self.serial_radio.setObjectName(_fromUtf8("serial_radio"))
        self.gridLayout.addWidget(self.serial_radio, 0, 0, 1, 1)
        self.serial_port = QtGui.QComboBox(ConnectDialog)
        self.serial_port.setEditable(True)
        self.serial_port.setObjectName(_fromUtf8("serial_port"))
        self.gridLayout.addWidget(self.serial_port, 0, 1, 1, 1)
        self.usb_radio = QtGui.QRadioButton(ConnectDialog)
        self.usb_radio.setObjectName(_fromUtf8("usb_radio"))
        self.gridLayout.addWidget(self.usb_radio, 1, 0, 1, 1)
        self.ip_radio = QtGui.QRadioButton(ConnectDialog)
        self.ip_radio.setObjectName(_fromUtf8("ip_radio"))
        self.gridLayout.addWidget(self.ip_radio, 3, 0, 1, 1)
        self.ip_port = QtGui.QComboBox(ConnectDialog)
        self.ip_port.setEditable(True)
        self.ip_port.setMaxVisibleItems(40)
        self.ip_port.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
        self.ip_port.setObjectName(_fromUtf8("ip_port"))
        self.gridLayout.addWidget(self.ip_port, 3, 1, 1, 1)
        self.pcs_radio = QtGui.QRadioButton(ConnectDialog)
        self.pcs_radio.setObjectName(_fromUtf8("pcs_radio"))
        self.gridLayout.addWidget(self.pcs_radio, 2, 0, 1, 1)
        self.pcs_port = QtGui.QComboBox(ConnectDialog)
        self.pcs_port.setEditable(True)
        self.pcs_port.setObjectName(_fromUtf8("pcs_port"))
        self.gridLayout.addWidget(self.pcs_port, 2, 1, 1, 1)
        self.noconn_radio = QtGui.QRadioButton(ConnectDialog)
        self.noconn_radio.setObjectName(_fromUtf8("noconn_radio"))
        self.gridLayout.addWidget(self.noconn_radio, 4, 0, 1, 1)
        self.usb_port = QtGui.QComboBox(ConnectDialog)
        self.usb_port.setEditable(True)
        self.usb_port.setObjectName(_fromUtf8("usb_port"))
        self.gridLayout.addWidget(self.usb_port, 1, 1, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 3)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.port_refresh = QtGui.QPushButton(ConnectDialog)
        self.port_refresh.setObjectName(_fromUtf8("port_refresh"))
        self.horizontalLayout.addWidget(self.port_refresh)
        self.port_start_pcs = QtGui.QPushButton(ConnectDialog)
        self.port_start_pcs.setObjectName(_fromUtf8("port_start_pcs"))
        self.horizontalLayout.addWidget(self.port_start_pcs)
        self.port_ok = QtGui.QDialogButtonBox(ConnectDialog)
        self.port_ok.setOrientation(QtCore.Qt.Horizontal)
        self.port_ok.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.port_ok.setObjectName(_fromUtf8("port_ok"))
        self.horizontalLayout.addWidget(self.port_ok)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(ConnectDialog)
        QtCore.QObject.connect(self.port_ok, QtCore.SIGNAL(_fromUtf8("accepted()")), ConnectDialog.accept)
        QtCore.QObject.connect(self.port_ok, QtCore.SIGNAL(_fromUtf8("rejected()")), ConnectDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ConnectDialog)

    def retranslateUi(self, ConnectDialog):
        ConnectDialog.setWindowTitle(QtGui.QApplication.translate("ConnectDialog", "IO Connection", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ConnectDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\'; font-size:18pt;\">Connect via:</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.serial_radio.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Connect to a serial port on your computer.", None, QtGui.QApplication.UnicodeUTF8))
        self.serial_radio.setText(QtGui.QApplication.translate("ConnectDialog", "Serial Port", None, QtGui.QApplication.UnicodeUTF8))
        self.serial_port.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Select a serial port", None, QtGui.QApplication.UnicodeUTF8))
        self.usb_radio.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Connect via USB directly (only available for sending files on Linux)", None, QtGui.QApplication.UnicodeUTF8))
        self.usb_radio.setText(QtGui.QApplication.translate("ConnectDialog", "USB directly", None, QtGui.QApplication.UnicodeUTF8))
        self.ip_radio.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Connect over network or wireless.", None, QtGui.QApplication.UnicodeUTF8))
        self.ip_radio.setText(QtGui.QApplication.translate("ConnectDialog", "Network", None, QtGui.QApplication.UnicodeUTF8))
        self.ip_port.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Enter an IP address", None, QtGui.QApplication.UnicodeUTF8))
        self.pcs_radio.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Connect with USB using the PCS driver (which must be installed).", None, QtGui.QApplication.UnicodeUTF8))
        self.pcs_radio.setText(QtGui.QApplication.translate("ConnectDialog", "USB using the PCS driver", None, QtGui.QApplication.UnicodeUTF8))
        self.pcs_port.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Select a discovered printer", None, QtGui.QApplication.UnicodeUTF8))
        self.noconn_radio.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Run without a connection.", None, QtGui.QApplication.UnicodeUTF8))
        self.noconn_radio.setText(QtGui.QApplication.translate("ConnectDialog", "No connection", None, QtGui.QApplication.UnicodeUTF8))
        self.usb_port.setToolTip(QtGui.QApplication.translate("ConnectDialog", "Select a USB device", None, QtGui.QApplication.UnicodeUTF8))
        self.port_refresh.setText(QtGui.QApplication.translate("ConnectDialog", "Refresh", None, QtGui.QApplication.UnicodeUTF8))
        self.port_start_pcs.setText(QtGui.QApplication.translate("ConnectDialog", "Start PCS", None, QtGui.QApplication.UnicodeUTF8))



# end connect.ui


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sift.ui'
#
# Created: Wed Sep 12 15:03:05 2012
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

  try:
    _fromUtf8 = QtCore.QString.fromUtf8
  except AttributeError:
    _fromUtf8 = lambda s: s

  class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(784, 700)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        MainWindow.setFont(font)
        self.MainWidget = QtGui.QWidget(MainWindow)
        self.MainWidget.setObjectName(_fromUtf8("MainWidget"))
        self.gridlayout = QtGui.QGridLayout(self.MainWidget)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(3)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.Tabs = QtGui.QTabWidget(self.MainWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Tabs.sizePolicy().hasHeightForWidth())
        self.Tabs.setSizePolicy(sizePolicy)
        self.Tabs.setObjectName(_fromUtf8("Tabs"))
        self.CommandsTab = QtGui.QWidget()
        self.CommandsTab.setObjectName(_fromUtf8("CommandsTab"))
        self.gridlayout1 = QtGui.QGridLayout(self.CommandsTab)
        self.gridlayout1.setMargin(0)
        self.gridlayout1.setSpacing(3)
        self.gridlayout1.setObjectName(_fromUtf8("gridlayout1"))
        self.FMTrace = QtGui.QGroupBox(self.CommandsTab)
        self.FMTrace.setObjectName(_fromUtf8("FMTrace"))
        self.FMTraceLayout = QtGui.QGridLayout(self.FMTrace)
        self.FMTraceLayout.setMargin(1)
        self.FMTraceLayout.setSpacing(2)
        self.FMTraceLayout.setObjectName(_fromUtf8("FMTraceLayout"))
        self.on = QtGui.QPushButton(self.FMTrace)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.on.sizePolicy().hasHeightForWidth())
        self.on.setSizePolicy(sizePolicy)
        self.on.setObjectName(_fromUtf8("on"))
        self.FMTraceLayout.addWidget(self.on, 0, 0, 1, 1)
        self.tock = QtGui.QPushButton(self.FMTrace)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tock.sizePolicy().hasHeightForWidth())
        self.tock.setSizePolicy(sizePolicy)
        self.tock.setObjectName(_fromUtf8("tock"))
        self.FMTraceLayout.addWidget(self.tock, 4, 1, 1, 1)
        self.nosweep = QtGui.QPushButton(self.FMTrace)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nosweep.sizePolicy().hasHeightForWidth())
        self.nosweep.setSizePolicy(sizePolicy)
        self.nosweep.setObjectName(_fromUtf8("nosweep"))
        self.FMTraceLayout.addWidget(self.nosweep, 4, 0, 1, 1)
        self.tick = QtGui.QPushButton(self.FMTrace)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tick.sizePolicy().hasHeightForWidth())
        self.tick.setSizePolicy(sizePolicy)
        self.tick.setObjectName(_fromUtf8("tick"))
        self.FMTraceLayout.addWidget(self.tick, 4, 2, 1, 1)
        self.off = QtGui.QPushButton(self.FMTrace)
        self.off.setObjectName(_fromUtf8("off"))
        self.FMTraceLayout.addWidget(self.off, 0, 1, 1, 1)
        self.get = QtGui.QPushButton(self.FMTrace)
        self.get.setObjectName(_fromUtf8("get"))
        self.FMTraceLayout.addWidget(self.get, 0, 2, 1, 2)
        self.reset = QtGui.QPushButton(self.FMTrace)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reset.sizePolicy().hasHeightForWidth())
        self.reset.setSizePolicy(sizePolicy)
        self.reset.setStyleSheet(_fromUtf8("color: rgb(0, 130, 0);"))
        self.reset.setObjectName(_fromUtf8("reset"))
        self.FMTraceLayout.addWidget(self.reset, 4, 3, 1, 1)
        self.label_5 = QtGui.QLabel(self.FMTrace)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_5.setFont(font)
        self.label_5.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.FMTraceLayout.addWidget(self.label_5, 6, 0, 1, 1)
        self.depth = QtGui.QSlider(self.FMTrace)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.depth.sizePolicy().hasHeightForWidth())
        self.depth.setSizePolicy(sizePolicy)
        self.depth.setMinimum(1)
        self.depth.setMaximum(10)
        self.depth.setPageStep(1)
        self.depth.setProperty(_fromUtf8("value"), 10)
        self.depth.setSliderPosition(10)
        self.depth.setTracking(False)
        self.depth.setOrientation(QtCore.Qt.Horizontal)
        self.depth.setTickPosition(QtGui.QSlider.TicksAbove)
        self.depth.setTickInterval(1)
        self.depth.setObjectName(_fromUtf8("depth"))
        self.FMTraceLayout.addWidget(self.depth, 7, 0, 1, 1)
        self.label_4 = QtGui.QLabel(self.FMTrace)
        self.label_4.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_4.setFont(font)
        self.label_4.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.FMTraceLayout.addWidget(self.label_4, 6, 1, 1, 3)
        self.single = QtGui.QComboBox(self.FMTrace)
        self.single.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.single.sizePolicy().hasHeightForWidth())
        self.single.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.single.setFont(font)
        self.single.setEditable(True)
        self.single.setMaxVisibleItems(80)
        self.single.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.single.setObjectName(_fromUtf8("single"))
        self.FMTraceLayout.addWidget(self.single, 7, 1, 1, 3)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.FMTraceLayout.addItem(spacerItem, 5, 0, 1, 1)
        self.horizontalLayout_13 = QtGui.QHBoxLayout()
        self.horizontalLayout_13.setObjectName(_fromUtf8("horizontalLayout_13"))
        self.flows_check = QtGui.QCheckBox(self.FMTrace)
        self.flows_check.setMaximumSize(QtCore.QSize(16777215, 15))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.flows_check.setFont(font)
        self.flows_check.setChecked(True)
        self.flows_check.setObjectName(_fromUtf8("flows_check"))
        self.horizontalLayout_13.addWidget(self.flows_check)
        self.globals_check = QtGui.QCheckBox(self.FMTrace)
        self.globals_check.setMaximumSize(QtCore.QSize(16777215, 15))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.globals_check.setFont(font)
        self.globals_check.setChecked(True)
        self.globals_check.setObjectName(_fromUtf8("globals_check"))
        self.horizontalLayout_13.addWidget(self.globals_check)
        self.locals_check = QtGui.QCheckBox(self.FMTrace)
        self.locals_check.setMaximumSize(QtCore.QSize(16777215, 15))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.locals_check.setFont(font)
        self.locals_check.setChecked(True)
        self.locals_check.setObjectName(_fromUtf8("locals_check"))
        self.horizontalLayout_13.addWidget(self.locals_check)
        self.keywords_check = QtGui.QCheckBox(self.FMTrace)
        self.keywords_check.setMaximumSize(QtCore.QSize(16777215, 15))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.keywords_check.setFont(font)
        self.keywords_check.setChecked(True)
        self.keywords_check.setObjectName(_fromUtf8("keywords_check"))
        self.horizontalLayout_13.addWidget(self.keywords_check)
        self.startup_check = QtGui.QCheckBox(self.FMTrace)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.startup_check.setFont(font)
        self.startup_check.setObjectName(_fromUtf8("startup_check"))
        self.horizontalLayout_13.addWidget(self.startup_check)
        self.slow_check = QtGui.QCheckBox(self.FMTrace)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.slow_check.setFont(font)
        self.slow_check.setObjectName(_fromUtf8("slow_check"))
        self.horizontalLayout_13.addWidget(self.slow_check)
        self.FMTraceLayout.addLayout(self.horizontalLayout_13, 1, 0, 1, 4)
        self.gridlayout1.addWidget(self.FMTrace, 0, 1, 1, 1)
        self.FMDebug = QtGui.QGroupBox(self.CommandsTab)
        self.FMDebug.setObjectName(_fromUtf8("FMDebug"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.FMDebug)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setMargin(0)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.flow_break = QtGui.QComboBox(self.FMDebug)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.flow_break.setFont(font)
        self.flow_break.setEditable(True)
        self.flow_break.setMaxVisibleItems(80)
        self.flow_break.setObjectName(_fromUtf8("flow_break"))
        self.verticalLayout_4.addWidget(self.flow_break)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.global_break = QtGui.QComboBox(self.FMDebug)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.global_break.setFont(font)
        self.global_break.setEditable(True)
        self.global_break.setMaxVisibleItems(80)
        self.global_break.setObjectName(_fromUtf8("global_break"))
        self.horizontalLayout.addWidget(self.global_break)
        self.global_break_value = QtGui.QComboBox(self.FMDebug)
        self.global_break_value.setMaximumSize(QtCore.QSize(60, 16777215))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.global_break_value.setFont(font)
        self.global_break_value.setEditable(True)
        self.global_break_value.setObjectName(_fromUtf8("global_break_value"))
        self.horizontalLayout.addWidget(self.global_break_value)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setSpacing(2)
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.fmstep = QtGui.QPushButton(self.FMDebug)
        self.fmstep.setObjectName(_fromUtf8("fmstep"))
        self.horizontalLayout_7.addWidget(self.fmstep)
        self.fmreturn = QtGui.QPushButton(self.FMDebug)
        self.fmreturn.setObjectName(_fromUtf8("fmreturn"))
        self.horizontalLayout_7.addWidget(self.fmreturn)
        self.verticalLayout_4.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtGui.QHBoxLayout()
        self.horizontalLayout_8.setSpacing(2)
        self.horizontalLayout_8.setObjectName(_fromUtf8("horizontalLayout_8"))
        self.fmnext = QtGui.QPushButton(self.FMDebug)
        self.fmnext.setObjectName(_fromUtf8("fmnext"))
        self.horizontalLayout_8.addWidget(self.fmnext)
        self.fmbt = QtGui.QPushButton(self.FMDebug)
        self.fmbt.setObjectName(_fromUtf8("fmbt"))
        self.horizontalLayout_8.addWidget(self.fmbt)
        self.verticalLayout_4.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtGui.QHBoxLayout()
        self.horizontalLayout_9.setSpacing(2)
        self.horizontalLayout_9.setObjectName(_fromUtf8("horizontalLayout_9"))
        self.fmgo = QtGui.QPushButton(self.FMDebug)
        self.fmgo.setObjectName(_fromUtf8("fmgo"))
        self.horizontalLayout_9.addWidget(self.fmgo)
        self.fmclear = QtGui.QPushButton(self.FMDebug)
        self.fmclear.setObjectName(_fromUtf8("fmclear"))
        self.horizontalLayout_9.addWidget(self.fmclear)
        self.verticalLayout_4.addLayout(self.horizontalLayout_9)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem1)
        self.gridlayout1.addWidget(self.FMDebug, 0, 2, 1, 1)
        self.Printer = QtGui.QGroupBox(self.CommandsTab)
        self.Printer.setObjectName(_fromUtf8("Printer"))
        self.PrinterLayout = QtGui.QGridLayout(self.Printer)
        self.PrinterLayout.setMargin(1)
        self.PrinterLayout.setSpacing(2)
        self.PrinterLayout.setObjectName(_fromUtf8("PrinterLayout"))
        self.rev = QtGui.QPushButton(self.Printer)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rev.sizePolicy().hasHeightForWidth())
        self.rev.setSizePolicy(sizePolicy)
        self.rev.setObjectName(_fromUtf8("rev"))
        self.PrinterLayout.addWidget(self.rev, 0, 0, 1, 1)
        self.tap = QtGui.QComboBox(self.Printer)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.tap.setFont(font)
        self.tap.setEditable(True)
        self.tap.setMaxVisibleItems(40)
        self.tap.setObjectName(_fromUtf8("tap"))
        self.PrinterLayout.addWidget(self.tap, 9, 0, 1, 1)
        self.label_tap = QtGui.QLabel(self.Printer)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_tap.setFont(font)
        self.label_tap.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.label_tap.setObjectName(_fromUtf8("label_tap"))
        self.PrinterLayout.addWidget(self.label_tap, 8, 0, 1, 1)
        self.state = QtGui.QPushButton(self.Printer)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.state.sizePolicy().hasHeightForWidth())
        self.state.setSizePolicy(sizePolicy)
        self.state.setObjectName(_fromUtf8("state"))
        self.PrinterLayout.addWidget(self.state, 4, 0, 1, 1)
        self.pwron = QtGui.QPushButton(self.Printer)
        self.pwron.setObjectName(_fromUtf8("pwron"))
        self.PrinterLayout.addWidget(self.pwron, 0, 1, 1, 1)
        self.dooropen = QtGui.QPushButton(self.Printer)
        self.dooropen.setObjectName(_fromUtf8("dooropen"))
        self.PrinterLayout.addWidget(self.dooropen, 4, 1, 1, 1)
        self.ok = QtGui.QPushButton(self.Printer)
        self.ok.setObjectName(_fromUtf8("ok"))
        self.PrinterLayout.addWidget(self.ok, 0, 2, 1, 1)
        self.doorclose = QtGui.QPushButton(self.Printer)
        self.doorclose.setObjectName(_fromUtf8("doorclose"))
        self.PrinterLayout.addWidget(self.doorclose, 4, 2, 1, 1)
        self.vtap = QtGui.QComboBox(self.Printer)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.vtap.setFont(font)
        self.vtap.setEditable(True)
        self.vtap.setMaxVisibleItems(40)
        self.vtap.setObjectName(_fromUtf8("vtap"))
        self.PrinterLayout.addWidget(self.vtap, 9, 1, 1, 1)
        self.component = QtGui.QComboBox(self.Printer)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.component.setFont(font)
        self.component.setEditable(True)
        self.component.setMaxVisibleItems(40)
        self.component.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
        self.component.setObjectName(_fromUtf8("component"))
        self.PrinterLayout.addWidget(self.component, 9, 2, 1, 1)
        self.label_virtual = QtGui.QLabel(self.Printer)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_virtual.setFont(font)
        self.label_virtual.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.label_virtual.setObjectName(_fromUtf8("label_virtual"))
        self.PrinterLayout.addWidget(self.label_virtual, 8, 1, 1, 1)
        self.label_ondebug = QtGui.QLabel(self.Printer)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_ondebug.setFont(font)
        self.label_ondebug.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.label_ondebug.setObjectName(_fromUtf8("label_ondebug"))
        self.PrinterLayout.addWidget(self.label_ondebug, 8, 2, 1, 1)
        self.status2 = QtGui.QLabel(self.Printer)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.status2.setFont(font)
        self.status2.setStyleSheet(_fromUtf8("color:blue"))
        self.status2.setText(_fromUtf8(""))
        self.status2.setAlignment(QtCore.Qt.AlignCenter)
        self.status2.setMargin(2)
        self.status2.setObjectName(_fromUtf8("status2"))
        self.PrinterLayout.addWidget(self.status2, 6, 0, 1, 3)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.PrinterLayout.addItem(spacerItem2, 7, 0, 1, 1)
        self.gridlayout1.addWidget(self.Printer, 0, 0, 1, 1)
        self.gridlayout1.setColumnStretch(0, 2)
        self.gridlayout1.setColumnStretch(1, 3)
        self.gridlayout1.setColumnStretch(2, 3)
        self.Tabs.addTab(self.CommandsTab, _fromUtf8(""))
        self.UserTab = QtGui.QWidget()
        self.UserTab.setObjectName(_fromUtf8("UserTab"))
        self.hboxlayout = QtGui.QHBoxLayout(self.UserTab)
        self.hboxlayout.setSpacing(3)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.gridlayout2 = QtGui.QGridLayout()
        self.gridlayout2.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.gridlayout2.setSpacing(2)
        self.gridlayout2.setObjectName(_fromUtf8("gridlayout2"))
        self.send0 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send0.sizePolicy().hasHeightForWidth())
        self.send0.setSizePolicy(sizePolicy)
        self.send0.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send0.setObjectName(_fromUtf8("send0"))
        self.gridlayout2.addWidget(self.send0, 0, 0, 1, 1)
        self.user0 = QtGui.QLineEdit(self.UserTab)
        self.user0.setObjectName(_fromUtf8("user0"))
        self.gridlayout2.addWidget(self.user0, 0, 1, 1, 1)
        self.send1 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send1.sizePolicy().hasHeightForWidth())
        self.send1.setSizePolicy(sizePolicy)
        self.send1.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send1.setObjectName(_fromUtf8("send1"))
        self.gridlayout2.addWidget(self.send1, 1, 0, 1, 1)
        self.user1 = QtGui.QLineEdit(self.UserTab)
        self.user1.setObjectName(_fromUtf8("user1"))
        self.gridlayout2.addWidget(self.user1, 1, 1, 1, 1)
        self.send2 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send2.sizePolicy().hasHeightForWidth())
        self.send2.setSizePolicy(sizePolicy)
        self.send2.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send2.setObjectName(_fromUtf8("send2"))
        self.gridlayout2.addWidget(self.send2, 2, 0, 1, 1)
        self.user2 = QtGui.QLineEdit(self.UserTab)
        self.user2.setObjectName(_fromUtf8("user2"))
        self.gridlayout2.addWidget(self.user2, 2, 1, 1, 1)
        self.send3 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send3.sizePolicy().hasHeightForWidth())
        self.send3.setSizePolicy(sizePolicy)
        self.send3.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send3.setObjectName(_fromUtf8("send3"))
        self.gridlayout2.addWidget(self.send3, 3, 0, 1, 1)
        self.user3 = QtGui.QLineEdit(self.UserTab)
        self.user3.setObjectName(_fromUtf8("user3"))
        self.gridlayout2.addWidget(self.user3, 3, 1, 1, 1)
        self.send4 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send4.sizePolicy().hasHeightForWidth())
        self.send4.setSizePolicy(sizePolicy)
        self.send4.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send4.setObjectName(_fromUtf8("send4"))
        self.gridlayout2.addWidget(self.send4, 4, 0, 1, 1)
        self.user4 = QtGui.QLineEdit(self.UserTab)
        self.user4.setObjectName(_fromUtf8("user4"))
        self.gridlayout2.addWidget(self.user4, 4, 1, 1, 1)
        self.send5 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send5.sizePolicy().hasHeightForWidth())
        self.send5.setSizePolicy(sizePolicy)
        self.send5.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send5.setObjectName(_fromUtf8("send5"))
        self.gridlayout2.addWidget(self.send5, 0, 2, 1, 1)
        self.user5 = QtGui.QLineEdit(self.UserTab)
        self.user5.setObjectName(_fromUtf8("user5"))
        self.gridlayout2.addWidget(self.user5, 0, 3, 1, 1)
        self.send6 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send6.sizePolicy().hasHeightForWidth())
        self.send6.setSizePolicy(sizePolicy)
        self.send6.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send6.setObjectName(_fromUtf8("send6"))
        self.gridlayout2.addWidget(self.send6, 1, 2, 1, 1)
        self.user6 = QtGui.QLineEdit(self.UserTab)
        self.user6.setObjectName(_fromUtf8("user6"))
        self.gridlayout2.addWidget(self.user6, 1, 3, 1, 1)
        self.send7 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send7.sizePolicy().hasHeightForWidth())
        self.send7.setSizePolicy(sizePolicy)
        self.send7.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send7.setObjectName(_fromUtf8("send7"))
        self.gridlayout2.addWidget(self.send7, 2, 2, 1, 1)
        self.user7 = QtGui.QLineEdit(self.UserTab)
        self.user7.setObjectName(_fromUtf8("user7"))
        self.gridlayout2.addWidget(self.user7, 2, 3, 1, 1)
        self.send8 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send8.sizePolicy().hasHeightForWidth())
        self.send8.setSizePolicy(sizePolicy)
        self.send8.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send8.setObjectName(_fromUtf8("send8"))
        self.gridlayout2.addWidget(self.send8, 3, 2, 1, 1)
        self.user8 = QtGui.QLineEdit(self.UserTab)
        self.user8.setObjectName(_fromUtf8("user8"))
        self.gridlayout2.addWidget(self.user8, 3, 3, 1, 1)
        self.send9 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send9.sizePolicy().hasHeightForWidth())
        self.send9.setSizePolicy(sizePolicy)
        self.send9.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send9.setObjectName(_fromUtf8("send9"))
        self.gridlayout2.addWidget(self.send9, 4, 2, 1, 1)
        self.user9 = QtGui.QLineEdit(self.UserTab)
        self.user9.setObjectName(_fromUtf8("user9"))
        self.gridlayout2.addWidget(self.user9, 4, 3, 1, 1)
        self.send10 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send10.sizePolicy().hasHeightForWidth())
        self.send10.setSizePolicy(sizePolicy)
        self.send10.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send10.setObjectName(_fromUtf8("send10"))
        self.gridlayout2.addWidget(self.send10, 0, 4, 1, 1)
        self.user10 = QtGui.QLineEdit(self.UserTab)
        self.user10.setObjectName(_fromUtf8("user10"))
        self.gridlayout2.addWidget(self.user10, 0, 5, 1, 1)
        self.send11 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send11.sizePolicy().hasHeightForWidth())
        self.send11.setSizePolicy(sizePolicy)
        self.send11.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send11.setObjectName(_fromUtf8("send11"))
        self.gridlayout2.addWidget(self.send11, 1, 4, 1, 1)
        self.send12 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send12.sizePolicy().hasHeightForWidth())
        self.send12.setSizePolicy(sizePolicy)
        self.send12.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send12.setObjectName(_fromUtf8("send12"))
        self.gridlayout2.addWidget(self.send12, 2, 4, 1, 1)
        self.send13 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send13.sizePolicy().hasHeightForWidth())
        self.send13.setSizePolicy(sizePolicy)
        self.send13.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send13.setObjectName(_fromUtf8("send13"))
        self.gridlayout2.addWidget(self.send13, 3, 4, 1, 1)
        self.send14 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send14.sizePolicy().hasHeightForWidth())
        self.send14.setSizePolicy(sizePolicy)
        self.send14.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send14.setObjectName(_fromUtf8("send14"))
        self.gridlayout2.addWidget(self.send14, 4, 4, 1, 1)
        self.user11 = QtGui.QLineEdit(self.UserTab)
        self.user11.setObjectName(_fromUtf8("user11"))
        self.gridlayout2.addWidget(self.user11, 1, 5, 1, 1)
        self.user12 = QtGui.QLineEdit(self.UserTab)
        self.user12.setObjectName(_fromUtf8("user12"))
        self.gridlayout2.addWidget(self.user12, 2, 5, 1, 1)
        self.user13 = QtGui.QLineEdit(self.UserTab)
        self.user13.setObjectName(_fromUtf8("user13"))
        self.gridlayout2.addWidget(self.user13, 3, 5, 1, 1)
        self.user14 = QtGui.QLineEdit(self.UserTab)
        self.user14.setObjectName(_fromUtf8("user14"))
        self.gridlayout2.addWidget(self.user14, 4, 5, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout2.addItem(spacerItem3, 5, 1, 1, 1)
        self.send15 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send15.sizePolicy().hasHeightForWidth())
        self.send15.setSizePolicy(sizePolicy)
        self.send15.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send15.setObjectName(_fromUtf8("send15"))
        self.gridlayout2.addWidget(self.send15, 0, 6, 1, 1)
        self.user15 = QtGui.QLineEdit(self.UserTab)
        self.user15.setObjectName(_fromUtf8("user15"))
        self.gridlayout2.addWidget(self.user15, 0, 7, 1, 1)
        self.send16 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send16.sizePolicy().hasHeightForWidth())
        self.send16.setSizePolicy(sizePolicy)
        self.send16.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send16.setObjectName(_fromUtf8("send16"))
        self.gridlayout2.addWidget(self.send16, 1, 6, 1, 1)
        self.send17 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send17.sizePolicy().hasHeightForWidth())
        self.send17.setSizePolicy(sizePolicy)
        self.send17.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send17.setObjectName(_fromUtf8("send17"))
        self.gridlayout2.addWidget(self.send17, 2, 6, 1, 1)
        self.send18 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send18.sizePolicy().hasHeightForWidth())
        self.send18.setSizePolicy(sizePolicy)
        self.send18.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send18.setObjectName(_fromUtf8("send18"))
        self.gridlayout2.addWidget(self.send18, 3, 6, 1, 1)
        self.send19 = QtGui.QPushButton(self.UserTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.send19.sizePolicy().hasHeightForWidth())
        self.send19.setSizePolicy(sizePolicy)
        self.send19.setMaximumSize(QtCore.QSize(50, 16777215))
        self.send19.setObjectName(_fromUtf8("send19"))
        self.gridlayout2.addWidget(self.send19, 4, 6, 1, 1)
        self.user16 = QtGui.QLineEdit(self.UserTab)
        self.user16.setObjectName(_fromUtf8("user16"))
        self.gridlayout2.addWidget(self.user16, 1, 7, 1, 1)
        self.user17 = QtGui.QLineEdit(self.UserTab)
        self.user17.setObjectName(_fromUtf8("user17"))
        self.gridlayout2.addWidget(self.user17, 2, 7, 1, 1)
        self.user18 = QtGui.QLineEdit(self.UserTab)
        self.user18.setObjectName(_fromUtf8("user18"))
        self.gridlayout2.addWidget(self.user18, 3, 7, 1, 1)
        self.user19 = QtGui.QLineEdit(self.UserTab)
        self.user19.setObjectName(_fromUtf8("user19"))
        self.gridlayout2.addWidget(self.user19, 4, 7, 1, 1)
        self.hboxlayout.addLayout(self.gridlayout2)
        self.Tabs.addTab(self.UserTab, _fromUtf8(""))
        self.HighlightTab = QtGui.QWidget()
        self.HighlightTab.setObjectName(_fromUtf8("HighlightTab"))
        self.highlightLayout = QtGui.QGridLayout(self.HighlightTab)
        self.highlightLayout.setMargin(4)
        self.highlightLayout.setSpacing(2)
        self.highlightLayout.setObjectName(_fromUtf8("highlightLayout"))
        self.hlcolor0 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor0.sizePolicy().hasHeightForWidth())
        self.hlcolor0.setSizePolicy(sizePolicy)
        self.hlcolor0.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor0.setObjectName(_fromUtf8("hlcolor0"))
        self.highlightLayout.addWidget(self.hlcolor0, 0, 0, 1, 1)
        self.hltext0 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext0.setObjectName(_fromUtf8("hltext0"))
        self.highlightLayout.addWidget(self.hltext0, 0, 1, 1, 1)
        self.hlcolor5 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor5.sizePolicy().hasHeightForWidth())
        self.hlcolor5.setSizePolicy(sizePolicy)
        self.hlcolor5.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor5.setObjectName(_fromUtf8("hlcolor5"))
        self.highlightLayout.addWidget(self.hlcolor5, 0, 2, 1, 1)
        self.hltext5 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext5.setObjectName(_fromUtf8("hltext5"))
        self.highlightLayout.addWidget(self.hltext5, 0, 3, 1, 1)
        self.hlcolor1 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor1.sizePolicy().hasHeightForWidth())
        self.hlcolor1.setSizePolicy(sizePolicy)
        self.hlcolor1.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor1.setObjectName(_fromUtf8("hlcolor1"))
        self.highlightLayout.addWidget(self.hlcolor1, 1, 0, 1, 1)
        self.hltext1 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext1.setObjectName(_fromUtf8("hltext1"))
        self.highlightLayout.addWidget(self.hltext1, 1, 1, 1, 1)
        self.hlcolor6 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor6.sizePolicy().hasHeightForWidth())
        self.hlcolor6.setSizePolicy(sizePolicy)
        self.hlcolor6.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor6.setObjectName(_fromUtf8("hlcolor6"))
        self.highlightLayout.addWidget(self.hlcolor6, 1, 2, 1, 1)
        self.hltext6 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext6.setObjectName(_fromUtf8("hltext6"))
        self.highlightLayout.addWidget(self.hltext6, 1, 3, 1, 1)
        self.hlcolor2 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor2.sizePolicy().hasHeightForWidth())
        self.hlcolor2.setSizePolicy(sizePolicy)
        self.hlcolor2.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor2.setObjectName(_fromUtf8("hlcolor2"))
        self.highlightLayout.addWidget(self.hlcolor2, 2, 0, 1, 1)
        self.hltext2 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext2.setObjectName(_fromUtf8("hltext2"))
        self.highlightLayout.addWidget(self.hltext2, 2, 1, 1, 1)
        self.hlcolor7 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor7.sizePolicy().hasHeightForWidth())
        self.hlcolor7.setSizePolicy(sizePolicy)
        self.hlcolor7.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor7.setObjectName(_fromUtf8("hlcolor7"))
        self.highlightLayout.addWidget(self.hlcolor7, 2, 2, 1, 1)
        self.hltext7 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext7.setObjectName(_fromUtf8("hltext7"))
        self.highlightLayout.addWidget(self.hltext7, 2, 3, 1, 1)
        self.hlcolor3 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor3.sizePolicy().hasHeightForWidth())
        self.hlcolor3.setSizePolicy(sizePolicy)
        self.hlcolor3.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor3.setObjectName(_fromUtf8("hlcolor3"))
        self.highlightLayout.addWidget(self.hlcolor3, 3, 0, 1, 1)
        self.hltext3 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext3.setObjectName(_fromUtf8("hltext3"))
        self.highlightLayout.addWidget(self.hltext3, 3, 1, 1, 1)
        self.hlcolor8 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor8.sizePolicy().hasHeightForWidth())
        self.hlcolor8.setSizePolicy(sizePolicy)
        self.hlcolor8.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor8.setObjectName(_fromUtf8("hlcolor8"))
        self.highlightLayout.addWidget(self.hlcolor8, 3, 2, 1, 1)
        self.hltext8 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext8.setObjectName(_fromUtf8("hltext8"))
        self.highlightLayout.addWidget(self.hltext8, 3, 3, 1, 1)
        self.hlcolor4 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor4.sizePolicy().hasHeightForWidth())
        self.hlcolor4.setSizePolicy(sizePolicy)
        self.hlcolor4.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor4.setObjectName(_fromUtf8("hlcolor4"))
        self.highlightLayout.addWidget(self.hlcolor4, 4, 0, 1, 1)
        self.hltext4 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext4.setObjectName(_fromUtf8("hltext4"))
        self.highlightLayout.addWidget(self.hltext4, 4, 1, 1, 1)
        self.hlcolor9 = ColorFrame(self.HighlightTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hlcolor9.sizePolicy().hasHeightForWidth())
        self.hlcolor9.setSizePolicy(sizePolicy)
        self.hlcolor9.setMinimumSize(QtCore.QSize(25, 25))
        self.hlcolor9.setObjectName(_fromUtf8("hlcolor9"))
        self.highlightLayout.addWidget(self.hlcolor9, 4, 2, 1, 1)
        self.hltext9 = QtGui.QLineEdit(self.HighlightTab)
        self.hltext9.setObjectName(_fromUtf8("hltext9"))
        self.highlightLayout.addWidget(self.hltext9, 4, 3, 1, 1)
        spacerItem4 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.highlightLayout.addItem(spacerItem4, 5, 1, 1, 1)
        self.Tabs.addTab(self.HighlightTab, _fromUtf8(""))
        self.DSIDTab = QtGui.QWidget()
        self.DSIDTab.setObjectName(_fromUtf8("DSIDTab"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.DSIDTab)
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setMargin(1)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.dsids = QtGui.QListWidget(self.DSIDTab)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.dsids.setFont(font)
        self.dsids.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.dsids.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.dsids.setObjectName(_fromUtf8("dsids"))
        self.horizontalLayout_2.addWidget(self.dsids)
        self.dsid_numbers = QtGui.QListWidget(self.DSIDTab)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.dsid_numbers.setFont(font)
        self.dsid_numbers.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.dsid_numbers.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.dsid_numbers.setObjectName(_fromUtf8("dsid_numbers"))
        self.horizontalLayout_2.addWidget(self.dsid_numbers)
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        self.Tabs.addTab(self.DSIDTab, _fromUtf8(""))
        self.UnderwareTab = QtGui.QWidget()
        self.UnderwareTab.setObjectName(_fromUtf8("UnderwareTab"))
        self.horizontalLayout_6 = QtGui.QHBoxLayout(self.UnderwareTab)
        self.horizontalLayout_6.setSpacing(2)
        self.horizontalLayout_6.setMargin(1)
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.underware = QtGui.QListWidget(self.UnderwareTab)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.underware.setFont(font)
        self.underware.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.underware.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.underware.setObjectName(_fromUtf8("underware"))
        self.horizontalLayout_5.addWidget(self.underware)
        self.underware_description = QtGui.QTextEdit(self.UnderwareTab)
        self.underware_description.setReadOnly(True)
        self.underware_description.setObjectName(_fromUtf8("underware_description"))
        self.horizontalLayout_5.addWidget(self.underware_description)
        self.horizontalLayout_6.addLayout(self.horizontalLayout_5)
        self.Tabs.addTab(self.UnderwareTab, _fromUtf8(""))
        self.VariablesTab = QtGui.QWidget()
        self.VariablesTab.setObjectName(_fromUtf8("VariablesTab"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.VariablesTab)
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setMargin(1)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.VariablesTab)
        self.label.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.globals = QtGui.QListWidget(self.VariablesTab)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.globals.setFont(font)
        self.globals.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.globals.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.globals.setObjectName(_fromUtf8("globals"))
        self.verticalLayout.addWidget(self.globals)
        self.horizontalLayout_4.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label_2 = QtGui.QLabel(self.VariablesTab)
        self.label_2.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_2.addWidget(self.label_2)
        self.constants = QtGui.QListWidget(self.VariablesTab)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.constants.setFont(font)
        self.constants.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.constants.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.constants.setObjectName(_fromUtf8("constants"))
        self.verticalLayout_2.addWidget(self.constants)
        self.horizontalLayout_4.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.label_3 = QtGui.QLabel(self.VariablesTab)
        self.label_3.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout_3.addWidget(self.label_3)
        self.named = QtGui.QListWidget(self.VariablesTab)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.named.setFont(font)
        self.named.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.named.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.named.setObjectName(_fromUtf8("named"))
        self.verticalLayout_3.addWidget(self.named)
        self.horizontalLayout_4.addLayout(self.verticalLayout_3)
        self.Tabs.addTab(self.VariablesTab, _fromUtf8(""))
        self.OptionsTab = QtGui.QWidget()
        self.OptionsTab.setObjectName(_fromUtf8("OptionsTab"))
        self.verticalLayout_9 = QtGui.QVBoxLayout(self.OptionsTab)
        self.verticalLayout_9.setSpacing(2)
        self.verticalLayout_9.setMargin(1)
        self.verticalLayout_9.setObjectName(_fromUtf8("verticalLayout_9"))
        self.horizontalLayout_10 = QtGui.QHBoxLayout()
        self.horizontalLayout_10.setSpacing(3)
        self.horizontalLayout_10.setMargin(3)
        self.horizontalLayout_10.setObjectName(_fromUtf8("horizontalLayout_10"))
        self.verticalLayout_5 = QtGui.QVBoxLayout()
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.groupBox = QtGui.QGroupBox(self.OptionsTab)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout_6 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_6.setSpacing(1)
        self.verticalLayout_6.setMargin(1)
        self.verticalLayout_6.setObjectName(_fromUtf8("verticalLayout_6"))
        self.guiOption = QtGui.QCheckBox(self.groupBox)
        self.guiOption.setObjectName(_fromUtf8("guiOption"))
        self.verticalLayout_6.addWidget(self.guiOption)
        self.searchOption = QtGui.QCheckBox(self.groupBox)
        self.searchOption.setObjectName(_fromUtf8("searchOption"))
        self.verticalLayout_6.addWidget(self.searchOption)
        self.updateOption = QtGui.QCheckBox(self.groupBox)
        self.updateOption.setObjectName(_fromUtf8("updateOption"))
        self.verticalLayout_6.addWidget(self.updateOption)
        self.verticalLayout_5.addWidget(self.groupBox)
        spacerItem5 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem5)
        self.revLabel = QtGui.QLabel(self.OptionsTab)
        self.revLabel.setText(_fromUtf8(""))
        self.revLabel.setObjectName(_fromUtf8("revLabel"))
        self.verticalLayout_5.addWidget(self.revLabel)
        self.horizontalLayout_10.addLayout(self.verticalLayout_5)
        self.verticalLayout_14 = QtGui.QVBoxLayout()
        self.verticalLayout_14.setObjectName(_fromUtf8("verticalLayout_14"))
        self.groupBox_4 = QtGui.QGroupBox(self.OptionsTab)
        self.groupBox_4.setObjectName(_fromUtf8("groupBox_4"))
        self.verticalLayout_10 = QtGui.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_10.setSpacing(1)
        self.verticalLayout_10.setMargin(1)
        self.verticalLayout_10.setObjectName(_fromUtf8("verticalLayout_10"))
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setSpacing(1)
        self.horizontalLayout_11.setMargin(1)
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.browseOption = QtGui.QRadioButton(self.groupBox_4)
        self.browseOption.setChecked(True)
        self.browseOption.setObjectName(_fromUtf8("browseOption"))
        self.horizontalLayout_11.addWidget(self.browseOption)
        self.sdvOption = QtGui.QRadioButton(self.groupBox_4)
        self.sdvOption.setObjectName(_fromUtf8("sdvOption"))
        self.horizontalLayout_11.addWidget(self.sdvOption)
        self.verticalLayout_10.addLayout(self.horizontalLayout_11)
        self.horizontalLayout_12 = QtGui.QHBoxLayout()
        self.horizontalLayout_12.setSpacing(2)
        self.horizontalLayout_12.setObjectName(_fromUtf8("horizontalLayout_12"))
        self.label_6 = QtGui.QLabel(self.groupBox_4)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.horizontalLayout_12.addWidget(self.label_6)
        self.sdvHost = QtGui.QLineEdit(self.groupBox_4)
        self.sdvHost.setObjectName(_fromUtf8("sdvHost"))
        self.horizontalLayout_12.addWidget(self.sdvHost)
        self.verticalLayout_10.addLayout(self.horizontalLayout_12)
        self.verticalLayout_14.addWidget(self.groupBox_4)
        spacerItem6 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_14.addItem(spacerItem6)
        self.horizontalLayout_10.addLayout(self.verticalLayout_14)
        spacerItem7 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_10.addItem(spacerItem7)
        self.verticalLayout_8 = QtGui.QVBoxLayout()
        self.verticalLayout_8.setObjectName(_fromUtf8("verticalLayout_8"))
        self.groupBox_3 = QtGui.QGroupBox(self.OptionsTab)
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.verticalLayout_13 = QtGui.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_13.setSpacing(1)
        self.verticalLayout_13.setMargin(1)
        self.verticalLayout_13.setObjectName(_fromUtf8("verticalLayout_13"))
        self.verticalLayout_12 = QtGui.QVBoxLayout()
        self.verticalLayout_12.setSpacing(1)
        self.verticalLayout_12.setMargin(1)
        self.verticalLayout_12.setObjectName(_fromUtf8("verticalLayout_12"))
        self.rawOption = QtGui.QCheckBox(self.groupBox_3)
        self.rawOption.setObjectName(_fromUtf8("rawOption"))
        self.verticalLayout_12.addWidget(self.rawOption)
        self.debugOption = QtGui.QCheckBox(self.groupBox_3)
        self.debugOption.setObjectName(_fromUtf8("debugOption"))
        self.verticalLayout_12.addWidget(self.debugOption)
        self.prereleaseOption = QtGui.QCheckBox(self.groupBox_3)
        self.prereleaseOption.setObjectName(_fromUtf8("prereleaseOption"))
        self.verticalLayout_12.addWidget(self.prereleaseOption)
        self.resetOption = QtGui.QCheckBox(self.groupBox_3)
        self.resetOption.setObjectName(_fromUtf8("resetOption"))
        self.verticalLayout_12.addWidget(self.resetOption)
        self.verticalLayout_13.addLayout(self.verticalLayout_12)
        self.verticalLayout_8.addWidget(self.groupBox_3)
        spacerItem8 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_8.addItem(spacerItem8)
        self.horizontalLayout_10.addLayout(self.verticalLayout_8)
        self.verticalLayout_9.addLayout(self.horizontalLayout_10)
        self.Tabs.addTab(self.OptionsTab, _fromUtf8(""))
        self.gridlayout.addWidget(self.Tabs, 0, 0, 1, 1)
        self.bufferView = BufferView()
        self.bufferView.setObjectName(_fromUtf8("bufferView"))
        self.gridlayout.addWidget(self.bufferView, 1, 0, 1, 1)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setSpacing(2)
        self.hboxlayout1.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.input = QtGui.QComboBox(self.MainWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.input.sizePolicy().hasHeightForWidth())
        self.input.setSizePolicy(sizePolicy)
        self.input.setEditable(True)
        self.input.setMaxVisibleItems(25)
        self.input.setDuplicatesEnabled(True)
        self.input.setObjectName(_fromUtf8("input"))
        self.hboxlayout1.addWidget(self.input)
        self.search = QtGui.QPushButton(self.MainWidget)
        self.search.setMaximumSize(QtCore.QSize(60, 16777215))
        self.search.setObjectName(_fromUtf8("search"))
        self.hboxlayout1.addWidget(self.search)
        self.browse = QtGui.QPushButton(self.MainWidget)
        self.browse.setMaximumSize(QtCore.QSize(60, 16777215))
        self.browse.setObjectName(_fromUtf8("browse"))
        self.hboxlayout1.addWidget(self.browse)
        self.edit = QtGui.QPushButton(self.MainWidget)
        self.edit.setMaximumSize(QtCore.QSize(60, 16777215))
        self.edit.setObjectName(_fromUtf8("edit"))
        self.hboxlayout1.addWidget(self.edit)
        self.savefile = QtGui.QPushButton(self.MainWidget)
        self.savefile.setMaximumSize(QtCore.QSize(60, 16777215))
        self.savefile.setObjectName(_fromUtf8("savefile"))
        self.hboxlayout1.addWidget(self.savefile)
        self.openfile = QtGui.QPushButton(self.MainWidget)
        self.openfile.setEnabled(True)
        self.openfile.setMaximumSize(QtCore.QSize(60, 16777215))
        self.openfile.setObjectName(_fromUtf8("openfile"))
        self.hboxlayout1.addWidget(self.openfile)
        self.connect = QtGui.QPushButton(self.MainWidget)
        self.connect.setMaximumSize(QtCore.QSize(60, 16777215))
        self.connect.setObjectName(_fromUtf8("connect"))
        self.hboxlayout1.addWidget(self.connect)
        self.sendfile = QtGui.QPushButton(self.MainWidget)
        self.sendfile.setMaximumSize(QtCore.QSize(60, 16777215))
        self.sendfile.setObjectName(_fromUtf8("sendfile"))
        self.hboxlayout1.addWidget(self.sendfile)
        self.clear = QtGui.QPushButton(self.MainWidget)
        self.clear.setMaximumSize(QtCore.QSize(60, 16777215))
        self.clear.setObjectName(_fromUtf8("clear"))
        self.hboxlayout1.addWidget(self.clear)
        self.flash = QtGui.QPushButton(self.MainWidget)
        self.flash.setMaximumSize(QtCore.QSize(60, 16777215))
        self.flash.setObjectName(_fromUtf8("flash"))
        self.hboxlayout1.addWidget(self.flash)
        self.gridlayout.addLayout(self.hboxlayout1, 2, 0, 1, 1)
        self.gridlayout.setRowStretch(0, 1)
        self.gridlayout.setRowStretch(1, 100)
        self.gridlayout.setRowStretch(2, 1)
        MainWindow.setCentralWidget(self.MainWidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 784, 21))
        self.menuBar.setObjectName(_fromUtf8("menuBar"))
        MainWindow.setMenuBar(self.menuBar)

        self.retranslateUi(MainWindow)
        self.Tabs.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Sift", None, QtGui.QApplication.UnicodeUTF8))
        self.FMTrace.setTitle(QtGui.QApplication.translate("MainWindow", "FM Trace", None, QtGui.QApplication.UnicodeUTF8))
        self.on.setToolTip(QtGui.QApplication.translate("MainWindow", "Turn on live tracing over serial and network (not available over USB)", None, QtGui.QApplication.UnicodeUTF8))
        self.on.setText(QtGui.QApplication.translate("MainWindow", "On", None, QtGui.QApplication.UnicodeUTF8))
        self.tock.setToolTip(QtGui.QApplication.translate("MainWindow", "Do not trace periodic ticks", None, QtGui.QApplication.UnicodeUTF8))
        self.tock.setText(QtGui.QApplication.translate("MainWindow", "No Ticks", None, QtGui.QApplication.UnicodeUTF8))
        self.nosweep.setToolTip(QtGui.QApplication.translate("MainWindow", "Do not trace print sweeps", None, QtGui.QApplication.UnicodeUTF8))
        self.nosweep.setText(QtGui.QApplication.translate("MainWindow", "No Swps", None, QtGui.QApplication.UnicodeUTF8))
        self.tick.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace sweeps and periodic ticks", None, QtGui.QApplication.UnicodeUTF8))
        self.tick.setText(QtGui.QApplication.translate("MainWindow", "Ticks", None, QtGui.QApplication.UnicodeUTF8))
        self.off.setToolTip(QtGui.QApplication.translate("MainWindow", "Turn off live tracing.", None, QtGui.QApplication.UnicodeUTF8))
        self.off.setText(QtGui.QApplication.translate("MainWindow", "Off", None, QtGui.QApplication.UnicodeUTF8))
        self.get.setToolTip(QtGui.QApplication.translate("MainWindow", "Retrieve the internal Sift buffer.", None, QtGui.QApplication.UnicodeUTF8))
        self.get.setText(QtGui.QApplication.translate("MainWindow", "Get Internal Trace", None, QtGui.QApplication.UnicodeUTF8))
        self.reset.setToolTip(QtGui.QApplication.translate("MainWindow", "Reset trace settings (turns trace off)", None, QtGui.QApplication.UnicodeUTF8))
        self.reset.setText(QtGui.QApplication.translate("MainWindow", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("MainWindow", "Depth", None, QtGui.QApplication.UnicodeUTF8))
        self.depth.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace only to a given call depth.  \"1\" will only show Master flow calls.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("MainWindow", "Trace a Single Flow or Keyword", None, QtGui.QApplication.UnicodeUTF8))
        self.single.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace a single flow or keyword.", None, QtGui.QApplication.UnicodeUTF8))
        self.flows_check.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace flow calls", None, QtGui.QApplication.UnicodeUTF8))
        self.flows_check.setText(QtGui.QApplication.translate("MainWindow", "Flows", None, QtGui.QApplication.UnicodeUTF8))
        self.globals_check.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace global variable changes", None, QtGui.QApplication.UnicodeUTF8))
        self.globals_check.setText(QtGui.QApplication.translate("MainWindow", "Globals", None, QtGui.QApplication.UnicodeUTF8))
        self.locals_check.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace flow local variable changes", None, QtGui.QApplication.UnicodeUTF8))
        self.locals_check.setText(QtGui.QApplication.translate("MainWindow", "Locals", None, QtGui.QApplication.UnicodeUTF8))
        self.keywords_check.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace keyword calls", None, QtGui.QApplication.UnicodeUTF8))
        self.keywords_check.setText(QtGui.QApplication.translate("MainWindow", "Keywords", None, QtGui.QApplication.UnicodeUTF8))
        self.startup_check.setToolTip(QtGui.QApplication.translate("MainWindow", "Trace printer startup.", None, QtGui.QApplication.UnicodeUTF8))
        self.startup_check.setText(QtGui.QApplication.translate("MainWindow", "Startup", None, QtGui.QApplication.UnicodeUTF8))
        self.slow_check.setToolTip(QtGui.QApplication.translate("MainWindow", "Slow printer to avoid serial overruns. (Use at your own risk.)", None, QtGui.QApplication.UnicodeUTF8))
        self.slow_check.setText(QtGui.QApplication.translate("MainWindow", "Slow", None, QtGui.QApplication.UnicodeUTF8))
        self.FMDebug.setTitle(QtGui.QApplication.translate("MainWindow", "FM Debug", None, QtGui.QApplication.UnicodeUTF8))
        self.flow_break.setToolTip(QtGui.QApplication.translate("MainWindow", "Set a breakpoint on a flow", None, QtGui.QApplication.UnicodeUTF8))
        self.global_break.setToolTip(QtGui.QApplication.translate("MainWindow", "Set a breakpoint on a global variable", None, QtGui.QApplication.UnicodeUTF8))
        self.global_break_value.setToolTip(QtGui.QApplication.translate("MainWindow", "Break only if the global variable changes to this value.", None, QtGui.QApplication.UnicodeUTF8))
        self.fmstep.setToolTip(QtGui.QApplication.translate("MainWindow", "Step one statement, entering called flows.", None, QtGui.QApplication.UnicodeUTF8))
        self.fmstep.setText(QtGui.QApplication.translate("MainWindow", "Step", None, QtGui.QApplication.UnicodeUTF8))
        self.fmreturn.setToolTip(QtGui.QApplication.translate("MainWindow", "Run until flow returns to caller.", None, QtGui.QApplication.UnicodeUTF8))
        self.fmreturn.setText(QtGui.QApplication.translate("MainWindow", "Return", None, QtGui.QApplication.UnicodeUTF8))
        self.fmnext.setToolTip(QtGui.QApplication.translate("MainWindow", "Run to next source line (jumping over flow calls)", None, QtGui.QApplication.UnicodeUTF8))
        self.fmnext.setText(QtGui.QApplication.translate("MainWindow", "Next", None, QtGui.QApplication.UnicodeUTF8))
        self.fmbt.setToolTip(QtGui.QApplication.translate("MainWindow", "Show current stack (while stopped at break)", None, QtGui.QApplication.UnicodeUTF8))
        self.fmbt.setText(QtGui.QApplication.translate("MainWindow", "Stack", None, QtGui.QApplication.UnicodeUTF8))
        self.fmgo.setToolTip(QtGui.QApplication.translate("MainWindow", "Resume execution", None, QtGui.QApplication.UnicodeUTF8))
        self.fmgo.setText(QtGui.QApplication.translate("MainWindow", "Go", None, QtGui.QApplication.UnicodeUTF8))
        self.fmclear.setToolTip(QtGui.QApplication.translate("MainWindow", "Clear all breakpoints and resume execution.", None, QtGui.QApplication.UnicodeUTF8))
        self.fmclear.setText(QtGui.QApplication.translate("MainWindow", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.Printer.setTitle(QtGui.QApplication.translate("MainWindow", "Printer", None, QtGui.QApplication.UnicodeUTF8))
        self.rev.setToolTip(QtGui.QApplication.translate("MainWindow", "Get FW revision and Sift status", None, QtGui.QApplication.UnicodeUTF8))
        self.rev.setText(QtGui.QApplication.translate("MainWindow", "Rev", None, QtGui.QApplication.UnicodeUTF8))
        self.tap.setToolTip(QtGui.QApplication.translate("MainWindow", "Internal test page", None, QtGui.QApplication.UnicodeUTF8))
        self.label_tap.setText(QtGui.QApplication.translate("MainWindow", "Tap", None, QtGui.QApplication.UnicodeUTF8))
        self.state.setToolTip(QtGui.QApplication.translate("MainWindow", "Get machine_state", None, QtGui.QApplication.UnicodeUTF8))
        self.state.setText(QtGui.QApplication.translate("MainWindow", "State", None, QtGui.QApplication.UnicodeUTF8))
        self.pwron.setToolTip(QtGui.QApplication.translate("MainWindow", "Power on printer with sm.on", None, QtGui.QApplication.UnicodeUTF8))
        self.pwron.setText(QtGui.QApplication.translate("MainWindow", "Pwr On", None, QtGui.QApplication.UnicodeUTF8))
        self.dooropen.setToolTip(QtGui.QApplication.translate("MainWindow", "Open printer door", None, QtGui.QApplication.UnicodeUTF8))
        self.dooropen.setText(QtGui.QApplication.translate("MainWindow", "Door Opn", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setToolTip(QtGui.QApplication.translate("MainWindow", "Press \"OK\" on front panel (may or may not work).", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("MainWindow", "OK", None, QtGui.QApplication.UnicodeUTF8))
        self.doorclose.setToolTip(QtGui.QApplication.translate("MainWindow", "Close printer door", None, QtGui.QApplication.UnicodeUTF8))
        self.doorclose.setText(QtGui.QApplication.translate("MainWindow", "Door Cls", None, QtGui.QApplication.UnicodeUTF8))
        self.vtap.setToolTip(QtGui.QApplication.translate("MainWindow", "Perform a virtual tap", None, QtGui.QApplication.UnicodeUTF8))
        self.component.setToolTip(QtGui.QApplication.translate("MainWindow", "Set a serial debug level, e.g. \"MECH 10\"", None, QtGui.QApplication.UnicodeUTF8))
        self.label_virtual.setText(QtGui.QApplication.translate("MainWindow", "Virtual", None, QtGui.QApplication.UnicodeUTF8))
        self.label_ondebug.setText(QtGui.QApplication.translate("MainWindow", "on_dbug", None, QtGui.QApplication.UnicodeUTF8))
        self.Tabs.setTabText(self.Tabs.indexOf(self.CommandsTab), QtGui.QApplication.translate("MainWindow", "Commands", None, QtGui.QApplication.UnicodeUTF8))
        self.send0.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send1.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send2.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send3.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send4.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send5.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send6.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send7.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send8.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send9.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send10.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send11.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send12.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send13.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send14.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send15.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send16.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send17.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send18.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.send19.setText(QtGui.QApplication.translate("MainWindow", "Send", None, QtGui.QApplication.UnicodeUTF8))
        self.Tabs.setTabText(self.Tabs.indexOf(self.UserTab), QtGui.QApplication.translate("MainWindow", "User Favorites", None, QtGui.QApplication.UnicodeUTF8))
        self.Tabs.setTabText(self.Tabs.indexOf(self.HighlightTab), QtGui.QApplication.translate("MainWindow", "User Highlights", None, QtGui.QApplication.UnicodeUTF8))
        self.dsids.setToolTip(QtGui.QApplication.translate("MainWindow", "Double click to query DSID", None, QtGui.QApplication.UnicodeUTF8))
        self.dsids.setSortingEnabled(True)
        self.dsid_numbers.setToolTip(QtGui.QApplication.translate("MainWindow", "Double click to query DSID", None, QtGui.QApplication.UnicodeUTF8))
        self.dsid_numbers.setSortingEnabled(True)
        self.Tabs.setTabText(self.Tabs.indexOf(self.DSIDTab), QtGui.QApplication.translate("MainWindow", "DSIDs", None, QtGui.QApplication.UnicodeUTF8))
        self.underware.setToolTip(QtGui.QApplication.translate("MainWindow", "Double click to copy underware to input box.", None, QtGui.QApplication.UnicodeUTF8))
        self.underware.setSortingEnabled(True)
        self.Tabs.setTabText(self.Tabs.indexOf(self.UnderwareTab), QtGui.QApplication.translate("MainWindow", "Underware", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Globals", None, QtGui.QApplication.UnicodeUTF8))
        self.globals.setToolTip(QtGui.QApplication.translate("MainWindow", "Double click to query global", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Constants", None, QtGui.QApplication.UnicodeUTF8))
        self.constants.setToolTip(QtGui.QApplication.translate("MainWindow", "Double click to query constant", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "Named Values", None, QtGui.QApplication.UnicodeUTF8))
        self.named.setToolTip(QtGui.QApplication.translate("MainWindow", "Double click to query named value", None, QtGui.QApplication.UnicodeUTF8))
        self.Tabs.setTabText(self.Tabs.indexOf(self.VariablesTab), QtGui.QApplication.translate("MainWindow", "FM Variables", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("MainWindow", "Startup Options", None, QtGui.QApplication.UnicodeUTF8))
        self.guiOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Start up in GUI Mode", None, QtGui.QApplication.UnicodeUTF8))
        self.guiOption.setText(QtGui.QApplication.translate("MainWindow", "GUI mode", None, QtGui.QApplication.UnicodeUTF8))
        self.searchOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Search for .all file at startup. This is handy but not perfect.", None, QtGui.QApplication.UnicodeUTF8))
        self.searchOption.setText(QtGui.QApplication.translate("MainWindow", "Auto search for .all", None, QtGui.QApplication.UnicodeUTF8))
        self.updateOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Auto update Sift when new updates are released. (Windows only)", None, QtGui.QApplication.UnicodeUTF8))
        self.updateOption.setText(QtGui.QApplication.translate("MainWindow", "Auto update Sift", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_4.setTitle(QtGui.QApplication.translate("MainWindow", "Browse With", None, QtGui.QApplication.UnicodeUTF8))
        self.browseOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Browse button opens Chrome or Firefox", None, QtGui.QApplication.UnicodeUTF8))
        self.browseOption.setText(QtGui.QApplication.translate("MainWindow", "Chrome/Firefox", None, QtGui.QApplication.UnicodeUTF8))
        self.sdvOption.setToolTip(QtGui.QApplication.translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Arial\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Browse button opens Sift Data Viewer (SDV). SDV is available here: <span style=\" font-weight:600; text-decoration: underline;\">\\\\vcslab\\root\\InkSystems\\SPHINKS\\Randal Morrison\\Sift Data Viewer\\</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.sdvOption.setText(QtGui.QApplication.translate("MainWindow", "Sift Data Viewer (SDV)", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setToolTip(QtGui.QApplication.translate("MainWindow", "Specify where SDV is running. Localhost is default.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("MainWindow", "SDV host:", None, QtGui.QApplication.UnicodeUTF8))
        self.sdvHost.setToolTip(QtGui.QApplication.translate("MainWindow", "Specify where SDV is running. Localhost is default.", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate("MainWindow", "Sift Diagnostics", None, QtGui.QApplication.UnicodeUTF8))
        self.rawOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Show raw trace data (new traces only).", None, QtGui.QApplication.UnicodeUTF8))
        self.rawOption.setText(QtGui.QApplication.translate("MainWindow", "Raw text", None, QtGui.QApplication.UnicodeUTF8))
        self.debugOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Sift\'s internal debug messages.", None, QtGui.QApplication.UnicodeUTF8))
        self.debugOption.setText(QtGui.QApplication.translate("MainWindow", "Debug", None, QtGui.QApplication.UnicodeUTF8))
        self.prereleaseOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Take prerelease updates. These preleases are not tested. (Windows only)", None, QtGui.QApplication.UnicodeUTF8))
        self.prereleaseOption.setText(QtGui.QApplication.translate("MainWindow", "Prereleases", None, QtGui.QApplication.UnicodeUTF8))
        self.resetOption.setToolTip(QtGui.QApplication.translate("MainWindow", "Reset persistent data. User Favorites are NOT reset. Reset occurs on next startup.", None, QtGui.QApplication.UnicodeUTF8))
        self.resetOption.setText(QtGui.QApplication.translate("MainWindow", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.Tabs.setTabText(self.Tabs.indexOf(self.OptionsTab), QtGui.QApplication.translate("MainWindow", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.input.setToolTip(QtGui.QApplication.translate("MainWindow", "Send command to printer.  History with uparrow.", None, QtGui.QApplication.UnicodeUTF8))
        self.search.setToolTip(QtGui.QApplication.translate("MainWindow", "Search for the given substring in DSIDs, underware, etc.", None, QtGui.QApplication.UnicodeUTF8))
        self.search.setText(QtGui.QApplication.translate("MainWindow", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.browse.setToolTip(QtGui.QApplication.translate("MainWindow", "Browse trace data in Chrome, Firefox, or SDV", None, QtGui.QApplication.UnicodeUTF8))
        self.browse.setText(QtGui.QApplication.translate("MainWindow", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.edit.setToolTip(QtGui.QApplication.translate("MainWindow", "Bring up flow editor", None, QtGui.QApplication.UnicodeUTF8))
        self.edit.setText(QtGui.QApplication.translate("MainWindow", "Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.savefile.setToolTip(QtGui.QApplication.translate("MainWindow", "Save current log to a file of your choice", None, QtGui.QApplication.UnicodeUTF8))
        self.savefile.setText(QtGui.QApplication.translate("MainWindow", "Save..", None, QtGui.QApplication.UnicodeUTF8))
        self.openfile.setToolTip(QtGui.QApplication.translate("MainWindow", "Open symbol files (.all .i .hlg) or raw trace files (.txt .log .bin .raw).", None, QtGui.QApplication.UnicodeUTF8))
        self.openfile.setText(QtGui.QApplication.translate("MainWindow", "Open..", None, QtGui.QApplication.UnicodeUTF8))
        self.connect.setToolTip(QtGui.QApplication.translate("MainWindow", "Connect to a printer", None, QtGui.QApplication.UnicodeUTF8))
        self.connect.setText(QtGui.QApplication.translate("MainWindow", "Port..", None, QtGui.QApplication.UnicodeUTF8))
        self.sendfile.setToolTip(QtGui.QApplication.translate("MainWindow", "Send a print file.  (USB only)", None, QtGui.QApplication.UnicodeUTF8))
        self.sendfile.setText(QtGui.QApplication.translate("MainWindow", "Print..", None, QtGui.QApplication.UnicodeUTF8))
        self.clear.setToolTip(QtGui.QApplication.translate("MainWindow", "Clear log file and screen", None, QtGui.QApplication.UnicodeUTF8))
        self.clear.setText(QtGui.QApplication.translate("MainWindow", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.flash.setToolTip(QtGui.QApplication.translate("MainWindow", "Flash printer (via USB only)", None, QtGui.QApplication.UnicodeUTF8))
        self.flash.setText(QtGui.QApplication.translate("MainWindow", "Flash", None, QtGui.QApplication.UnicodeUTF8))


  ####################################################################################################
  #
  # Gui Class
  #
  # This class is our custom GUI wrapper, a.k.a. interface, to the PyQt module and thus the GUI.
  # Although the above code is auto-generated by Qt Designer and pyuic4, the following class is
  # manually coded and can contain GUI custimations not possible by Qt Designer.
  #
  ####################################################################################################

  class Gui(QtGui.QMainWindow):
    global command_parser
    global history

    NUM_USER_LINES = 20
    NUM_HIGHLIGHT_LINES = 10
    exception = QtCore.pyqtSignal(QtCore.QString)
    dataready = QtCore.pyqtSignal()
    ioready   = QtCore.pyqtSignal()

    def __init__(self):
        if (os.name == "posix") and (sys.platform != "darwin") and (not X_is_running()):
            raise IOError 
        self.app = QtGui.QApplication(sys.argv)
        QtGui.QMainWindow.__init__(self)
        self.setAcceptDrops(True)
        # super(QtGui.QMainWindow, self).__init__()
        self.app.setOrganizationName("Hewlett-Packard")
        self.app.setOrganizationDomain("hp.com")
        self.app.setApplicationName("Sift")
        self.app.aboutToQuit.connect(self.aboutToQuit)
        for dir in RESOURCE_PATH:
            icon_file = os.path.join(dir, SIFT_ICON)
            if os.path.isfile(icon_file):
                self.app.setWindowIcon(QtGui.QIcon(icon_file))
                debug("Icon at", icon_file)
                break
        self.exception.connect(self.handle_exception, QtCore.Qt.QueuedConnection)
        self.dataready.connect(self.handle_dataready, QtCore.Qt.QueuedConnection)
        self.ioready.connect(self.handle_ioready, QtCore.Qt.QueuedConnection)
        if sys.platform == "darwin":
            self.app.setStyle("Cleanlooks")
            # for s in QtGui.QStyleFactory.keys(): print s
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.set_title()
        self.pace = False

        geometry = QtCore.QSettings().value("geometry").toByteArray()
        if geometry != None:
            self.restoreGeometry(geometry)
        self.show()
        self.process_events()

        self.dsids_loaded = False
        self.underware_loaded = False
        self.variables_loaded = False
        self.global_breaks_loaded = False
        self.favorites_loaded = False
        self.data_ready_event = threading.Event()
        self.openfile_history = QtCore.QStringList()
        self.filename = ""
        self.last_input = None 
        self.write_time = 0
        self.default_port = "3ksdj23lkj3kj2"
        self.allow_serial = True
        self.allow_usb = True
        self.allow_pcs = True
        self.allow_ip = True
        self.allow_noconn = True
        self.siftFlowWin = None

        # Read the on_dbug components
        self.ui.component.addItem("")
        try:
            for component in open(os.path.join(SIFT_CONFIG_DIR, ONDBUG_FILE)).readlines():
                self.ui.component.addItem(component.strip())
        except IOError: pass

        # Setup favorites, history, pull downs, etc
        self.favorites = []
        try:
            for favorite in open(os.path.join(SIFT_CONFIG_DIR, FAVORITE_FILE)).readlines():
                self.favorites.append(favorite.strip())
        except IOError: pass
        else:
            try:
                for i in xrange(Gui.NUM_USER_LINES):
                    self.ui.__dict__['user'+str(i)].setText(self.favorites[i])
            except IndexError:
                pass
        self.process_events()

        # Default highlight colors
        self.ui.hlcolor0.setColor(QtGui.QColor(255, 191, 191))
        self.ui.hlcolor1.setColor(QtGui.QColor(191, 255, 191))
        self.ui.hlcolor2.setColor(QtGui.QColor(191, 191, 255))
        self.ui.hlcolor3.setColor(QtGui.QColor(191, 255, 255))
        self.ui.hlcolor4.setColor(QtGui.QColor(255, 191, 127))
        self.ui.hlcolor5.setColor(QtGui.QColor(255, 223, 223))
        self.ui.hlcolor6.setColor(QtGui.QColor(223, 244, 223))
        self.ui.hlcolor7.setColor(QtGui.QColor(223, 223, 244))
        self.ui.hlcolor8.setColor(QtGui.QColor(223, 255, 255))
        self.ui.hlcolor9.setColor(QtGui.QColor(255, 223, 191))

        # Saved highlights
        self.highlights = []
        try:
            for highlight in open(os.path.join(SIFT_CONFIG_DIR, HIGHLIGHT_FILE)).readlines():
                try:
                    cl, hltext = highlight.strip().split(';', 1)
                    try:
                        cl = QtGui.QColor(int(cl[0:2], 16), int(cl[2:4], 16), int(cl[4:6], 16))
                    except:
                        # Couldn't parse the color -- just use the default
                        cl = None
                except ValueError:
                    hltext = highlight.strip()
                    cl = None
                self.highlights.append((cl, hltext))
        except IOError: pass
        else:
            try:
                for i in xrange(Gui.NUM_HIGHLIGHT_LINES):
                    if self.highlights[i][0] is None:
                        self.highlights[i] = (self.ui.__dict__['hlcolor'+str(i)].color(), self.highlights[i][1])
                    else:
                        self.ui.__dict__['hlcolor'+str(i)].setColor(self.highlights[i][0])
                    self.ui.__dict__['hltext'+str(i)].setText(self.highlights[i][1])
            except IndexError:
                pass
        self.setHighlights()
        self.process_events()

        # Fill out the various numeric drop downs
        for i in xrange(4,150):
            self.ui.tap.addItem(str(i))
            self.ui.vtap.addItem(str(i))
        self.ui.tap.setCurrentIndex(0)
        self.ui.vtap.setCurrentIndex(0)

        # Tick to force Python interpreter to run a bit to catch ^C signals
        self.ui.periodic_tick = QtCore.QTimer()
        self.ui.periodic_tick.timeout.connect(self.periodic_tick)
        self.ui.periodic_tick.start(300)

        # Main Window
        self.ui.Tabs.currentChanged.connect(self.load_tab)
        self.ui.input.lineEdit().returnPressed.connect(self.input)
        # self.ui.send.clicked.connect(self.input)
        self.ui.search.clicked.connect(self.search)
        self.ui.browse.clicked.connect(self.browse)
        self.ui.savefile.clicked.connect(self.savefile)
        self.ui.openfile.clicked.connect(self.openfile)
        self.ui.connect.clicked.connect(self.connect)
        self.ui.sendfile.clicked.connect(self.sendfile)
        self.ui.clear.clicked.connect(self.clear)
        self.ui.flash.clicked.connect(self.flash)
        self.ui.bufferView.execCommand.connect(self.parse)
        self.ui.edit.clicked.connect(self.sf_launch)

        # Printer Commands
        self.ui.rev.clicked.connect(self.rev)
        self.ui.state.clicked.connect(self.state)
        self.ui.pwron.clicked.connect(self.pwron)
        self.ui.ok.clicked.connect(self.ok)
        self.ui.dooropen.clicked.connect(self.door_open)
        self.ui.doorclose.clicked.connect(self.door_close)
        self.ui.tap.activated.connect(self.tap)
        self.ui.vtap.activated.connect(self.vtap)
        self.ui.component.activated.connect(self.component)

        # FM Trace Commands
        self.ui.on.clicked.connect(self.on)
        self.ui.off.clicked.connect(self.off)
        self.ui.get.clicked.connect(self.get)
        self.ui.startup_check.stateChanged.connect(self.set_startup)
        self.ui.slow_check.stateChanged.connect(self.on)
        self.ui.flows_check.stateChanged.connect(self.on)
        self.ui.globals_check.stateChanged.connect(self.on)
        self.ui.locals_check.stateChanged.connect(self.on)
        self.ui.keywords_check.stateChanged.connect(self.on)
        self.ui.nosweep.clicked.connect(self.nosweep)
        self.ui.tick.clicked.connect(self.tick)
        self.ui.tock.clicked.connect(self.tock)
        self.ui.reset.clicked.connect(self.reset)
        self.ui.depth.valueChanged.connect(self.depth)
        self.ui.depth.sliderPressed.connect(self.depth)
        self.ui.single.activated.connect(self.single)
        self.ui.single.lineEdit().returnPressed.connect(self.single)

        # FM Debug Commands
        self.ui.flow_break.activated.connect(self.flow_break)
        self.ui.flow_break.lineEdit().returnPressed.connect(self.flow_break)
        self.ui.global_break.activated.connect(self.global_break)
        self.ui.global_break.lineEdit().returnPressed.connect(self.global_break)
        self.ui.global_break_value.activated.connect(self.global_break_value)
        self.ui.global_break_value.lineEdit().returnPressed.connect(self.global_break_value)
        self.ui.fmstep.clicked.connect(self.fmstep)
        self.ui.fmnext.clicked.connect(self.fmnext)
        self.ui.fmreturn.clicked.connect(self.fmreturn)
        self.ui.fmgo.clicked.connect(self.fmgo)
        self.ui.fmbt.setEnabled(False)
        self.ui.fmbt.clicked.connect(self.fmbt)
        self.ui.fmclear.clicked.connect(self.fmclear)

        # DSIDs, Underware, FM Variables
        self.ui.dsids.itemDoubleClicked.connect(self.send_item)
        self.ui.dsid_numbers.itemDoubleClicked.connect(self.send_item)
        self.ui.underware.itemDoubleClicked.connect(self.enter_item)
        self.ui.globals.itemDoubleClicked.connect(self.send_item)
        self.ui.constants.itemDoubleClicked.connect(self.send_item)
        self.ui.named.itemDoubleClicked.connect(self.send_item)

        # User Favorites
        for i in xrange(Gui.NUM_USER_LINES):
            self.ui.__dict__['user'+str(i)].returnPressed.connect(lambda which=i: self.send(which))
            self.ui.__dict__['send'+str(i)].clicked.connect(lambda checked=False, which=i: self.send(which))

        for i in xrange(Gui.NUM_HIGHLIGHT_LINES):
            self.ui.__dict__['hltext'+str(i)].textChanged.connect(lambda text: self.setHighlights())
            self.ui.__dict__['hlcolor'+str(i)].colorChanged.connect(self.setHighlights)

        # self.show()
        self.process_events()

        # Options
        self.ui.revLabel.setText("Sift "+REV)
        if 'gui' in user_options: self.ui.guiOption.setChecked(user_options['gui'])
        if 'talk' not in user_options:
            # Per Erik:  Don't ask on Windows, since we can get it from FlexTool
            if os.name != 'nt':
                talk = QtGui.QMessageBox.question(self, "Auto search for .all",
                        "Would you like Sift to automatically search for a .all file at startup?  " + \
                        "Please note that this may take a long time if you have lots of builds or " + \
                        "your filesystem is uncached.  You can change this option at any time via " + \
                        "the Options Tab.",
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
                self.set_option('talk', talk == QtGui.QMessageBox.No)
            else:
                self.set_option('talk', False)
        self.ui.searchOption.setChecked(not user_options['talk'])
        if 'autoupdate' in user_options: self.ui.updateOption.setChecked(user_options['autoupdate'])
        if 'sdv' in user_options: self.ui.sdvOption.setChecked(user_options['sdv'])
        if 'debug' in user_options: self.ui.debugOption.setChecked(user_options['debug']) 
        if 'raw' in user_options: self.ui.rawOption.setChecked(user_options['raw']) 
        if 'prerelease' in user_options: self.ui.prereleaseOption.setChecked(user_options['prerelease'])
        if 'reset' in user_options: self.ui.resetOption.setChecked(user_options['reset']) 
        if 'sdv_host' in user_options: self.ui.sdvHost.setText(user_options['sdv_host'])
        self.update()

        self.ui.guiOption.toggled.connect(lambda checked, which='gui': self.set_option(which, checked))
        self.ui.searchOption.toggled.connect(lambda checked, which='talk': self.set_option(which, checked, inverse=True))
        self.ui.updateOption.toggled.connect(lambda checked, which='autoupdate': self.set_option(which, checked))
        # self.ui.lastPortOption.toggled.connect(lambda checked, which='last_port': self.set_option(which, checked))
        self.ui.sdvOption.toggled.connect(lambda checked, which='sdv': self.set_option(which, checked))
        self.ui.debugOption.toggled.connect(lambda checked, which='debug': self.set_option(which, checked))
        self.ui.rawOption.toggled.connect(lambda checked, which='raw': self.set_option(which, checked))
        self.ui.prereleaseOption.toggled.connect(lambda checked, which='prerelease': self.set_option(which, checked))
        self.ui.sdvHost.textChanged.connect(lambda text, which='sdv_host': self.set_text_option(which, text))
        self.ui.resetOption.toggled.connect(lambda checked, which='reset': self.set_option(which, checked))

    def set_title(self):
        title = "Sift"
        if options.title:
            title += ' "'+options.title+'"'
        try:
            title += " ("+str(printer.port.name)+")"
        except AttributeError:
            pass
        self.setWindowTitle(title)
        
    def dragEnterEvent(self, event):
        mimedata = event.mimeData()
        if mimedata and mimedata.hasUrls():
            if mimedata.urls()[0].toLocalFile():
                event.acceptProposedAction()

    def dropEvent(self, event):
        mimedata = event.mimeData()
        if mimedata and mimedata.hasUrls():
            cmd = "open"
            for url in mimedata.urls():
                file = str(url.toLocalFile())
                if file:
                    cmd += " '" + file + "'"
            self.parse(cmd)

    def closeEvent(self, event):
        global options
        global quit_event

        QtCore.QSettings().setValue("geometry", self.saveGeometry())
        options.gui = False      # sends any remaining output to stdout
        quit_event.set()

        try:
            f = open(os.path.join(SIFT_CONFIG_DIR, FAVORITE_FILE), 'w')
            for i in xrange(Gui.NUM_USER_LINES):
                f.write(str(self.ui.__dict__['user'+str(i)].text())+EOLN)
            f.close()
        except IOError: pass

        try:
            f = open(os.path.join(SIFT_CONFIG_DIR, HIGHLIGHT_FILE), 'w')
            for i in xrange(Gui.NUM_HIGHLIGHT_LINES):
                color = self.ui.__dict__['hlcolor'+str(i)].color()
                f.write('%02x%02x%02x;' % (color.red(), color.green(), color.blue()))
                f.write(str(self.ui.__dict__['hltext'+str(i)].text())+EOLN)
            f.close()
        except IOError: pass

    def run(self):
        """Run the main QT event loop"""
        self.app.exec_()
        
    def periodic_tick(self):
        """Periodic tick for some Python interpreter time to catch ^C and kills"""
        # if gui.pace > 100:
        #     time.sleep(.1)
        # elif gui.pace > 1000:
        #     time.sleep(.5)
        pass
        
    def aboutToQuit(self):
        """Recommended method to cleanup because exec_() is not guaranteed to return"""
        cleanup() 

    def handle_exception(self, message):
        """Gui exception handler called via a signal from other threads."""
        reply = QtGui.QMessageBox.critical(self, "Sift Error", message,
                      QtGui.QMessageBox.Abort, QtGui.QMessageBox.Abort )
        quit_event.set()
        cleanup()
        sys.exit(1)

    def process_events(self):
        """Allow long executions in Sift to give the GUI some CPU time"""
        self.app.processEvents(QtCore.QEventLoop.AllEvents, 100)

    def sendfile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Send Print File", shelf['send_dir'],
                "Print files (*.prn *.pcl);;All files (*.*)",
                options=QtGui.QFileDialog.DontResolveSymlinks)
        if filename:
            filename = str(filename)
            self.parse("lp "+filename)
            shelf['send_dir'] = os.path.dirname(filename)

    def openfile(self):
        """Open Files""" 
        filenames = QtGui.QFileDialog.getOpenFileNames(self, "Open File", shelf['open_dir'],
                "Symbol Files (*.all *.i *.hlg *.lua);;Raw Trace Files (*.txt *.log *.raw *.bin);;Lua Files (*.lua *.luc);;All files (*.*)",
                options=QtGui.QFileDialog.DontResolveSymlinks)
        if len(filenames) > 0:
            cmd = "open"
            for f in filenames:
                cmd += " '" + f + "'"
            self.parse(cmd)
            shelf['open_dir'] = os.path.dirname(str(filenames[0]))


    def sf_launch(self):
        if(not siftflow):
            print 'SiftFlow not available.'
            return

        try:
            self.siftFlowWin = SiftFlow(self)
        except:
            print "SiftFlow Launch Error: "
            print "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
            return

        self.siftFlowWin.loadProject(file_dirs, project_dir, project_name, project_type)
        self.siftFlowWin.show()

        #Disable edit button so only one instance of siftflow can be run at a time, reenabled in siftflows closeEvent
        self.ui.edit.setDisabled(True)
        UsageThread("edit").start()

    def sf_reload(self):
        if(self.siftFlowWin != None and self.siftFlowWin.isVisible()):
            self.siftFlowWin.loadProject(file_dirs, project_dir, project_name, project_type)

    def sf_displayFlow(self, flowName):
        if(not siftflow):
            print 'SiftFlow not available.'
            return

        if(self.siftFlowWin != None and self.siftFlowWin.isVisible()):
            self.siftFlowWin.displayFlowFromSift(flowName, project_name)
        elif((self.siftFlowWin == None) or (self.siftFlowWin != None and not self.siftFlowWin.isVisible())):
            self.sf_launch()
            self.siftFlowWin.displayFlowFromSift(flowName, project_name)

    def savefile(self):
        # Try to create a convenient, unique filename
        dir = shelf['save_dir']
        if not os.path.isdir(dir):
            dir = os.path.expanduser("~")
        default_base = os.path.join(dir,datetime.datetime.now().strftime("%y%b%d"))
        for id in xrange(1,999):
            default_name = "%s_%03d.sift" % (default_base, id)
            if not os.path.isfile(default_name):
                break
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save trace", default_name)
        if filename:
            filename = str(filename)
            shelf['save_dir'] = os.path.dirname(filename)
            self.parse("save "+filename)
            
    def set_serial(self, i, n=0):
        self.cui.serial_radio.setChecked(True)

    def set_usb(self, i, n=0):
        self.cui.usb_radio.setChecked(True)

    def set_pcs(self, i, n=0):
        self.cui.pcs_radio.setChecked(True)

    def set_ip(self, i, n=0):
        self.cui.ip_radio.setChecked(True)

    def refresh_ports(self):
        """Refresh the dynamic fields of an active connect dialog."""
        self.load_ports()

    def start_pcs(self):
        try:
            PCSPort().start_server()
            time.sleep(.3)
        except NoService, e:
            output_str("Couldn't start PCS on this PC."+EOLN, "warning")
            print "NoService:", e
        self.load_ports()

    def load_ports(self, default_port=None, allow_serial=None,
        allow_usb=None, allow_pcs=None, allow_ip=None, allow_noconn=None):
        """Load up all the dynamic fields of the connect dialog."""

        self.cui.serial_radio.setEnabled(False)
        self.cui.serial_port.setEnabled(False)
        self.cui.serial_port.clear()
        self.cui.usb_radio.setEnabled(False)
        self.cui.usb_port.setEnabled(False)
        self.cui.usb_port.clear()
        self.cui.ip_port.clear()
        self.cui.pcs_radio.setEnabled(False)
        self.cui.pcs_port.setEnabled(False)
        self.cui.port_start_pcs.setEnabled(False)
        self.cui.pcs_port.clear()
        self.process_events()

        # static defaults
        if default_port is not None:
            self.default_port = default_port
        if allow_serial is not None:
            self.allow_serial = allow_serial
        if allow_usb is not None:
            self.allow_usb = allow_usb
        if allow_pcs is not None:
            self.allow_pcs = allow_pcs
        if allow_ip is not None:
            self.allow_ip = allow_ip
        if allow_noconn is not None:
            self.allow_noconn = allow_noconn

        # serial ports (FUTURE: determine if ports are actually available) 
        if not self.default_port: 
            self.default_port = "3kn3jidj"

        if pyserial:
            if os.name == "nt":             # load serial ports
                for i in xrange(1,10):
                    self.cui.serial_port.addItem("COM"+str(i))
            elif sys.platform == "darwin":
                self.cui.serial_port.addItem("/dev/cu.usbserial")
            else: 
                for i in xrange(0,9): 
                    if os.path.exists("/dev/ttyS"+str(i)):
                         self.cui.serial_port.addItem("/dev/ttyS"+str(i))
            if self.cui.serial_port.count() == 0:
                self.cui.serial_port.addItem("Not available")
            else:
                if self.allow_serial: 
                    self.cui.serial_radio.setEnabled(True)
                self.cui.serial_port.setEnabled(True)
        else:
            self.cui.serial_port.addItem("pySerial not installed")
            self.cui.serial_port.setToolTip("Get from http://pyserial.sourceforge.net")
        self.process_events()

        # direct USB ports
        if os.name == "posix":
            if os.path.exists("/dev/usb"):
                for dev in os.listdir("/dev/usb"):
                    self.cui.usb_port.addItem("/dev/usb/"+dev)
            if self.cui.usb_port.count() == 0:
                if self.allow_usb:
                    if pcs_printers:
                        self.cui.usb_port.addItem("PCS running instead")
                    else:
                        self.cui.usb_port.addItem("No printers found")
                        self.cui.usb_port.setToolTip("Plug in or powerup printer")
                        self.cui.usb_radio.setToolTip("Plug in or powerup printer")
                else:
                    self.cui.usb_port.addItem("Not available")
        else:
            self.cui.usb_port.addItem("Not avail on Windows")
        if self.allow_usb and self.cui.usb_port.count() > 0:
            self.cui.usb_radio.setEnabled(True)
            self.cui.usb_port.setEnabled(True)
        else:
            self.cui.usb_radio.setEnabled(False)
            self.cui.usb_port.setEnabled(False)
        self.process_events()

        # IP addresses
        if self.allow_ip:
            self.cui.ip_radio.setEnabled(True)
        else:
            self.cui.ip_radio.setEnabled(False)
        try:                       
            with open(os.path.join(SIFT_CONFIG_DIR, IPADDRESS_FILE)) as f:
                for line in f:
                    line = line.strip() 
                    if self.cui.ip_port.findText(line) == -1:
                        self.cui.ip_port.addItem(line)
        except IOError: pass
        self.process_events()

        # No connection
        if self.allow_noconn:
            self.cui.noconn_radio.setEnabled(True)
        else:
            self.cui.noconn_radio.setEnabled(False)

        # PCS Printers
        try:
            pcs_printers = PCSPort().printers()
        except (NoService, LostService), e:
            if options.debug: print e 
            pcs_printers = None
            self.cui.pcs_port.addItem("PCS not running")
            self.cui.pcs_port.setToolTip("You need to Start PCS.")
            self.cui.port_start_pcs.setEnabled(True)
        else:
            if len(pcs_printers) > 0:
                for id, model, serial in pcs_printers:
                    if (model and serial):
                        self.cui.pcs_port.addItem(model+' '+serial)
                    else:
                        self.cui.pcs_port.addItem(id)
                self.cui.pcs_radio.setEnabled(True)
                self.cui.pcs_port.setEnabled(True)
            else:
                self.cui.pcs_port.addItem("PCS running, no printers found")
                self.cui.pcs_port.setToolTip("Plug in or powerup printer")
        self.process_events()

        # Try to set the default
        class DefaultFound(Exception): 
            pass
        try: 
            is_default = self.cui.usb_port.findText(self.default_port)
            if is_default > -1:
                self.cui.usb_radio.setChecked(True)
                self.cui.usb_port.setCurrentIndex(is_default)
                raise DefaultFound 
            if "pcs" in self.default_port:
                self.cui.pcs_radio.setChecked(True)
                is_default = self.cui.pcs_port.findText(self.default_port)
                if is_default > -1:
                    self.cui.pcs_port.setCurrentIndex(is_default)
                raise DefaultFound 
            for i in xrange(self.cui.ip_port.count()):
                if str(self.cui.ip_port.itemText(i)) in self.default_port:
                    self.cui.ip_port.setCurrentIndex(i)
                    self.cui.ip_radio.setChecked(True)
                    raise DefaultFound 
            if self.default_port == "No Connection":
                self.cui.noconn_radio.setChecked(True)
                raise DefaultFound 
            self.cui.serial_radio.setChecked(True)
            is_default = self.cui.serial_port.findText(self.default_port)
            if is_default > -1:
                self.cui.serial_port.setCurrentIndex(is_default)
        except DefaultFound:
                pass
        self.process_events()

    def select_port(self, label=None):
        dialog = QtGui.QDialog(self)
        self.cui = Ui_ConnectDialog()
        self.cui.setupUi(dialog)
        dialog.show() 
        self.process_events()

        self.cui.serial_port.lineEdit().cursorPositionChanged.connect(self.set_serial)
        self.cui.usb_port.lineEdit().cursorPositionChanged.connect(self.set_usb)
        self.cui.pcs_port.lineEdit().cursorPositionChanged.connect(self.set_pcs)
        self.cui.ip_port.lineEdit().cursorPositionChanged.connect(self.set_ip)
        self.cui.port_refresh.clicked.connect(self.refresh_ports)
        self.cui.port_start_pcs.clicked.connect(self.start_pcs)
        if label:
            self.cui.label.setText(label)

        try:
            current_port = printer.port.name
        except:
            current_port = None
        self.load_ports(default_port=current_port, allow_serial=True, allow_usb=False,
                allow_pcs=True, allow_ip=True, allow_noconn=True)

        result = None
        if (dialog.exec_()):
            if self.cui.serial_radio.isChecked():
                result = str(self.cui.serial_port.currentText())
            elif self.cui.usb_radio.isChecked():
                result = str(self.cui.usb_port.currentText())
            elif self.cui.pcs_radio.isChecked():
                if self.cui.pcs_port.currentText():
                    # REVISIT, we're assuming the last, fixed 10 digits will
                    # end up exactly within the Device ID. When this was 14, this
                    # was a false, we accidently grabbed some of the model number.
                    # This 'currentText' is set above in load_ports, then the
                    # result is used in PCS open to identify a printer.
                    result = "pcs#%s" % self.cui.pcs_port.currentText()[-10:]
                else:
                    result = "pcs"
            elif self.cui.ip_radio.isChecked():
                self.cui.ip_port.addItem(self.cui.ip_port.currentText())
                try:
                    with open(os.path.join(SIFT_CONFIG_DIR, IPADDRESS_FILE), 'w') as f:
                        for i in xrange(0, self.cui.ip_port.count()):
                            ip = str(self.cui.ip_port.itemText(i)).strip()
                            if len(ip) > 0:
                                f.write(ip+'\n')
                except IOError: pass
                result = str(self.cui.ip_port.currentText())
            elif self.cui.noconn_radio.isChecked():
                result = "none"

        return result

    def connect(self):
        port = self.select_port(label="Connect to printer via:")
        if port:
            self.parse("port " + port)

    def load_tab(self, index):
        """Load the given tab with it's dynamic data"""
        if (not self.favorites_loaded) and (index == self.ui.Tabs.indexOf(self.ui.UserTab)):
            self.data_ready_event.wait(2)
            if self.data_ready_event.isSet():
                for i in xrange(Gui.NUM_USER_LINES):
                    gui_completer = QtGui.QCompleter(everything)
                    gui_completer.setModelSorting(QtGui.QCompleter.CaseInsensitivelySortedModel)
                    if QtCore.QT_VERSION >= 0x040600 and QtCore.PYQT_VERSION >= 0x040700:
                        # This was in Qt 4.6, but PyQt doesn't provide access
                        # to it until sometime later...  Since Riverbank is
                        # stingy about providing historical changelogs and
                        # releases, the 4.7 check is a complete wild guess
                        gui_completer.setMaxVisibleItems(30)
                    gui_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                    self.ui.__dict__['user'+str(i)].setCompleter(gui_completer)
                    gui.process_events()

                self.favorites_loaded = True

        if (not self.dsids_loaded) and (index == self.ui.Tabs.indexOf(self.ui.DSIDTab)):
            self.data_ready_event.wait(2)
            if self.data_ready_event.isSet():
                count = 0
                dsid_names = []
                dsid_numbers = []
                for dsid in dsids:
                    if not dsid.startswith("DSID_"):
                        dsid_names.append("%s  (%05d)" % (dsid, int(dsids_by_name[dsid])))
                dsid_names.sort()
                self.ui.dsids.addItems(dsid_names)
                self.process_events();

                for dsid in dsids:
                    if not dsid.startswith("DSID_"):
                        dsid_numbers.append("(%05d)  %s" % (int(dsids_by_name[dsid]),dsid))
                dsid_numbers.sort()
                self.ui.dsid_numbers.addItems(dsid_numbers)
                self.dsids_loaded = True

        elif (not self.underware_loaded) and (index == self.ui.Tabs.indexOf(self.ui.UnderwareTab)):
            self.data_ready_event.wait(2)
            if self.data_ready_event.isSet():
                self.ui.underware.addItems(underware)
                self.underware_loaded = True

        elif (not self.variables_loaded) and (index == self.ui.Tabs.indexOf(self.ui.VariablesTab)):
            self.data_ready_event.wait(2)
            if self.data_ready_event.isSet():
                if len(global_names):
                    globals_sorted = global_names.keys()
                    globals_sorted.sort()
                    self.ui.globals.addItems(globals_sorted)
                    self.process_events()
                    if not self.global_breaks_loaded:
                        self.ui.global_break.addItem("");
                        self.ui.global_break.addItems(globals_sorted)
                        self.global_breaks_loaded = True
                        self.process_events()

                consts = []
                named  = []
                for name, value in constant_name2value.items():
                    id = constant_names[name]
                    if (id == "-1"): named.append(("%s = %s" % (name, value)).upper())
                    else:            consts.append(("%s = %s" % (name, value)).upper())
                self.process_events()
                consts.sort()
                named.sort()
                self.ui.constants.addItems(consts)
                self.process_events()
                self.ui.named.addItems(named)
                self.variables_loaded = True

    def load_tabs(self):
        """Force load all the tabs. Usually after a new .all file is loaded"""
        self.load_tab(self.ui.Tabs.indexOf(self.ui.UserTab))
        self.load_tab(self.ui.Tabs.indexOf(self.ui.DSIDTab))
        self.load_tab(self.ui.Tabs.indexOf(self.ui.UnderwareTab))
        self.load_tab(self.ui.Tabs.indexOf(self.ui.VariablesTab))

    def io_ready(self):
        self.ioready.emit()

    def handle_ioready(self):
        """A new I/O connection to the printer has been established"""
        self.ui.flash.setEnabled(True)
        self.ui.sendfile.setEnabled(True)
        self.set_title()

    def data_ready(self, first_time = False):
        self.first_time = first_time
        self.dataready.emit()

    def handle_dataready(self):
        """The .i/.hlg files have been loaded"""
        global everything
        global dsids
        global underware
        global constant_names

        self.data_ready_event.set()
        gui.process_events()

        # Make sure everything is cleared
        if not self.first_time:
            self.ui.single.clear()
            self.ui.flow_break.clear()
            self.ui.global_break.clear()
            self.ui.input.clear()
            self.dsids_loaded = False
            self.ui.dsids.clear()
            self.ui.dsid_numbers.clear()
            self.underware_loaded = False
            self.ui.underware.clear()
            self.variables_loaded = False
            self.ui.globals.clear()
            self.ui.global_break.clear()

        # Tab enables
        self.ui.Tabs.setTabEnabled(self.ui.Tabs.indexOf(self.ui.DSIDTab), len(dsids) > 0)
        self.ui.Tabs.setTabEnabled(self.ui.Tabs.indexOf(self.ui.UnderwareTab), len(underware) > 0)
        self.ui.Tabs.setTabEnabled(self.ui.Tabs.indexOf(self.ui.VariablesTab), len(global_names)+len(constant_names) > 0)

        # trace singles
        if len(flows) + len(keywords) > 0:
            self.ui.single.addItem("")
            self.ui.single.addItems(flows)
            self.ui.single.addItems(keywords)
            self.ui.single.setEnabled(True)
            self.ui.label_4.setEnabled(True)
        else:
            self.ui.single.setEnabled(False)
            self.ui.label_4.setEnabled(False)

        # break singles
        if len(flows) + len(global_names) > 0:
            self.ui.flow_break.addItem("")
            self.ui.flow_break.addItems(flows)
            globals_sorted = global_names.keys()
            globals_sorted.sort()
            self.process_events()
            self.ui.global_break.addItem("");
            self.ui.global_break.addItems(globals_sorted)
            self.ui.FMDebug.setEnabled(True)
        else:
            self.ui.FMDebug.setEnabled(False)

        # main input text
        self.ui.input.addItems(everything)
        self.ui.input.addItems(history)
        self.ui.input.setCurrentIndex(self.ui.input.count()-1)
        self.ui.input.clearEditText()
        self.ui.input.lineEdit().setFocus()
        self.ui.status2.setText(self.filename[-30:])
        gui.process_events()

        # load tabs
        if not self.first_time:              # The first time we load only on demand
            self.load_tabs()

        #Reload SiftFlow
        self.sf_reload()

    def write(self, text):              # Stdout compatibility (filter non-printables first)
        t0 = time.clock()
        self.ui.bufferView.insertPlainText(text)
        self.write_time += time.clock() - t0

    def flush(self):                    # Stdout compatibility
        self.process_events()

    def parse(self, text):
        """Parse the given Sift command"""
        text = str(text).strip()        # Might be a QString
        if command_parser:
            output_str(text+EOLN,"F")
            command_parser.put(text)
        else:
            output_str("Sift startup wasn't complete, try again.","error")
        self.ui.input.lineEdit().setFocus()

    # Misc little buttons
    def rev(self):              self.parse("rev")
    def state(self):            self.parse("ds2.get 65541")
    def tap(self):              self.parse("tap "+str(self.ui.tap.currentText()))
    def vtap(self):             self.parse("vtap "+str(self.ui.vtap.currentText()))
    def door_open(self):        self.parse("door open")
    def door_close(self):       self.parse("door close")
    def tick(self):             self.parse("tick")
    def tock(self):             self.parse("tock")
    def nosweep(self):          self.parse("nosweep")
    def off(self):              self.parse("trace off")
    def get(self):              self.parse("trace get")
    def flash(self):            self.parse("flash")
    def fmstep(self):           self.parse("step")
    def fmnext(self):           self.parse("next")
    def fmreturn(self):         self.parse("finish")
    def fmgo(self):             self.parse("go")
    def fmbt(self):             self.parse("bt")
    def pwron(self):            self.parse("power on")
    def ok(self):               self.parse("ok")

    def update(self):
        """Update any dynamic GUI things"""
        if ("sdv" in user_options) and user_options["sdv"]:
            self.ui.browse.setText("SDV")
        else:
            self.ui.browse.setText("Browse")

    def set_option(self, name, checked, inverse=False):
        """Set options by name and save in persistent storage."""
        if inverse: checked = not checked
        options.__dict__[name] = checked
        user_options[name] = checked
        self.update()
        write_items(user_options, os.path.join(SIFT_CONFIG_DIR, SETTINGS_FILE))

    def set_text_option(self, name, text):
        user_options[name] = str(text)
        self.update()
        write_items(user_options, os.path.join(SIFT_CONFIG_DIR, SETTINGS_FILE))

    def component(self):
        """On_dbug. Sorry, named it component because that's what the first XXXX is called."""
        index = self.ui.component.currentIndex()
        text  = str(self.ui.component.currentText())
        m = on_dbug_re.match(text)
        if m:
            comp  = m.group("component").upper()
            if m.group("level"): level = int(m.group("level"))
            else:                level = 10
            display_text = comp + " " + str(level)
            send_text = '"%-4s" %d' % (comp, level)
            self.parse("on_dbug " + send_text)
            self.ui.component.setItemText(index, display_text)
            if self.ui.component.count() > 0:
                try:
                    f = open(os.path.join(SIFT_CONFIG_DIR, ONDBUG_FILE),"w")
                except IOError: pass
                else:
                    for i in range(0, self.ui.component.count()):
                        if on_dbug_re.match(str(self.ui.component.itemText(i))):
                            f.write(self.ui.component.itemText(i)+"\n")
                    f.close()
        else:
            self.parse(str(self.ui.component.currentText()))

    def set_startup(self):
        """Set Sift's startup flag"""
        if self.ui.startup_check.isChecked():
            setting = 0
            if self.ui.slow_check.isChecked():     setting += TRACE_FLUSH
            if self.ui.flows_check.isChecked():    setting += TRACE_FLOWS
            if self.ui.globals_check.isChecked():  setting += TRACE_GLOBALS
            if self.ui.locals_check.isChecked():   setting += TRACE_LOCALS
            if self.ui.keywords_check.isChecked(): setting += TRACE_KEYWORDS
            self.parse("trace startup "+str(setting))
        else:
            self.parse("trace startup 0")

    def printer_started_up(self):
        """Printer rebooted"""
        if self.ui.startup_check.isChecked():
            self.set_startup()

    def on(self):
        """Trace On"""
        setting = 0
        if self.ui.slow_check.isChecked():     setting += TRACE_FLUSH
        if self.ui.flows_check.isChecked():    setting += TRACE_FLOWS
        if self.ui.globals_check.isChecked():  setting += TRACE_GLOBALS
        if self.ui.locals_check.isChecked():   setting += TRACE_LOCALS
        if self.ui.keywords_check.isChecked(): setting += TRACE_KEYWORDS
        if (setting != 30):
            self.parse("trace %d" % setting)
        else:
            self.parse("trace on")

    def reset(self):
        """Trace reset"""
        self.ui.single.setCurrentIndex(0)
        self.ui.startup_check.setChecked(False)
        self.ui.slow_check.setChecked(False)
        self.ui.flows_check.setChecked(True)
        self.ui.globals_check.setChecked(True)
        self.ui.locals_check.setChecked(True)
        self.ui.keywords_check.setChecked(True)
        self.ui.depth.setValue(self.ui.depth.maximum())
        self.parse("trace reset")

    def single(self):
        flow = str(self.ui.single.currentText())
        if len(flow):
            self.parse("trace "+str(self.ui.single.currentText()))
        else:
            self.parse("trace reset")

    def depth(self):
        if self.ui.depth.value() == self.ui.depth.maximum():
            self.parse("depth 100")
        else:
            self.parse("depth "+str(self.ui.depth.value()))

    def send_item(self, item):
        if len(self.ui.input.currentText()) > 0:
            self.enter_item(item)
        else:
            item_string = str(item.text()).strip()
            if (" = " in item_string):
                item_string = item_string.split()[0]
            item_string = re.sub("\(\d{5}\)", "", item_string).strip()
            self.parse(item_string)

    def enter_item(self, item):
        item_string = str(item.text()).strip()
        item_string = re.sub("\(\d{5}\)", "", item_string).strip()
        if (" = " in item_string):
            item_string = item_string.split()[0]
        else:
            item_string = item_string.split()[-1]
        current_text = str(self.ui.input.currentText())
        if len(current_text) > 0:
            if current_text[-1].isalnum():
                current_text += " "
        current_text += item_string
        self.ui.input.setEditText(current_text)
        self.ui.input.lineEdit().setFocus()

    def update_history(self):
        """Update command line history -- this is called by a QTimer slightly after a command
           is entered and parsed. The goal is to allow the printer's responses to arrive and display
           ASAP by delaying updating command history while the user isn't doing anything.
           Manipulating the huge QCombobox takes noticeable time on RedHat."""
        text = self.last_input
        self.last_input = None 

        if text and len(text) > 0:
            global history
            global history_pointer
            history.append(text); history_pointer += 1

            # Add a blank entry to create an empty box after entry, also makes up-arrow show the last command entered.
            self.ui.input.addItem("")

            # Remove any previous blank we added before
            count = self.ui.input.count()
            if (count >= 3) and (self.ui.input.itemText(count-3) == ""):
                self.ui.input.removeItem(count-3)

            # Assure we're at the bottom even if the user had selected an item already in the list 
            self.ui.input.setCurrentIndex(self.ui.input.count()-1)

    def input(self):
        """Text box for manual entry commands"""
        self.last_input = uni2str(self.ui.input.currentText())
        self.ui.input.lineEdit().clear()
        self.ui.bufferView.scrollToEnd()
        self.parse(self.last_input)
        QtCore.QTimer.singleShot(200, self.update_history)      # try to hide GUI delays when updating history

    def search(self):
        cmd = uni2str(self.ui.input.currentText())
        if len(cmd) > 0:
            self.parse("/"+cmd+"/")
            self.ui.input.clearEditText()

    def clear(self):
        self.parse("clearlogs")
        self.ui.bufferView.clear()
        self.ui.input.clearEditText()

    def browse(self):
        if ("sdv" in user_options) and (user_options["sdv"]):
            self.parse("sdv")
        else:
            self.parse("browse")

    def flow_break(self):
        self.parse("trace")
        self.parse("break " + self.ui.flow_break.currentText())
    def global_break(self):
        self.parse("trace")
        self.parse("break " + self.ui.global_break.currentText())
    def global_break_value(self):
        self.parse("trace")
        self.parse("break " + self.ui.global_break.currentText() + " " +
                                                  self.ui.global_break_value.currentText())
    def fmclear(self):
        self.ui.flow_break.setCurrentIndex(0)
        self.ui.global_break.setCurrentIndex(0)
        self.ui.global_break_value.setCurrentIndex(0)
        self.parse("clear")
        self.fmgo()

    def send(self, which):
        self.parse(self.ui.__dict__['user'+str(which)].text())

    def setHighlights(self):
        self.ui.bufferView.clearColorMatches()
        for i in xrange(Gui.NUM_HIGHLIGHT_LINES):
            text = self.ui.__dict__['hltext'+str(i)].text()
            if str(text).strip() != '':
                color = self.ui.__dict__['hlcolor'+str(i)].palette().color(QtGui.QPalette.Window)
                self.ui.bufferView.addColorMatch(text, color)


def installThreadExcepthook():
    """
    Workaround for sys.excepthook thread bug
    Call once from __main__ before creating any threads.
    """
    init_old = threading.Thread.__init__
    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run
        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                if sys:
                    sys.excepthook(*sys.exc_info())
        self.run = run_with_except_hook
    threading.Thread.__init__ = init

def handle_exception(exc_type, exc_value, exc_traceback):
    global gui

    filename, line, dummy, dummy = traceback.extract_tb(exc_traceback).pop()
    filename = os.path.basename(filename)
    error = "%s: %s" % (exc_type.__name__, exc_value)

    if not gui:
        # Try to get the terminal window cleaned up
        if os.name == "nt":
            try:    set_text_attr(FOREGROUND_GREY)
            except: pass
        else:
            try:    os.system("stty sane")   # Reset all stty modes to reasonable values
            except: pass

    sys.stderr.write(EOLN
        + "*** Sift Error ***" + EOLN 
        + EOLN
        + "Sorry about this. You just found a bug. You can help us improve Sift" + EOLN
        + "by sending the following text to sift@hp.com. Again, so sorry." + EOLN
        + EOLN
        + "Sift Revision " + REV + EOLN
        + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

    if gui:
        gui.exception.emit(
          "Sorry about this. You just found a Sift bug. You can help improve Sift by "
          + "sending the following text along with a short description to "
          + "<a href='mailto:sift@hp.com'>sift@hp.com</a>:<br/><br/>"
          + "<span style='color:darkgreen'>"
          + "Sift Revision " + REV + "<br/><br/>"
          + "%s" % error
          + ". It occured at line %d of file %s.</span><br/><br/>" % (line, filename)
          + "Again, sorry and thank you for your help.")

    else:
        quit_event.set()
        cleanup()
        sys.exit(1)



######################################################################################################
#
# Help
#
######################################################################################################

def interactive_help(short = False):
    if not short:
        output_str('-------------------------------------------------------------------------------'+EOLN)
        output_str('| Sift Help                                                                   |'+EOLN)
        output_str('-------------------------------------------------------------------------------'+EOLN)
        output_str('| <text>            - <text> sent to printer (serial only)                    |'+EOLN)
        output_str('| <under.ware>      - Send underware to printer                               |'+EOLN)
        output_str('| /something/       - Search for something                                    |'+EOLN)
        output_str('| ENTER             - Pause/resume output                                     |'+EOLN)
        output_str('|                                                                             |'+EOLN)
        output_str('| PRINTER QUERIES, WATCHING DSIDs, FLOW AND KEYWORD CALLING                   |'+EOLN)
        output_str('| <variable> [=val] - Query or set an FML variable                            |'+EOLN)
        output_str('| <dsidname> [=val] - Query or set a DSID ("DSID_" optional, ignores case)    |'+EOLN)
        output_str('| watch <dsidname>  - Watch changes to a DSID live (e.g. watch machine_state) |'+EOLN)
        output_str('| flow_name(1,2)    - Call flow                                               |'+EOLN)
        output_str('| cmd_name(1,2)     - Call keyword                                            |'+EOLN)
        output_str('|                                                                             |'+EOLN)
        output_str('| TRACE CONTROL                                                               |'+EOLN)
        output_str('| help trace        - Displays Debug Help Window for Trace Control            |'+EOLN)
        output_str('|                                                                             |'+EOLN)
        output_str('| DEBUGGING                                                                   |'+EOLN)
        output_str('| help debug        - Displays Debug Help Window for Debugging                |'+EOLN)
        output_str('|                                                                             |'+EOLN)
        output_str('| CONVENIENCE COMMANDS                                                        |'+EOLN)
        output_str('| rev               - Query firmware revision                                 |'+EOLN)
        output_str('| tap #   vtap #    - Button tap and virtual tap                              |'+EOLN)
        output_str('| door open|close   - Open/close the main door                                |'+EOLN)
        output_str('| dot4              - Enable dot4                                             |'+EOLN)
        output_str('| ok                - Front panel "OK"                                        |'+EOLN)
        output_str('| flash <filename>  - Flash printer (Linux only via USB cable)                |'+EOLN)
        output_str('| help <substring>  - Search for <substring> within all identifiers           |'+EOLN)
        output_str('| !linux_cmd        - Execute linux command in shell                          |'+EOLN)
        output_str('| q                 - Quit (and save log file)                                |'+EOLN)
        output_str('-------------------------------------------------------------------------------'+EOLN)
    else:
        output_str(" Home page:        ", "args")
        output_str("http://sift.vcd.hp.com/" +EOLN)

        if not gui:
            output_str(" Command summary:  ", "args")
            output_str("-> help sift" +EOLN)
            output_str(" Start trace with: ", "args")
            output_str("-> trace" +EOLN)
            output_str(" Get FW revision:  ", "args")
            output_str("-> rev" +EOLN)

def help_trace():
    output_str('-------------------------------------------------------------------------------'+EOLN)
    output_str('| TRACE CONTROL HELP                                                          |'+EOLN)
    output_str('-------------------------------------------------------------------------------'+EOLN)
    output_str('| trace [on|off]    - Enable and disable serial tracing                       |'+EOLN)
    output_str('| tick | tock       - Enable/disable periodic tick tracing                    |'+EOLN)
    output_str('| sweep | nosweep   - Enable/disable print sweep control tracing              |'+EOLN)
    output_str('| trace get         - Retrieve INTERNAL RAM trace buffer                      |'+EOLN)
    output_str('| trace fill        - Fill up INTERAL RAM buffer fully and then stop          |'+EOLN)
    output_str('| trace start       - Start continuous INTERAL RAM buffer (powerup default)   |'+EOLN)
    output_str('| trace <flow>      - Trace only a given flow or keyword                      |'+EOLN)
    output_str('| trace <f> <f>     - Trace a range of flows or keywords                      |'+EOLN)
    output_str('| depth <value>     - Max call depth to show (100 is default, 3 is nice)      |'+EOLN)
    output_str('| level <value>     - 0=Off 10=Normal 20=PeriodicTick 30=Verbose Loops        |'+EOLN)
    output_str('| trace [slow] [flows] [globals] [locals] [keywords] - Trace only these       |'+EOLN)
    output_str('| trace reset       - Reset all trace settings to default                     |'+EOLN)
    output_str('-------------------------------------------------------------------------------'+EOLN)

def help_debug():
    output_str('-------------------------------------------------------------------------------'+EOLN)
    output_str('| DEBUGGING HELP                                                              |'+EOLN)
    output_str('-------------------------------------------------------------------------------'+EOLN)
    output_str('| b <flow_name>     - Breakpoint on first statement of a flow                 |'+EOLN)
    output_str('| b <file>:<line>   - Breakpoint at file:line (e.g. "b pen:7136")             |'+EOLN)
    output_str('| b <varname> <val> - Breakpoint on variable write, <val> is optional         |'+EOLN)
    output_str('| b <linel>         - Breakpoint on line in current file                      |'+EOLN)
    output_str('| l[ist]            - Lists current locations fml code (advancing on next l)  |'+EOLN)
    output_str('| l <flow_name>     - List flow source code                                   |'+EOLN)
    output_str('| l <file>:<line>   - Lists source code in file starting at line number       |'+EOLN)
    output_str('| l.                - Lists source code around break point or assert          |'+EOLN)
    output_str('| l+ or l-          - Advance 10 lines forward(+) or back(-) in source code   |'+EOLN)
    output_str('| l <line>          - Lists source code in current file at line number        |'+EOLN)
    output_str('| o[pen]            - Open current fml file                                   |'+EOLN)
    output_str('| o[pen] <file>     - Opens file if in current directroy or path given        |'+EOLN)
    output_str('| g[o]              - Run after hitting breakpoint                            |'+EOLN)
    output_str('| s[tep]            - Step one statement (step into flows)                    |'+EOLN)
    output_str('| n[ext]            - Run to next statement (step over flows)                 |'+EOLN)
    output_str('| f[inish]          - Finish current flow (step out of flow)                  |'+EOLN)
    output_str('| c[lear]           - Clear all breakpoints                                   |'+EOLN)
    output_str('-------------------------------------------------------------------------------'+EOLN)


####################################################################################################
#
# Process Command Line Options
#
####################################################################################################

def process_options():
    global options
    global args
    global dot_all_file
    global dot_all_file_path
    config_dict = {}
    global max_output_file_size
    global popen_editor_of_choice
    global socket_host
    global socket_port_number
    global using_socket
    global html_output_size
    global pcs_channel
    global pcs_printer_id
    global give_gui_install_info
    global user_options
    global shelf

    using_socket = False

    # User defined default command line arguments
    try:
        config = ConfigParser.ConfigParser()
        config.read([os.path.join(SIFT_CONFIG_DIR, SIFT_INI)])
        arg_options = config.options("Arguments")
        for option in arg_options:
            config_dict[option] = config.get("Arguments",option).strip()
            if option == "indent" and config_dict[option] == "tab":
                config_dict[option] = "\t"
    except:
        pass

    # so people do not need to put large numbers in ini file for max size
    units = {"KB" : 1024, "MB" : 1048576, "GB" : 1073741824}

    # Sets how big output file can grow before it is copied over to back up file
    try:
        max_output_file_size = DEFAULT_OUTPUT_FILE_SIZE
        arg_options = config.options("Max_Output_File_Size")
        for option in arg_options:
            if option == "maxsize":
                val = config.get("Max_Output_File_Size",option.strip())
                val_set = False
                for keys in units:
                    if keys in val:
                        val = int(val.strip(keys))
                        max_output_file_size = val * units[keys]
                        val_set = True
                        break

                if not val_set:
                    max_output_file_size = int(val)
    except:
        max_output_file_size = DEFAULT_OUTPUT_FILE_SIZE


    # Sets text editor to use when using open command
    try:
        popen_editor_of_choice = ""
        arg_options = config.options("Editor")
        for option in arg_options:
            if option == "windows" and os.name == "nt":
                popen_editor_of_choice = "start " + config.get("Editor",option.strip())
            elif option == "linux" and not os.name == "nt":
                popen_editor_of_choice = config.get("Editor",option.strip())
    except:
        popen_editor_of_choice = ""

    # Process the command line arguments
    parser = optparse.OptionParser(add_help_option=False,
        usage="Usage: %prog [options] [input_file] [all_file]",
        description="Decodes mech sift traces. Decodes the output you get by turning "
            + "on 'udws \"fm.trace on\"' on the device. Requires matching .i, .hlg, or .all file -- "
            + "which it will try to find on your system. Also provides a command line interpreter "
            + "which implements a basic terminal emulator.")
    parser.add_option ("-f", "--file", dest="file",
        help="input file [default: IO port is used instead]")
    parser.add_option ("-o", "--output", dest="output",
        help="output file [default: %s]" % (DEFAULT_LOGFILE))
    parser.add_option ("--port", "-p", type="string",
        help="port [default:com1] (e.g. com1 or /dev/ttyS0 for serial, [hostname][:port][/channel][#id] " +
             "for network. port is <n>|pcs|ss|shell. channel is print|debug. id is any substring of serial " +
             "number or model name.")

    parser.add_option ("-g", "--gui", action="store_true",
        help="use the graphical user interface")
    parser.add_option ("-n", "--nogui", action="store_true",
        help="no GUI, don't use the graphical interface")

    parser.add_option ("-i", "--ifile", dest="ifile",
        help=".i file [default:auto]")
    parser.add_option ("--hlg",
        help=".hlg file [default:auto]")

    parser.add_option ("-t", "--talk", action="store_true",
        help="tktalk / dumb terminal mode (no symbols are loaded)")
    parser.add_option ("--nohtml", action="store_true",
        help="no HTML generated")
    parser.add_option ("--html", action="store_true",
        help=SUPPRESS_HELP)

    # parser.add_option ("--server",  dest="server", default=False, action="store_true",
    #     help=SUPPRESS_HELP)
    parser.add_option ("--nocolor", action="store_true",
        help=SUPPRESS_HELP)
    parser.add_option ("--sdv", action="store_true",
        help=SUPPRESS_HELP)
    parser.add_option ("-q", "--quiet", action="store_true",
        help="no standard input or output")
    parser.add_option ("--noout", action="store_true",
        help="no output files generated")
    parser.add_option ("-s", type="string", dest="startup",
        help="run Sift commands from out of a file")
    parser.add_option ("-c", type="string", dest="command",
        help="run a single Sift command and quit")
    parser.add_option ("--indent", type="string",
        help=SUPPRESS_HELP)
    parser.add_option ("--raw", action="store_true",
        help=SUPPRESS_HELP)
    parser.add_option ("--sim", action="store_true",
        help=SUPPRESS_HELP)
    parser.add_option ("--debug", action="store_true",
        help=SUPPRESS_HELP)
    parser.add_option ("--nodebug", dest="debug", action="store_false",
        help=SUPPRESS_HELP)
    parser.add_option ("--title", type="string", dest="title",
        help="Window title")
    parser.add_option ("--monitor", action="store_true",
        help=SUPPRESS_HELP)
    parser.add_option ("-a", type="string", dest="flashhost",
        help="Alternative hostname to send flash (assumes PCS)")
    parser.add_option ("-z", "--reset", action="store_true",
        help="reset persistent options (except User Favorites)")
    parser.add_option ("-?", "-h", "--help", action="help",
        help="show this help message and quit")
    parser.add_option ("-v", "--version", dest="version", action="store_true",
        help="show version and quit")
    parser.add_option ("--errcodes", action="store_true",
        help=SUPPRESS_HELP)
    parser.add_option ("-e", "--edit", action="store_true", help="open SiftFlow")
    parser.set_defaults(**config_dict)          # want to remove use of config_dict
    parser.set_defaults(**user_options)
    (options, args) = parser.parse_args()

    if options.reset:
        reset_sift() 

    # Version
    if options.version:
        print REV
        sys.exit(0)

    # List errcodes
    if options.errcodes:
        errcodes()
        sys.exit(0)

    # Default look for .all file in cwd
    dot_all_file_path = os.getcwd()
    dot_all_file =None

    # If we get a positional argument, use it as the input file, unless we're just opeing the editor
    if (len(args) > 0 and not options.edit):
        if args[0].endswith('.all') or args[0] == ".":
            dot_all_file = args[0]
            if(len(args)>1) and not options.file:
                options.file = args[1]
        elif not options.file:
            options.file = args[0]
            if(len(args)>1):
                dot_all_file = args[1]

    # HTML decision
    options.html = True                 # now always default True

    if (options.file):                  # if processing file:
        options.html = True             #   - force HTML
        options.gui = False             #   - no GUI
        html_output_size = sys.maxint   #   - let HTML file be as big as needed
    else:
        html_output_size = MAX_HTML_SIZE

    if (options.nohtml):                # force no HTML file
        options.html = False

    if options.nogui:                   # force no GUI
        options.gui = False

    if options.gui:                     # error check GUI
        if not QtGui:
            options.gui = False
            give_gui_install_info = True
            exit("QT4_NOT_INSTALLED")

    if options.talk:
        options.html = False

####################################################################################################
#
# Load symbols
#
####################################################################################################

def load_symbols(filename=None, first_time=False):

    global dot_all_file
    global project_name
    global project_dir

    # Parse the filename
    if filename:
        (root,ext) = os.path.splitext(filename)
        if ext:
            dot_all_file = None
            options.ifile = None
            options.hlg = None
            if ext == ".all":
                dot_all_file = filename
            elif ext == ".i":
                options.ifile = filename
            elif ext == ".hlg":
                options.hlg = filename

    # initialize things
    init_arrays_and_dictionaries ()
    init_arrays_and_dict_for_hlg()

    # Process the .all file if one is given
    if dot_all_file:
        options.ifile = None
        options.hlg = None
        output_str(" Opening "+os.path.abspath(dot_all_file)+EOLN)
        project_name = os.path.basename(dot_all_file.replace(".all",""))
        project_dir = os.path.abspath(os.path.join(SIFT_CONFIG_DIR, ALL_DIRECTORY, project_name + "_all"))

        # If a file does not already exist for the curProject make one
        process_dot_all()
        process_hlg(find_best_filename(".hlg", [(project_dir, False)]))
        # Compile .i and .dwn files
        if compile() == "failed":
            print "compile failed"
            pass
    else:
        project_name =  ""

    # Process .i and .hlg files
    if options.talk:
        options.talk = False
    else:
        find_and_process_i_and_hlg_files()

    # Tell GUI we have all the data
    if gui:
        gui.data_ready(first_time)


####################################################################################################
#
# Read/Write Dictionary Items 
#
# Used for reading/writing settings for Sift in an easy, human readable fashion, that is also
# easily usable by Windows apps.
#
####################################################################################################

def read_items(filename):
    """Read key,value pairs from a file. Return as dictionary."""
    items = {}
    try:
        with open(filename) as f:
            data = re.sub(r'[\n\r]', '', f.read())
            exec("items = {" + data + "}")
    except IOError:
        pass
    except (NameError, SyntaxError):
        sys.stderr.write("sift.settings is messed up, fixing by defaulting settings.")
    return items

def write_items(items, filename):
    """Write key,value pairs to a file."""
    try:
        with open(filename, 'w') as f:
            for key, value in items.iteritems():
                f.write(("%s: %s,"+EOLN) % (key.__repr__(), value.__repr__()))
    except IOError:
        pass


####################################################################################################
#
# Reset Sift 
#
# Clean up everything possible and exit so the next startup will be a fresh startup. 
# (Do not delete User Favorites.)
#
####################################################################################################

def reset_sift():
    options.gui = False
    try:
        shelf.close()
    except: pass
    try:    os.remove(os.path.join(SIFT_CONFIG_DIR, SETTINGS_FILE))
    except: pass
    try:    os.remove(os.path.join(SIFT_CONFIG_DIR, SHELF_FILE))
    except: pass
    try:    os.remove(os.path.join(SIFT_CONFIG_DIR, HISTORY_FILE))
    except: pass
    try:    os.remove(os.path.join(SIFT_CONFIG_DIR, ONDBUG_FILE))
    except: pass
    try:    os.remove(os.path.join(SIFT_CONFIG_DIR, IPADDRESS_FILE))
    except: pass
    try:    os.remove(os.path.join(SIFT_CONFIG_DIR, LASTPORT_FILE))
    except: pass
    try:    os.remove(os.path.join(SIFT_CONFIG_DIR, LAST_FILE))
    except: pass
    try:    shutil.rmtree(os.path.join(SIFT_CONFIG_DIR, ALL_DIRECTORY), ignore_errors=True)
    except: pass
    exit("RESET_EXIT")


####################################################################################################
#
# Log File Class
#
# Used for the decoded Sift trace, an HTML version, and keeping a copy of the raw data.
#
####################################################################################################

class LogFile():

    def __init__(self, default_name, enabled=True, max_size=None):
        global options

        self.file = None
        try:
            self.lock.acquire()
        except AttributeError:
            self.lock = threading.RLock()
            self.lock.acquire()

        try:
            if (not enabled) or (options.noout):  # user disabled output
                return 
            elif options.output:  # user specified an output file name
                self.name = options.output + os.path.splitext(default_name)[1]
            elif options.file:  # user specified an input file name
                (root,ext) = os.path.splitext(options.file)
                self.name = root + os.path.splitext(default_name)[1]
            else:  # use the default
                self.name = default_name

            if os.path.splitext(self.name)[1] == os.path.splitext(DEFAULT_LOGFILE)[1]:
                backup_file(self.name)
        
            try:
                self.file = open(self.name, "w")
            except IOError:
                print "Couldn't open " + self.name
                return

            self.size = os.path.getsize(self.name)
            self.ext  = os.path.splitext(self.name)[1]
            self.max_size = max_size

            # Prevent users from accidentally causing sift to feed off of itself
            if (self.name == options.file):
                output_str("Output file and Input file can not be the same; please rename " +EOLN, "error")
                exit(1)

            # Add on the HTML header if this is an HTML file
            if self.ext == os.path.splitext(DEFAULT_HTML_FILE)[1]:
                self.write(HTML_HEADER_BLOCK)
        finally:
            self.lock.release()


    def write(self, str):
        if self.file:
            self.lock.acquire()
            try:
                try:
                    self.file.write(str)
                except (IOError, AttributeError):
                    print "Couldn't write to " + self.file
                    self.file = None
                    pass
                else:
                    if self.max_size:
                        self.size += len(str)
                        if self.size >= self.max_size:
                            try:
                                self.file.close()
                                backup_file(self.name)
                                self.file = open(self.name, "w")
                                self.size = 0
                            except IOError:
                                print "Couldn't backup " + self.file
                                self.file = None
            finally:
                self.lock.release()

    def close(self, quiet=False):
        if self.file:
            self.lock.acquire()
            try:
                try:
                    self.file.close()
                except:
                    print "Error closing " + self.name

                self.file = None
                if not quiet:
                    if self.ext == ".html":
                        output_str("HTML saved in:    " + self.name + " (suggest Google Chrome)" + EOLN, "warning")
                    elif self.ext == ".raw":
                        pass
                    else:
                        output_str("Output saved in:  " + self.name + EOLN, "warning")
            finally:
                self.lock.release()

    def save(self, dest, quiet=False):

        if self.file:
            (root, ext) = os.path.splitext(dest)
            if ext == '':
                ext = self.ext
            dest = root + ext
            if not quiet:
                output_str("Saving " + dest + EOLN, "info")
            
            try:
                self.lock.acquire()
                self.file.flush()
                try:
                    shutil.copyfile(self.name, dest)
                except IOError:
                    output_str("Couldn't write " + dest + EOLN, "error")
                except Error:
                    output_str("Log file already named " + dest + EOLN, "error")
            finally:
                self.lock.release()
           
    def clear(self):

        if self.file:
            self.lock.acquire()
            self.close(quiet=True)
            self.__init__(default_name=self.name, max_size=self.max_size)
            self.lock.release()


###################################################################################################
#
# Monitor Thread 
#
# Monitor's internal performance. Activated with the --monitor option.
#
###################################################################################################

class MonitorThread(threading.Thread):
    def __init__(self, input_fifo):
        super(MonitorThread, self).__init__()
        self.setDaemon(True)
        self.input_fifo = input_fifo 

    def run(self):
        last_time  = time.time()
        input_lines_received = 0
        last_input_lines_received = 0
        last_lines_processed = 0
        last_time_processing = 0
        last_time_writing = 0
        last_time_painting = 0
        last_paint_count = 0
        #gui_lines_appended = 0
        #last_gui_lines_appended = 0
        gui_write_time = 0
        last_gui_write_time = 0
        #gui_emits = 0
        #last_gui_emits = 0
        header = 0

        while True:
            time.sleep(2)

            current_time = time.time()
            current_period = current_time - last_time

            input_lines_received = self.input_fifo.lines_appended

            if gui:
                #gui_lines_appended = gui.ui.bufferView.lines.linesAppended
                #gui_emits = gui.ui.bufferView.textAddedEmits
                gui_write_time = gui.write_time

            if header == 0:
                sys.stderr.write(    "\n%13s  %7s %7s %7s %7s %7s | %7s %7s %7s %7s %7s\n" % ("",
                    "Receive", "Process", "ProcesT", "OutpuT", "FifoNow",
                    "GuiApnd", "WriteT", "PaintT", "Emits", "Paints"))
                header = 20

            sys.stderr.write("monitor %1.2fs: %7d %7d %7.3f %7.3f %7d |     --- %7.3f %7.3f     --- %7d\n" % (current_period,
                input_lines_received - last_input_lines_received, lines_processed - last_lines_processed, 
                    time_processing - last_time_processing, 
                    time_writing - last_time_writing, 
                    len(self.input_fifo), 
                    #gui_lines_appended-last_gui_lines_appended,
                    gui_write_time-last_gui_write_time,
                    time_painting - last_time_painting,
                    #gui_emits - last_gui_emits,
                    paint_count - last_paint_count))

            last_time = current_time 
            last_input_lines_received = input_lines_received
            last_lines_processed = lines_processed
            #last_gui_lines_appended = gui_lines_appended
            #last_gui_emits = gui_emits
            last_gui_write_time = gui_write_time
            last_time_processing = time_processing
            last_time_writing = time_writing
            last_time_painting = time_painting
            last_paint_count = paint_count
            header -= 1


##############################################################################
#
# Usage Thread
#
# Balancing between animitidy and enough info to understand what unique
# users are doing. Reducing bandwidth. And sprinkling in things the server
# can use to identify validity of this data.
#
##############################################################################

class UsageThread(threading.Thread):

    def __init__(self, type="start"):
        super(UsageThread, self).__init__()
        self.setDaemon(True)
        self.type = type

    def data(self):
        values = {}
        now = datetime.datetime.utcnow()
        pid = os.getpid() % 1000

        # system
        values["tp"] = self.type
        values["dt"] = now.strftime("%m/%d/%y")
        values["tm"] = now.strftime("%H:%M:%S")
        values["tz"] = int(time.timezone/3600)
        values["se"] = pid
        values["is"] = 100+int(pid/3+2)+now.hour*314-now.day*3
        values["pj"] = project_name[0:2]
        values["py"] = platform.python_version()
        values["sy"] = platform.system()[0:2]
        values["re"] = platform.release()[0:3]
        values["si"] = REV
        try:
            ip = socket.gethostbyname(socket.gethostname()).split('.')
            values["ri"] = "%04x" % (int(ip[2])*256 + int(ip[3]))
        except:
            values["ri"] = "%04x" % (0)


        # options
        for attr, value in options.__dict__.iteritems():
            if value != None:
                if type(value) is bool:
                    if value==True:
                        values[attr[0:3]] = "T"
                elif type(value) is int: values[attr[0:3]] = value
                else: values[attr[0:3]] = str(value)[0:3]

        return values

    def run(self):
        time.sleep(2)
        values = self.data()
        params = urllib.urlencode(values, True)
        req = urllib2.Request(SIFT_SERVER+USAGE_SCRIPT, params)
        req.add_header ("Content-type", "application/x-www-form-urlencoded")
        debug ("Usage:", params)
        try:
            with open (os.path.join(SIFT_CONFIG_DIR, USAGE_FILE), "a") as f:
                f.write (params+"\r\n")
        except Exception, err:
            if options.debug:
                sys.stderr.write ("Sift: " + str(err) + "\r\n")
        try:
            urllib2.urlopen(req)
        except Exception, err:
            if options.debug:
                sys.stderr.write ("Sift: " + str(err) + "\r\n")

###################################################################################################
#
# Main
#
# Main routine to instantiate and start everyting.
#
# Future design intent:
#
#   I'd like main() to slowly evolve into a smaller routine. I'd like to design sift.py to be importable
#   by other Python scripts.  To achieve this goal, I'd like main() to be broken up into two parts:
#
#   Printer Class Initializer:
#   One part would initialize all the things a Python script would need to initialized in order to talk
#   to the printer. This might best become the initializer for the Printer ClasClass.
#
#   Sift Application:
#   Another part would stay "main()" and become the Sift Application. It would instantiate a Printer
#   class and then only do what the Sift Application (as it exists today) does.
#
###################################################################################################

def signal_handler(signum, frame):
    quit_event.set()
    if gui:
        gui.app.exit(0)


# The main function. Execution starts here.
def main():
    global printer
    global output_file
    global command_parser
    global project_dir
    global project_name
    global project_path
    global was_l_minus          # for list commands
    global break_or_assert_pc   # for list commands
    global break_or_assert_file # for list commands
    global compatibility_error  # using flextool data so feature will not work
    global at_a_break_point
    global process_fifo_thread
    global dir_sift_started_in
    global keyboard
    global html_output_file
    global raw_output_file
    global line_class
    global line_indent
    global wrap_count
    global quit_event
    global startup_seen
    global ready_for_flash_file
    global underware_result_seen
    global gui
    global sift_flow
    global hlg_filename
    global dot_i_filename
    global i_file_directory
    global shelf
    global give_gui_install_info
    global user_options
    global lines_processed
    global time_processing
    global time_writing
    global time_painting
    global paint_count
    global trace_startup
    global current_fml_file
    global current_fml_line
    global fiber

    was_l_minus           = False
    break_or_assert_pc    = None
    break_or_assert_file  = None
    compatibility_error   = False
    dir_sift_started_in   = os.getcwd()
    project_dir           = dir_sift_started_in
    output_file_size      = 0
    at_a_break_point      = False
    line_class            = None
    line_indent           = None
    html_output_file      = None
    raw_output_file       = None
    wrap_count            = 0
    gui                   = None
    sift_flow             = None
    output_file           = None
    hlg_filename          = None
    dot_i_filename        = None
    i_file_directory      = os.getcwd()
    command_parser        = None
    give_gui_install_info = False
    lines_processed       = 0
    time_processing       = 0
    time_writing          = 0
    time_painting         = 0
    paint_count           = 0
    trace_startup         = 0
    current_fml_file      = None
    current_fml_line      = None
    fiber                 = ""

    # Calculate user options
    user_options = DEFAULT_USER_OPTIONS
    if (os.name == "nt"):
        for sdv in SDV_LIST:
            if os.path.exists(sdv):
                user_options['sdv'] = True
                break
    user_options.update(read_items(os.path.join(SIFT_CONFIG_DIR, SETTINGS_FILE)))
    write_items(user_options, os.path.join(SIFT_CONFIG_DIR, SETTINGS_FILE))

    # Use a friendlier exception and signal handlers
    sys.excepthook = handle_exception;
    installThreadExcepthook()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Inter-thread communication                # FUTURE: I think thread stuff mainly stays in main()
    port_fifo    = Fifo()                       # Need to design a rearchitecture of main() to know.
    parser_idle  = threading.Event()
    prompt_seen  = threading.Event()
    prompt       = threading.Event()
    quit_event   = threading.Event()
    sync_seen    = threading.Event()
    startup_seen = threading.Event()
    ready_for_flash_file = threading.Event()
    underware_result_seen = threading.Event()

    # Set up persistent data (sorry, multiple ways are used right now)
    try:
        shelf = shelve.open(os.path.join(SIFT_CONFIG_DIR, SHELF_FILE))
    except:
        shelf = {}

    if 'send_dir' not in shelf: shelf['send_dir'] = os.path.expanduser("~")
    if 'open_dir' not in shelf: shelf['open_dir'] = SIRIUS_BUILD_DIR
    if 'save_dir' not in shelf: shelf['save_dir'] = os.path.expanduser("~")
    load_history()

    # Get everything set up
    update_old_files()
    check_for_sift_directory()
    process_options()

    # Misc debug info
    debug("os.getcwd() =", os.getcwd())
    debug("os.sys.path[0] =", os.sys.path[0])

    # Set up log files
    output_file =  LogFile(default_name=DEFAULT_LOGFILE,
                            max_size=max_output_file_size)
    html_output_file = LogFile(default_name=DEFAULT_HTML_FILE,
                            enabled=(not (options.nohtml)),
                            max_size=MAX_HTML_SIZE)

    # Create the "Printer"
    printer = Printer()

    # Create the GUI and redirect stdout to it
    if (options.gui):
        try:
            gui = Gui()
        except IOError:
            options.gui = False
            gui = None
            output_str(EOLN+" Gui failed to start. No X11 service."+EOLN, "error")
        except NameError:
            options.gui = False
            gui = None
            output_str(EOLN+" Gui failed to start (bad Gui)."+EOLN, "error")
        except ImportError:
            options.gui = False
            gui = None
            if not SiftWidget:
                output_str(EOLN+" Gui failed to start (no SiftWidget)."+EOLN, "error")
            if not QtGui:
                output_str(EOLN+" Gui failed to start (no QtGui)."+EOLN, "error")
        else:
            if not options.debug: sys.stdout = gui
    else:
        gui = None

    #Create SiftFlow if the user has not also tried to open gui, gui has priority
    if(options.edit and not options.gui and siftflow):
        try:
            sift_flow = SiftFlow()
            sift_flow.loadFiles(args)
            sift_flow.run()
            UsageThread("edit").start()
            return

        except:
            options.edit = False
            sift_flow = None
            output_str(EOLN+" SiftFlow Launch Error: "+ 
                        "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])) +
                        EOLN, "error")
    else:
        sift_flow = None

    output_str(EOLN)
    output_str(" Sift " + REV + EOLN)
    output_str(" -------------------------------------------------------------------------" +EOLN)
    interactive_help(short = True)
    output_str(" -------------------------------------------------------------------------" +EOLN)
    if gui: gui.process_events()

    headers[0] = Header(id="1", name="SiftCoreDump", numArgs=0, argList=[])
    headers[1] = Header(id="1", name="Sift", numArgs=4,
        argList=["TRACE_BUFFER_REV","NUM_FLOWS","NUM_VARS","NUM_CONSTANTS"])
    headers[2] = Header(id="1", name="SiftBufferSize", numArgs=2,
        argList=["FM_TRACE_SIZE","sizeof(data)"])
    headers[3] = Header(id="1", name="SiftBufferPtr", numArgs=3,
        argList=["who","wrap_line","wrap_ptr"])

    # Load the symbols (using the command line options)
    load_symbols(first_time=True)

    # Batch process input file
    if options.file:
        UsageThread("file").start()
        process_file(options.file)

    # Interactive mode
    else:
        UsageThread("start").start()
        if gui:
            if (not "gui" in user_options) or (not user_options["gui"]):
                output_str(' You can permanently enable GUI Mode in the Options tab.'+EOLN,"G")
            elif (len(flows) == 0) and (len(dsids) == 0):
                output_str(' No symbols loaded. Use "Open.." to select an .all file.'+EOLN,"G")
        else:
            if not options.nogui or not isinstance(gui, Gui):
                output_str(' Sift has a GUI when started with "-g".'+EOLN, "G")

        if not siftflow:
                output_str(' SiftFlow editor not present.'+EOLN, "G")

        output_str(EOLN)

        # Open the printer
        if (options.port):                      # open the given port
            printer.open(options.port)
        else:
            try:                                # lookup the last port
                with open(os.path.join(SIFT_CONFIG_DIR, LASTPORT_FILE)) as f:
                    last_port = f.readline().strip()
            except IOError:
                printer.open(DEFAULT_PORT)
            else:
                printer.open(last_port)

        if not printer.port:
            print "Printer port didn't open", printer, printer.port

        if not printer.is_open_event.isSet():
            print "Printer didn't open", printer.is_open

        if isinstance(printer.port, NoConnectionPort): 
            if gui:
                output_str(" Use the 'Port..' button to connect to a printer."+EOLN, "info")
                gui.process_events()
            else:
                output_str(" Type the 'port' command to connect to a printer. Examples:"+EOLN, "info") 
                output_str("    port com1"+EOLN, "info") 
                output_str("    port 10.0.0.34"+EOLN, "info") 

        # Init raw file
        raw_output_file = LogFile(RAW_OUTPUT_FILE, max_size=max_output_file_size)

        # Process serial data (pausing when CommandParser isn't idle)
        if not options.sim:
            PortToFifoThread(printer, port_fifo, prompt_seen, "InputFifo", 
                startup_seen, quit_event).start()

        process_fifo_thread = ProcessFifoThread(port_fifo, processing_allowed=parser_idle,
                        quit_event=quit_event, sync_seen=sync_seen)
        process_fifo_thread.start()

        # Perform interactive command processing
        command_parser = CommandParserThread(parser_idle, prompt_seen, prompt, quit_event, sync_seen)

        command_parser.start()

#       if options.server:                                      # create listener on port 9999
#           listener = ListenThread(command_parser, SIFT_PORT, quit_event)
#           listener.start()
#
        startup_trace(printer)

        if gui or options.quiet:
            pass
        else:
            keyboard = KeyboardThread(command_parser, quit_event)  # create keyboard reader
            keyboard.start()

        if give_gui_install_info:
            output_str(EOLN+" The GUI requires PyQt to be installed. Go to this website:"+EOLN, "warning")
            output_str("    www.riverbankcomputing.co.uk/software/pyqt/download"+EOLN, "info")
            if (os.name == "nt"):
                output_str(" Install the file who's name starts with:"+EOLN, "warning")
                bit_size = 8 * struct.calcsize("P")
                if bit_size == 32: bit_size_ver = "86"
                elif bit_size == 64: bit_size_ver = "64"
                else: bit_size_ver = "__"
                output_str("    PyQt-Py%d.%d-x%s-gpl-4.xxxx.exe" %
                    (sys.version_info[0], sys.version_info[1], bit_size_ver), "info")
                output_str(EOLN)
            elif (sys.platform == "darwin"):
                output_str(" Use MacPorts to install:"+EOLN, "G")
                output_str("    sudo port install py27-pyqt4"+EOLN, "F")

        if printer.is_open_event.isSet():
            if printer.port.running_shell:
                printer.port.write("\n\n")
            elif printer.port.running_udw:
                output_str(EOLN)
                printer.port.write(ECHO_PROMPT)   # revisit PCS_PROMPT

        if options.monitor:
            MonitorThread(port_fifo).start()

        ########################################
        #
        # Main Loop
        #
        ########################################

        # image_formats = QtGui.QImageReader.supportedImageFormats()
        # for x in image_formats:
        #     print x 

        if gui:
            gui.run()
        else:
            quit_event.wait()


####################################################################################
#
# Cleanup -- Runs after main has exited
#
####################################################################################

# Cleanup
def cleanup():
    global output_file
    global raw_output_file
    global options
    global gui
    global sift_flow
    global shelf

    sys.stdout = sys.__stdout__                 # restore stdout 

    try:
        save_history()
    except: pass

    # Write out options.  Not sure I want to do this here.  It's done when
    # options are changed on the GUI.
    # write_items(user_options, os.path.join(SIFT_CONFIG_DIR, SETTINGS_FILE))

    try:
        shelf.close()                           # close persistent settings
    except: pass

    try:
        gui.close()  
    except: pass

    if siftflow:
        try:
            sift_flow.close()  
        except: pass

    try:
        printer.close() 
    except: pass

    if not gui:                                 # clean up terminal
        try:
            output_text_type("none"); output_str(EOLN)
        except: pass
        try:
            if os.name == "nt": set_text_attr(FOREGROUND_GREY)
            else:               os.system("stty sane")
        except: pass

    try:
        output_file.close()
    except: pass

    try:
        raw_output_file.close()
    except: pass

    try:
        html_output_file.close()
    except: pass

    try:
        if (not gui) and (os.name == "nt"):
            raw_input(GOODBYE)                  # Windows only, prompt user to close window
    except: pass

    debug("bye")
    PortToFifoThread.quitted_event.wait(timeout=1) 
    if not PortToFifoThread.quitted_event.isSet():
        debug("PortToFifoThread timeout")
    debug("bye")


####################################
#
# Sift Application or Sift Module
#
####################################

if __name__ == "__main__":              # We have been called as the Sift Application

    main()
    cleanup()

