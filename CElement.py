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
Created on Nov 24, 2016

@author: Tom Spargo

2/25/2020. Added mutual inductor, 'm', coupled inductor 'k', & ideal transformer, 't'.
'''
import Support

class CElement(object):
    '''
    classdocs
    '''
    #commands = ['solve', 'output', 'answer', ';', '*']
    #elementTypes = 'cefghilrv'
    eTypes = 'cefghiklmrtv'
    eWithValues = 'cefghklmrt'
    eOptionalValues = 'iv'
    eWith2Nodes = 'cilrv'
    eWith2NodesAndLabel = 'fh'
    eWith4Nodes = 'egt'
    eWith2Labels = 'km'
    def __init__(self, elementType, label, node1, node2, node3=0, node4=0, value=None):
        '''
        Constructor for all elements except k & m
        '''
        self.elementType = elementType.lower()
        self.label = label
        self.value = value
        if value is None:
            self.valueSet = False
        else:
            self.valueSet = True
        # for F and H elements, this is the ivs that senses the current
        self.iSenseLabel = 'None'
        self.nodes = [0]*4
        self.userNodes = [0]*4
        self.setNodes1234( node1, node2, node3, node4)
        self.setUserNodes1234(node1, node2, node3, node4)
        self.isAddedElement = False

        # If an element is a source, this node is the extra one added in the matrix.
        # They only use internal node numbers.
        # For CCVS (H) elements, this points to the first node of the two that are
        # added. They are in consecutive rows in the matrix
        # For mutual inductors, this points to the first inductor listed in the 'M' card.
        self.sourceNode1 = -1
        # The second source is added for CCVS (H) elements, or for the second inductor listed
        # for m-inductor (M) elements.
        self.sourceNode2 = -1
        
    @classmethod
    def getETypes(cls):
        """The class variable elementTypes"""
        return cls.eTypes
    
    @classmethod
    def getEWithValues(cls): return cls.eWithValues
    @classmethod
    def getEWithTwoNodes(cls): return cls.eWith2Nodes
    @classmethod
    def getEWith2NodesAndLabel(cls): return cls.eWith2NodesAndLabel
    @classmethod
    def getEWith4Nodes(cls): return cls.eWith4Nodes
    @classmethod
    def getEWith2Labels(cls): return cls.eWith2Labels
    def hasTwoNodes(self): return self.elementType in self.eWith2Nodes
    def hasTwoNodesAndLabel(self): return self.elementType in self.eWith2NodesAndLabel
    def hasFourNodes(self): return self.elementType in self.eWith4Nodes
    def hasTwoLabels(self): return self.elementType in self.eWith2Labels
    def valueIsSet(self): return self.valueSet
    """The instance variable elementType"""
    def getElementType(self): return self.elementType
    def getEType(self): return self.elementType
    def setElementType(self, et): self.elementType = et.lower()
    def setEType(self, et): self.elementType = et.lower()
    def setLabel(self, lbl): self.label = lbl
    def getLabel(self): return self.label
    
    def setValue(self, value):
        self.value = value
        if value is None:
            self.valueSet = False
        else:
            self.valueSet = True
        
    def getValue(self): return self.value
    def setSourceNode1(self, number): self.sourceNode1 = number
    def setSourceNode2(self, number): self.sourceNode2 = number
    def setISenseLabel(self, strng): 
        
        if Support.gVerbose > 2:
            print(Support.myName(), "Setting ", self.getLabel(), " iSense label to", strng)
        self.iSenseLabel = strng
        print(Support.myName(), "    Now", self.getLabel(), " iSense label is", self.getISenseLabel())
    def setIsAddedElement(self, yorn): self.isAddedElement = yorn
    def getIsAddedElement(self): return self.isAddedElement
    def getSourceNode1(self): return self.sourceNode1
    def getSourceNode2(self): return self.sourceNode2
    def getISenseLabel(self): return self.iSenseLabel
    def getNodes(self): return self.nodes
    def getNode1(self): return self.nodes[0]
    def getNode2(self): return self.nodes[1]
    def getNode3(self): return self.nodes[2]
    def getNode4(self): return self.nodes[3]
    def getUserNodes(self): return self.userNodes
    def getUserNode1(self): return self.userNodes[0]
    def getUserNode2(self): return self.userNodes[1]
    def getUserNode3(self): return self.userNodes[2]
    def getUserNode4(self): return self.userNodes[3]
    
    def setNodes1234(self, n1, n2, n3, n4):
        self.nodes[0] = n1
        self.nodes[1] = n2
        self.nodes[2] = n3
        self.nodes[3] = n4
    
    def setNodes12(self, n1, n2):
        self.nodes[0] = n1
        self.nodes[1] = n2
        
    def setUserNodes1234(self, n1, n2, n3, n4):
        self.userNodes[0] = n1
        self.userNodes[1] = n2
        self.userNodes[2] = n3
        self.userNodes[3] = n4
        
    def setUserNodes12(self, n1, n2):
        self.userNodes[0] = n1
        self.userNodes[1] = n2

    # Use a char to ID whether an element is two nodes, two nodes + label,
    # or four nodes.
    def getElementFormatCode(self):
        add = "N"
        if self.getIsAddedElement(): add="Y" 
        
        code = '2N'
        if self.hasFourNodes(): code = '4N'
        if self.hasTwoNodesAndLabel(): code = 'NL'
        if self.hasTwoLabels(): code = '2L'
    
        return code+' '+add
    # Prints an element using the internal node numbers
    def printElement(self):
        if not self.hasTwoLabels():
            self.printElementGen(False)
        else:
            self.printKMElement()
    
    # Prints an element using user node numbers.
    def printElementU(self):
        if not self.hasTwoLabels():
            self.printElementGen(True)
        else:
            self.printKMElement()
            
    def printElementGen(self, f_userNodes):
        if f_userNodes:
            nds = self.getUserNodes()
        else:
            nds = self.getNodes()
        char = self.getElementFormatCode()
        if self.valueIsSet():
            val = str(self.getValue())
        else:
            val = '---'
        
        if self.getSourceNode1() != -1 or self.getSourceNode2() != -1:
            src_str = ' src1={0:2d} src2={1:2d}'.format(self.getSourceNode1(), self.getSourceNode2() )
        else:
            src_str = ''
        
        eT = self.getEType()
        lbl = self.getLabel()
        iSL = self.getISenseLabel()
        if self.hasTwoNodes():
            #            fmt   eType  Label     ND1     ND2               val     src    iSL
            print('    {0:4s}  {1:1s} {2:<4s} {3:<4d} {4:<4d}           {5:<4s} {6:16s} {7:4s}'.format( \
                       char,   eT,    lbl,    nds[0], nds[1],             val,  src_str, iSL))

        elif self.hasTwoNodesAndLabel():
            #            fmt   eType  Label     ND1     ND2               val    src      iSL
            print('    {0:4s}  {1:1s} {2:<4s} {3:<4d} {4:<4d}           {5:<4s} {6:<16s} {7:4s}'.format( \
                        char,  eT,    lbl,    nds[0], nds[1],             val, src_str,  iSL), )
        elif self.hasFourNodes():
            #            fmt   eType  Label     ND1     ND2     ND3     ND4    val    src      iSL
            print('    {0:4s}  {1:1s} {2:<4s} {3:<4d} {4:<4d} {5:<4d} {6:<4d} {7:<4s} {8:16s} {9:4s}'.format( \
                        char,  eT,    lbl,    nds[0], nds[1], nds[2], nds[3],  val,   src_str, iSL))
        elif self.hasTwoLabels():
            #            fmt   eType  Label     L1      L2                val     src    iSL
            print('    {0:4s}  {1:1s} {2:<4s} {3:<4s} {4:<4s}           {5:<4s} {6:16s} {7:4s}'.format( \
                        char,  eT,    lbl, self.getL1(), self.getL2(),    val, src_str, iSL))
        
    def printKMElement(self):
        print('    {0:4s} {1:4s} {2:4s} k={3:s} M={4:s}'.format(self.label, \
              self.getL1(), self.getL2(), self.getK(), self.getM() ) )


    # Print everything about the element, regardless of what it is.
    def dumpElement(self, f_intNodes):
        if f_intNodes:
            nds = self.getNodes()
        else:
            nds = self.getUserNodes()
        char = self.getElementFormatCode()
        if self.valueIsSet():
            val = str(self.getValue())
        else:
            val = '---'
        
        if self.getSourceNode1() != -1 or self.getSourceNode2() != -1:
            src_str = ' src1={0:2d} src2={1:2d}'.format(self.getSourceNode1(), self.getSourceNode2() )
        else:
            src_str = ''
        #        fmt   eType  Label     ND1     ND2     ND3     ND4    val    src  iSense   isAddedEle
        print(' {0:4s}  {1:1s} {2:<4s} {3:<4d} {4:<4d} {5:<4d} {6:<4d} {7:<4s} {8:16s} {9:5s}'.format( \
                char, self.getEType(), self.getLabel(), nds[0], nds[1], nds[2], nds[3], val, src_str, \
                self.getISenseLabel()))


    # Print methods specifically for the 'solve' elements.
    # Prints a solve statement using the internal node numbers.
    def printElementS(self):
        self.printSolveElement(False)
    
    # Prints a solve statement using the user node numbers.
    def printElementUS(self):
        self.printSolveElement(True)

    # Print method for the 'solve' element using either kind of node numbers.
    def printSolveElement(self, f_userNodes):
        if f_userNodes:
            nd1 = self.getUserNode1()
            nd2 = self.getUserNode2()
        else:
            nd1 = self.getNode1()
            nd2 = self.getNode2()
            
        if self.elementType == 'v':
            print('    V({0:d}, {1:d})'.format( nd1, nd2) )
        if self.elementType == 'i':
            print('    I({0:s})'.format( self.label) )  

class KMElement(CElement):
    def __init__(self, eType, label, l1_lbl, l2_lbl, value):
        # For K and M elements, need to save the names of the two L's they connect together
        self.setEType(eType)
        self.setLabel(label)
        self.L1 = l1_lbl     # Name of the first coupled inductor
        self.L2 = l2_lbl     # "     "  "  second  "       "
        self.setValue(value)
        self.orgL1Value = None  # Original value of L1
        self.orgL2Value = None  # Original value of L2
        self.otherValue = 0     # If this is a 'k', this holds the 'm' value and
                                # vice-versa
                                  
    def setL1(self, lbl): self.L1 = lbl
    def setL2(self, lbl): self.L2 = lbl
    def getL1(self): return self.L1
    def getL2(self): return self.L2
    def setOrgL1Value(self, val): self.orgL1Value = val
    def setOrgL2Value(self, val): self.orgL2Value = val
    def getOrgL1(self): return self.orgL1Value
    def getOrgL2(self): return self.orgL2Value
    def setOtherValue(self, val): self.otherValue = val
    def getOtherValue(self): return self.otherValue
    
    
    
