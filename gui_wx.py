"""
Copyright 2019 Thomas Spargo

This file is part of LaSolv.

    LaSolv is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    LaSolv is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with LaSolv.  If not, see <https://www.gnu.org/licenses/>.
"""
'''
Created on Jan 2, 2019

@author: Thomas

Bugs fixed since ~12/19:
    Under some circumstances one term of the solution, if it is a voltage,
        was being subtracted.
    Voltage & current source polarity wasn't being put into the matrix
        correctly, resulting in sign errors. 
    Under some circumstances, the reordering algorithm could fail even
        though there was an order that would work
    The reordering algorithm has been significantly sped up for circuits
        with > 7 or 8 nodes.
    If an IVS was used to sense current, it wasn't handled right and
        would result in a sort-of nonsensical answer.
    If the current through a controlling source for an F or H element was requested
        as either the input or output part of the solutions, the result was probably wrong.
    * 
    
TODO:
    In the user version, the text output should be logged instead of going
        to stdout.
    Need to figure out how to pass exceptions up the stack so that whatever
        being done can stop and wait for the user to fix the problem. See
        doughellmann.com example.
        try...finally block?
        try: ...  except: ...raise
'''
#
# Most recent Mac source code
# Programming/LaSolv_main/LaSolv_wx_2021_1108/
import wx
import wx.stc as stc
import engineering_notation as eno
from sympy import fraction, N
import configparser
import eqnSolver
import UI_Classes as ui
import Support
from sys import platform
import os.path

class xmlSTC(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)
        self.SetUseTabs(False)
        self.SetTabWidth(4)

class xmlPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.xmlView = xmlSTC(self)

def formFileName(fn):
    suffix = ".txt"
    if '.' in fn[-5:-3]:
        suffix = ""
    (pth, fname) = os.path.split(fn)
    return fname+suffix

class Equations(wx.Frame):
    def __init__(self, ID=wx.ID_ANY, title="LaSolv 0.9.5"):
        """
        Constructor
        """
        wx.Frame.__init__(self, None, ID, title, pos=(20,20), size=(800, 400))

        #self.plot_format = 0
        #self.use_dB = True
        #self.SorP = 0
        #self.alwaysPlotR = True
        #self.runTestMode = False
        self.fnNPath = ''
        self.showTestMode = True

        self.textChanged = False
        self.numer = 0.0
        self.denom = 1.0
        self.fnpFile = "circuit.txt"
        self.fnpPath = "~/Programming/Python/LaSolv_support/Examples"
        self.homeDir = os.getcwd()
        self.eqSetFullPath(self.fnpPath, self.fnpFile)
        self.configFN = 'LaSolv.ini'
        self.getConfig()

        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        self.topPanel = wx.Panel(self, wx.ID_ANY)

        self.TextPanel = ui.TextPanel(self)
        #self.TextPanel.CktPanel.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
        self.ButtonPanel = ui.ButtonPanel(self)
        self.TextPanel.CktPanel.circuit_text.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)

        self.ud_sizer = wx.BoxSizer(wx.VERTICAL)
        self.ud_sizer.Add(self.TextPanel, 1,   wx.ALL, 5)
        self.ud_sizer.Add(self.ButtonPanel, 1,   wx.ALL, 5)

        self.topPanel.SetSizerAndFit(self.ud_sizer)
        self.Show()

        self.menubar = self.buildMenu()

        self.plotFrame = None
        self.plotPanel = None

        self.eqSolver = eqnSolver.eqn_solver()

    def initVar(self):
        self.eqSetFilenameNPath('')
        self.eqSetTestMode(True)
        self.eqSetResultText('')
        self.eqSetCircuitText('')

        self.textChanged = False
        self.numer = 0.0
        self.denom = 1.0
        self.ButtonPanel.uiSetInitModes()
        if self.plotPanel:
            self.plotPanel.closeFigure()
        if self.plotFrame:
            self.plotFrame.Close()

    def eqGetPlotFrom(self):
        return self.ButtonPanel.uiGetPlotFrom()

    def eqGetPlotTo(self):
        return self.ButtonPanel.uiGetPlotTo()

    def eqGetSorP(self):
        return self.ButtonPanel.uiGetSorPMode()

    def eqGetAlwaysPlotR(self):
        return self.ButtonPanel.uiGetAlwaysPlotRMode()

    def eqGetDBMode(self):
        return self.ButtonPanel.uiGetDBMode()

    def eqGetPlotFormat(self):
        return self.ButtonPanel.uiGetPlotFormat()

    def eqSetAlwaysPlotRMode(self, rm):
        self.ButtonPanel.alwaysPlotRBox.SetValue(rm)

    def eqSetFilenameNPath(self, fnp):
        """Assumes the filename suffix is already checked."""
        self.fnNPath = fnp
        (self.fnpPath, self.fnpFile) = os.path.split(fnp)
        self.fnpFile = formFileName(self.fnpFile)

    def eqSetFullPath(self, pth, fn):
        self.fnpPath = pth
        self.fnNPath = os.path.join(pth, formFileName(fn))

    def buildMenu(self):
        self.file_menu = wx.Menu()
        about_item = self.file_menu.Append(wx.ID_ABOUT, "About LaSolv", "INFO")
        self.Bind(wx.EVT_MENU, self.onAbout, about_item)
        self.file_menu.AppendSeparator()
        quit_item = self.file_menu.Append(wx.ID_EXIT, "&Quit")
        self.Bind(wx.EVT_MENU, self.onQuit, quit_item)

        new_item = self.file_menu.Append(wx.ID_NEW, "")
        self.Bind(wx.EVT_MENU, self.onNew, new_item)
        open_item = self.file_menu.Append(wx.ID_OPEN, "")
        self.Bind(wx.EVT_MENU, self.onOpen, open_item)
        save_item = self.file_menu.Append(wx.ID_SAVE, "")
        self.Bind(wx.EVT_MENU, self.onSave, save_item)
        saveas_item = self.file_menu.Append(wx.ID_SAVEAS, "")
        self.Bind(wx.EVT_MENU, self.onSaveAs, saveas_item)

        # The edit menu items seem to work without any extra code.
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_COPY, "")
        edit_menu.Append(wx.ID_CUT, "")
        edit_menu.Append(wx.ID_PASTE, "")

        solve_menu = wx.Menu()
        solve_item = solve_menu.Append(wx.ID_ANY, "&Solve\tCTRL+e")
        self.Bind(wx.EVT_MENU, self.onSolve, solve_item)
        plot_item = solve_menu.Append(wx.ID_ANY, "Plot\tCTRL+T")
        self.Bind(wx.EVT_MENU, self.onPlot, plot_item)

        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ANY, "Help")
        self.Bind(wx.EVT_MENU, self.onHelp, help_item)

        menu_bar = wx.MenuBar()
        menu_bar.Append(self.file_menu, "&File")
        menu_bar.Append(edit_menu, "Edit")
        menu_bar.Append(solve_menu, "Solve")
        menu_bar.Append(help_menu, "Help")
        self.SetMenuBar(menu_bar)
        return menu_bar

    def getConfig(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.configFN):
            config.read(self.configFN)
            if 'DEFAULT' in config:
                print("getConfig: ")
                print(config.keys())
                self.homeDir = '~'
            else:
                # DEFAULT s/b in the config file, so maybe it's corrupted?
                print("getConfig: config exists but no DEFAULT line; creating new config ")
                self.createConfig(config)
        else:
            # No config exists, create it
            print("getConfig: creating a config")
            self.createConfig(config)

    def createConfig(self, configP):
        # set ckt directory to be the dir LaSolv is in unless the user changes it.
        configP['DEFAULT'] = {'cktDir': self.homeDir}
        with open(self.configFN, 'w') as configfile:
            configP.write(configfile)

    # Guarantees that some filetype extension is present, if none is passed with
    # the filename, '.txt' is used.
    # Input: filename or path+filename.
    # Output: filename with '.txt' at the end

    def eqSetPlotFormat(self, fmt):
        self.ButtonPanel.uiSetPlotFormat(fmt)

    def eqSetSorPMode(self, sp):
        self.SorP = sp

    def eqSetDBMode(self, db):
        self.use_dB = db

    # def setAlwaysUseR(self, r):
    #     self.ButtonPanel.alwaysPlotRBox.SetValue(r)
    #
    # def enable_dBBox(self, flag):
    #     if flag:
    #         self.ButtonPanel.dBBox.Enable()
    #     else:
    #         self.ButtonPanel.dBBox.Disable()
    #
    # def enableSPBox(self, flag):
    #     if flag:
    #         self.ButtonPanel.spBox.Enable()
    #     else:
    #         self.ButtonPanel.spBox.Disable()

#####################
# Option Callbacks
#####################
    def eqSetTestMode(self, tm):
        self.ButtonPanel.uiSetTestMode(tm)

    def eqGetTestMode(self):
        return self.ButtonPanel.uiGetTestMode()

    # If format set to mag/ang:
    #    Enable the dBBox.
    #    Disable the s/p radio buttons
    # If format is set to Re/Im or RLC:
    #    Enable the series/parallel box.
    #    Disable the dBBox
    def onPlotFormat(self, event):
        #self.plot_format = self.eqGetPlotFormat()
        #print('onPlotFormat: plot_format=', self.plot_format)
        #cb = event.GetEventObject()
        #pfVal = event.GetSelection()
        pfVal = self.eqGetPlotFormat()
        self.eqSetPlotFormat(pfVal)
        self.ButtonPanel.uiSet_dBBoxEnabled(pfVal)
        self.ButtonPanel.uiSetAlwaysPlotREnabled(pfVal)
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)

    def ondBMode(self, event):
        cb = event.GetEventObject()
        #self.use_dB = cb.GetValue()
        self.eqSetDBMode(cb.GetValue())
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)

    def onSP(self, event):
        self.eqSetSorPMode(cb.GetValue())
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)

    def onAlwaysPlotR(self, event):
        cb = event.GetEventObject()
        self.eqSetAlwaysPlotRMode(cb.GetValue())
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)

    def setTextChangeFlag(self, flg):
        self.textChanged = flg
        if Support.gVerbose > 9:
            print(Support.myName(), 'textChanged=', self.textChanged)

########################
# Progress bar updater
########################
    def updateProgress(self, p):
        """
        Update the progress bar
        """
        self.ButtonPanel.gauge.SetValue(p)

#######################
# Button/Menu Callbacks
#######################
    def onAbout(self, event):
        if platform == 'win32':
            dlg = wx.MessageDialog(self, "LaSolv for Windows 0.9.5\nCopyright 2022 by Thomas Spargo", "About LaSolv...", wx.OK)
        else:
            dlg = wx.MessageDialog(self, "LaSolv for Mac 0.9.5\nCopyright 2022 by Thomas Spargo", "About LaSolv...", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def onHelp(self, event):
        thePath = None
        pths = ["../help.htm", "help.htm", "../../help.htm"]
        for pth in pths:
            if os.path.exists(pth):
                thePath = pth
                break

        if thePath is not None:
            provider = wx.SimpleHelpProvider()
            wx.HelpProvider.Set(provider)

            helpWin = ui.HtmlHelpWindow(self, 'Helpful window', thePath)
            helpWin.Show()
        else:
            self.eqSetMssg("Sorry, I can't find the help file :(")

    def onNew(self, event):
        if self.textChanged:
            if wx.MessageBox('The text has been modified, save before opening a new one?',
                             'Alert', wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
                self.onSave(event)
            self.newFile()
        else:
            self.newFile()

    def onOpen(self, event):
        if self.textChanged:
            if wx.MessageBox('The text has been modified, save before opening a new one?',
                             'Alert', wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
                self.onSave(event)
            self.readFile()
        else:
            self.readFile()

    def onPlot(self, event, solveFirst=True):
        if solveFirst:
            self.onSolve(event)
            self.onPlot(event, False)
        #if self.eqSolver.getEvalAnswer() is not None:
        if self.eqSolver.allValuesDefined():
            if self.eqGetPlotFrom() == '' or self.eqGetPlotTo() == '':
                f_start = f_stop = -1
            else:
                f_start = float(eno.EngNumber(self.eqGetPlotFrom()))
                f_stop = float(eno.EngNumber(self.eqGetPlotTo()))
                if f_start > f_stop:
                    self.eqSetMssg('Starting frequency is > stop frequency')
                    return
            if self.eqSolver.getPlotFrame() is not None:
                self.eqSolver.closePlot()
            err_txt = self.eqSolver.eqnPlot(f_start, f_stop, self.updateProgress,
                        self.eqGetPlotFormat(), self.eqGetDBMode(), self.eqGetSorP() )
            if err_txt != "":
                self.eqSetMssg(err_txt)
        else:
            self.eqSetMssg("All components (except v's & i's) must have a value in order to plot")

    def onQuit(self, event):
        if self.textChanged:
            self.onSave(event)
        if self.eqSolver.getPlotFrame() is not None:
            print("onQuit: eqSolver.closePlot()")
            self.eqSolver.closePlot()
        print("onQuit: Destroy")
        self.Close(True)
        #wx.CallAfter(self.Destroy)

    def onSave(self, event):
        if self.fnNPath == None:
            self.onSaveAs(event)
        else:
            t = self.eqGetCircuitText()
            self.saveFile(t)
            #file1 = open(self.fnNPath, "w+")
            #file1.write(t)
            #file1.close()
            #self.setTextChangeFlag(False)

    def onSaveAs(self, event):
        #initialdir = '/Users/Thomas/eclipse-workspace/ESGui_Python/Circuit files')
        t = self.eqGetCircuitText()
        with wx.FileDialog(self, "Save as:", wildcard = 'txt files (*.txt)|*.txt',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.fnNPath = fileDialog.GetPath()
            self.saveFile(t)
            #try:
            #    with open(self.fnNPath, 'w+') as f1:
            #        f1.write(t)
            #        f1.close()
            #        self.fnNPath.SetLabel(self.fnNPath)
            #        self.setTextChangeFlag(False)
            #except IOError:
            #    wx.LogError("Cannot save the file in '%s'." % self.fnNPath)

    def onSolve(self, event):
        if self.eqGetTestMode():
            # Re-init the solver which may have values left over from a prior 'solve'
            self.eqSolver.__init__()
            self.eqSolver.eqnSolveEntry(None, True)
        else:
            if self.textChanged or self.fnNPath is not None:
                self.eqSetMssg('Solving.....')
                self.eqSetResultText('')
                #wx.AppConsole().Yield()
                wx.GetApp().Yield()
                self.onSave(event)
                #self.eqSolver.__init__()
                result = self.eqSolver.eqnSolveEntry(self.fnNPath, False)
                self.eqSetMssg(self.fnNPath)
                if result == 0:     # ie, if no error occurred
                    if Support.gVerbose > 2:
                        print(Support.myName(), ' result=', result)
                        print(Support.myName(), 'raw=', self.eqSolver.getRawAnswer())
                        print(Support.myName(), 'simpl=', self.eqSolver.getSimplAnswer())
                        print(Support.myName(), 'eval=', self.eqSolver.getEvalAnswer())
                        print(Support.myName(), 'evalF=', self.eqSolver.getEvalFAnswer())
                        print(Support.myName(), 'best=', self.eqSolver.getBestAnswer())
                    self.setResultEqn()
                else:
                    Support.myExit(result)
            else:
                self.eqSetMssg('You must load or type in a circuit first')

########################################
# Keyboard Callback
########################################
    def onKeyPress(self, event):
        #if event.GetUnicodeKey().chr() in string.printable:
        uni_key = event.GetUnicodeKey()
        if uni_key != 0:
            self.setTextChangeFlag(True)
            #print('%s: %c %d' % (Support.myName(), uni_key, uni_key ) )
        event.Skip()

########################################
# Text setters and getters
########################################
    def eqGetCircuitText(self):
        return self.TextPanel.tpGetCircuitText()

    def eqSetCircuitText(self, txt):
        self.TextPanel.tpSetCircuitText(txt)

    def eqSetResultText(self, txt):
        self.TextPanel.tpSetResultText(txt)

    def eqSetMssg(self, mssg):
        self.ButtonPanel.uiSetMssg(mssg)

    def nd2string(self, eqn, prec=3):
        """ Take a sympy numer, denom and convert to a string expression like:
          numer
        ---------
          denom
        """
        n, d = fraction(eqn)
        numer_str = str(N(n, prec))
        if d != 1.0:
            denom_str = str(N(d, prec))
            width = max(len(numer_str), len(denom_str))
            sep = width*'-'
            txt = numer_str+'\n'+sep+'\n'+denom_str
        else:
            txt = numer_str
        return txt
    #print("(",i,",",j,")", sympy.N(self.m[i,j], 2))

    #def setResultEqn(self, eqn, simple_eqn=None, best_eqn=None):
    def setResultEqn(self):
        ''' Take polynomial fraction and prints it in the result text window'''
        raw = self.eqSolver.getRawAnswer()
        best = self.eqSolver.getBestAnswer()

        txt = self.nd2string(raw)
        if best is not None:
            temp = self.nd2string(best)
            txt = txt + '\n\nWhich simplifies to:\n' + temp
        # Use evalF if it exists, otherwise use eval if it exists.
        evals = self.eqSolver.getEvalFAnswer()
        if evals is None: evals = self.eqSolver.getEvalAnswer()
        if evals is not None:
            temp = self.nd2string(evals, 5)
            txt = txt + '\n\nWith values substituted, it becomes:\n' + temp
        self.eqSetResultText(txt)

    def newFile(self):
        self.initVar()
        self.SetTitle('')
        self.setTextChangeFlag(False)
        self.eqSetFullPath(self.fnpPath, "circuit.txt")

    def readFile(self):
        (path, file) = os.path.split(self.fnNPath)
        with wx.FileDialog(self, "Open...", defaultDir=self.fnpPath, defaultFile=self.fnpFile, wildcard="txt files (*.txt)|*.txt", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                #dirname = dlg.GetDirectory()
                #self.fnNPath = self.dirname+'/'+self.filename
                #self.fnNPath = os.path.join(dirname, filename)
                #self.fnNPath = dlg.GetPath()
                self.eqSetFilenameNPath(dlg.GetPath())
                if Support.gVerbose > 2:
                    print(Support.myName(), ' full path=', self.fnNPath)
                f1 = open(self.fnNPath, 'r')
                fileText = f1.read()
                f1.close()
                self.eqSetResultText('')
                #self.lbl.SetLabel(self.fnNPath)
                self.eqSetMssg(self.fnNPath)
                self.eqSetCircuitText(fileText)
                self.setTextChangeFlag(False)
                self.SetTitle(os.path.split(self.fnNPath)[1])
            #dlg.Destroy()

    def saveFile(self, txt):
        try:
            with open(self.fnNPath, 'w+') as f1:
                f1.write(txt)
                f1.close()
                self.eqSetMssg(self.fnNPath)
                self.setTextChangeFlag(False)
        except IOError:
            wx.LogError("Cannot save the file in '%s'." % self.fnNPath)

if __name__ == '__main__':
    app = wx.App()
    #eqns = Equations("LaSolv", (20, 30), (600, 800))
    eqns = Equations()
    eqns.Show()
    app.MainLoop()
    #run_lasolv()
