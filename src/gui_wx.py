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
'''
import wx.html
import engineering_notation as eno
import eqnSolver
import Support
#from os import getcwd
from sys import platform
import os.path
import Enums

class eqs(wx.Frame):
    

    def __init__(self, title):
        '''
        Constructor
        '''        
        self.dir = '/Users/Thomas/git/ESGui_Python/Circuit files/'
        self.usePlotting = True
        self.showTestMode = True
        
        wx.Frame.__init__(self, None, wx.ID_ANY, title=title, size=(800,300))
        self.Bind(wx.EVT_CLOSE, self.onQuit)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.plotFrame = None
        self.plotPanel = None
        
        self.eqSolver = eqnSolver.eqn_solver()

        self.initVar()
        self.create_windows()
        self.add_menus()

    def initVar(self):
        self.fullPath = None
        self.theFile = None
        self.plot_format = 0
        self.use_dB = True
        self.SorP = 0
        self.runTestMode = False
        self.textChanged = False
        self.filename = ''
        self.dirname = ''
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
        self.splitter.SetSashGravity(0.35)

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
        #info_sizer.Add(self.plotBtn,    pos=(0, 4), flag=wx.ALIGN_CENTER_VERTICAL, border=5)
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
        #info_sizer.Add(self.plot_to,    pos=(2, 4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.Add(self.plot_to,    pos=(2, 4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, border=5)

        info_sizer.Add(self.lbl,        pos=(3, 0), span=(1, 5), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        info_sizer.AddGrowableCol(1)
        info_sizer.AddGrowableCol(4)
        
        main_sizer.Add(info_sizer, 0)

        #self.panel.SetSizerAndFit(main_sizer)
        self.panel.SetSizer(main_sizer)
        #self.Layout()
        self.Show()
        #self.Fit()
        
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
        self.SetMenuBar(menu_bar)

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
        
#####################
# Button/Menu Callbacks
#####################
    def onAbout(self, event):
        if platform == 'win32':
            dlg = wx.MessageDialog(self, "LaSolv 0.8.1\nCopyright 2019 by Thomas Spargo", "About LaSolv...", wx.OK)
        else:
            dlg = wx.MessageDialog(self, "LaSolv 0.8.3\nCopyright 2019 by Thomas Spargo", "About LaSolv...", wx.OK)
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
            self.lbl.SetValue("Sorry, I can't find the help file :(")
    
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
        with wx.FileDialog(self, "Save as:", wildcard = '.txt files (*.txt)|*.txt', \
            style = wx.FD_SAVE) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.fullPath = fileDialog.GetPath()
            try:
                with open(self.fullPath, 'w+') as f1:
                    f1.write(t)
                    f1.close()
                    self.lbl.SetLabel(self.fullPath)
                    self.setTextChangeFlag(False)
            except IOError:
                wx.LogError("Cannot save the file in '%s'." % self.fullPath)

    def onSolve(self, event):
        if self.getTestMode():
            result = self.eqSolver.eqnSolveEntry(None, True)
        else:
            if self.textChanged or self.fullPath != None:
                self.lbl.SetLabel('Solving.....')
                #wx.AppConsole().Yield()
                wx.GetApp().Yield()
                self.onSave(event)
                result = self.eqSolver.eqnSolveEntry(self.fullPath, False)
                self.lbl.SetLabel(self.fullPath)
                if result == 0:
                    if Support.gVerbose > 3:
                        print(Support.myName(), ' result=', result)
                    self.numer = self.eqSolver.getNumer()
                    self.denom = self.eqSolver.getDenom()
                    if self.eqSolver.getEvalAnswer() is None:
                        self.setResultEqn(self.numer, self.denom)
                    else:
                        self.setResultEqn(self.numer, self.denom, \
                                          self.eqSolver.getBestAnswer())
                else:
                    # eqSolver returned an error string as the first arg to result
                    self.setResultText(result)
            else:
                self.lbl.SetLabel('You must load or type in a circuit first')  
       
    def onPlot(self, event, solveFirst=True):
        if solveFirst:
            self.onSolve(event)
        if self.eqSolver.getEvalAnswer() is not None:
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
            self.lbl.SetLabel('You must add values to all components (except v, i) to plot')

    def onQuit(self, event):
        if self.eqSolver.getPlotFrame() is not None:
            self.eqSolver.closePlot()
        #self.Close()    Causes infinite loop
        self.Destroy()
        #wx.CallAfter(self.Close)
        
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
    
    def setResultEqn(self, numer, denom, final_eqn=None):
        ''' Take polynomial fraction and prints it in the result text window'''
        self.numer = numer
        self.denom = denom
        numer_str = str(numer)
        denom_str = str(denom)
        width = max(len(numer_str), len(denom_str))
        if Support.gVerbose > 2:
            print(Support.myName(), ' width=', width, '  numer_str=', numer_str, \
                  '  denom_str=', denom_str)
        sep = width*'-'
        txt = numer_str+'\n'+sep+'\n'+denom_str
        #txt = txt + '\n' + str(denom.expand())
        if final_eqn is not None:
            txt = txt + '\n\nWith values substituted, the result is:\n'+str(final_eqn)
        self.setResultText(txt)

    def newFile(self):
        self.initVar()
        self.setResultText('')
        self.lbl.SetLabel('')
        self.setMainText('')
        self.setTextChangeFlag(False)

    def readFile(self):
        dlg = wx.FileDialog(self, "Open...", self.dir, "", "*.txt", wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
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
            self.lbl.SetLabel(self.fullPath)
            self.setMainText(self.theFile)
            self.setTextChangeFlag(False)

        dlg.Destroy()


class HtmlHelpWindow(wx.Frame):
    def __init__(self, parent, title, pth): 
        wx.Frame.__init__(self, parent, -1, title, size = (600,400)) 
        html = wx.html.HtmlWindow(self) 
          
        if "gtk2" in wx.PlatformInfo: 
            html.SetStandardFonts() 
        
        html.LoadPage(pth) 
                           
class HelpWindow(wx.Frame):
    def __init__(self, parent, title, txt):
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY, title=title,
            style=(wx.DEFAULT_FRAME_STYLE | wx.WS_EX_CONTEXTHELP) ,
            pos=(20, 20))
        self.SetExtraStyle(wx.FRAME_EX_CONTEXTHELP)
        self.CreateStatusBar()
        panel = wx.Panel(self)
        self.label = wx.StaticText(panel)
        self.label.SetLabel(txt)    
        self.okButton = wx.Button(self, wx.ID_OK)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(panel, 1, wx.EXPAND | wx.ALL)
        vbox.Add(self.okButton, 0, wx.ALL, 3)
        self.Bind(wx.EVT_BUTTON, self.closeHelp, self.okButton)
        self.SetSizer(vbox)

        self.Show()
    
    def closeHelp(self, event):
        self.Close()
        
app = wx.App(False)
app.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
frm = eqs("LaSolv")
app.MainLoop()
