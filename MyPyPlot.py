'''
Created on Feb 6, 2019

@author: Thomas

'''

#import matplotlib
#matplotlib.use('WXAgg')
#import matplotlib.pyplot as plt

import wx
import wx.lib.plot as plot

import lumpy
import Enums
from math import ceil, floor

"""
class CanvasPanel(wx.Frame):
    def __init__(self, parent, gui, f_array, m_array, p_array):
        '''
        Takes a solved equation numer/denom, and plots it, xaxis is f_array, and y's are m_ & p_.
        '''
        self.panel = wx.Panel.__init__(self, parent)

        self.gui = gui
        self.xValues = f_array
        self.y1Values = m_array
        self.y2Values = p_array
        self.plot = None
        self.fig_size = None

    def getFigSize(self):
        return self.fig_size
    
    def closeFigure(self):
        self.fig_size = self.plot.get_size_inches()
        #print('closeFigure: fig-size=', self.fig_size)
        plt.close('all')
        #self.Close()
        
    def draw(self, plot_format, use_db, s_or_p, rlc_units, new_plot, fig_size):
        if fig_size is not None:
            self.fig_size = fig_size
        if new_plot:
            self.doSomething(plot_format, use_db, s_or_p, rlc_units)
        else:
            plt.close()
            self.doSomething(plot_format, use_db, s_or_p, rlc_units)
    
    def doSomething(self, plot_format, use_db, s_or_p, rlc_units):
        if self.fig_size is None:
            self.plot = plt.figure(1, figsize=(6,6))
        else:
            self.plot = plt.figure(1, figsize=self.fig_size)
        plt.subplot(2,1,1)
        plt.xscale('log')
        plt.subplots_adjust(hspace=0.55, top=0.92, left=0.15)
        plt.plot(self.xValues, self.y1Values)
        plt.grid(True)
        if plot_format == Enums.pf_list[0]:
            # Mag/Angle
            plt.title('Magnitude')
            if use_db:
                plt.ylabel('Magnitude, dB')
            else:
                plt.ylabel('Magnitude, V/V')
        elif plot_format == Enums.pf_list[1]:
            # Real/Imag
            if s_or_p == Enums.format_sp[0]:
                # Series
                plt.title('Resistance')
                plt.ylabel('Ohms')
            else:
                # Parallel
                plt.title('Conductance')
                plt.ylabel('Siemens')
        else:
            # RLC
            if s_or_p == Enums.format_sp[0]:
                # Series
                plt.title('Resistance')
                plt.ylabel('Ohms')
            else:
                # Parallel
                plt.title('Conductance')
                plt.ylabel('Siemens')
        plt.xlabel('Frequency')
        
        plt.subplot(2,1,2)
        plt.xscale('log')
        if plot_format == Enums.pf_list[0]:
            # Mag/Angle
            plt.title('Phase')
            plt.subplots_adjust(hspace=0.45, top=0.95)
            plt.ylabel('Phase, Degrees')
        elif plot_format == Enums.pf_list[1]:
            # Real/Imag
            if s_or_p == Enums.format_sp[0]:
                # Series
                plt.title('Reactance')
                plt.ylabel('Ohms')
            else:
                # Parallel
                plt.title('Susceptance')
                plt.ylabel('Siemens')
        else:
            # RLC
            if rlc_units == 'C':
                # Series
                plt.title('Capacitance')
                plt.ylabel('Farads')
            else:
                # Parallel
                plt.title('Inductance')
                plt.ylabel('Henries')
        plt.xlabel('Frequency')
        plt.plot(self.xValues, self.y2Values)
        plt.grid(True)
        if plot_format == Enums.pf_list[0]:
            bottom, top = plt.ylim()
            newB = floor(bottom/45.0)*45.0
            newT = ceil(top/45.0+1)*45.0
            if newB != newT:
                yt = lumpy.arange(newB, newT, 45.0)
            else:
                yt = [newB]
            plt.yticks(yt)
        #plt.draw()
        plt.show()

1) Define our data :

We insert your data in a list of tuples.
Each tuple will have two items.

data = [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5), (x6, y6)]

2) Create a plotting canvas we create an object of a PlotCanvas as a child of a frame :
   frame = wx.Frame(self, -1)
   client = wx.lib.plot.PlotCanvas(frame)
3) Create a graph There are two classes :
PolyLine and PolyMarker. PolyLine class defines line graphs.
Its constructor is :
PolyLine(list data, wx.Colour colour, integer width, integer style, string legend)
- data parameter is the data to be displayed.
- colour defines the colour of the line.
- width is the width of the pen, used to draw the graph.
- Possible style flags are wx.Pen styles.
- legend defines the line legend.
PolyMarker can be used to create scatter graphs and bar graphs as well.
Constructor :
PolyMarker(list data, wx.Colour colour, integer size, wx.Colour fillcolour, integer fillstyle, string markershape, string legend)
fillstyle is also various wx.Pen styles.

Marker Shapes :
circle
dot
square
triangle
triangle_down
cross
plus

4) Create a graph container :
Graph container is a container that holds a graph object and its title and labels.
PlotGraphics(list objects, string title, string xLabel, string yLabel)
objects is a list of one or more graph objects
title - title shown at top of graph
xLabel - label shown on x-axis
yLabel - label shown on y-axis
5) Draw a graph :
Finally we draw the graph.

client.Draw(gc,  xAxis=(0,15), yAxis=(0,15))

gc is a graph container object. xAxis and yAxis define the range of the axes (info by ZetCode / Jan Bodnar).
    """
class MyPyPlot(wx.Dialog):
    def __init__(self, parent, id, f_array, m_array, p_array):
        wx.Dialog.__init__(self, parent, id, "A Plot", size=(180, 280))

        #------------

        icon = wx.Icon("LaSolv_icon.icns")
        self.SetIcon(icon)

        #------------
        data1 = list()
        data2 = list()

        print(len(f_array))
        print(len(m_array))
        for inx in range(len(f_array)):
            print(inx, f_array[inx], m_array[inx])
            data1.append(  [f_array[inx], m_array[inx]] )
            data2.append(  [f_array[inx], p_array[inx]] )

        self.data = [(1,2), (2,3), (3,5), (4,6), (5,8), (6,8), (10,10)]
        self.OnLine()

    def OnLine(self):
        frm = wx.Frame(self, -1, 'Line', size=(600, 450))
        icon = wx.Icon("LaSolv_icon.icns")
        frm.SetIcon(icon)
        
        pnl = wx.Panel(frm, -1)        
        pnl.SetBackgroundColour(wx.WHITE)

        #------------
        
        client = plot.PlotCanvas(pnl)
        line = plot.PolyLine(self.data, legend='', colour='pink', width=1)
        gc = plot.PlotGraphics([line], 'Line Graph', 'X Axis', 'Y Axis')
        client.Draw(gc,  xAxis= (0,15), yAxis= (0,15))

        #------------
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(client, 1, wx.EXPAND | wx.ALL, 10)   
        pnl.SetSizer(mainSizer)

        #------------
        
        frm.Show(True)
