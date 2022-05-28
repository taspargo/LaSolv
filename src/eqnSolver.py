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
Created on Nov 27, 2016

@author: Tom Spargo

cse    common sub-expression detection and collection. Use for eval at a point. See Term Rewriting
subs    substitute expression for another. can be used for simplifying or
        In sympy.core.basic.
            
ToDo:
    * Make file reader take a text string instead of a filename so the file doesn't need to be saved
    before solving
    * Automatic simplification of equantions over a given freq range-
        Sweep freq, keep the magnitude of each term at each freq point
        Determine which, if any terms are small compared to the sum, remove those
        Do the same in the symobic equation and simplify.
'''

from wx import Frame, Yield
from ntpath import dirname
import sympy
import lumpy
from math import log10, pow, floor, pi, sqrt, atan2

from os import chdir, getcwd
import time
import CCircuit as CCircuit
import CFileReader as CFileReader
import CSimpList
from CLinearEquations import CLinearEquations
import Support
import MyPlot
import Enums

def round10(flt, direction):
    logf = floor(log10(flt))
    
    if direction == 0:
        res = logf
    else:
        res = logf+1
    ans = pow(10, res)
    return round(ans)
    
def round125(flt, direction):
    '''Rounds to 1, 2, 5 numbers, in the direction given- 0 is down, 1 is up'''
    log2 = log10(2)
    log5 = log10(5)
    
    logf = log10(flt)
    flr = floor(logf)
    mod = logf-flr
    if direction==0:
        if mod < log2:
            result = flr
        elif mod < log5:
            result = flr+log2
        else:
            result = flr+log5
    else:
        if mod > log5:
            result = flr+1
        elif mod > log2:
            result = flr+log5
        else:
            result = flr+log2
    ans = pow(10, result)
    return round(ans)

class eqn_solver(object):
    
    def __init__(self):
        self.solved = 0
        self.failed = 0
        self.matched = 0
        self.didntMatch = 0
        self.theCircuit = None
        self.linearEquations = None
        self.simpList = None
        self.subList = None
        self.numer = None
        self.denom = None
        self.rawAnswer = None   # Answer with all original components in it.
        self.simpAnswer = None  # Raw answer + simplifying assumptions
        self.subAnswer = None   # SimpAnswer + substitute values put in
        self.evalAnswer = None  # subAnswer with component values put in, not freq
        self.evalFAnswer = None # Answer with components and freq put in.
        self.testAnswer = None  # Answer from some files with the 'answer' keyword
        
        self.plotFrame = None 
        self.plotPanel = None
        self.use_db = True
        self.fig_size = None
        self.length = 100

    def getPlotFrame(self):
        return self.plotFrame
    
    def getPlotPanel(self):
        return self.plotPanel
    
    def getNumer(self):
        return self.numer
    
    def getDenom(self):
        return self.denom
    
    def getRawAnswer(self):
        return self.rawAnswer
    
    def getEvalAnswer(self):
        return self.evalAnswer
    
    def getEvalFAnswer(self):
        return self.evalFAnswer
    
    def getBestAnswer(self):
        '''Returns evalFAnswer if it exists, otherwise returns evalAnswer.'''
        if self.evalFAnswer is not None:
            return self.evalFAnswer
        else:
            return self.evalAnswer
        
    def getLinEqn(self):
        return self.linearEquations
    
    def eqnSolveEntry(self, filePath, testMode):
        """Run self-tests (testMode = True or False) or analyze the theCircuit in the filename 'theFile'.
        Inputs:     filePath = full path+filename
                    testMode = 0 or 1, 0 to analyze the circuit in the pass file, or 1 to solve a bunch of circuits and see
                        if the answers match those in the file.
        Output:     testMode = 0: Returns 0
                    testMode = 1: Returns err_text"""
        
        if testMode:
            self.solved = 0
            self.failed = 0
            self.matched = 0
            self.didntMatch = 0
            
            onesThatFailed = [ ]
            onesThatDidntMatch = [ ]
            print('main: cwd=', getcwd())
            
            chdir('../Examples_w_answers')
            print('main: cwd=', getcwd())
            filesToUse = ['ota_output.txt']
            filesToUse.append('test_bjt.txt')
            filesToUse.append('test_bjt_ronly.txt')
            filesToUse.append('test_casc_gain_no_cpi.txt')
            filesToUse.append('test_cccs.txt')
            filesToUse.append('test_ccvs.txt')
            filesToUse.append('test_ce_degen_zout.txt')
            filesToUse.append('test_ef_zin.txt')
            filesToUse.append('test_ef_zout_inc_Re.txt')
            filesToUse.append('test_ef_zout.txt')
            filesToUse.append('test_f.txt')
            filesToUse.append('test_f2.txt')
            filesToUse.append('test_h.txt')
            filesToUse.append('test_h2.txt')
            filesToUse.append('test_h3.txt')
            filesToUse.append('test_h4.txt')
            filesToUse.append('test_rcr.txt')
            filesToUse.append('test_vccs.txt')
            filesToUse.append('test_vcvs.txt')
             
            for it in filesToUse:
                err_txt = self.eqnSolve(it, testMode)

                print(Support.myName(), ' answer=', self.numer+'\n---------------------'+self.denom)
                if err_txt == 0:
                    self.solved += 1
                    result = self.numer/self.denom
                    # Undo the substitution done in CReadEquation::readCPoly to
                    # prevent the sympy error from 're'.
                    # ONLY needs to be done when an equation is read using
                    # simpify!
                    result = result.subs('r__e', 're')
                    diff = result-self.testAnswer
                    
                    diff = diff.simplify()
                    diff = diff.expand()
                    if Support.gVerbose > 1:
                        print('After simplify', diff)
    
                    if diff == 0.0:
                        self.matched += 1
                    else:
                        self.didntMatch += 1
                        onesThatDidntMatch.append(it)
                        if Support.gVerbose > 0:
                            print('Solution:', result)
                            print('Answer:', self.testAnswer)
                            print('Diff:', diff)
                else:
                    self.failed += 1
                    onesThatFailed.append(it)
            
            chdir('../src')

            print()
            print('Number that solved:', self.solved)
            print('Number that failed:', self.failed)
            print('Number that matched:', self.matched)
            print("Number that didn't match:", self.didntMatch)
            
            if self.failed:
                print('Files that failed to find a solution:')
                for it in onesThatFailed:
                    print(it)
            
            if self.didntMatch:
                print("Files that didn't get the right answer:")
                for it in onesThatDidntMatch:
                    print(it)
            return 0
        else:
            err_txt = self.eqnSolve(filePath, testMode)

        return err_txt
    
    def readCircuitFile(self, fn):
        print('Reading circuit file ', fn)
        
        # Save the fileReader object so that we can access the answer that was read
        # in from the text file.
        
        fileReader = CFileReader.CFileReader(fn, 'Macbook')
        fileReader.readFile()
        self.testAnswer = fileReader.getTestAnswer()
        self.theCircuit = CCircuit.CCircuit(fileReader.getEList(),
                           fileReader.getInputSource(),
                           fileReader.getOutputSource(),
                           fileReader.getFreq(),
                           fileReader.getHTMLFilename()
                           )
        self.simpList = fileReader.getSimpList()
        self.subList = fileReader.getSubList()
        
    def eqnSolve(self, fullPath, testMode):
        '''Read the theCircuit file, create required objects, solve equations, print solution.
        Returns a list:
        [0] = 0 if it found a solution.
        [1] = the solution equation.
        [2] = the correct answer that was read in from the text file.'''
        startTime = time.time()
        
        self.rawAnswer = None
        self.evalAnswer = None
        self.evalFAnswer = None

        self.readCircuitFile(fullPath)
        # Print the theCircuit with user node numbers
        if Support.gVerbose > 1:
            print(Support.myName(), ': The parsed input file with user nodes:')
        self.theCircuit.regurgitate(useInternalNodeNumbers = False)
        self.simpList.printSimpList()
        
        # Determine the number of nodes needed
        nNodes = self.theCircuit.createIndexList()
        
        # Renumber the nodes using internal node numbers
        self.theCircuit.renumberNodes()
        
        # Renumber the source nodes as well
        self.theCircuit.setControllingSourceNodes()
        
        # Print again using internal node numbers
        if Support.gVerbose > 1:
            print(Support.myName(), ': The parsed input file with internal nodes:')
        self.theCircuit.regurgitate(useInternalNodeNumbers = True)
                
        # Create a linear equations object and fill the matrix with elements from the self.theCircuit object
        self.linearEquations = CLinearEquations(nNodes)
        self.linearEquations.fillMatrix(self.theCircuit)
        
        # Try to solve the equations.
        if self.linearEquations.solveEquations():
            print(Support.myName(), ': Matrix cannot be solved. Exiting.')
            Support.myExit(26)
        
        if Support.gVerbose > 0:
            self.printSolvedMatrix(self.linearEquations)
        
        self.numer, self.denom = self.linearEquations.calculateSolution(self.theCircuit)
        err_txt = ""

        if self.denom == 0:
            err_txt =           "The solution denominator is 0.0. You may be asking to"
            err_txt = err_txt + " solve for somethign 'weird'. Try solving for something"
            err_txt = err_txt + " slightly different. For instance, if you have something"
            err_txt = err_txt + " like this in your circuit file:"
            err_txt = err_txt + "     Vin 1 0"
            err_txt = err_txt + "     ....(other stuff)"
            err_txt = err_txt + "     Rload 8 0 "
            err_txt = err_txt + "     solve 8 0 vin"
            err_txt = err_txt + " Trying changing the solve statement to: "
            err_txt = err_txt + "     solve 8 0 1 0"
            endTime = time.time()
            print('Equation Solver finished in {0:.3f} seconds.'.format(endTime-startTime) )
            return [err_txt, (0, 0), 0, 0]
        elif self.numer == 0:
            err_txt =           "The solution is 0.0. There's probably something wrong"
            err_txt = err_txt + " with the circuit definition- a floating node (a"
            err_txt = err_txt + " node with only one connection) is a common issue."
            endTime = time.time()
            print('Equation Solver finished in {0:.3f} seconds.'.format(endTime-startTime) )
            return [err_txt, (0, 0), 0, 0]

        else:
            if Support.gVerbose > 0:
                if self.simpList.size() == 0:
                    self.announceAnswer(self.numer, self.denom, 'The solution is\n')
                else:
                    self.announceAnswer(self.numer, self.denom, 'The solution before simplification is\n')
        
        self.rawAnswer = self.numer / self.denom
        if self.simpList.size() != 0:
            self.numer, self.denom = self.linearEquations.gtltSimplify(self.rawAnswer, self.simpList)
            self.announceAnswer(self.numer, self.denom, 'The solution after simplification is\n')
            #self.rawAnswer = self.numer / self.denom
            self.simpAnswer = self.numer / self.denom

        if not testMode:
            if len(self.subList) != 0:
                self.subAnswer = self.linearEquations.substituteEqns(self.subList)
            # If an HTML file is requested, make the filename and create the HTML file.
            html_fn = self.theCircuit.getHTMLFilename()
            if html_fn != '':
                pth = dirname(fullPath)
                #print(html_fn+' '+pth+' '+fullPath)
                self.createHTMLFile(pth+'/'+html_fn, self.linearEquations, self.rawAnswer)
        
            if self.theCircuit.anyValuesDefined():
                self.evalAnswer = self.linearEquations.substituteValues(self.theCircuit.getEList())
                if Support.gVerbose > 1:
                    print(Support.myName(), 'Set evalAnswer=', self.evalAnswer)
                if self.linearEquations.getFreq() is not None:
                    self.evalFAnswer = self.linearEquations.evalAtFreq(self.linearEquations.getFreq())
                    if Support.gVerbose > 1:
                        print(Support.myName(), 'Set evalFAnswer=', self.evalFAnswer)

        endTime = time.time()
        print('Finished ', fullPath)
        print('Equation Solver finished in {0:.3f} seconds.'.format(endTime-startTime) )
        return 0
    
    def printSolvedMatrix(self, eqns):
        print('\nSolution Matrix:')
        eqns.printES(eqns.aMatrix)
        print('\nvColumn:')
        eqns.printES(eqns.vColumn)
        print('\nSolution iColumn:')
        eqns.printES(eqns.iColumn)
        print('\nSolution column:')
        eqns.printES(eqns.solution)
        
        # Now print the input and output sources
        print('\n\nNow, solving for (internal nodes):')
        self.theCircuit.getOutputSource().printElementS()
        print('    --------')
        self.theCircuit.getInputSource().printElementS()
        print('\n\nOr in user node numbers:')
        self.theCircuit.getOutputSource().printElementUS()
        print('    --------')
        self.theCircuit.getInputSource().printElementUS()
        print('\n')
    
    def createHTMLFile(self, filename, eqns, theEqn):
        '''Takes a sympy object, not a string'''
        if Support.gVerbose > 0:
            print(Support.myName(), ': Creating HTML file at ', filename, '.')
        
        try:
            f = open(filename, 'w')
        except PermissionError:
            print("Can't open file ", filename)
            Support.myExit(28)
        f.write('<!DOCTYPE html>\n')
        f.write('<html>\n')
        f.write('<body>\n')
        f.write('<h1>Solution</h1>\n')  
        f.write('<p>\n')
        eqns.printES_HTML(theEqn, f)
        f.write('<p>\n')
        #f.write('<h1>Solution iColumn</h1>\n')  
        #f.write('<p>\n')
        #eqns.printES_HTML_Mat(eqns.getIColumn(), f)

        f.write('</body>\n')
        f.write('</html>\n')
        f.close()
    
    def eqnPlot(self, f_start, f_stop, update_fcn, plot_format, use_db, s_or_p):

        #lst= [9450232, 301322, 5, 572101, 11121, 2, 889, 125, 201, 499, 199.9]
        #for n in lst:
            #print('{0:8}  {1:8}  {2:8} '.format(n, round125(n, 0), round125(n, 1)))
        
        self.plot_format = Enums.pf_list[plot_format]
        self.use_db = use_db
        self.SorP = Enums.format_sp[s_or_p]
        self.numer, self.denom = self.evalAnswer.as_numer_denom()
        self.updateFcn = update_fcn
        eval_fcn = self.linearEquations.evalAtFreq
        
        if f_start == -1 or f_stop == -1:
            numer_range = self.estFreqRange(self.numer)
            denom_range = self.estFreqRange(self.denom)
            if Support.gVerbose > 2:
                print(Support.myName(), 'numer_range=', numer_range)
                print(Support.myName(), 'denom_range=', denom_range)
            if numer_range[0] == 0 and denom_range[0] == 0:
                print("This can't be worth plotting!")
                return "This can't be worth ploatting!"
            elif numer_range[0] == 0:
                numer_range = denom_range
            elif denom_range[0] == 0:
                denom_range = numer_range
            elif numer_range[0] == -1 or denom_range == -1:
                print("This circuit is unstable, can't plot the equation")
                return "This circuit is unstable, can't plot the equation"
            self.f_start = min(numer_range[0], denom_range[0])/10.0
            self.f_stop = max(numer_range[1], denom_range[1])*10.0
            self.f_start = round10(self.f_start, 0)
            self.f_stop = round10(self.f_stop, 1)
        else:
            self.f_start = f_start
            self.f_stop = f_stop
        if Support.gVerbose > 2:
            print(Support.myName(), 'f_start=', self.f_start)
            print(Support.myName(), 'f_stop=', self.f_stop)
        self.fValues = lumpy.geomSpace(self.f_start, self.f_stop, self.length)
        self.y1 = lumpy.zeros(self.length, 'f')
        self.y2 = lumpy.zeros(self.length, 'f')
        self.calculateValues(update_fcn, eval_fcn)
        
        if 1:
            if self.plotFrame is None:
                self.plotFrame = Frame(None, title='LaPlot')
                self.plotPanel = MyPlot.CanvasPanel(self.plotFrame, self, self.fValues, self.y1, self.y2)
                self.plotPanel.draw(self.plot_format, self.use_db, self.SorP, self.rlc_units, True, self.fig_size)
            else:
                print("THIS SHOULDN'T HAPPEN!")
                self.plotPanel.draw(self.plot_format, self.use_db, self.SorP, self.rlc_units, False)
        else:
            pass
            #plot = pygalPlot.PygalPlot(self, self.fValues, self.mags, self.angles)
            #plot.draw(self.use_db)
        update_fcn(0)
        return ""

    def closePlot(self):
        #print('closePlot: fig_size=', self.fig_size)
        self.fig_size = self.plotPanel.getFigSize()
        #print('closePlot: Now fig_size=', self.fig_size)
        self.plotPanel.closeFigure()
        self.plotPanel.Close()
        self.plotFrame.Close()
        self.plotPanel = None
        self.plotFrame = None
    
    def clearPlot(self):
        self.plotPanel.closeFigure()
        
    def calculateValues(self, upd_fcn, eval_fcn):
        '''Did all of these in a loop because the angle had to be, more or less...'''
        r2d = 180.0/pi
        
        start = time.time()
        rlc_units = 'C'
        for inx in range(self.length):
            # Convert sympy type to Python complex type.
            zin = complex(eval_fcn(self.fValues[inx]))
            if Support.gVerbose > 2:
                print(Support.myName(), 'Zin=', zin)
            if self.plot_format == Enums.pf_list[0]:
                # Mag/Angle
                mag = sqrt(zin.real**2+zin.imag**2)
                ang = atan2(zin.imag, zin.real)
                if self.use_db:
                    self.y1[inx] = 20*log10(mag)
                else:
                    self.y1[inx] = mag
                self.y2[inx] = ang*r2d
            elif self.plot_format == Enums.pf_list[1]:
                # Re, Im
                if self.SorP == Enums.format_sp[1]:
                    # Parallel
                    yin = 1/zin
                    if Support.gVerbose > 2:
                        print(Support.myName(), 'Re/Im, Zin=', zin)
                    self.y1[inx] = yin.real
                    self.y2[inx] = yin.imag
                else:
                    self.y1[inx] = zin.real
                    self.y2[inx] = zin.imag
            else:
                # RLC
                if self.SorP == Enums.format_sp[1]:      # Parallel
                    yin = 1/zin
                    if Support.gVerbose > 2:
                        print(Support.myName(), 'RLC, Zin=', zin)
                    self.y1[inx] = yin.real
                    if yin.imag < 0:    # inductor. B=1/(2*pi*f*Lp),  Lp=1/(2*pi*f*B)
                        self.y2[inx] = -1/(yin.imag*2*pi*self.fValues[inx])
                        rlc_units = 'L'
                    else:               # Cap. B=2*pi*f*Cp, Cp=B/(2*pi*f)
                        self.y2[inx] = yin.imag/(2*pi*self.fValues[inx])
                        rlc_units = 'C'
                else:   # Series
                    self.y1[inx] = zin.real
                    if zin.imag > 0:    # inductor. X=2*pi*f*Ls, Ls=X/(2*pi*f)
                        self.y2[inx] = zin.imag/(2*pi*self.fValues[inx])
                        rlc_units = 'L'
                    else:               # cap. X=1/(2*pi*f*Cs), Cs=1/(X*2*pi*f)
                        self.y2[inx] = -1/(zin.imag*2*pi*self.fValues[inx])
                        rlc_units = 'C'
                        
            upd_fcn(floor(100*inx/self.length))
            Yield()
        end = time.time()
        upd_fcn(100)
        self.rlc_units = rlc_units
        if Support.gVerbose > 0:
            print(Support.myName(), ' took {0:8.6} seconds'.format(end-start) )

    def estFreqRange(self, poly):
        '''Takes a factored polynomial and looks at each factor, calculates the corner frequency
        and returns the minimum and maximum corner frequecies.
        If there are no roots (maybe a circuit of just resistors), then
        0, 0 is returned.
        If the root solution is a negative frequency, -1, -1 is returned.'''
        # factor_list returns a tuple, tuple[0] being a constant, and tuple[1] is a list of tuples,
        # with each tuple in the list being a factor and a power
        # (1, [(e, 1), (f*g+h, 1)]) = e*(f*g+h)
        # (1, [(2*e-3*h, 2)]) = 4*e^2-12*e*h+9*h^2
        # (-1660, []) = -1660
        
        f, s = sympy.symbols('f s')
        wj = f*2*sympy.pi*sympy.I
        poly_wj = poly.subs({s: wj})
        f_list = sympy.factor_list(poly_wj)
        if Support.gVerbose > 2:
            print(Support.myName(), 'poly_w=', poly_wj)
            print(Support.myName(), 'factor_list=', f_list)
        
        the_min = 1e99
        the_max = 0
        if f_list[1] != []:
            for rt in f_list[1]:
                if Support.gVerbose > 2:
                    print(Support.myName(), 'rt=', rt)
    
                fs = rt[0].free_symbols
                if f in fs:
                    rt_solv = sympy.solve(rt[0], f)
                    if Support.gVerbose > 2:
                        print(Support.myName(), 'rt_solv=', rt_solv)
                        print(Support.myName(), 'rt_solv[0]=', rt_solv[0])
                    if rt_solv != []:
                        f_rt = abs(rt_solv[0])
                        if Support.gVerbose > 2:
                            print(Support.myName(), 'f_rt=', f_rt)
                        if f_rt > 0:
                            if f_rt > the_max:
                                the_max = f_rt
                            if f_rt < the_min:
                                the_min = f_rt
                            if Support.gVerbose > 2:
                                print(Support.myName(), 'min=', the_min)
                                print(Support.myName(), 'max=', the_max)
                        elif f_rt == 0:
                            return 0, 0
                        else:
                            # Negative roots means the circuit is unstable
                            return -1, -1
            return the_min, the_max
        else:
            return 0, 0

    def announceAnswer(self, num, den, txt):
        if Support.gVerbose > 0:
            print()
            print('***************************************')
            print()
            print(txt, num)
            print('----------------------------------')
            print(den)
            print()
            print('***************************************')
            print()

