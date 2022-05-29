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
import wx.html2
import engineering_notation as eno
from sympy import fraction, N
import configparser
import eqnSolver
import Support
from sys import platform
import os.path
import Enums

#class LaSolvApp(wx.App):
#    def OnInit(self):
        #app = wx.App(False)
        #self.frame = eqs(None, -1, "LaSolv")
        #app.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        #frm = eqs("LaSolv")
        #app.MainLoop()
 #       eqnsFrame = Equations("LaSolv 0.9.3", (50, 60), (800, 500))
 #       eqnsFrame.Show()
 #       self.SetTopWindow(eqnsFrame)

#        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

#        return True

class xmlSTC(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)
        self.SetUseTabs(False)
        self.SetTabWidth(4)

class xmlPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.xmlView = xmlSTC(self)

'''
      Original hierarchy
                        Frame
                        panel
                        Splitter Window
                        (main_sizer V)
                    __________|___________
                    |                    |
                main_panel        result_panel
                [main_text]       [result_text]
                (mn_sizer H)       (rs_sizerH)
                    |____________________|
                              |
                       GridBagSizer
        Open     Save    SaveAs     Solve Plot     O Mag/Angle |_| dB
        Quit                        Start xxxxx    O Re/Im      O Series
        Progress xxxxxxxxxxxxxxx     Stop xxxxx    O RLC        O Parallel
        Messages xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        '''

class CircuitPanel(wx.Panel):
    """Holds the circuit text"""
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # To detect when the text has changed
        #self.splitter = wx.SplitterWindow(self.panel, wx.ID_ANY)
        #self.splitter.SetMinimumPaneSize(200)

        self.circuit_text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
       # mn_sizer = wx.BoxSizer(wx.HORIZONTAL)
       # mn_sizer.Add(self.circuit_text, 1, wx.EXPAND)
       # self.SetSizer(mn_sizer)

        # Add this to the frame class
        #self.circuit_text.Bind(wx.EVT_KEY_DOWN, self.circuit_text.onKeyPress)

class ResultPanel(wx.Panel):
    """Holds the results text"""
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.result_text = wx.TextCtrl(self, style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.result_text.SetEditable(False)
       # rs_sizer = wx.BoxSizer(wx.HORIZONTAL)
       # rs_sizer.Add(self.result_text, 1, wx.EXPAND)
       # self.SetSizer(rs_sizer)

class TextPanel(wx.SplitterWindow):
    """Holds the circuit and results panels"""
    def __init__(self, parent, *args, **kwargs):
        wx.SplitterWindow.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.CktPanel = CircuitPanel(self)
        self.ResPanel = ResultPanel(self)
        self.SplitVertically(self.CktPanel, self.ResPanel)
        self.SetSashGravity(0.25)
        self.SetSashPosition(150, redraw=True)

        #main_panel.SetSizer(mn_sizer)
       # main_sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)
    def GetCircuitText(self):
        return self.GetCircuitText()

    def SetCircuitText(self, text):
        self.SetCircuitText(text)

    def SetResultText(self, text):
        self.SetResultText(text)

class ButtonPanel(wx.Panel):
    """The buttons and radioButton are here"""
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(parent, *args, **kwargs)
        self.parent = parent

        self.newBtn = wx.Button(self.parent, wx.ID_ANY, "New")
        self.newBtn.Bind(wx.EVT_BUTTON, self.parent.onNew)
        self.openBtn = wx.Button(self.parent, wx.ID_ANY, "Open...")
        self.openBtn.Bind(wx.EVT_BUTTON, self.parent.onOpen)
        self.saveBtn = wx.Button(self.parent, wx.ID_ANY, "Save")
        self.saveBtn.Bind(wx.EVT_BUTTON, self.parent.onSave)
        self.saveAsBtn = wx.Button(self.parent, wx.ID_ANY, "Save As...")
        self.saveAsBtn.Bind(wx.EVT_BUTTON, self.parent.onSaveAs)
        self.solveBtn = wx.Button(self.parent, wx.ID_ANY, "Solve")
        self.solveBtn.Bind(wx.EVT_BUTTON, self.parent.onSolve)
        self.quitBtn = wx.Button(self.parent, wx.ID_ANY, "Quit")
        self.quitBtn.Bind(wx.EVT_BUTTON, self.parent.onQuit)
        self.empty = wx.StaticText(self.parent, label=' ')
        if self.parent.showTestMode:
            self.testModeBox = wx.CheckBox(self.parent, label='Test Mode')
            self.testModeBox.Bind(wx.EVT_CHECKBOX, self.parent.setTestMode)
        else:
            self.testModeBox = wx.StaticText(self.parent, wx.ID_ANY, ' ')

        self.plotBtn = wx.Button(self.parent, wx.ID_ANY, "Plot")
        self.plotBtn.Bind(wx.EVT_BUTTON, self.parent.onPlot)
        from_lbl = wx.StaticText(self.parent, wx.ID_ANY, "Start freq:")
        self.plot_from = wx.TextCtrl(self.parent, wx.ID_ANY)
        to_lbl = wx.StaticText(self.parent, wx.ID_ANY, "Stop freq:")
        self.plot_to = wx.TextCtrl(self.parent, wx.ID_ANY)

        # self.fnNPath = wx.StaticText(self.parent, wx.ID_ANY, 130*' ')
        self.fnNPath = wx.StaticText(self.parent, wx.ID_ANY, 80 * ' ')
        font = wx.Font(16, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        self.fnNPath.SetFont(font)

        self.plotFormatBox = wx.RadioBox(self.parent, label='',
                                         choices=Enums.pf_list, style=wx.RA_SPECIFY_ROWS)
        self.plotFormatBox.Bind(wx.EVT_RADIOBOX, self.parent.onPlotFormat)
        self.plotFormatBox.SetSelection(self.parent.plot_format)

        self.dBBox = wx.CheckBox(self.parent, label='dB')
        self.dBBox.SetValue(self.parent.use_dB)
        self.dBBox.Enable(self.parent.plot_format == 0)
        self.dBBox.Bind(wx.EVT_CHECKBOX, self.parent.ondBMode)

        self.spBox = wx.RadioBox(self.parent, label='',
                                 choices=Enums.format_sp, style=wx.RA_SPECIFY_ROWS)
        self.spBox.Bind(wx.EVT_RADIOBOX, self.parent.onSP)
        self.spBox.Enable(self.parent.plot_format != 0)

        self.alwaysPlotRBox = wx.CheckBox(self.parent, label='Always plot R')
        self.alwaysPlotRBox.SetValue(self.parent.alwaysPlotR)
        # self.enabledAlwaysPlotRBox(self.SorP==Enums.format_sp2)

        prgs = wx.StaticText(self.parent, wx.ID_ANY, "Progress")
        self.gauge = wx.Gauge(self.parent, range=100, size=(200, 20),
                              style=wx.GA_HORIZONTAL)

class Equations(wx.Frame):
    def __init__(self, parent, wxid, title):
        """
        Constructor
        """
        wx.Frame.__init__(self, None, -1, title, pos=(20,20), size=(800,400))
        #wx.Frame.__init__(self, parent, wxid, title, size=(800,400))

        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        self.menus = TheMenus(self)

        #self.fileDir= '/Users/Thomas/Programming/Python/Wing_Projects/LaSolv/Examples/'
        self.fileDir = os.getcwd()
        self.configFN = 'LaSolv.ini'
        self.usePlotting = True
        self.showTestMode = True

        self.TextPanel = TextPanel(self)
        self.ButtonPanel = ButtonPanel(self)
        self.fnNPath = self.ButtonPanel.fnNPath

        ud_sizer = wx.BoxSizer(wx.VERTICAL)
        ud_sizer.Add(self.TextPanel, wx.ALIGN_CENTER_VERTICAL, wx.EXPAND)
        ud_sizer.Add(self.ButtonPanel, wx.ALIGN_CENTER_VERTICAL, wx.EXPAND)

        #self.panel = wx.Panel(self, wx.ID_ANY)
        #self.panel = xmlPanel(self, wx.ID_ANY)
        self.plotFrame = None
        self.plotPanel = None

        self.getConfig()

        self.eqSolver = eqnSolver.eqn_solver()
        self.initVar()

    def GetPlotFrom(self):
        return self.ButtonPanel.plot_from.GetValue()

    def GetPlotTo(self):
        return self.ButtonPanel.plot_to.GetValue()

    def GetSorP(self):
        return self.ButtonPanel.spBox.GetSelection()

    def GetAlwaysPlotR(self):
        return self.ButtonPanel.alwaysPlotRBox.GetValue()

    def GetUseDB(self):
        return self.ButtonPanel.dBBox.GetValue()

    def SetUseDB(self, d):
        self.ButtonPanel.dBBox.SetValue(d)


    # def _init_file_menu(self):
    #     """ Create the "File" menu items. """
    #     menu = wx.Menu()
    #     menu.Append(205, 'E&xit', 'Enough of this already!')
    #     self.Bind(wx.EVT_MENU, self.OnFileExit, id=205)
    #     self.mainmenu.Append(menu, '&File')

    def OnFileExit(self, event):
        self.Close()

    def getConfig(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.configFN):
            config.read(self.configFN)
            if 'DEFAULT' in config:
                print(config.keys())
                self.fileDir = '/Users/Thomas/'
                #self.fileDir= config['cktDir']
            else:
                # DEFAULT s/b in the config file, so maybe it's corrupted?
                self.createConfig(config)
        else:
            # No config exists, create it
            self.createConfig(config)

    def createConfig(self, configP):
        # set ckt directory to be the dir LaSolv is in unless the user changes it.
        configP['DEFAULT'] = {'cktDir': self.fileDir}
        with open(self.configFN, 'w') as configfile:
            configP.write(configfile)

    def initVar(self):
        self.fullPath = None
        self.theFile = None
        self.plot_format = 0
        self.use_dB = True
        #self.SorP = 0
        #self.alwaysPlotR = True
        self.runTestMode = False
        self.textChanged = False
        self.filename = ''
        self.dirname = ''
        self.numer = 0.0
        self.denom = 0.0


#####################
# Option Callbacks
#####################
    def setTestMode(self, event):
        cb = event.GetEventObject()
        self.runTestMode = cb.GetValue()

    def getTestMode(self):
        return self.runTestMode

    # If format set to mag/ang:
    #    Enable the dBBox.
    #    Disable the s/p radiobuttons
    # If format is set to Re/Im or RLC:
    #    Enable the series/parallel box.
    #    Disable the dBBox
    def onPlotFormat(self, event):
        #self.plot_format = self.plotFormatBox.GetSelection()
        #print('onPlotFormat: plot_format=', self.plot_format)
        if self.plot_format == 0:
            self.enabledBBox(True)
            self.enableSPBox(False)
        else:
            self.enabledBBox(False)
            self.enableSPBox(True)
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)


    def ondBMode(self, event):
        cb = event.GetEventObject()
        self.use_dB = cb.GetValue()
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)

    def enabledBBox(self, flag):
        if flag:
            self.ButtonPanel.dBBox.Enable()
        else:
            self.ButtonPanel.dBBox.Disable()

    def enableSPBox(self, flag):
        if flag:
            self.ButtonPanel.spBox.Enable()
        else:
            self.ButtonPanel.spBox.Disable()

    def onSP(self, event):
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)

    def onAlwaysPlotR(self, event):
        if self.eqSolver.getPlotFrame() is not None:
            pass

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
            dlg = wx.MessageDialog(self, "LaSolv 0.9.5\nCopyright 2022 by Thomas Spargo", "About LaSolv...", wx.OK)
        else:
            dlg = wx.MessageDialog(self, "LaSolv 0.9.5\nCopyright 2022 by Thomas Spargo", "About LaSolv...", wx.OK)
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

            helpWin = HtmlHelpWindow(self, 'Helpful window', thePath)
            helpWin.Show()
        else:
            self.fnNPath.SetLabel("Sorry, I can't find the help file :(")

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
        #if self.textChanged:
        if 1:
            if solveFirst:
                self.onSolve(event)
                self.onPlot(event, False)
            #if self.eqSolver.getEvalAnswer() is not None:
            if self.eqSolver.allValuesDefined():
                if self.GetPlotFrom() == '' or self.GetPlotTo() == '':
                    f_start = f_stop = -1
                else:
                    f_start = float(eno.EngNumber(self.GetPlotFrom()))
                    f_stop = float(eno.EngNumber(self.GetPlotTo()))
                    if f_start > f_stop:
                        self.fnNPath.SetLabel('Starting frequency is > stop frequency')
                        return
                if self.eqSolver.getPlotFrame() is not None:
                    self.eqSolver.closePlot()
                err_txt = self.eqSolver.eqnPlot(f_start, f_stop, self.updateProgress,
                                                self.plot_format, self.GetUseDB(), self.GetSorP() )
                if err_txt != "":
                    self.fnNPath.SetLabel(err_txt)
            else:
                self.fnNPath.SetLabel('All components (except v, i) must have a value in order to plot')

    def onQuit(self, event):
        if self.textChanged:
            self.onSave(event)
        if self.eqSolver.getPlotFrame() is not None:
            print("onQuit: eqSolver.closePlot()")
            self.eqSolver.closePlot()
        print("onQuit: Destroy")
        self.Close()
        #wx.CallAfter(self.Destroy)

    def onSave(self, event):
        if self.fullPath == None:
            self.onSaveAs(event)
        else:
            t = self.getText()
            file1 = open(self.fullPath, "w+")
            file1.write(t)
            file1.close()
            self.setTextChangeFlag(False)

    def onSaveAs(self, event):
        #initialdir = '/Users/Thomas/eclipse-workspace/ESGui_Python/Circuit files')
        t = self.getText()
        with wx.FileDialog(self, "Save as:", wildcard = '.txt files (*.txt)|*.txt',
            style = wx.FD_SAVE) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.fullPath = fileDialog.GetPath()
            try:
                with open(self.fullPath, 'w+') as f1:
                    f1.write(t)
                    f1.close()
                    self.fnNPath.SetLabel(self.fullPath)
                    self.setTextChangeFlag(False)
            except IOError:
                wx.LogError("Cannot save the file in '%s'." % self.fullPath)

    def onSolve(self, event):
        if self.getTestMode():
            # Re-init the solver which may have values left over from a prior 'solve'
            self.eqSolver.__init__()
            result = self.eqSolver.eqnSolveEntry(None, True)
        else:
            if self.textChanged or self.fullPath != None:
                self.fnNPath.SetLabel('Solving.....')
                self.setResultText('')
                #wx.AppConsole().Yield()
                wx.GetApp().Yield()
                self.onSave(event)
                self.fnNPath.SetLabel(self.fullPath)
                #self.eqSolver.__init__()
                result = self.eqSolver.eqnSolveEntry(self.fullPath, False)
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
                    if result == 30:
                        err_txt =           "The solution denominator is 0.0. You may be asking to"
                        err_txt = err_txt + " solve for something 'weird'. Try solving for something"
                        err_txt = err_txt + " slightly different. For instance, if you have something"
                        err_txt = err_txt + " like this in your circuit file:"
                        err_txt = err_txt + "     Vin 1 0"
                        err_txt = err_txt + "     ....(other stuff)"
                        err_txt = err_txt + "     Rload 8 0 "
                        err_txt = err_txt + "     solve 8 0 vin"
                        err_txt = err_txt + " Trying changing the solve statement to: "
                        err_txt = err_txt + "     solve 8 0 1 0"
                    elif result == 31:
                        err_txt =           "The solution is 0.0. There's probably something wrong"
                        err_txt = err_txt + " with the circuit definition- a floating node (a"
                        err_txt = err_txt + " node with only one connection) is a common issue."
                    else:
                        # The error should have already been printed and a dialog been opened.
                        print("EqnSolveEntry returned error code ", str(result))
                        err_txt = ''
                    self.setResultText(err_txt)
            else:
                self.fnNPath.SetLabel('You must load or type in a circuit first')

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
# Text Callbacks, setters and getters
########################################
    def getText(self):
        return self.TextPanel.GetCircuitText()

    def setTextChangeFlag(self, flg):
        self.textChanged = flg
        if Support.gVerbose > 9:
            print(Support.myName(), 'textChanged=', self.textChanged)

    def setCircuitText(self, txt):
        self.TextPanel.SetCircuitText(txt)

    def setResultText(self, txt):
        self.TextPanel.SetResultText(txt)

    ## Take a sympy numer, denom and convert to a string expression like:
    ## "numer
    ##  -----------
    ##  denominator"

    def nd2string(self, eqn, prec=3):
        n, d = fraction(eqn)
        #numer_str = str(n)
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
        self.setResultText(txt)

    def newFile(self):
        self.initVar()
        self.setResultText('')
        self.fnNPath.SetLabel('')
        self.setCircuitText('')
        self.SetTitle('')

        self.setTextChangeFlag(False)

    def readFile(self):
        dlg = wx.FileDialog(self, "Open...", self.dirname, "", "*.txt", wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.fullPath = self.dirname+'/'+self.filename
            if Support.gVerbose > 2:
                print(Support.myName(), ' filename=', self.filename)
                print(Support.myName(), ' directory=', self.dirname)
                print(Support.myName(), ' full path=', self.fullPath)
            file1 = open(self.fullPath, 'r')
            self.theFile = file1.read()
            file1.close()
            self.setResultText('')
            #self.lbl.SetLabel(self.fullPath)
            self.setCircuitText(self.theFile)
            self.setTextChangeFlag(False)
            self.SetTitle(self.filename)

        dlg.Destroy()

class TheMenus(wx.Menu):
    def __init__(self, parent, *args, **kwargs):
        wx.Menu.__init__(self, *args, **kwargs)
        self.parent = parent

        self.file_menu = wx.Menu()
        about_item = self.file_menu.Append(wx.ID_ABOUT, "About LaSolv", "INFO")
        self.Bind(wx.EVT_MENU, self.parent.onAbout, about_item)
        self.file_menu.AppendSeparator()
        quit_item = self.file_menu.Append(wx.ID_EXIT, "&Quit")
        self.Bind(wx.EVT_MENU, self.parent.onQuit, quit_item)

        new_item = self.file_menu.Append(wx.ID_NEW, "")
        self.Bind(wx.EVT_MENU, self.parent.onNew, new_item)
        open_item = self.file_menu.Append(wx.ID_OPEN, "")
        self.Bind(wx.EVT_MENU, self.parent.onOpen, open_item)
        save_item = self.file_menu.Append(wx.ID_SAVE, "")
        self.Bind(wx.EVT_MENU, self.parent.onSave, save_item)
        saveas_item = self.file_menu.Append(wx.ID_SAVEAS, "")
        self.Bind(wx.EVT_MENU, self.parent.onSaveAs, saveas_item)

        # The edit menu items seem to work without any extra code.
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_COPY, "")
        edit_menu.Append(wx.ID_CUT, "")
        edit_menu.Append(wx.ID_PASTE, "")

        solve_menu = wx.Menu()
        solve_item = solve_menu.Append(wx.ID_ANY, "&Solve\tCTRL+e")
        self.Bind(wx.EVT_MENU, self.parent.onSolve, solve_item)
        plot_item = solve_menu.Append(wx.ID_ANY, "Plot\tCTRL+T")
        self.Bind(wx.EVT_MENU, self.parent.onPlot, plot_item)

        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ANY, "Help")
        self.Bind(wx.EVT_MENU, self.parent.onHelp, help_item)

        menu_bar = wx.MenuBar()
        menu_bar.Append(self.file_menu, "&File")
        menu_bar.Append(edit_menu, "Edit")
        menu_bar.Append(solve_menu, "Solve")
        menu_bar.Append(help_menu, "Help")
        self.parent.SetMenuBar(menu_bar)
        #self.parent.CreateStatusBar(1)
        #self.parent.SetStatusText(wx.wxT("Still LaSolv"))

class HtmlHelpWindow(wx.Frame):
    def __init__(self, parent, title, pth): 
        wx.Frame.__init__(self, parent, -1, title, size = (600,400)) 
        html = wx.html2.WebView.New(self)

        if "gtk2" in wx.PlatformInfo: 
            html.SetStandardFonts() 
        with open(pth, 'r') as file:
            html_str = file.read()
        html.SetPage(html_str,"")

#def run_lasolv():
#    LaSolvApp()

if __name__ == '__main__':
    app = wx.App()
    #eqns = Equations("LaSolv", (20, 30), (600, 800))
    eqns = Equations("LaSolv")
    eqns.Show()
    app.MainLoop()
    #run_lasolv()
