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

    def __init__(self, theLines):
        '''
        Constructor
        '''
        self.theLines = theLines
    
    def nextLine(self, inx):
        line = self.theLines[inx]
        return inx+1, line
    
    # Input: index pointing at the 'answer' keyword line
    # Output: index pointing at the last line used, the test answer
    def readEquationFromList(self, inx):
        inx, line = self.nextLine(inx+1)
        if Support.gVerbose > 1:
            print(Support.myName(), ': Convert string to numer:', line)
        numer = self.readCPoly(line)
        if numer != 0:
            if Support.gVerbose > 1:
                print(Support.myName(), ': numerator:', numer)
                
            inx, line = self.nextLine(inx)      # Should be '------'
            if Support.gVerbose > 1:
                print(Support.myName(), ': Read line separator:', line)
            inx, line = self.nextLine(inx)
            if Support.gVerbose > 1:
                print(Support.myName(), ': Convert string to denom=', line)
            if line != '1.0':
                denom = self.readCPoly(line)
            else:
                denom = 1.0
            if Support.gVerbose > 1:
                print(Support.myName(), ': denominator:', denom)
            if denom != 0:
                theEquation = numer / denom
                if Support.gVerbose > 0:
                    print(Support.myName(), ': theEquation=', theEquation)
                return inx, theEquation
            else:
                print(Support.myName(), ': Read denominator = 0')
                return inx, 0.0
        else:
            print(Support.myName(), ': Read numerator = 0')
            return 0.0, 0.0
        return inx, theEquation

    
    def readCPoly(self, string):
        # Don't need to sub r__e for re anymore; it was trying to use 're' as in real().
        # {'re':sympy.Symbol('re') } forces it to use the Sympy symbol 're'.
        sympi = sympy.sympify(string, {'re':sympy.Symbol('re')})
        sympi.as_poly(extension=True)
        return sympi
        
            