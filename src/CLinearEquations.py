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
''' 1/31/2019. Removed solveEquations2, swapRows, reorderEquations, and zeroDiagonal.
    2/3/2019. Fixed jw substitution.
    Need to check for oo and zoo (infinity & complete infinity) in the solution
    equation. Import them as sympy.S.Infinity and sympy.S.ComplexInfinity
'''
import sympy
from sympy import factor
from sympy.printing.mathml import mathml
#from sympy.matrices import SparseMatrix
import CSimpList
import Support

import re as reg
import engineering_notation as eno

class CLinearEquations(object):
    """
    Solves linear systems using symbolic equations.
    
    Given a circuit object, the matrices are filled with the respective admittances.
    Uses Gaussian elmination and back substitution to obtain the nodal voltages in the circuit
    """

    def __init__(self, order):
        """Create the matrix, i(current) column and v(voltage) column"""
        """ aMatrix * vColumn = iColumn """
        self.aMatrix = sympy.zeros(order)
        self.iColumn = sympy.zeros(order, 1)
        self.vColumn = sympy.zeros(order, 1)
        self.solution = sympy.zeros(order, 1)
        self.nNodes = order
        self.answer = None      # Raw answer with no value substituted.
        self.evalAnswer = None  # Answer with component values put in, not freq
        self.freq = None
        if Support.gVerbose > 2:
            print(Support.myName(), ' order=', order)
    
    def getAnswer(self):
        return self.answer
    
    def setFreq(self, frq):
        self.freq = frq
        
    def getFreq(self):
        return self.freq
                
    def getAMatrix(self):
        return self.aMatrix
    
    def getIColumn(self):
        return self.iColumn
    
    def getVColumn(self):
        return self.vColumn
    
    def solveEquations(self):
        # Matrix * vColumn = iColumn
        # vColumn = Matrix.inv * iColumn
        #err = self.reorderEquations()

        if Support.gVerbose > 2:
            print(Support.myName(), ': aMatrix before deleting:')
            self.printES(self.aMatrix)
            print(Support.myName(), ': iColumn before deleting:')
            self.printES(self.vColumn)
            print(Support.myName(), ': vColumn before deleting:')
            self.printES(self.iColumn)

        self.aMatrix.row_del(0)
        self.aMatrix.col_del(0)

        self.iColumn.row_del(0)
        self.vColumn.row_del(0)
        self.nNodes = self.nNodes - 1
        
        if Support.gVerbose > 2:
            print(Support.myName(), ': aMatrix after deleting the 0 column and row:')
            self.printES(self.aMatrix)
            print(Support.myName(), ': iColumn after deleting the 0 column and row:')
            self.printES(self.vColumn)
            print(Support.myName(), ': vColumn after deleting the 0 column and row:')
            self.printES(self.iColumn)
        
        if (self.aMatrix).det() == 0:
            print(Support.myName(), ': aMatrix det = 0.')
            return 26
            
        self.solution = (self.aMatrix).inv() * self.iColumn
        if Support.gVerbose > 0:
            print(Support.myName(), ': aMatrix after inverting and multiplying by iColumn:')
            print(self.aMatrix)
        
        return 0
    
    def calculateSolution(self, circuit):
        top = circuit.calculateVorIEqn(self.solution, circuit.getOutputSource())
        bottom = circuit.calculateVorIEqn(self.solution, circuit.getInputSource())
        
        if Support.gVerbose > 2:
            print(Support.myName(), ': top=', top)
            print(Support.myName(), ': bottom=', bottom)
        #if sympy.Ne(bottom, 0):
        if bottom != 0:
            self.answer = top.factor() / bottom.factor()
            #self.answer = top / bottom
            #self.answer = self.answer.simplify()
            #self.answer = self.answer.factor()
        else:
            if Support.gVerbose > 1:
                print(Support.myName(), ': Solution denom = 0')
            self.answer = sympy.S.Infinity
            return (sympy.S.Infinity, 0.0)
        print('calcSoln: self.answer=', self.answer)
        top, bottom = self.answer.as_numer_denom()
        return (top, bottom)

    def fillMatrix(self, circuit):
        """Fill up the matrix, i-column and v-column with admittances from the circuit"""
        self.fillVColumn(circuit)
        self.fillAMatrix(circuit)
    
    def fillAMatrix(self, circuit):
        """Fill the eqnSolver n x n matrix with admittances"""        
        if Support.gVerbose > 1:
            print(Support.myName(), ': len(eList)=', len(circuit.getEList()))
        for elNum in range(len(circuit.getEList() )):
            element = circuit.getEList()[elNum]
            # Get the connecting nodes for all type of elements
            # i, j are the nodes the element is connected between.
            # m is the row that was added for an E, F, G, H, or V element. For H's, two rows are added and n is that row.
            # k, l are the controlling nodes for E, F, G, or H elements.
            i = element.getNode1()
            j = element.getNode2()
            # Get all the nodes, even if we don't need them for some element types.
            k = element.getNode3()
            l = element.getNode4()
            m = element.getSourceNode1()
            n = element.getSourceNode2()
            iSenseLabel = 'None'
            if Support.gVerbose > 1:
                print(Support.myName(), ': Element #', elNum)
                element.printElement()
            if Support.gVerbose > 2:
                print(Support.myName(), ': i=', i, ', j=', j, ', k=', k, ', l=', l, ', m=', m, ', n=', n, \
                        ', isense=', iSenseLabel)
            et = element.getElementType()
            sym = sympy.symbols(element.getLabel())
            sSym = sympy.symbols('s')
            if et == 'c':
                self.addElementToMatrix(i, j, sym*sSym)
            elif et == 'e':     # VCVS     Checked
                                # Vk * E - Vi + Vj - Vl * E = 0
                                # Ii = Io
                                # Ij = -Io
                self.addSourceToMatrixH(j, i, m, 1.0)   # - Vi + Vj
                self.addSourceToMatrixV(i, j, m, 1.0)   # Ii = Io   Ij = -Io
                self.addSourceToMatrixH(k, l, m, sym)   # Completes Vk * E - Vi + Vj - Vl * E
            elif et == 'f':     # CCCS     Checked
                                # Vk - Vl = 0
                                # Ii = Io
                                # Ij = -Io
                                # Ik = Io/F
                                # Il = -Io/F
                self.addSourceToMatrixH(k, l, m, 1.0)
                self.addSourceToMatrixV(i, j, m, 1.0)
                self.addSourceToMatrixV(k, l, m, 1.0/sym)   # Vk - Vl = 0 (IVS for current sensing)
                                                            # Ik = Iout/F  Il = -Iout/F
            elif et == 'g':     # VCCS     Checked
                                # Vk - Vl - Io/G = 0
                                # Ii = Io
                                # Ij = -Io 
                                # Ik = Il = 0
                self.addSourceToMatrixH(k, l, m, 1.0)   # Vk - Vl
                self.addSourceToMatrixV(i, j, m, 1.0)   # Ii = Io  Ij = -Io
                self.addSourceToMatrixH(m, 0, m, -1.0/sym)  # not admittance, it's 1/G.
                                                            # -G (completes Vk - Vl - Iout/G = 0)
            elif et == 'h':     # CCVS, the only dependent source with two extra unknowns
                                # Vk - Vl = 0             n row
                                # Vi - Vj - Iin * H = 0   m row
                                # Ii = Io                 n column
                                # Ij = -Io                n column
                                # Ik = Iin                m column
                                # Il = -Iin               m column
                self.addSourceToMatrixH(k, l, n, 1.0)   # Vk - Vl                             C
                self.addSourceToMatrixH(i, j, m, 1.0)   # Vi - Vj                             A
                self.addSourceToMatrixV(k, l, n, 1.0)   # Ii = Iout  Ij = -Iout               D
                self.addSourceToMatrixH(n, 0, m, 0-sym)  # 1/trans-R. -G (completes Vi-Vj-H*Iin=0) A
                self.addSourceToMatrixV(i, j, m, 1.0)   # Ik = Iin  Il = -Iin                     B
            elif et == 'i':     # Independent current source
                                # I column, Ii = Io, Ij = -Io
                self.addElementToIColumn(i, j, sym)
            elif et == 'l':
                self.addElementToMatrix(i, j, 1.0/(sym*sSym))
            elif et == 'r':
                self.addElementToMatrix(i, j, 1.0/sym)
            elif et == 'v':     # Independent voltage source
                                # Vi-Vj = E + transpose
                                # If it's a sensing source for a controlled source, don't add it into the matrix like its an IVS.
                                # the controlled source element will put in the correct matrix entries.
                if not circuit.isControlledSourceSensingVS(element):
                    self.addSourceToMatrixH(i, j, m, 1.0)
                    self.addSourceToMatrixV(i, j, m, 1.0)
                    self.addElementToIColumn(m, 0, sym)
            else:
                print(Support.myName(), ': Unknown element ', element.getElementType(), ' encountered. Exiting.')
                Support.myExit(24)
            
        if Support.gVerbose > 2:
            print(Support.myName(), ': Matrix entries:')
            self.printES(self.aMatrix)
            print(Support.myName(), ': V Column entries:')
            self.printES(self.vColumn)
            print(Support.myName(), ': I Column entries:')
            self.printES(self.iColumn)

    def printES(self, mat, print_zeros=False):
        sz = mat.shape
        if sz[0] == 1 or sz[1] == 1:
            if sz[0] == 1:
                print('Row Matrix')
            else:
                print('Column Matrix')
            for zz in range( self.nNodes):
                if mat[zz] != 0.0 or print_zeros:
                    if mat[zz] == 1.0:
                        print('    [{0:d}]= 1.0'.format(zz))
                    elif mat[zz] == -1.0:
                        print('    [{0:d}]= -1.0'.format(zz))
                    else:
                        print('    [{0:d}]='.format(zz), mat[zz])
        else:
            for yy in range(self.nNodes):
                for zz in range(self.nNodes):
                    if mat[yy, zz] != 0.0 or print_zeros:
                        if mat[yy, zz] == 1.0:
                            print('    [{0:d}, {1:d}]= 1.0'.format(yy, zz))
                        elif mat[yy, zz] == -1.0:
                            print('    [{0:d}, {1:d}]= -1.0'.format(yy, zz))
                        else:
                            print('    [{0:d}, {1:d}]='.format(yy, zz), mat[yy, zz])
    
    def printES_iC_HTML(self, f):
        f.write('<math>\n')
        f.write(mathml(self.iColumn, printer='presentation'))
        f.write('</math>\n')
        
    def printES_HTML(self, eqn, f):
        """Prints a single equation (if its non-zero) into the HTML file 'f'"""
        if eqn != 0.0:
            # This is broken up because sympy likes to print umpteen digits of precision
            # when printing 1.000000000000
#             f.write('<html>')
#             f.write('<head>')
#             f.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-MML-AM_CHTML" async></script>')
#             f.write('</head>')
#             f.write('<body>')
            #Ra, Ca, Cb, s, eq = sympy.symbols('Ra Ca Cb s eq')
            #eq = R_1**2*C1**2*s**3+R_1*C1*s**2+R_1*(C1+C2)*s
            #eq = Ra*Cb+Ca*s**2
            mth = sympy.mathml(sympy.N(eqn, 2), printer='presentation')
            print(Support.myName(), 'mth before pretty_html', mth)
            mth = self.pretty_html(mth)
            print(Support.myName(), 'mth after pretty_html', mth)
            f.write('<math>\n')
            f.write( mth )
            f.write('<p>')
            f.write('</math>\n')

    def printES_HTML_Mat(self, mat, f):
        """Prints a matrix, either 1D or 2D, into the file 'f'. Only non-zero eqns are printed"""
        sz = mat.shape
        if sz[0] == 1 or sz[1] == 1:
            f.write(r'<math>\n')
            f.write( mathml( sympy.N(mat, 2), printer='presentation'))
            f.write('</math>\n')

            if 0:
                for zz in range( self.nNodes):
                    if mat[zz] != 0.0:
                        f.write('<math>\n')
                        #sympyfied = sympy.sympify( sympy.N(mat[zz], 2) )
                        #print(sympyfied)
                        #print
                        #f.write( mathml( sympy.N(mat[zz], 2), printer='presentation') )
                        f.write( mathml( mat[zz], printer='presentation') )
                        f.write('<p>')
                        f.write('</math>\n')
        else:
            for yy in range(self.nNodes):
                for zz in range(self.nNodes):
                    if mat[yy, zz] != 0.0:
                        f.write('<table>\n')
                        if mat[yy, zz] == 1.0:
                            f.write('<tr><td nowrap>[%2s, %2d]= 1.0</td>' % (yy, zz))
                        elif mat[yy, zz] == -1.0:
                            f.write('<tr><td nowrap>[%2d, %2d]= -1.0</td>' % (yy, zz))
                        else:
                            fract = sympy.fraction(mat[yy, zz])
                            f.write('</tr><tr></td><td></td><td>%s' % fract[0])
                            f.write('[%2d, %2d]= %s' % (yy, zz, mat[yy, zz]) )
                            f.write('</tr><tr></td><td>[%2d, %2d] = </td><td> -------------\n' % (yy, zz) )
                            f.write('</tr><tr></td><td></td><td>%s' % fract[1])
                    f.write('</td>\n')
                    f.write('</tr>\n')
                    f.write('</table>\n')
                    f.write(r'<p>\n</p>')
                    f.write('\n')

    def pretty_html(self, strng):
        # Fix the Safari bug
        p1 = reg.sub(r'<mi><msub><mi>(\w+)</mi><mi>(\w+)</mi></msub></mi>', \
                     r'<msub><mi>\1</mi><mi>\2</mi></msub>', strng)
        # Split up identifiers into first letter then the rest to allow substripts
        p2 = reg.sub(r'<mi>(\w)(\w+)</mi>', r'<msub><mi>\1</mi><mi>\2</mi></msub>', p1)
        # Change invisible times to '*'
        #p3 = p2.replace('&InvisibleTimes;', '*')
        # Remove the unneeded '1.0*' before most terms
        p3 = reg.sub(r'<mrow><mn>1.0</mn><mo>&InvisibleTimes;</mo>', r'<mrow>', p2)
        # Remove a '-1.0*' before many terms 
        p4 = reg.sub(r'<mrow><mo>-</mo><mn>1.0</mn><mo>&InvisibleTimes;</mo>', \
                     r'<mrow><mo>-</mo>', p3)
        # Change any remaining '1.0's to '1'
        p5 = reg.sub(r'<mn>1.0</mn>', r'<mn>1</mn>', p4)

        if Support.gVerbose > 2:
            print(Support.myName(), ' p1=', p1)
            print(Support.myName(), ' p2=', p2)
            print(Support.myName(), ' p3=', p3)
            print(Support.myName(), ' p4=', p4)
            print(Support.myName(), ' p5=', p5)
        return p5
    
    def fillVColumn(self, circuit):
        # Make the V column entries Vn if 1 <= i <= nNodes, or In if i>nNodes.
        # The v Column isn't used for anything real, it's just there to help me follow what's going on.
        nn = circuit.getNumOfNodes()
        add = circuit.getNumOfAddedNodes()
        i = 1
        if Support.gVerbose > 1:
            print(Support.myName(), ': nNodes=', nn, ', addedNodes=', add)
        while i < nn:
            if i < nn-add:
                tmp = 'v'
                tmp += str(circuit.getUserNode(i))
                if Support.gVerbose > 2:
                    print(Support.myName(), ': i=', i, ', label=', tmp)
            else:
                tmp = 'i'
                addedNodeNum = i-(nn-add)
                addedElement = circuit.getAddedNodeElement(addedNodeNum)
                if Support.gVerbose > 2:
                    print(Support.myName(), ': i=', i, ', addedNodeNum=', addedNodeNum, \
                    ', addedElement label=', addedElement.getLabel(), \
                    ', c.iSenseLabel=', addedElement.getISenseLabel())
                labelTmp = addedElement.getLabel()
                tmp += str(labelTmp)
                if Support.gVerbose > 2:
                    print(Support.myName(), ': labelTmp=', labelTmp)
                # If there's an 'H' element we use two labels from it- it's label and the name of the voltage
                # source it's uses. First use it's label, bump i, then get the name of the voltage source. Fall
                # into the regular path to add that to the V-column.
                if addedElement.getElementType() == 'h':
                    sym = sympy.symbols(tmp)
                    self.getVColumn()[i] = sym
                    i += 1
                    tmp = 'i'
                    tmp += addedElement.getISenseLabel()
            sym = sympy.symbols(tmp)
            self.getVColumn()[i] = sym
            i += 1

    def addElementToMatrix(self, i, j, adm):
        """Add an elements admittance to the matrix"""
        if i==0 or j==0:
            n=i+j
            self.aMatrix[n, n] += adm
        else:
            self.aMatrix[i, i] += adm
            self.aMatrix[j, j] += adm
            self.aMatrix[i, j] -= adm
            self.aMatrix[j, i] -= adm
    
    def addElementToIColumn(self, i, j, cterm):
        """Add an elements admittance to the i-column"""
        if Support.gVerbose > 2:
            print(Support.myName(), ': i=', i, ', j=', j, ', cterm=', cterm)
        if i==0:
            self.iColumn[j] -= cterm
        elif j==0:
            self.iColumn[i] += cterm
        else:
            self.iColumn[i] += cterm
            self.iColumn[j] -= cterm

    def addSourceToMatrixH(self, i, j, m, adm):
        """Add a source to the matrix in two different rows, i & j, column m"""
        if Support.gVerbose > 2:
            print(Support.myName(), ': i=', i, ', j=', j, ', m=', m, ' adm=', adm)
        if i != 0:
            self.aMatrix[m, i] += adm
        if j != 0:
            self.aMatrix[m, j] -= adm
    
    def addSourceToMatrixV(self, i, j, m, adm):
        """Add a source to the matrix in two different columns, i & j, row m"""
        if Support.gVerbose > 2:
            print(Support.myName(), ': i=', i, ', j=', j, ', m=', m, ' adm=', adm)
        if i != 0:
            self.aMatrix[i, m] += adm
        if j != 0:
            self.aMatrix[j, m] -= adm     

    #self.numer, self.denom = self.linearEquations.applyRelations(self.simpList)
    def gtltSimplify(self, eqn, simpList):
        """Simplify eqn by using x >> y relationships.
        For the numer and denom separately, collect terms of the same order of 's' and factor.
        Then sub x for x+y (since y is really small).
        Finally expand, put back into a fraction and sympy simplify.
        Return numer, denom"""
        n, d = sympy.fraction(eqn)
        if Support.gVerbose > 2:
            print(Support.myName(), 'Begin applyRelations on numer')
        s_numer = self.applyRelationList(n, simpList)
        if Support.gVerbose > 2:
            print(Support.myName(), 'Begin applyRelations on denom')
        s_denom = self.applyRelationList(d, simpList)
        ratio = s_numer / s_denom
        e_ratio = sympy.expand(ratio)
        s_ratio = sympy.simplify(e_ratio)
        new_n, new_d = sympy.fraction(s_ratio)
        new_fn = sympy.factor(new_n)
        new_fd = sympy.factor(new_d)
        if Support.gVerbose > 2:
            print(Support.myName(), 'ratio=', ratio)
            print(Support.myName(), 'expanded=', e_ratio)
            print(Support.myName(), 'simplified=', s_ratio)
            print(Support.myName(), 'new_n=', new_n)
            print(Support.myName(), 'new_d=', new_d)
            print(Support.myName(), 'factored(new_n)=', new_fn)
            print(Support.myName(), 'factored(new_d)=', new_fd)
        return new_fn, new_fd

    def applyRelationList(self, eqn, simpList):
        old_eqn = eqn
        print('simp list is:')
        simpList.printSimpList()
        for rel in simpList.getSimpList():
            new_eqn = self.applyRelation(old_eqn, rel)
            if Support.gVerbose > 1:
                print(Support.myName(), 'rel=', end=" "),
                rel.printRelation()
                print(Support.myName(), 'old_eqn=', old_eqn, ':')
                print(Support.myName(), 'new_eqn=', new_eqn, ':')
            old_eqn = new_eqn
        return new_eqn
    
    '''
        collf = sympy.collect(efn, s, factor, evaluate=False)
        print('collected by s then factor:', collf)
        s_part = collf[s]
        print('s-part=', s_part)
        fixd = s_part.subs(rf1+rs1, rf1)
        print('fixd=:', fixd)
        o_part = coll[1]
        fixdo = o_part.subs(rf1+rs1, rf1)
        print('1-part=', o_part)
        print('fixdo=', fixdo)
    '''
    def applyRelation(self, eqn, relation):
        s = sympy.symbols('s')
        exp_eqn = eqn.expand()
        collf = sympy.collect(exp_eqn, s, factor, evaluate=False)
        if Support.gVerbose > 2:
            print(Support.myName(), 'eqn to simplify=', exp_eqn)
            print(Support.myName(), 'collected factors=', collf)
            print(Support.myName(), 'relation:', end=" "), relation.printRelation()

        dct = {'1':0, 's':1}
        #    dct., 's**2':2, 's**3':3, 's**4':4, 's**5':5, 's**6':6}
        for x in range(2, 10):
            dct[x] = 's**'+str(x)
        print('dct=', dct)
        
        for pows, vals in collf.items():
            #strng = relation.getSmaller()+"+"+relation.getBigger()
            strng = str(relation.getSmaller()+"+"+relation.getBigger())
            subs_from = sympy.sympify(strng)
            subs_to = sympy.sympify(str(relation.getBigger()))
            if Support.gVerbose > 3:
                print(Support.myName(), 'small=', relation.getSmaller(), ' big=', relation.getBigger())
                print(Support.myName(), 'subs_from=', subs_from, '  subs_to=', subs_to)
                print(Support.myName(), 'power=', pows, '  old val=', vals)
            new_vals = vals.subs(subs_from, subs_to)
            if Support.gVerbose > 3:
                print(Support.myName(), 'power=', pows, '  new val=', new_vals)
            collf[pows] = new_vals
            
        if Support.gVerbose > 2:
            print(Support.myName(), 'Simplified factors=', collf)
        
        ans = 0
        for pows, vals in collf.items():
            ans = ans+pows*vals
        if Support.gVerbose > 2:
            print(Support.myName(), 'Simplified eqn=', ans)
        
        return ans

    def substituteEqns(self, subList):
        temp = self.answer
        for s in subList:
            sym_from = sympy.sympify(s[0])
            sym_to = sympy.sympify(s[1])
            temp = temp.subs({sym_from: sym_to})
            if Support.gVerbose > 2:
                print(Support.myName(), 'After replacing ', sym_from, ' with ', sym_to, ', solution is: ')
                print(temp)
        #self.evalAnswer = temp
        return temp

    def substituteValues(self, eList):
        """Sub numerical values into eqn. Varlist is a list of strings in the form
        element=value, eg r1=1k or e1=10.0
        """
        temp = self.answer
        for element in eList:
            if element.valueIsSet():
                if Support.gVerbose > 2:
                    print(Support.myName(), 'Substituting', element.getLabel(), '=', element.getValue(), 'into the solved equations')                
                sym = sympy.symbols(element.getLabel())
                flt = float(eno.EngNumber(element.getValue()))
                temp = temp.subs({sym: flt})
                if Support.gVerbose > 2:
                    print(Support.myName(), 'After sub, solution is: ')
                    print(temp)
        
        self.evalAnswer = temp
        return self.evalAnswer
        # Can't set self.answer to evalAtFreq result since plotting needs the equation without
        # the freq being substituted in.
        #if self.freq is not None:
            #return self.evalAtFreq(self.freq)
        #else:
            #return self.answer

    def evalAtFreq(self, frq):
        if self.evalAnswer is not None:
            temp = self.evalAnswer
            sym = sympy.symbols('s')
            jw = frq*2*sympy.pi*sympy.I
            temp = temp.subs({sym: jw})
            if Support.gVerbose > 3:
                print(Support.myName(), 'Subs', sym, ' for ', jw, '. Now:')
                print(temp)
            return temp
        else:
            return None
