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

import sympy
import CElement
import CSimpList
from Support import myName, myExit, gVerbose
#from Support import myExit
#from eqnSolver import *

class CCircuit(object):
    '''
    classdocs
    '''
    MAXNODES = 100
    
    @classmethod
    # Not using self.eList so that CFileReader can call this method and pass the eList it's 
    # constructing from the input file.
    def elementExists(self, eList, name):
        found = False
        for it in eList:
            if name.casefold() == it.getLabel().casefold():
                found = True
                if gVerbose > 2:
                    print(myName(), ': found=', found, ' name=', name, ' lbl=', it.getLabel())
                break
            if gVerbose > 2:
                print(myName(), ': found=', found, ' name=', name, ' lbl=', it.getLabel())
        return found

    def __init__(self, eList, inSource, outSource, freq, htmlFilename=''):
        '''
        Constructor
        '''
        self.eList = eList      # List of elements in the circuit
        self.inputSource = inSource    # Input source element
        self.outputSource = outSource  # Output source element
        self.htmlFilename = htmlFilename
        self.freq = freq
        self.nNodes = 0         # Number of nodes in the circuit, including extras for unknown currents
        self.addedNodes = 0     # Number of extra nodes in the circuit that were added for unknown currents
        self.nodeIndex = [0]*self.MAXNODES   # Contains the user nodes, index is the internal node
        #self.addedNodeElement = [0]*self.MAXNODES  # So we can find which element corresponds to each of the added nodes
        self.addedNodeElement = []  # So we can find which element corresponds to each of the added nodes
    
    def getFreq(self):
        return self.freq
    
    def getEList(self):
        return self.eList
    
    def getNumOfNodes(self):
        return self.nNodes
    
    def setNumOfNodes(self, num):
        self.nNodes = num
        
    def getNumOfAddedNodes(self):
        return self.addedNodes
    
    def setNumOfAddedNodes(self, num):
        self.addedNodes = num
    
    def getUserNode(self, index):
        return self.nodeIndex[index]
        
    def getOutputSource(self):
        return self.outputSource
    
    def getInputSource(self):
        return self.inputSource
        
    # True if at least 1 element specifies a value
    def anyValuesDefined(self):
        valuesDefined = False
        for element in self.eList:
            if element.valueIsSet():
                valuesDefined = True
                if gVerbose > 2:
                    print(myName(), 'For element', element.getLabel(), \
                          'valuesDefined=', valuesDefined)
                break
        return valuesDefined
    
    # True if all non-source elements have a value- ie, cefghlr
    def allValuesDefined(self):
        allDefined = True
        for element in self.eList:
            if element.getElementType().lower() in 'cefghlr':
                if not element.valueIsSet():
                    allDefined = False
                    if gVerbose > 2:
                        print(myName(), 'With element ', element.getLabel(), \
                              ' allDefined=', allDefined)
                    break
        return allDefined

    def getHTMLFilename(self):
        return self.htmlFilename
    
    def createIndexList(self):
        """Generate an array of the node numbers that are used. Zeroth entry is gnd. This
        is where the number of nodes required is determined"""
        self.nNodes = 1
        extraNodes = 0      # Temp var to keep track of # added nodes in the 2nd loop below.
        self.nodeIndex[0] = 0
        for element in self.eList:
            self.addNode(element.getNode1())
            self.addNode(element.getNode2())

        for element in self.eList:
            etype = element.getElementType().lower()
            if (etype in 'efgh') or (etype == 'v' and not self.isControlledSourceSensingVS(element) ):
                # e- VCVS. Need var for current through VS
                # f- CCCS. Need var for current through CS
                # g- VCCS. Need var for current through CS
                element.setSourceNode1(self.nNodes)
                self.nodeIndex[self.nNodes] = self.nNodes
                self.nNodes += 1
                # Add the current element to the addedNodeElement list.
                self.addedNodeElement.append(element)
                extraNodes += 1
                if (gVerbose > 2):
                    print(myName(), ': Added extra node ', self.nNodes-1, ' for element ', element.getLabel())
                    print(myName(), ': iSenseLabel = ', element.getISenseLabel())
                    print(myName(), ': extraNodes=', extraNodes)
                    print(myName(), ': size(addedNodeElement)=', len(self.addedNodeElement))
            
            if etype == 'h':
                # h- CCVS. Need var for current through VS and the controlling current.
                element.setSourceNode2(self.nNodes)
                self.nodeIndex[self.nNodes] = self.nNodes
                self.nNodes += 1
                hElement = CElement.CElement('h', 'i'+element.getLabel(), 0, 0, 0, 0)
                # Defaults for iSenseLabel & sourceNode1
                self.addedNodeElement.append(hElement)
                extraNodes += 1
                if gVerbose > 2:
                    print(myName(), ': Added 2nd extra node ', self.nNodes-1, ' for element ', element.getLabel())
                    print(myName(), ': extraNodes=', extraNodes)
                    print(myName(), ': size(addedNodeElement)=', len(self.addedNodeElement))
                
        self.setNumOfAddedNodes(extraNodes)
        if gVerbose > 0:
            print(myName(), ': The nodeIndex is')
            print('Internal    User')
            for i in range(self.nNodes-self.addedNodes):
                print(i, '           ', self.nodeIndex[i])
            print(myName(), ': There are ', self.nNodes, ' nodes, including ground.')
            print(myName(), ': ', self.addedNodes, ' nodes were added to account for sources.')
            print(myName(), ': The added elements are (in user node numbers):')
            for i in range(self.addedNodes):
                addedEl = self.getAddedNodeElement(i)
                print(addedEl.getLabel(), addedEl.getNode1(), addedEl.getNode2())
        return self.nNodes
            
    def addNode(self, number):
        if number != 0:     # Don't add the ground node to the list
            if self.reverseLookup(number) == -1:
                if self.nNodes < self.MAXNODES-1:
                    self.nodeIndex[self.nNodes] = number
                    self.nNodes += 1
                else:
                    print(myName(), ': Maximum number of nodes exceeded (seriously?):', self.MAXNODES)
                    myExit(2)
                return True
            else:
                return False
        else:
            return False
    
    def renumberNodes(self):
        renumberedList = self.eList
        for original, renumbered in zip(self.eList, renumberedList):
            if original.twoNodes():
                if gVerbose > 2:
                    print(myName(), ': twoNodes reverse lookup for nodes ', \
                        original.getNode1(), ' and ', original.getNode2() )
                renumbered.setNodes12(self.reverseLookup(original.getNode1()), \
                    self.reverseLookup(original.getNode2()))
            
            elif original.twoNodesAndLabel():
                if gVerbose > 2:
                    print(myName(), ': twoNodesAndLabel reverse lookup for nodes ', \
                        original.getNode1(), ', ', original.getNode2(), ', ', \
                        original.getNode3(), ' and ', original.getNode4())
                renumbered.setNodes1234(self.reverseLookup(original.getNode1()), \
                    self.reverseLookup(original.getNode2()), \
                    self.reverseLookup(original.getNode3()), \
                    self.reverseLookup(original.getNode4()))
            
            elif original.fourNodes():
                if gVerbose > 2:
                    print(myName(), ': fourNodes reverse lookup for nodes ', \
                        original.getNode1(), ', ', original.getNode2(), ', ', \
                        original.getNode3(), ' and ', original.getNode4())
                renumbered.setNodes1234(self.reverseLookup(original.getNode1()), \
                    self.reverseLookup(original.getNode2()), \
                    self.reverseLookup(original.getNode3()), \
                    self.reverseLookup(original.getNode4()))
        
        self.eList = renumberedList
        
        # Take care of the solve elements as well
        if gVerbose > 1:
            print(myName(), ': Renumbering output source nodes')
        self.renumberSourceNodes(self.outputSource)
        if gVerbose > 1:
            print(myName(), ': Renumbering input source nodes')
        self.renumberSourceNodes(self.inputSource)
    
    def renumberSourceNodes(self, source):
        if source.getElementType() == 'v':
            if gVerbose > 2:
                print('CCircuit::renumberSourceNodes: node1=', source.getUserNode1(), \
                      ', node2=', source.getUserNode2())
            n1 = self.reverseLookup(source.getUserNode1())
            if n1 == -1:
                print('CCircuit::renumberSourceNodes: The node ', source.getUserNode1(), \
                      ' does not exist in source ', source.getLabel(), '. Exiting.')
                myExit(3)
            n2 = self.reverseLookup(source.getUserNode2())
            if n2 == -1:
                print('CCircuit::renumberSourceNodes: The node ', source.getUserNode2(), \
                      ' does not exist in source ', source.getLabel(), '. Exiting.')
                myExit(4)
            if gVerbose > 2:
                print(myName(), ': Renumbering source node ', source.getLabel(), \
                      ' to nodes ', n1, ', ', n2)
            source.setNodes12(n1, n2)


    
    # Return the internal node given the user node. If the user node isn't found, -1 is returned.
    def reverseLookup(self, val):
        #try:
        #    node = (key for key,value in self.nodeIndex.items() if value==val).next()
        #    return node
        #except KeyError:
        #    return -1
        for i in range(len(self.nodeIndex)):
            if self.nodeIndex[i] == val:
                return i

        return -1

    # F and H elements have controlling sources whose nodes aren't listed in the input deck. Now that
    # the numbers of nodes has been determined and been renumbered, look for F and H elements and fill
    # in the controlling source node numbers.
    def setControllingSourceNodes(self):
        theControllingElement = CElement.CElement('c', '', 0, 0, 0, 0)
        for it in self.eList:
            if it.twoNodesAndLabel():
                n1 = it.getNode1()
                n2 = it.getNode2()
                # Find the controlling element using its label, then extract its connecting nodes.
                controllingElementLabel = it.getISenseLabel()
                theControllingElement = self.findElementWithLabel(controllingElementLabel)
                
                # Finally, set the F or H element connecting nodes to what they already are, and set
                # the controlling nodes to the controlling elements connecting nodes
                cn1 = theControllingElement.getNode1()
                cn2 = theControllingElement.getNode2()
                it.setNodes1234(n1, n2, cn1, cn2)
                if gVerbose > 1:
                    print('CCircuit::setControllingSourceNodes: Added controlling nodes for element ', it.getLabel())
                if gVerbose > 2:
                    print('CCircuit::setControllingSourceNodes:    Controlling element is ', it.getISenseLabel())
                    print('                                        Controlling nodes are ', cn1, ' and ', cn2)                
    
    def findElementWithLabel(self, lbl):
        for it in self.eList:
            if it.getLabel() == lbl:
                return it
        print('CCircuit::findElementWithLabel: ***** Error: Label ', lbl, ' was not found.')
        return None
        
    def getAddedNodeElement(self, index):
        return self.addedNodeElement[index]
    
    def getAddedNodeElementIndex(self, label):
        i = self.getNumOfAddedNodes()
        for it in self.addedNodeElement:
            lbl = it.getLabel()
            if gVerbose > 2:
                print('CCircuit::getAddedNodeElementIndex: Search label = ', label, ', checking ', lbl, ', index = ', i)
            if lbl == label:
                return self.nNodes-i
            else:
                if gVerbose > 2:
                    print('CCircuit::getAddedNodeElementIndex: label =', lbl, ', num of added nodes = ', i)
                i -= 1
        print('CCircuit::getAddedNodeElementIndex: ***** Error, label ', label, ' was not found, i=', i)
        myExit(5)
        return -1

    def isAddedElement(self, anElement):
        nn = self.getAddedNodeElementIndex(anElement.getLabel())
        return (self.addedNodes-self.nNodes > nn)
    
    def regurgitate(self, useInternalNodeNumbers=True):
        if gVerbose > 0:
            if useInternalNodeNumbers:
                print(myName(), ': Dumping eList contents, internal node numbers.')
            else:
                print(myName(), ': Dumping eList contents, user node numbers.')
            for it in self.eList:
                if useInternalNodeNumbers:
                    it.printElement()
                else:
                    it.printElementU()
            
            if useInternalNodeNumbers:
                print('Solve for (int node numbers):')
                self.outputSource.printElementS()
                print('----------')
                self.inputSource.printElementS()
            else:
                print('Solve for (user node numbers):')
                self.outputSource.printElementUS()
                print('----------')
                self.inputSource.printElementUS()
            print(myName(), ': End of file dump')
            
    def calculateVorIEqn(self, iC, sourceElement):
        elType = sourceElement.getElementType()
        if gVerbose > 2:
            print(myName(), 'elType=', elType)
        #iC = le.getIColumn()
        if elType == 'v':
            pNode = sourceElement.getNode1()
            nNode = sourceElement.getNode2()
            # The source element node numbers are still referring to the
            # pre-column & row deletion version of the matrix. So they are
            # off by 1. And 0 means ground so it's always 0.
            if pNode == 0:
                pEqn = 0.0
            else:
                pEqn = iC[pNode-1]
            if nNode == 0:
                nEqn = 0.0
            else:
                nEqn = iC[nNode-1]
            
            eqn = pEqn - nEqn
            if gVerbose > 1:
                print(myName(), ': Calculating V(', pNode, ')-V(', nNode, ')')
                print(myName(), ': pEqn=', pEqn)
                print(myName(), ': nEqn=', nEqn)
                print(myName(), ': eqn=', eqn)
        elif elType == 'i':  # Requesting the current through this source- must be an IVS or ICS or controlled source
            if CCircuit.elementExists(self.eList, sourceElement.getLabel()):   # Should always work
                elementLabel = sourceElement.getLabel()
                if not elementLabel[0].lower() == 'i':
                    pNode = self.getAddedNodeElementIndex(elementLabel)
                    if gVerbose > 1:
                        print(myName(), ': Using getAddedNodeElementIndex, The row for this current is ', pNode)
                    if pNode != -1:
                        if (pNode != -1 and pNode < self.nNodes):
                            eqn = iC[pNode-1]
                            if gVerbose > 1:
                                print(myName(), ': Looking for current, using node ', pNode)
                                print(myName(), ': eqn=', eqn)
                        else:
                            print(myName(), ':1 pNode ', pNode, ' >= nNodes ', self.nNodes)
                            print(myName(), ': Element ', elementLabel)
                    else:
                        pNode = self.findElementWithLabel(elementLabel)
                        if pNode is not None and pNode < self.nNodes:
                            eqn = iC[pNode-1]
                            if gVerbose > 1:
                                print(myName(), ': Looking for current, using node ', pNode)
                                print(myName(), ': eqn=', eqn)
                        else:
                            print(myName(), ':2 pNode ', pNode, ' >= nNodes ', self.nNodes)
                            print(myName(), ': Element ', elementLabel)
                else:   # Need the current through an ICS. Since this is part of the iColumn, the current
                        # should be part of the equation in the solutions. Just multiply by label.
                    eqn = sympy.symbols(elementLabel)
                    if gVerbose > 1:
                        print(myName(), ': Need current through an ICS, which is part of the iColumn.')
                        print(myName(), ': Just multiply by ICS name.')
                        print(myName(), ': ICS: eqn=', eqn)
            else:
                print(myName(), ': Element with label ', sourceElement.getLabel(), ' not found.')
                myExit(6)
        else:
            print(myName(), ': Unknown source equation requested- ', elType, '.')
            myExit(7)
        return eqn

    def isControlledSourceSensingVS(self, el):
        if gVerbose > 2:
            print(myName(), ': Checking element ', el.getLabel())
        for it in self.eList:
            isSensingIVS = it.getISenseLabel() == el.getLabel()
            if isSensingIVS:
                if gVerbose > 2:
                    print(myName(), ': Returning True for element ', el.getLabel())
                return True
        
        if gVerbose > 2:
            print(myName(), ': Returning False for element ', el.getLabel())
        return False
            