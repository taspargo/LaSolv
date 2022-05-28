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
'''

import sympy
import Support


class CReadEquation(object):
    '''
    classdocs
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        self.inFile = None
    
    def readEquationGivenFilename(self, filename):
        f = open(filename, 'r')
        theEquation = self.readEquationFromOpenFile(f)
        return theEquation
    
    def readEquationFromOpenFile(self, fid):
        
        #saveVerbose = Support.gVerbose
        #Support.gVerbose = 0
        line = fid.readline()
        if Support.gVerbose > 2:
            print(Support.myName(), ': numer string=', line)
        numer = self.readCPoly(line)
        if numer != 0:
            if Support.gVerbose > 1:
                print(Support.myName(), ': Read numerator:', line)
            line = fid.readline()       # Should be '-----'
            if Support.gVerbose > 1:
                print(Support.myName(), ': Read line separator:', line)
            line = fid.readline()
            if Support.gVerbose > 2:
                print(Support.myName(), ': denom string=', line)
                

            if Support.gVerbose > 1:
                print(Support.myName(), ': Read denominator:', line)
            denom = self.readCPoly(line)
            if denom != 0:
                theEquation = numer / denom
                r__e, re = sympy.symbols('r__e re')
                theEquation = theEquation.subs(r__e, re)
                if Support.gVerbose > 0:
                    print(Support.myName(), ': theEquation=', theEquation)
                #Support.gVerbose = saveVerbose
                return theEquation
            else:
                print(Support.myName(), ': Read denominator = 0')
                return 0.0
        else:
            print(Support.myName(), ': Read numerator = 0')
            return 0.0
    
    def readCPoly(self, string):
        # Need to search for 're' and sub in r__e to prevent an error from sympy. It
        # may be interpreting the string and thinking re means 're' as in regular expression.
        string = string.replace('re', 'r__e')
        sympi = sympy.sympify(string)
        return sympi
        
            