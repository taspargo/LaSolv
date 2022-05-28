'''
Created on Feb 6, 2019

@author: Thomas

'''

#import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt

import wx
import lumpy
import Enums
from math import ceil, floor

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
