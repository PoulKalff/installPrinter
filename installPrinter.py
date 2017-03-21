#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import curses
import signal
import urllib2
import platform
import argparse

version = "v0.82"   # Implemented commandline-switches

# --- Variabler ----------------------------------------------------------------------------------

selectLists = [[], [], []]
urlPrinterList = 'http://172.19.17.66/lgr/installPrinter.list'

resAdr  = {'fib':'Fibigerstraede',
           'kst':'Kroghstraede',
           'myr':'Myrdalstraede',
           'pon':'Pontoppidanstraede',
           'acm':'A.C.Meyers Vaenge',
           'njv':'Niels Jernes Vej',
           'lan':'Langagervej',
           'frb':'Fredrik Bajersvej',
           'skj':'Skjernvej',
           'slv':'Selma Lagerlofsvej',
           'ssk':'Sdr.Skovvej',
           'bad':'Badehusvej',
           'nbv':'Niels Bohrs Vej',
           'fkv':'Fyrkildevej',
           'glt':'Gammeltorv',
           'rdb':'Rendsburggade',
           'skb':'Skibbrogade',
           'str':'Strandvejen',
           'slo':'Slotspladsen',
           'msp':'Musik.Plads',
           'nbg':'Nybrogade',
           'nhg':'Nyhavnsgade',
           'ntv':'Nytorv',
           'vhp':'V.H.Promenade',
           'tgp':'Teglgaards Plads',
           'sof':'Sofiendalsvej',
           'sgv':'Sohngaardsholmvej',
           'fkj':'Frederikskaj',
           'trv':'Troensevej'}

# --- Funktions ----------------------------------------------------------------------------------

def checkCredentials():
    email = args.user if args.user else raw_input("\n  Please provide your email address : ")
    if not '@' in email:
        sys.exit("    ERROR Invalid email address!\n" + str(email))
    user, domain = email.split('@')
    if not domain.endswith('.aau.dk'):
        sys.exit("    ERROR: Must be an AAU email address!\n")
    short_domain = (domain.split('.')[0]).lower()
    Cuser = short_domain + '\\' + user
    Cpass = args.password if args.password else raw_input("  Please provide the password for the printer : ")
    return (Cuser, Cpass)

def addLinuxCredentials(prt, crUser, crPass):
    gk.item_create_sync(None, gk.ITEM_GENERIC_SECRET, prt, {'user': crUser.lower(), 'domain':'', 'uri': 'ipp://localhost:631/printers/' + prt, 'server': 'mfc-print03.aau.dk', 'protocol': 'smb'}, crPass, True)
    return 1

def checkPackages():
    """ Checks if required packages are installed, installs them if not """
    getPackages = 'dpkg -l samba libsmbclient smbclient python-gnomekeyring'
    instPackages = 'sudo apt-get install samba libsmbclient smbclient -y'
    reply = os.popen(getPackages).read()
    if reply.count('ii  ') == 4:
       return
    else:
       print '\n  Required packages were not found on the system, installing.....',
       reply = os.popen(instPackages).read()
       print 'done!'
       raw_input('  Any key to proceed to installation of printers...\n')

def getPrinters(liste):
    objFile = liste.split('\n')
    objFile.pop()  # remove empty last line
    return objFile

def getAdresses(liste):
    objFile = getPrinters(liste)
    adresses = {}
    for line in objFile:
        adPart = line.split('-')[1]
        adStreet = adPart[:3]
        adNumber = adPart[3:]
        if adStreet not in adresses:
            adresses[adStreet] = [adNumber]
        elif adNumber not in adresses[adStreet]:
            adresses[adStreet].append(adNumber)
    return adresses

def resizeHandler(signum, frame):
    pass # resize-window signal caught


# --- Classes --------------------------------------------------------------------------------------


class ShowScreen:
    """ Presents the screen of a program """

    def __init__(self, liste):
        # Start en screen op
        self.running = True
        self.pointer = [0, 0]
        self.keyPressed = 0
        self.selected = [-1, -1, -1]
        self.screen = curses.initscr()
        self.screen.border(0)
        self.selectLists = liste
        curses.noecho()
        curses.start_color()
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)

    def run(self):
        while self.running:
            self.screen.clear()
            if self.selected[0] != -1:
                selectLists[1] = self.getNoForAdress(self.selected[0])
                if self.selected[1] != -1:
                    selectLists[2] = self.getPrintersForAdress(self.selected[1])
            self.displayList(self.screen, selectLists[self.pointer[0]])
            self.screen.refresh()
            self.keyPressed = self.screen.getch()
            # --- Keyboard Inputs ---
            if self.keyPressed == 66:           # Cursor DOWN
                if self.pointer[1] < len(selectLists[self.pointer[0]]) - 1:
                    self.pointer[1] += 1
            if self.keyPressed == 65:           # Cursor UP
                if self.pointer[1] > 0:
                    self.pointer[1] -= 1
            if self.keyPressed == 68:           # Cursor LEFT
                if self.pointer[0] > 0:
                    self.selected[self.pointer[0]] = -1
                    self.pointer[0] -= 1
                    self.pointer[1] = self.selected[self.pointer[0]]
            if self.keyPressed == 67 or self.keyPressed == 10: # Cursor RIGHT or RETURN
                if selectLists[self.pointer[0]][self.pointer[1]] == "":
                    pass
                elif selectLists[self.pointer[0]][self.pointer[1]] == "Follow-You":
                    self.doInstallPrinter("Follow-You")
                elif self.pointer[0] == 2:
                    self.doInstallPrinter(selectLists[2][self.pointer[1]])
                elif self.pointer[0] < 2:
                    self.selected[self.pointer[0]] = self.pointer[1]
                    self.pointer[0] += 1
                    self.pointer[1] = self.selected[self.pointer[0]]
                    if self.pointer[1] < 0: self.pointer[1] = 0
                    if self.pointer[1] > len(selectLists[self.pointer[0]]) : self.pointer[1] = 0
        #    if self.keyPressed == 10:           # Return (Select)
        #        if self.selected[2] != -1:
        #            sys.exit("Selection completed")
            if self.keyPressed == 113:          # Keypress 'q' = End Application
                self.running = False
        self.killScreen()


    def displayList(self, object, liste):
        self.screen.addstr(0, 0, 'Please make your selection and press <return>: ', curses.color_pair(0))
        self.screen.addstr(1, 0, '------------------------------------------------------------', curses.color_pair(0))
        for nr, name in enumerate(liste):
            if nr == self.pointer[1]:
                self.screen.addstr(nr + 2, 0, name, curses.color_pair(1))
            else:
                self.screen.addstr(nr + 2, 0, name, curses.color_pair(2))
        self.screen.addstr(len(liste) + 2, 0, '-----------------------------------------------------------', curses.color_pair(0))
        self.screen.addstr(len(liste) + 3, 0, 'Cursor-keys up/down to move, enter/right to select, "Q" to quit : ', curses.color_pair(0))
    #    screen.addstr(len(liste) + 4, 0, 'X: ' + str(self.pointer[0]), curses.color_pair(0))

    def getNoForAdress(self, addressIndex):
        """ Tager et index-nummer fra liste eet, og genererer liste 2, adressenumre """
        shortAddress = resAdr.keys()[resAdr.values().index(selectLists[0][addressIndex])]
        return dictAdresses[shortAddress]

    def getPrintersForAdress(self, addressNoIndex):
        """ Tager et index-nummer fra liste 2, og genererer liste 3, printere """
        shortStreet = resAdr.keys()[resAdr.values().index(selectLists[0][self.selected[0]])]
        address = shortStreet + selectLists[1][addressNoIndex]
        ud = []
        for p in listPrinters:
            if address in p:
                ud.append(p)
        return ud

    def doInstallPrinter(self, pName):
        prtExec = 'lpadmin -p %s -v smb://mfc-print03.aau.dk/%s -E -o auth-info-required=username,password -o Media=A4 -o PageSize=A4 -o Duplex=DuplexNoTumble -o printer-is-shared=false %s'
        prtDrv_Ubuntu = '-m foomatic-db-compressed-ppds:0/ppd/foomatic-ppd/Xerox-WorkCentre_7345-pxlcolor.ppd'
        prtDrv_Mac = '-P /System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/PrintCore.framework/Versions/A/Resources/Generic.ppd'
        if platform.system() == 'Linux':
            pDriver = prtDrv_Ubuntu
        else:
            pDriver = prtDrv_Mac
        self.screen.clear()
        reply = os.popen(prtExec % (pName, pName, pDriver))
        if platform.system() == 'Linux':
            addLinuxCredentials(pName, *linuxCredentials)
        self.screen.addstr(2, 2, "'" + pName.upper() + "' was installed ok", curses.color_pair(0))
        if args.single:
            self.screen.refresh()
            self.running = False
        else:
            self.screen.addstr(4, 2, '  Install another? (y/n)', curses.color_pair(0))
            self.screen.refresh()
            while 1:
                keyPressed = self.screen.getch()
                if keyPressed == 121:           # y
                    # reset interface
                    self.pointer = [0, 0]
                    self.selected = [-1, -1, -1]
                    break
                elif keyPressed == 110:     # n
                    self.running = False
                    break

    def killScreen(self):
        # Set everything back to normal
        self.screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()


# --- Main Program -------------------------------------------------------------------------------

parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=100))
parser.add_argument('files', type=str, nargs="*")
parser.add_argument("-s", "--single",    action="store_true", dest='single',   help="Do not prompt to install more printers")
parser.add_argument("-v", "--version",   action="store_true", dest='version',  help="Prints version and quits")
parser.add_argument("-u", "--user",      action="store",      dest='user',     help="User/email to authenticate printer", nargs='?')
parser.add_argument("-p", "--pass",      action="store",      dest='password', help="Password to User/email to authenticate printer", nargs='?')
args = parser.parse_args()

if args.version:
    sys.exit(version)

# resize terminal
print "\x1b[8;32;100t"

# overwrite resize-handling
signal.signal(signal.SIGWINCH, resizeHandler)

# only import packages/ask for creds if on linux
if platform.system() == 'Linux':
    import gnomekeyring as gk
    checkPackages()
    linuxCredentials = checkCredentials()

# get printers available
pList = urllib2.urlopen(urlPrinterList).read()
listPrinters = getPrinters(pList)
dictAdresses = getAdresses(pList)
reqSize = str(len(dictAdresses) + 4)

for a in dictAdresses.iterkeys():
    if a in resAdr:
       selectLists[0].append(resAdr[a])
    else:
       selectLists[0].append(a)
selectLists[0].sort()
selectLists[0].append("")
selectLists[0].append("Follow-You")
pClass = ShowScreen(selectLists)
pClass.run()
print("  Program terminated normally\n");


