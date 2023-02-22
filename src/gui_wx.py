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
        try...11finally block?
        try: ...  except: ...raise
'''
import wx
import wx.stc as stc
import wx.html2 as wxh2
from sympy import fraction, N
#import sympy
import configparser
import eqnSolver
import Support
from sys import platform
import os.path
import ntpath
import Enums

class LaSolvApp(object):
    def __init__(self):
        #self.app = wx.App()
        #self.app.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        #self.frame.Show(True)
        #self.app.MainLoop()

        app = wx.App(False)
        self.__version__ = '1.0.0'
        __version_info__ = ('1', '0', '0')
        self.frame = eqs(None, -1, "LaSolv")
        app.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        #frm = eqs("LaSolv")
        app.MainLoop()

class xmlSTC(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)
        self.SetUseTabs(False)
        self.SetTabWidth(4)

class xmlPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent)
        self.xmlView = xmlSTC(self)

class eqs(wx.Frame):
    def __init__(self, parent, wxid, title):
        '''
        Constructor
        '''
        wx.Frame.__init__(self, parent, wxid, title, wx.DefaultPosition, (800, 600))
        self.Bind(wx.EVT_CLOSE, self.onQuit)

        #self.fileDir = os.getcwd()
        self.dirname = os.getcwd()
        self.configFN = 'LaSolv.ini'
        self.usePlotting = True
        self.showTestMode = True

        self.mainmenu = wx.MenuBar()
        self._init_file_menu()

        self.panel = wx.Panel(self, wx.ID_ANY)
        #self.panel = xmlPanel(self, wx.ID_ANY)
        self.plotFrame = None
        self.plotPanel = None

        self.getConfig()
        self.eqSolver = eqnSolver.eqn_solver()
        self.initVar()
        self.create_windows()
        self.add_menus()

    def _init_file_menu(self):
        """ Create the "File" menu items. """
        menu = wx.Menu()
        menu.Append(205, 'E&xit', 'Enough of this already!')
        self.Bind(wx.EVT_MENU, self.OnFileExit, id=205)
        self.mainmenu.Append(menu, '&File')

    def OnFileExit(self, event):
        self.Close()

    def getConfig(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.configFN):
            config.read(self.configFN)
            if 'DEFAULT' in config:
                print(config.keys())
                #self.fileDir = '/Users/Thomas/'
                self.dirname = '~'
                #self.fileDir= config['cktDir']
            else:
                # DEFAULT s/b in the config file, so maybe it's corrupted?
                self.createConfig(config)
        else:
            # No config exists, create it
            self.createConfig(config)

    def createConfig(self, configP):
        # set ckt directory to be the dir LaSolv is in unless the user changes it.
        configP['DEFAULT'] = {'cktDir': self.dirname}
        with open(self.configFN, 'w') as configfile:
            configP.write(configfile)

    def initVar(self):
        self.fullPath = None        # path + filename
        self.filename = ''          # filename
        self.dirname = ''           # path only
        self.theFile = None         # Text of the file, if one has been loaded
        self.plot_format = 0
        self.use_dB = True
        self.SorP = 0
        self.runTestMode = False
        self.textChanged = False
        self.numer = 0.0
        self.denom = 0.0

    def create_windows(self):
        '''
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
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # To detect when the text has changed
        self.splitter = wx.SplitterWindow(self.panel, wx.ID_ANY)
        self.splitter.SetMinimumPaneSize(200)

        main_panel = wx.Panel(self.splitter, wx.ID_ANY)
        self.main_text = wx.TextCtrl(main_panel, style=wx.TE_MULTILINE)
        mn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mn_sizer.Add(self.main_text, 1, wx.EXPAND)
        main_panel.SetSizer(mn_sizer)

        result_panel = wx.Panel(self.splitter, wx.ID_ANY)
        self.result_text = wx.TextCtrl(result_panel, style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.result_text.SetEditable(False)
        rs_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rs_sizer.Add(self.result_text, 1, wx.EXPAND)
        result_panel.SetSizer(rs_sizer)

        self.splitter.SplitVertically(main_panel, result_panel)
        self.splitter.SetSashGravity(0.25)
        self.splitter.SetSashPosition(150, redraw=True)

        main_sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)

        self.main_text.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)

        self.newBtn = wx.Button(self.panel, wx.ID_ANY, "New" )
        self.newBtn.Bind(wx.EVT_BUTTON, self.onNew)
        self.openBtn = wx.Button(self.panel, wx.ID_ANY, "Open..." )
        self.openBtn.Bind(wx.EVT_BUTTON, self.onOpen)
        self.saveBtn = wx.Button(self.panel, wx.ID_ANY, "Save")
        self.saveBtn.Bind(wx.EVT_BUTTON, self.onSave)
        self.saveAsBtn = wx.Button(self.panel, wx.ID_ANY, "Save As...")
        self.saveAsBtn.Bind(wx.EVT_BUTTON, self.onSaveAs)
        self.solveBtn = wx.Button(self.panel, wx.ID_ANY, "Solve")
        self.solveBtn.Bind(wx.EVT_BUTTON, self.onSolve)
        self.quitBtn = wx.Button(self.panel, wx.ID_ANY, "Quit")
        self.quitBtn.Bind(wx.EVT_BUTTON, self.onQuit)
        self.empty = wx.StaticText(self.panel, label=' ')
        if self.showTestMode:
            self.testModeBox = wx.CheckBox(self.panel, label = 'Test Mode')
            self.testModeBox.Bind(wx.EVT_CHECKBOX, self.setTestMode)
        else:
            self.testModeBox = wx.StaticText(self.panel, wx.ID_ANY, ' ')

        self.plotBtn = wx.Button(self.panel, wx.ID_ANY, "Plot" )
        self.plotBtn.Bind(wx.EVT_BUTTON, self.onPlot)
        from_lbl = wx.StaticText(self.panel, wx.ID_ANY, "Start freq:")
        self.plot_from = wx.TextCtrl(self.panel, wx.ID_ANY)
        to_lbl = wx.StaticText(self.panel, wx.ID_ANY, "Stop freq:")
        self.plot_to = wx.TextCtrl(self.panel, wx.ID_ANY)

        self.lbl = wx.StaticText(self.panel, wx.ID_ANY, 130*' ')
        font = wx.Font(16, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        self.lbl.SetFont(font)

        self.plotFormatBox = wx.RadioBox(self.panel, label = '', \
                                    choices=Enums.pf_list, style=wx.RA_SPECIFY_ROWS)
        self.plotFormatBox.Bind(wx.EVT_RADIOBOX, self.onPlotFormat)
        self.plotFormatBox.SetSelection(self.plot_format)

        self.dBBox = wx.CheckBox(self.panel, label = 'dB')
        self.dBBox.SetValue(self.use_dB)
        self.enabledBBox(self.plot_format==0)
        self.dBBox.Bind(wx.EVT_CHECKBOX, self.ondBMode)

        self.spBox = wx.RadioBox(self.panel, label = '', \
                                    choices=Enums.format_sp, style=wx.RA_SPECIFY_ROWS)
        self.spBox.Bind(wx.EVT_RADIOBOX, self.onSP)
        self.enableSPBox(self.plot_format!=0)

        prgs = wx.StaticText(self.panel, wx.ID_ANY, "Progress")
        self.gauge = wx.Gauge(self.panel, range=100, size=(200, 20), \
                              style=wx.GA_HORIZONTAL)

        '''
        new      open        solve    plot
        save     saveas
        '''

        info_sizer = wx.GridBagSizer(3, 3)
        info_sizer.Add(self.newBtn,     pos=(0, 0), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.openBtn,    pos=(0, 1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.quitBtn,    pos=(0, 2), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.solveBtn,   pos=(0, 3), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.plotBtn,    pos=(0, 4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.plotFormatBox, pos=(0, 5), span=(3, 1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.dBBox,      pos=(0, 6),  flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        info_sizer.Add(self.saveBtn,    pos=(1, 0), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.saveAsBtn,  pos=(1, 1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.testModeBox,pos=(1, 2), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(from_lbl,        pos=(1, 3), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, border=5)
        info_sizer.Add(self.plot_from,  pos=(1, 4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        #info_sizer.Add(self.plot_from,  pos=(1, 4), flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        info_sizer.Add(self.spBox,         pos=(1, 6), span=(2, 1), flag=wx.ALIGN_TOP, border=5)

        info_sizer.Add(prgs,            pos=(2, 0), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.gauge,      pos=(2, 1), span=(1, 2), flag=wx.RIGHT|wx.ALIGN_TOP, border=5)
        info_sizer.Add(to_lbl,          pos=(2, 3), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, border=5)
        info_sizer.Add(self.plot_to,    pos=(2, 4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)

        info_sizer.Add(self.lbl,        pos=(3, 0), span=(1, 5), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.AddGrowableCol(1)
        info_sizer.AddGrowableCol(4)

        main_sizer.Add(info_sizer, 0)

        self.panel.SetSizer(main_sizer)
        self.Show()

    def add_menus(self):
        file_menu = wx.Menu()
        about_item = file_menu.Append(wx.ID_ABOUT, "About LaSolv", "INFO")
        self.Bind(wx.EVT_MENU, self.onAbout, about_item)
        file_menu.AppendSeparator()
        quit_item = file_menu.Append(wx.ID_EXIT, "&Quit")
        self.Bind(wx.EVT_MENU, self.onQuit, quit_item)

        menu_bar = wx.MenuBar()

        new_item = file_menu.Append(wx.ID_NEW, "")
        self.Bind(wx.EVT_MENU, self.onNew, new_item)
        open_item = file_menu.Append(wx.ID_OPEN, "")
        self.Bind(wx.EVT_MENU, self.onOpen, open_item)
        save_item = file_menu.Append(wx.ID_SAVE, "")
        self.Bind(wx.EVT_MENU, self.onSave, save_item)
        saveas_item = file_menu.Append(wx.ID_SAVEAS, "")
        self.Bind(wx.EVT_MENU, self.onSaveAs, saveas_item)
        menu_bar.Append(file_menu, "&File")

        # The edit menu items seem to work without any extra code.
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_COPY, "")
        edit_menu.Append(wx.ID_CUT, "")
        edit_menu.Append(wx.ID_PASTE, "")
        menu_bar.Append(edit_menu, "Edit")

        solve_menu = wx.Menu()
        solve_item = solve_menu.Append(wx.ID_ANY, "&Solve\tCTRL+e")
        self.Bind(wx.EVT_MENU, self.onSolve, solve_item)
        plot_item = solve_menu.Append(wx.ID_ANY, "Plot\tCTRL+T")
        self.Bind(wx.EVT_MENU, self.onPlot, plot_item)

        menu_bar.Append(solve_menu, "Solve")

        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ANY, "Help")
        self.Bind(wx.EVT_MENU, self.onHelp, help_item)

        menu_bar.Append(help_menu, "Help")
        self.SetMenuBar(menu_bar)
        self.CreateStatusBar(1)

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
        self.plot_format = self.plotFormatBox.GetSelection()
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
            self.dBBox.Enable()
        else:
            self.dBBox.Disable()

    def enableSPBox(self, flag):
        if flag:
            self.spBox.Enable()
        else:
            self.spBox.Disable()

    def onSP(self, event):
        self.SorP = self.spBox.GetSelection()
        if self.eqSolver.getPlotFrame() is not None:
            self.onPlot(event, False)

########################
# Progress bar updater
########################
    def updateProgress(self, p):
        """
        Update the progress bar
        """
        self.gauge.SetValue(p)

#######################
# Button/Menu Callbacks
#######################
    def onAbout(self, event):
        if platform == 'win32':
            dlg = wx.MessageDialog(self, "LaSolv 1.0.0\nCopyright 2023 by Thomas Spargo", "About LaSolv...", wx.OK)
        else:
            dlg = wx.MessageDialog(self, "LaSolv 1.0.0\nCopyright 2023 by Thomas Spargo", "About LaSolv...", wx.OK)
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
            self.lbl.SetLabel("Sorry, I can't find the help file :(")

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
        if solveFirst:
            self.onSolve(event)
            self.onPlot(event, False)
        #if self.eqSolver.getEvalAnswer() is not None:
        if self.eqSolver.allValuesDefined():
            if self.plot_from.GetValue() == '' or self.plot_to.GetValue() == '':
                f_start = f_stop = -1
            else:
                f_start = float(eno.EngNumber(self.plot_from.GetValue()))
                f_stop = float(eno.EngNumber(self.plot_to.GetValue()))
                if f_start > f_stop:
                    self.lbl.SetLabel('Starting frequency is > stop frequency')
                    return
            if self.eqSolver.getPlotFrame() is not None:
                self.eqSolver.closePlot()
            err_txt = self.eqSolver.eqnPlot(f_start, f_stop, self.updateProgress, \
                                            self.plot_format, self.use_dB, self.SorP )
            if err_txt != "":
                self.lbl.SetLabel(err_txt)
        else:
            self.lbl.SetLabel('All components (except v, i) must have a value in order to plot')

    def onQuit(self, event):
        if self.textChanged:
            self.onSave(event)
        if self.eqSolver.getPlotFrame() is not None:
            self.eqSolver.closePlot()
        #self.Close()    Causes infinite loop
        self.Destroy()
        #wx.CallAfter(self.Close)

    def onSave(self, event):
        if self.fullPath==None:
            if Support.gVerbose > 2:
                print(Support.myName(), ' onSave calling onSaveAs')
            self.onSaveAs(event)
        else:
            t = self.getText()
            file1 = open(self.fullPath, "w+")
            file1.write(t)
            file1.close()
            self.setTextChangeFlag(False)

    def onSaveAs(self, event):
        # initialdir = '/Users/Thomas/eclipse-workspace/ESGui_Python/Circuit files')
        t = self.getText()
        with wx.FileDialog(self, "Save as:", wildcard='.txt files (*.txt)|*.txt',
            style=wx.FD_SAVE) as fileDialog:
            if fileDialog.ShowModal()==wx.ID_CANCEL:
                return
            fp = fileDialog.GetPath()
            try:
                with open(fp, 'w+') as f1:
                    f1.write(t)
                    f1.close()

            except IOError:
                wx.LogError("Cannot save the file in '%s'." % self.fullPath)

            self.setPathAndFilename(ntpath.dirname(fp), ntpath.basename(fp))

    def onSolve(self, event):
        if self.getTestMode():
            # Re-init the solver which may have values left over from a prior 'solve'
            self.eqSolver.__init__()
            result = self.eqSolver.eqnSolveEntry(None, True)
            if result:
                print("All tests passed")
        else:
            if not self.textChanged and self.fullPath==None:
                self.lbl.SetLabel('You must load or type in a circuit first')
            else:
                self.lbl.SetLabel('Solving.....')
                self.setResultText('')
                # wx.AppConsole().Yield()
                wx.GetApp().Yield()
                self.onSave(event)
                self.lbl.SetLabel(self.fullPath)
                #strng = "0.5*Rd*Rg*Rkn + 0.5*Rd*Rg*Rn + 0.5*Rd*Rg*Rs + 0.5*Rd*Rkn**2 + 1.0*Rd*Rkn*Rn + 1.0*Rd*Rkn*Rs + 0.5*Rd*Rn**2 + 1.0*Rd*Rn*Rs + 0.5*Rg*Rkn**2 + 1.0*Rg*Rkn*Rn + 0.5*Rg*Rkn*Rs + 0.5*Rg*Rn**2 + 0.5*Rg*Rn*Rs + 0.5*Rkn**2*Rs + 1.0*Rkn*Rn*Rs + 0.5*Rn**2*Rs"
                #eqnReader = cre.CReadEquation(strng)
                #eqn = eqnReader.readCPoly(strng)
                #print('Factored: ', sympy.factor(eqn))
                # self.eqSolver.__init__()
                result = self.eqSolver.eqnSolveEntry(self.fullPath, False)
                if result==0:  # ie, if no error occurred
                    if Support.gVerbose > 2:
                        print(Support.myName(), ' result=', result)
                        print(Support.myName(), 'raw=', self.eqSolver.getRawAnswer())
                        print(Support.myName(), 'simpl=', self.eqSolver.getSimplAnswer())
                        print(Support.myName(), 'eval=', self.eqSolver.getEvalAnswer())
                        print(Support.myName(), 'evalF=', self.eqSolver.getEvalFAnswer())
                        print(Support.myName(), 'best=', self.eqSolver.getBestAnswer())
                    self.setResultEqn()
                else:
                    if result==30:
                        err_txt =           "The solution denominator is 0.0. You may be asking LaSolv to\n"
                        err_txt = err_txt + "  solve for voltage in the wrong way. Remember that putting\n"
                        err_txt = err_txt + "  the name of a voltage source in the solve statement\n"
                        err_txt = err_txt + "  means 'calculate the current through this source'\n\n"
                        err_txt = err_txt + "Example: You want to find Vout/Vin, and you have this in\n"
                        err_txt = err_txt + "  your circuit file-\n"
                        err_txt = err_txt + "     Vin 1 0\n"
                        err_txt = err_txt + "     ....(other stuff)\n"
                        err_txt = err_txt + "     Rload 8 0\n"
                        err_txt = err_txt + "     solve 8 0 vin\n\n"
                        err_txt = err_txt + "Or:\n"
                        err_txt = err_txt + "     Vin 1 0\n"
                        err_txt = err_txt + "     ....(other stuff)\n"
                        err_txt = err_txt + "     Rload 8 0\n"
                        err_txt = err_txt + "     solve Rload Vin\n\n"
                        err_txt = err_txt + "This is the right way to get Vout/Vin:\n"
                        err_txt = err_txt + "     solve 8 0 1 0\n"
                    elif result==31:
                        err_txt = "The solution is 0.0. There's probably something wrong"
                        err_txt = err_txt + " with the circuit definition- a floating node (a"
                        err_txt = err_txt + " node with only one connection) is a common issue."
                    else:
                        # The error should have already been printed and a dialog been opened.
                        print("EqnSolveEntry returned error code ", str(result))
                        err_txt = ''
                    self.setResultText(err_txt)

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
        return self.main_text.GetValue()

    def setTextChangeFlag(self, flg):
        self.textChanged = flg
        if Support.gVerbose > 9:
            print(Support.myName(), 'textChanged=', self.textChanged)

    def setMainText(self, txt):
        self.main_text.SetValue(txt)

    def setResultText(self, txt):
        self.result_text.SetValue(txt)

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

    def setPathAndFilename(self, dir, fn):
        self.dirname = dir
        self.filename = fn
        self.fullPath = dir+'/'+fn
        self.setLabelAndTitle()

    def setLabelAndTitle(self):
        # If we're changing the title and label, the file has been saved or read or
        # something, so I set setTextChangeFlag to False.
        self.setTextChangeFlag(False)
        self.setResultText('')
        self.lbl.SetLabel(self.fullPath)
        self.SetTitle(self.filename)

###############################
#   Main menu item callbacks
###############################
    def newFile(self):
        self.initVar()
        self.setMainText('')
        self.setPathAndFilename(self.dirname, self.filename)
        #self.setResultText('')
        #self.lbl.SetLabel('')
        #self.SetTitle('')
        #self.setTextChangeFlag(False)

    def readFile(self):
        """Read the file, display in editing box. self.theFile is separate from self.theLines and
        self.theOrgLines, which is hokey but an artifact of Equation Solver being a non-GUI app initially."""
        dlg = wx.FileDialog(self, "Open...", self.dirname, "", "*.txt", wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.setPathAndFilename(dlg.GetDirectory(), dlg.GetFilename() )
            #self.filename = dlg.GetFilename()
            #self.dirname = dlg.GetDirectory()
            #self.fullPath = self.dirname+'/'+self.filename
            if Support.gVerbose > 2:
                print(Support.myName(), ' filename=', self.filename)
                print(Support.myName(), ' directory=', self.dirname)
                print(Support.myName(), ' full path=', self.fullPath)
            file1 = open(self.fullPath, 'r')
            self.theFile = file1.read()
            file1.close()
            self.setMainText(self.theFile)
        dlg.Destroy()


class HtmlHelpWindow(wx.Frame):
    def __init__(self, parent, title, pth): 
        wx.Frame.__init__(self, parent, -1, title, size = (600,400)) 
        html = wxh2.WebView.New(self)
        if "gtk2" in wx.PlatformInfo: 
            html.SetStandardFonts() 
        with open(pth, 'r') as file:
            html_str = file.read()
        html.SetPage(html_str,"")

def run_lasolv():

    LaSolvApp()

if __name__ == '__main__':
    run_lasolv()
