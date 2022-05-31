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

@author: Thomas Spargo

'''
"""
      Original hierarchy
                        eqn=Frame
                        panel
main_sizerV+            Splitter Window
                    __________|___________
                    |                    |
    mn_sizerH=    main_panel        result_panel      =rs_sizerH
    mn_sizerH+   [main_text]       [result_text]     rs_sizerH+
                    |____________________|
                              |
                            GridBagSizer
info_sizer+     Open     Save    SaveAs     Solve Plot     O Mag/Angle |_| dB
info_sizer+     Quit                        Start xxxxx    O Re/Im      O Series
info_sizer+     Progress xxxxxxxxxxxxxxx     Stop xxxxx    O RLC        O Parallel
info_sizer+     Messages xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
main_sizer+     info_sizer
panel=          main_sizer
"""

import wx
import wx.html2

import Enums

class CircuitPanel(wx.Panel):
    """Holds the circuit text"""
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.parent = args[0]

        self.circuit_text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        #self.cktSizer = wx.BoxSizer(wx.HORIZONTAL)
        #self.cktSizer.Add(self.circuit_text, 1, wx.EXPAND)
        #self.SetSizer(self.cktSizer)
        #self.circuit_text.Bind(wx.EVT_KEY_DOWN, self.circuit_text.onKeyPress)

class ResultPanel(wx.Panel):
    """Holds the results text"""
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.parent = args[0]

        self.result_text = wx.TextCtrl(self, style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.result_text.SetEditable(False)
        #self.resSizer = wx.BoxSizer(wx.HORIZONTAL)
        #self.resSizer.Add(self.result_text, 1, wx.EXPAND)
        #self.SetSizer(self.resSizer)

class TextPanel(wx.SplitterWindow):
    """Holds the circuit and results panels"""
    def __init__(self, *args, **kwargs):
        wx.SplitterWindow.__init__(self, *args, **kwargs)
        self.parent = args[0]

        self.SetMinimumPaneSize(200)
        self.CktPanel = CircuitPanel(self)
        self.ResPanel = ResultPanel(self)
        self.SplitVertically(self.CktPanel, self.ResPanel)
        self.SetSashGravity(0.25)
        self.SetSashPosition(150, redraw=True)
        #self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        #self.sizer.Add(self.CktPanel, 1, wx.EXPAND)
        #self.sizer.Add(self.ResPanel, 1, wx.EXPAND)
        #self.SetSizer(self.sizer)

    def getCircuitText(self):
        return self.CktPanel.circuit_text.GetValue()

    def setCircuitText(self, text):
        self.CktPanel.circuit_text.SetValue(text)

    def setResultText(self, text):
        self.ResPanel.result_text.SetValue(text)

class ButtonPanel(wx.Panel):
    """The buttons and radioButton are here"""
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.parent = args[0]

        self.newBtn = wx.Button(self, wx.ID_ANY, "New")
        self.newBtn.Bind(wx.EVT_BUTTON, self.parent.onNew)
        self.openBtn = wx.Button(self, wx.ID_ANY, "Open...")
        self.openBtn.Bind(wx.EVT_BUTTON, self.parent.onOpen)
        self.saveBtn = wx.Button(self, wx.ID_ANY, "Save")
        self.saveBtn.Bind(wx.EVT_BUTTON, self.parent.onSave)
        self.saveAsBtn = wx.Button(self, wx.ID_ANY, "Save As...")
        self.saveAsBtn.Bind(wx.EVT_BUTTON, self.parent.onSaveAs)
        self.solveBtn = wx.Button(self, wx.ID_ANY, "Solve")
        self.solveBtn.Bind(wx.EVT_BUTTON, self.parent.onSolve)
        self.quitBtn = wx.Button(self, wx.ID_ANY, "Quit")
        self.quitBtn.Bind(wx.EVT_BUTTON, self.parent.onQuit)
        self.empty = wx.StaticText(self, label=' ')
        if self.parent.showTestMode:
            self.testModeBox = wx.CheckBox(self, label='Test Mode')
            self.testModeBox.Bind(wx.EVT_CHECKBOX, self.parent.setTestMode)
        else:
            self.testModeBox = wx.StaticText(self.parent, wx.ID_ANY, ' ')

        self.plotBtn = wx.Button(self, wx.ID_ANY, "Plot")
        self.plotBtn.Bind(wx.EVT_BUTTON, self.parent.onPlot)
        from_lbl = wx.StaticText(self, wx.ID_ANY, "Start freq:")
        self.plot_from = wx.TextCtrl(self, wx.ID_ANY)
        to_lbl = wx.StaticText(self, wx.ID_ANY, "Stop freq:")
        self.plot_to = wx.TextCtrl(self, wx.ID_ANY)

        self.fnNPath = wx.StaticText(self, wx.ID_ANY, 80 * ' ')
        font = wx.Font(16, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        self.fnNPath.SetFont(font)

        self.plotFormatBox = wx.RadioBox(self, label='',
                                         choices=Enums.pf_list, style=wx.RA_SPECIFY_ROWS)
        self.plotFormatBox.Bind(wx.EVT_RADIOBOX, self.parent.onPlotFormat)

        self.dBBox = wx.CheckBox(self, label='dB')
        self.dBBox.Bind(wx.EVT_CHECKBOX, self.parent.ondBMode)

        self.spBox = wx.RadioBox(self, label='',
                                 choices=Enums.format_sp, style=wx.RA_SPECIFY_ROWS)
        self.spBox.Bind(wx.EVT_RADIOBOX, self.parent.onSP)

        self.alwaysPlotRBox = wx.CheckBox(self, label='Always plot R')

        prgs = wx.StaticText(self, wx.ID_ANY, "Progress")
        self.gauge = wx.Gauge(self, range=100, size=(200, 20),
                              style=wx.GA_HORIZONTAL)

        sizer = wx.GridBagSizer(3, 3)  # 3, 3 are the gap dimensions
        sizer.Add(self.newBtn, pos=(0, 0), flag=wx.ALIGN_LEFT | wx.ALL, border=3)
        sizer.Add(self.openBtn, pos=(0, 1), flag=wx.ALIGN_LEFT | wx.ALL, border=3)
        sizer.Add(self.solveBtn, pos=(0, 2), flag=wx.ALIGN_LEFT | wx.ALL, border=3)
        sizer.Add(self.plotBtn, pos=(0, 3), flag=wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, border=3)
        sizer.Add(self.plotFormatBox, pos=(0, 4), span=(3, 1), flag=wx.ALIGN_LEFT | wx.ALL, border=1)
        sizer.Add(self.spBox, pos=(0, 5), span=(2, 1), flag=wx.ALIGN_LEFT | wx.ALL, border=1)
        sizer.Add(self.dBBox, pos=(0, 6), flag=wx.ALIGN_LEFT | wx.ALL, border=3)

        sizer.Add(self.saveBtn, pos=(1, 0), flag=wx.ALIGN_LEFT | wx.ALL, border=3)
        sizer.Add(self.saveAsBtn, pos=(1, 1), flag=wx.ALIGN_LEFT | wx.ALL, border=3)
        sizer.Add(from_lbl, pos=(1, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, border=3)
        sizer.Add(self.plot_from, pos=(1, 3), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, border=3)
        sizer.Add(self.alwaysPlotRBox, pos=(1, 6), flag=wx.ALIGN_LEFT | wx.ALL, border=3)

        sizer.Add(self.quitBtn, pos=(2, 0), flag=wx.ALIGN_LEFT | wx.ALL, border=3)
        sizer.Add(to_lbl, pos=(2, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, border=3)
        sizer.Add(self.plot_to, pos=(2, 3), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, border=3)
        sizer.Add(self.testModeBox, pos=(2, 6), flag=wx.ALIGN_LEFT | wx.ALL, border=3)

        sizer.Add(prgs, pos=(3, 0), flag=wx.ALIGN_LEFT | wx.ALL, border=3)
        sizer.Add(self.gauge, pos=(3, 1), span=(1, 3), flag=wx.ALIGN_LEFT | wx.RIGHT, border=3)

        sizer.Add(self.fnNPath, pos=(4, 0), span=(1, 7), flag=wx.EXPAND | wx.ALL, border=3)
        self.SetSizer(sizer)

        self.SetInitOptions()

    def SetFormatOption(self, fmt):
        pass

    def SetdbOption(self, db):
        self.dBBox.SetValue(db)

    def SetSPOption(self, sp):
        pass

    def SetAlwaysPlotROption(self, ar):
        self.alwaysPlotRBox.SetValue(ar)



    def Set_dBBoxEnabled(self, plot_fmt):
        self.dBBox.Enable(plot_fmt != 0)
        #self.dBBox.Enable(self.parent.plot_format == 0)

    def SetOptions(self, plt_fmt, dB, sp, rAlways, gage):
        self.plotFormatBox.SetSelection(plt_fmt)
        self.dBBox.SetValue(dB)
        self.spBox.SetSelection(sp)
        self.alwaysPlotRBox.SetValue(rAlways)
        self.gauge.SetValue(gage)

    def SetInitOptions(self):
        self.SetOptions(plt_fmt=0, dB=True, sp=0, rAlways=0, gage=0)

#    def EnableDisable(self):
##        self.Set_dBBoxEnabled(self.parent.GetPlot)
#        self.enabledAlwaysPlotRBox(self.SorP==Enums.format_sp)

class HtmlHelpWindow(wx.Frame):
    def __init__(self, parent, title, pth):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = (600,400))
        html = wx.html2.WebView.New(self)

        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        with open(pth, 'r') as file:
            html_str = file.read()
        html.SetPage(html_str,"")
