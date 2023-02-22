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

#from itertools import permutations
import sympy
from sympy.printing.mathml import mathml
import Support
from sympy import factor, pprint, init_printing, zeros, degree
import Reorder

import CGauss
#from main import *
import re as reg
import time

import engineering_notation as eno


class CLinearEquations(object):
    """
    Solves linear systems using symbolic equations.
    
    Given a circuit object, the matrices are filled with the respective admittances.
    Uses Gaussian elimination and back substitution to obtain the nodal voltages in the circuit
    """
    @staticmethod
    def static_pp(mat):
        sympy.pprint(mat)

    def __init__(self, order):
        """Create the matrix, i(current) column and v(voltage) column"""
        self.aMatrix = zeros(order, order)
        self.iColumn = zeros(order, 1)
        self.vColumn = zeros(order, 1)
        self.solution = zeros(order, 1)
        self.nNodes = order
        self.answer = None      # Raw answer with no value substituted.
        self.evalAnswer = None  # Answer with component values put in, not freq
        self.freq = None

        if Support.gVerbose > 2:
            print(Support.myName(), ' order=', order)
        init_printing()
    
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
        t_start = time.time()

        if Support.gVerbose > 1:
            print(Support.myName(),': Deleting row & column 0 from matrix and column vectors')

        self.aMatrix.row_del(0)
        self.aMatrix.col_del(0)

        self.iColumn.row_del(0)
        self.vColumn.row_del(0)
        self.nNodes = self.nNodes - 1
        
        if Support.gVerbose > 1:
            print(Support.myName(), ': aMatrix after deleting row & column 0:')
            self.pp(self.aMatrix)
            print(Support.myName(), ': vColumn after deleting row 0:')
            self.pp(self.vColumn)
            print(Support.myName(), ': iColumn after deleting row 0:')
            self.pp(self.iColumn)
        if Support.gVerbose > 1:
            print(Support.myName(),': Starting ReorderEquations')
        new_mat, new_col = Reorder.reorderEquations(self.aMatrix, self.iColumn)
        if new_mat == -1:
            print(Support.myName(), ': ReorderEquations failed. Exiting.')
            code = Support.myExit(25)
            return code
        self.aMatrix = new_mat
        self.iColumn = new_col
        if Support.gVerbose > 1:
            print(Support.myName(),': Finished ReorderEquations')

        le = CGauss.CGauss(self.aMatrix, self.iColumn)
        le.elimination()
        if Support.gVerbose > 1:
            print(Support.myName(), ': aMatrix after elimination:')
            sympy.pprint(self.aMatrix)
            print()
            print(Support.myName(), ': iColumn after elimination:')
            sympy.pprint(self.iColumn)
            print()
            print(Support.myName(), ': Beginning back-substitution')
        le.back_subs()
        if Support.gVerbose > 1:
            print(Support.myName(), ': aMatrix after back-substitution:')
            sympy.pprint(self.aMatrix)
            print()
            print(Support.myName(), ': iColumn after back-substitution:')
            sympy.pprint(self.iColumn)
        t_end = time.time()
        if (Support.gVerbose > 0):
            print(Support.myName(), "Time to solve: ", t_end-t_start)
        return 0
    
    def calculateSolution(self, circuit):
        if Support.gVerbose > 1:
            print(Support.myName(), ': Calculating output source equation')
        top = circuit.calculateVorIEqn(self.iColumn, self.vColumn, circuit.getOutputSource())
        if Support.gVerbose > 1:
            print(Support.myName(), ': Calculating input source equation')
        bottom = circuit.calculateVorIEqn(self.iColumn, self.vColumn, circuit.getInputSource())
        
        if Support.gVerbose > 2:
            print(Support.myName(), ': top=', top)
            print(Support.myName(), ': bottom=', bottom)
        if bottom != 0 and bottom is not None:
            self.answer = top.factor() / bottom.factor()
            self.answer = sympy.cancel(self.answer)
            self.answer = self.answer.factor()
        else:
            if Support.gVerbose > 1:
                print(Support.myName(), ': Solution denom = 0')
            self.answer = sympy.S.Infinity
            return (sympy.S.Infinity, 0.0)
        top, bottom = self.answer.as_numer_denom()
        return (top, bottom)
    
    def fillMatrix(self, circuit):
        """Fill up the matrix, i-column and v-column with admittances from the circuit"""
        self.fillVColumn(circuit)
        self.fillAMatrix(circuit)
    
    def fillAMatrix(self, circuit):
        """Fill the main n x n matrix with admittances"""        
        if Support.gVerbose > 1:
            print(Support.myName(), ': len(eList)=', len(circuit.getEList()))
            
        sSym = sympy.symbols('s')
        #for elNum in range(len(circuit.getEList() )):
        for elNum, element in enumerate(circuit.getEList(), 1 ):
            #element = circuit.getEList()[elNum]
            # Get the connecting nodes for all type of elements
            # i, j are the nodes the element is connected between.
            # m is the row that was added for an E, F, G, H, T, or V element. For H's, two rows are added and n is that row.
            # k, l are the controlling nodes for E, F, G, or H elements.
            i = element.getNode1()
            j = element.getNode2()
            # Get all the nodes, even if we don't need them for some element types.
            k = element.getNode3()
            l = element.getNode4()
            m = element.getSourceNode1()
            n = element.getSourceNode2()
            #iSenseLabel = 'None'
            if Support.gVerbose > 1:
                print(Support.myName(), ': Element #', elNum)
                element.printElement()
            if Support.gVerbose > 2:
                print(Support.myName(), ': i=', i, ', j=', j, ', k=', k, ', l=', l, ', m=', m, ', n=', n)
            et = element.getElementType()
            lbl = element.getLabel()
            sym = sympy.symbols(lbl)
            if et == 'c':
                self.addElementToMatrix(i, j, sym*sSym)
            elif et == 'e':     # VCVS     Checked
                # Vk * E - Vi + Vj - Vl * E = 0
                # Ii = Io
                # Ij = -Io
                self.addSourceToMatrix2C(j, i, m, 1.0)   # - Vi + Vj
                self.addSourceToMatrix2R(i, j, m, 1.0)   # Ii = Io   Ij = -Io
                self.addSourceToMatrix2C(k, l, m, sym)   # Completes Vk * E - Vi + Vj - Vl * E
            elif et == 'f':     # CCCS     Checked
                # Vk - Vl = 0
                # Ii = Io
                # Ij = -Io
                # Ik = Io/F
                # Il = -Io/F
                self.addSourceToMatrix2C(k, l, m, 1.0)
                self.addSourceToMatrix2R(i, j, m, 1.0)
                self.addSourceToMatrix2R(k, l, m, 1.0/sym)   # Vk - Vl = 0 (IVS for current sensing)
                # Ik = Iout/F  Il = -Iout/F
            elif et == 'g':     # VCCS     Checked
                # Vk - Vl - Io/G = 0
                # Ii = Io
                # Ij = -Io
                # Ik = Il = 0
                self.addSourceToMatrix2C(k, l, m, 1.0)   # Vk - Vl
                self.addSourceToMatrix2R(i, j, m, 1.0)   # Ii = Io  Ij = -Io
                self.addSourceToMatrix2C(m, 0, m, -1.0/sym)  # not admittance, it's 1/G.
                # -G (completes Vk - Vl - Iout/G = 0)
            elif et == 'h':     # CCVS, the only dependent source with two extra unknowns
                # Vk - Vl = 0             n row
                # Vi - Vj - Iin * H = 0   m row
                # Ii = Io                 n column
                # Ij = -Io                n column
                # Ik = Iin                m column
                # Il = -Iin               m column
                self.addSourceToMatrix2C(k, l, n, 1.0)   # Vk - Vl                             C
                self.addSourceToMatrix2C(i, j, m, 1.0)   # Vi - Vj                             A
                self.addSourceToMatrix2R(k, l, n, 1.0)   # Ii = Iout  Ij = -Iout               D
                self.addSourceToMatrix2C(n, 0, m, -sym)  # 1/trans-R. -G (completes Vi-Vj-H*Iin=0) A
                self.addSourceToMatrix2R(i, j, m, 1.0)   # Ik = Iin  Il = -Iin                     B
            elif et == 'i':     # Independent current source
                # I column, Ii = Io, Ij = -Io.
                                # Input is N+ node (tail of arrow)
                # Output is N- node (on the pointy arrow end).
                self.addElementToIColumn(i, j, sym)
            elif et == 'k':
                pass
            elif et == 'l':
                self.addElementToMatrix(i, j, 1.0/(sym*sSym))
            elif et == 'm':
                # [    .    .    .    .    1       0    ]    [V1]    [I1]    Ib1 = I1
                # [    .    .    .    .   -1       0    ]    [V2]    [I2]   -Ib1 = I2
                # [    .    .    .    .    0       1    ] *  [V3] =  [I3]    Ib2 = I3
                # [    .    .    .    .    0      -1    ]    [V4]    [I4]   -Ib2 = I4
# line for Ind1   [    1   -1    0    0    sL1    sk*L  ]    [Ib1]   [0 ]
# line for Ind2   [    0    0    1   -1    sk*L   sL2   ]    [Ib2]   [0 ]    L = sqrt(L1*L2)
                # Ind1 eqn    V1-V2+ s*L1*Ib1 + s*k*L*Ib2 = 0
                # Ind2 eqn    V3-V4+ s*k*L    + s*L2*Ib2  = 0
                l1 = element.getL1()
                l2 = element.getL2()
                l1n1 = l1.getNode1()
                l1n2 = l1.getNode2()
                l2n1 = l2.getNode1()
                l2n2 = l2.getNode2()
                k_l1 = element.getOtherValue() * sSym * sympy.symbols(l1)
                k_l2 = element.getOtherValue() * sSym * sympy.symbols(l2)
                self.addElementToMatrix(m, n, k_l1)
                self.addElementToMatrix(n, m, k_l2)
                self.addSourceToMatrix2C(l1n1, l1n2, m, 1)
                self.addSourceToMatrix2C(l2n1, l2n2, n, 1)
                self.addSourceToMatrix2R(l1n1, l1n2, m, 1)
                self.addSourceToMatrix2R(l2n1, l2n2, n, 1)
            elif et == 'r':
                self.addElementToMatrix(i, j, 1.0/sym)
            elif et == 't':
                # [    .    .    .    .   -1    ]   [V1]   [I1]
                # [    .    .    .    .    T    ]   [V2]   [I2]
                # [    .    .    .    .   -T    ] * [V3] = [I3]
                # [    .    .    .    .    1    ]   [V4]   [I4]
                # [    1   -T    T   -1    0    ]   [It]   [0 ]
                # T*(V2-V3) = V1-V4    -> V1-T*V2 + T*V3 - V4 = 0
                self.addSourceToMatrix2C(i, l, m, 1)    # row m: V1 - V4
                self.addSourceToMatrix2R(i, l, m, -1)   # col m: -It1 = I1, It4 = I4
                self.addSourceToMatrix2C(j, k, m, sym)  # row m: -T*V2 + T*V3
                self.addSourceToMatrix2R(j, k, m, -sym) # col m: T*It2 = I2, -T*It = I3
                #        row m total: V1 + T*V3 - V4 - T*V2
            elif et == 'v':
                # Independent voltage source
                # Vi-Vj = E + transpose
                # If it's a sensing source for a controlled source, don't add it into the matrix like its an IVS.
                # the controlled source element will put in the correct matrix entries.
                #if not circuit.isControlledSourceSensingVS(element):
                # The sensing sources aren't put in the input deck anymore, so we should have to
                # check for it.
                # TODO: Should a check be in here in case someone does put one in anyway?
                self.addSourceToMatrix2C(i, j, m, 1.0)
                self.addSourceToMatrix2R(i, j, m, 1.0)
                self.addElementToIColumn(m, 0, sym)
            else:
                print(Support.myName(), ': Unknown element ', element.getElementType(), ' encountered. Exiting.')
                Support.myExit(10)
        
        for i in range(self.nNodes-1):
            self.aMatrix[i,0] = 0
            self.aMatrix[0,i] = 0
            
        if Support.gVerbose > 0:
            print()
            print(Support.myName(), ': Matrix entries:')
            self.pp(self.aMatrix)
            #self.pp(self.aMatrix)
            print()
            print(Support.myName(), ': V Column entries:')
            self.pp(self.vColumn)
            #self.pp(self.vColumn)
            print()
            print(Support.myName(), ': I Column entries:')
            self.pp(self.iColumn)
            #self.pp(self.iColumn)
    
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
                tmp = 'V'
                tmp += str(circuit.getUserNode(i))
                if Support.gVerbose > 2:
                    print(Support.myName(), ': i=', i, ', label=', tmp)
            else:
                tmp = ''
                addedNodeNum = i-(nn-add)
                addedElement = circuit.getAddedNodeElement(addedNodeNum)
                if Support.gVerbose > 2:
                    print(Support.myName(), ': i=', i, ', addedNodeNum=', addedNodeNum, \
                    ', addedElement label=', addedElement.getLabel())
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
                    tmp = 'I(' + addedElement.getNode3() + ',' + addedElement.getNode4() + ')'
                    tmp += addedElement.getISenseLabel()
            sym = sympy.symbols(tmp)
            self.getVColumn()[i] = sym
            i += 1
        
    def pp(self, mat):
        #temp = mat.copy()
        sympy.pprint(mat)
        
    def print_HTML(self, something, f):
        print(type(something))
        mth = sympy.mathml(sympy.N(something, 2), printer='presentation')
        mth2 = self.pretty_html(mth)
        f.write('<math>\n')
        f.write( mth2 )
        f.write('<p>')
        f.write('</math>\n')
        
    # Takes a mathml string and makes corrections.
    def pretty_html(self, strng):
        p1 = reg.sub(r'<mi>(\w)(\w+)</mi>', r'<msub><mi>\1</mi><mi>\2</mi></msub>', strng)
        p2 = p1.replace('&InvisibleTimes;', '*')
        p3 = reg.sub(r'^<mfrac><mrow><mn>1.0</mn><mo>*</mo>', r'<mfrac><mrow>', p2)
        p4 = reg.sub(r'^<mfrac><mo>-</mo><mn>1.0</mn><mo>*</mo>(.*)', \
                     r'<mfrac><mrow><mo>-</mo>\1', p3)

        if Support.gVerbose > 2:
            print(Support.myName(), ' p1=', p1)
            print(Support.myName(), ' p2=', p2)
            print(Support.myName(), ' p3=', p3)
            print(Support.myName(), ' p4=', p4)
        return p4

    #             i,i        i,j
    # [  .    .   adm    .  -adm     .]
    # [  .    .   .      .   .       .]
    # [  .    .  -adm    .   adm     .]
    #             j,i        j,j
    def addElementToMatrix(self, i, j, adm):
        """Add the elements admittance to the matrix"""
        if i==0 or j==0:
            n=i+j
            self.aMatrix[n, n] += adm
        else:
            self.aMatrix[i, i] += adm
            self.aMatrix[j, j] += adm
            self.aMatrix[i, j] -= adm
            self.aMatrix[j, i] -= adm
    
    def addElementToIColumn(self, i, j, cterm):
        """Add an elements label to the i-column"""
        """For the iColumn it matters if one of i or j is zero, which one it is"""
        if Support.gVerbose > 2:
            print(Support.myName(), ': i=', i, ', j=', j, ', cterm=', cterm)
        if i==0:
            self.iColumn[j] += cterm
        elif j==0:
            self.iColumn[i] -= cterm
        else:
            self.iColumn[i] += cterm
            self.iColumn[j] -= cterm

    #      column:  i            j
    # row m: [.    adm    .    -adm    .    ]
    def addSourceToMatrix2C(self, i, j, m, adm):
        """Add a source to the matrix in two different columns, i & j, row m"""
        if Support.gVerbose > 2:
            print(Support.myName(), ': row m=', m, ', col i=', i, ' adm=', adm)
            print(Support.myName(), ': row m=', m, ', col j=', j, ' adm=', -adm)
        if i != 0:
            self.aMatrix[m, i] += adm
        if j != 0:
            self.aMatrix[m, j] -= adm
    
    #       column: m
    # row i: [.    adm    .]
    # row j: [.   -adm    .]
    def addSourceToMatrix2R(self, i, j, m, adm):
        """Add a source to the matrix in two different rows, i & j, column m"""
        if Support.gVerbose > 2:
            print(Support.myName(), ': row i=', i, ', col m=', m, ' adm=', adm)
            print(Support.myName(), ': row j=', j, ', col m=', m, ' adm=', -adm)
        if i != 0:
            self.aMatrix[i, m] += adm
        if j != 0:
            self.aMatrix[j, m] -= adm     

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
        s_ratio = sympy.simplify(ratio)

        new_ratio = sympy.factor(s_ratio)
        new_n, new_d = sympy.fraction(new_ratio)
        
        if Support.gVerbose > 0:
            print(Support.myName(), 'ratio=', ratio)
            print(Support.myName(), 'simplified=', s_ratio)
            print(Support.myName(), 'new_n=', new_n)
            print(Support.myName(), 'new_d=', new_d)
        return new_ratio

    def applyRelationList(self, eqn, simpList):
        old_eqn = eqn
        if Support.gVerbose > 1:
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
    
    def applyRelation(self, eqn, relation):
        s = sympy.symbols('s')
        exp_eqn = eqn.expand()
        collf = sympy.collect(exp_eqn, s, factor, evaluate=False)
        if Support.gVerbose > 2:
            print(Support.myName(), 'eqn to simplify=', exp_eqn)
            print(Support.myName(), 'collected factors=', collf)
            print(Support.myName(), 'relation:', end=" "),
            relation.printRelation()
            print(Support.myName(), 'smaller relation:', relation.getSmaller())
            print(Support.myName(), 'bigger relation:', relation.getBigger())

        dct = {'1':0, 's':1}
        #    dct., 's**2':2, 's**3':3, 's**4':4, 's**5':5, 's**6':6}
        for x in range(2, 10):
            dct[x] = 's**'+str(x)
        if Support.gVerbose > 2:
            print(Support.myName(), 'dct=', dct)
        
        for pows, vals in collf.items():
            #tmp = vals.factor()
            #print('applyRelation: vals.factor()=', tmp)
            #temp_str = relation.getSmaller()+"+"+relation.getBigger()
            add_1 = sympy.sympify(relation.getSmaller(), {'re': sympy.Symbol('re')} )
            add_2 = sympy.sympify(relation.getBigger(), {'re': sympy.Symbol('re')} )
            subs_from = add_1 + add_2
            #temp_str = repr(relation.getSmaller() + relation.getBigger())
            #subs_from = sympy.sympify(temp_str)
            subs_to = sympy.sympify(relation.getBigger())
            if Support.gVerbose > 2:
                print(Support.myName(), 'subs_from=', subs_from)
                print(Support.myName(), 'subs_to=', subs_to)
                print(Support.myName(), 'subs_from=', subs_from, '  subs_to=', subs_to)
                print(Support.myName(), 'power=', pows, '  old val=', vals)
            new_vals = vals.subs(subs_from, subs_to)
            if Support.gVerbose > 2:
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

    def subEqns(self, eqn, subList):
        temp = eqn.copy()
        for s in subList:
            sym_from = sympy.sympify(s[0])
            sym_to = sympy.sympify(s[1])
            temp = temp.subs({sym_from: sym_to})
            if Support.gVerbose > 2:
                print(Support.myName(), 'After replacing ', sym_from, ' with ', sym_to, ', solution is: ')
                print(temp)
        return temp

    def subValues(self, eqn, eList):
        """Sub numerical values into eqn. elist is a list of strings in the form
        element=value, eg r1=1k or e1=10.0
        """
        temp = eqn
        for element in eList:
            if element.valueIsSet():
                if Support.gVerbose > 2:
                    print(Support.myName(), 'Substituting', element.getLabel(), '=', \
                          element.getValue(), 'into the solved equations')                
                sym = sympy.symbols(element.getLabel())
                flt = float(eno.EngNumber(element.getValue()))
                temp = temp.subs({sym: flt})
                if Support.gVerbose > 2:
                    print(Support.myName(), 'After sub, solution is: ')
                    print(temp)
        
        # Needs to be saved since this is the one we need if plotting it requested.
        self.evalAnswer = temp

        return self.evalAnswer

    def evalAtFreq(self, frq):
        temp = self.evalAnswer
        sym = sympy.symbols('s')
        jw = frq*2*sympy.pi*sympy.I
        temp = temp.subs({sym: jw})
        if Support.gVerbose > 3:
            print(Support.myName(), ': Subs', sym, ' for ', sympy.N(jw, 5), '. Now:', end='')
            print(sympy.N(temp, 5))
        return temp
    
    def eeForm(self, eqn):
        ''' Put the passed eqn into 'EE' form- with the highest coeff of 's'
        denom being 1 by dividing top and bottom by whatever the coeff is.'''
        numer, denom = sympy.fraction(eqn)
        s = sympy.symbols('s')
        hi_order_n = degree(numer, gen=s)
        hi_order_d = degree(denom, gen=s)
        if hi_order_n > hi_order_d:
            coeff = numer.coeff(s, hi_order_n)
        else: 
            coeff = denom.coeff(s, hi_order_d)
        new_numer = sympy.expand(numer / coeff)
        new_denom = sympy.expand(denom / coeff)
        return new_numer, new_denom
        
        
        
        
        

            
