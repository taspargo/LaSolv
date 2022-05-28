"""  
Copyright 2020 Thomas Spargo

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
"""'''
Created on Jul 30, 2015

@author: Tom Spargo

m[i,j] =
m[1,2] =     [ x00 x01 x02 ]
       i=1>  [ x10 x11 x12 ]
             [ x20 x21 x22 ]
                        ^
                       j=2
                    
'''
import sympy
from sympy import init_printing
import Support

class CGauss(object):
    '''
    Gaussian elimination and back substitution algorithms.
    '''

    # [ i ] = [ M ] [ v ]
    def __init__(self, matrix, column):
        #self.m = sympy.zeros(matrix.shape[0])
        self.m = matrix
        self.c = column
        self.temp = sympy.symbols('temp')
        init_printing()
        
        #print("CGauss ctor- m=")
        #self.pprint(self.m)

    def elimination(self):
        '''Using Gaussian elimination, turn the square matrix into an upper triangular one.'''
        n = self.m.shape[0]
        for i in range(n):   # From the top moving down
            if Support.gVerbose > 0:
                print(Support.myName(), ": Beginning Gaussian elimination", i)
            p = 1/self.m[i,i]
            if Support.gVerbose > 2:
                print(Support.myName(), ": Normalizing pivot row {0:d} with".format(i))
                self.pprint(p)
            if p != 1.0:
                for j in range(i, n):   # From the left moving right
                    self.m[i,j] *= p
                    simpler = sympy.simplify(self.m[i,j], ratio=1.7)
                    if Support.gVerbose > 3:
                        print(Support.myName(), ': aMatrix [{0:d}, {1:d}] after norm'.format(i,j))
                        self.pprint(self.m[i,j])
                    self.m[i,j] = simpler
                self.c[i] *= p
                self.c[i] = sympy.simplify(self.c[i], ratio=1.7)
                if Support.gVerbose > 3:
                    print(Support.myName(), ': iColumn  [{0:d}] after norm'.format(j))
                    self.pprint(self.c)
                
            if Support.gVerbose > 3:
                print(Support.myName(), ": Zeroing the columns below the pivot at m[{0:d},{0:d}]".format(i,i))
            for j in range(i+1, n):
                p = self.m[j,i]
                for k in range(i, n):
                    if self.m[i,k] == 1.0:
                        self.m[j,k] -= p
                    elif p == 1.0:
                        self.m[j,k] -= self.m[i,k]
                    else:
                        self.m[j,k] = self.m[j,k]-p*self.m[i,k]
                        #print('before    [{0:d}, {1:d}]='.format(j, k), self.m[j, k])
                        simpler = sympy.simplify(self.m[j,k], ratio=1.7)
                        #print('after     [{0:d}, {1:d}]='.format(j, k), simpler)
                        self.m[j,k] = simpler
                if self.c[i] == 1.0:
                    self.c[j] -= p
                elif p == 1.0:
                    self.c[j] -= self.c[i]
                else:
                    self.c[j] = self.c[j]-p*self.c[i]
            if Support.gVerbose > 2:
                print(Support.myName(), ": Matrix at end of Gaussian elimination #", i)
                self.pprint(self.m)
                print(Support.myName(), ": Column at end of Gaussian elimination #", i)
                self.pprint(self.c)
        #return [self.m, self.c]
        return 0
    
    # Dim  count    /n^3    /n^2
    # 3      8      0.3      0.88    n*(n-1)*(n-2)-1
    # 5     70      0.56     2.8     59
    # 7    168      0.49     3.4     209
    # 9    240      0.33     3.0     503
    # i=1..n
    #    k=i+1..n
    #        j=i+1..n  n* (n-(i+1)) * (n-(i+1))  (n-i-1)^2 = n^2-ni-n-ni+i^2+i-n+i+1 = n^2-2ni-2n+i^2+2i+1
    # = n^2-2n*(i+1) + i^2+2i+1
    #  n*(n*(n-1))/2 = (n^3-n^2)/2
    # n
    # 3    9
    # 5    50
    # 7    147
    # 9    324
    '''
    for i in 0..n-1
        for k in i+1..n-1
            for j in i+1..n-1
                m[i,j] = m[i,j] - m[i,k] * m[k,j]
    '''
    def back_subs(self):
        '''Back-substitute the upper triangular matrix to get the final answers.'''
        n = self.m.shape[0]
        for i in range(n):
            for k in range(i+1, n):
                p = self.m[i,k]
                if Support.gVerbose > 3:
                    print(Support.myName(), "pivot m[{0:d},{1:d}] = ".format(i,k))
                    self.pprint(self.m[i,k])
                for j in range(i+1, n):
                    self.m[i,j] = self.m[i,j] - p*self.m[k,j]
                    if Support.gVerbose > 3:
                        #print(Support.myName(), 'before    m[{0:d}, {1:d}]='.format(i, j), self.m[i, j])
                        print(Support.myName(), "back_subs: m[{0:d},{1:d}] = m[{0:d},{1:d}] - m[{0:d},{2:d}] * m[{2:d},{1:d}]".format(i, j, k))
                    simpler = sympy.simplify(self.m[i,j], ratio=1.7)
                    if Support.gVerbose > 3:
                        print(Support.myName(), 'after     [{0:d}, {1:d}]='.format(i, j), simpler)
                    self.m[i,j] = simpler
                if Support.gVerbose > 3:
                    print(Support.myName(), " Before: c[{0:d}]=c[{0:d}]-pivot*c[{1:d}]".format(i, k))
                    #self.pprint(self.c[i])
                if self.c[k] == 1.0:
                    self.c[i] -= p
                elif p == 1.0:
                    self.c[i] -= self.c[k]
                else:
                    self.c[i] = self.c[i] - p*self.c[k]
                    # not sure if this helps or not.
                    numer, denom = self.c[i].as_numer_denom()
                    #simpler = sympy.expand(self.c[i])
                    self.c[i] = numer/denom
            if Support.gVerbose > 2:
                print(Support.myName(), " End of back sub #{0:d}, matrix=".format(i))
                self.pprint(self.m)
                print(Support.myName(), " End of back sub #{0:d}, iColumn=".format(i))
                self.pprint(self.c)
    
    def pprint(self, sm):
        sympy.pprint(sm)
    
    def print_matrix(self, printZeros):
        sympy.pprint(self.m)
        
    def print_matrix2(self, printZeros):
        n = self.m.shape[0]
        typ = type(self.m[0,0])
        nm = typ.__name__
        sparse = 'Sparse' in nm
        for i in range(1,n):
            for j in range(1, n) :
                if self.m[i,j] != 0 or printZeros:
                    if sparse:
                        print(self.m[i,j])
                    else:
                        temp = sympy.factor(self.m[i,j])
                        self.m[i,j] = sympy.expand(temp)
                        self.m[i,j] = sympy.nsimplify(self.m[i,j])
                        #self.m[i,j] = sympy.fraction(self.m[i,j])
                        #print("(",i,",",j,")", self.m[i,j])
                        print("(",i,",",j,")", sympy.N(self.m[i,j], 2))
                    
    def print_column(self, printZeros):
        n = self.m.shape[0]
        typ = type(self.m[0,0])
        nm = typ.__name__
        sparse = 'Sparse' in nm
        for i in range(1, n):
            if self.c[i] != 0 or printZeros:
                if sparse:
                    print('(', i, ')', self.c[i])
                else:
                    temp = sympy.factor(self.c[i])
                    self.c[i] = sympy.expand(temp)
                    print('(', i, ')', self.c[i])

                