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
'''

#from Support import myName

class CElement(object):
    '''
    classdocs
    '''
    #commands = ['solve', 'output', 'answer', ';', '*']
    elementTypes = 'cefghilrv'


    def __init__(self, elementType, label, node1, node2, node3, node4, value=None):
        '''
        Constructor
        '''
        self.elementType = elementType
        self.label = label
        self.value = value
        if self.value is None:
            self.valueSet = False
        else:
            self.valueSet = True
        # for F and H elements, this is the ivs that senses the current
        self.iSenseLabel = 'None'
        self.nodes = [0]*4
        self.userNodes = [0]*4
        self.setNodes1234( node1, node2, node3, node4)
        self.setUserNodes1234(node1, node2, node3, node4)
        # If an element is a source, this node is the extra one added in the matrix.
        # They only use internal node numbers.
        # For CCVS (H) elements, this points to the first node of the two that are
        # added. They are in consecutive rows in the matrix
        self.sourceNode1 = -1
        # The second source added for CCVS (H) elements.
        self.sourceNode2 = -1

    @classmethod
    def getElementTypes(cls):
        """The class variable elementTypes"""
        return cls.elementTypes
     
    def valueIsSet(self):
        return self.valueSet
        
    def getElementType(self):
        """The instance variable elementType"""
        return self.elementType.lower()
    
    def setElementType(self, et):
        self.elementType = et.lower()
    
    def setLabel(self, lbl):
        self.label = lbl
        
    def getLabel(self):
        return self.label
    
    def getValue(self):
        return self.value
    
    def setSourceNode1(self, number):
        self.sourceNode1 = number
        
    def setSourceNode2(self, number):
        self.sourceNode2 = number
        
    def getSourceNode1(self):
        return self.sourceNode1

    def getSourceNode2(self):
        return self.sourceNode2
            
    # Prints an element using the internal node numbers.
    def printElement(self):
        print('    {0:4s} '.format(self.label), end='' )
        print('{0:2d} {1:2d}'.format(self.getNode1(), self.getNode2() ), end='' )
        if self.twoNodesAndLabel():
            print(' {0:7s}'.format(self.iSenseLabel), end='' )
        elif self.fourNodes():
            print(' {0:2d} {1:2d}'.format( self.getNode3(), self.getNode4() ), end=''  )
        
        
        if self.value is not None:
            print(' {}'.format(self.value))
        else:
            print()
    
    # Prints an element using the user node numbers.
    def printElementU(self):
        print('    {0:4s} '.format(self.label), end='' )
        print('{0:2d} {1:2d}'.format(self.getUserNode1(), self.getUserNode2() ), end='' )
        if self.twoNodesAndLabel():
            print(' {0:7s}'.format(self.iSenseLabel), end='')
        elif self.fourNodes():
            print(' {0:2d} {1:2d}'.format(self.getUserNode3(), self.getUserNode4()), end='' )

        if self.value is not None:
            print(' {}'.format(self.value))
        else:
            print()
    
    # A print method specifically for the 'solve' element only.
    # Needs to have html version added
    # Prints a solve statement using the internal node numbers.
    def printElementS(self):
        if self.elementType == 'v':
            print('    V({0:d}, {1:d})'.format(self.getNode1(), self.getNode2() ))
        if self.elementType == 'i':
            print('    I({0:s})'.format(self.label) )

    # A print method specifically for the 'solve' element only.
    # Needs to have html version added
    # Prints a solve statement using the user node numbers.
    def printElementUS(self):
        if self.elementType == 'v':
            print('    V({0:d}, {1:d})'.format( self.getUserNode1(), self.getUserNode2() ))
        if self.elementType == 'i':
            print('    I({0:s})'.format( self.label) )  
                    
    def twoNodes(self):
        return self.elementType in 'cilrv'
    
    def twoNodesAndLabel(self):
        return self.elementType in 'fh'
    
    def fourNodes(self):
        return self.elementType in 'eg'
    
    def getNodes(self):
        return self.nodes
    
    def getNode1(self):
        return self.nodes[0]
    
    def getNode2(self):
        return self.nodes[1]
    
    def getNode3(self):
        return self.nodes[2]
    
    def getNode4(self):
        return self.nodes[3]
    
    def getUserNodes(self):
        return self.userNodes
    
    def getUserNode1(self):
        return self.userNodes[0]
    
    def getUserNode2(self):
        return self.userNodes[1]
    
    def getUserNode3(self):
        return self.userNodes[2]
    
    def getUserNode4(self):
        return self.userNodes[3]
    
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
    
    def setISenseLabel(self, strng):
        self.iSenseLabel = strng
        
    def getISenseLabel(self):
        return self.iSenseLabel
    
        