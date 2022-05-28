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

from math import sqrt
import sympy
import CElement
import Support

class CCircuit(object):
    '''
    classdocs
    '''
    #MAXNODES = 100
    
    @classmethod
    # Not using self.eList so that CFileReader can call this method and pass the eList it's 
    # constructing from the input file.
    def elementExists(self, eList, name):
        found = False
        for it in eList:
            if name == it.getLabel().upper() or \
                name == it.getLabel().lower() or \
                name == it.getLabel():
                found = True
                if Support.gVerbose > 0: #2
                    print(Support.myName(), ': found=', found, ' name=', name, ' lbl=', it.getLabel())
                break
            if Support.gVerbose  > 0: #2
                print(Support.myName(), ': found=', found, ' name=', name, ' lbl=', it.getLabel())
        return found

    def __init__(self, eList, inSource, outSource, freq, htmlFilename=''):
        '''
        I think the format for regular nodes and added nodes is:
        nodeIndex[0..(nNodes-1)]               length=nNodes
        addedNodeElements[0..(numAddedNodes-1)]    length=numAddedNodes
        '''
        self.eList = eList      # List of elements in the circuit
        self.newEList = []
        self.inputSource = inSource    # Input source element
        self.outputSource = outSource  # Output source element
        self.stimulus = None    # Label of the indep src that's the stimulus for the ckt.
        self.htmlFilename = htmlFilename
        self.freq = freq
        self.nNodes = 0         # Number of nodes in the circuit, including extras for unknown currents
        self.numAddedNodes = 0     # Number of extra nodes in the circuit that were added for unknown currents
        self.nodeIndex = []     # Contains the user nodes, index is the internal node
        self.addedNodeElements = []  # So we can find which element corresponds to each of the added nodes
        self.finishKMElements()
    
    def getStimulus(self): return self.stimulus
    def setStimulus(self, st): self.stimulus = st
    def getFreq(self): return self.freq
    def getEList(self): return self.eList
    
    def getNumOfNodes(self):
        if (Support.gVerbose > 3):
            print(Support.myName(), "size(nodes)=", len(self.nodeIndex),
                  "  size(numAddedNodes)=", len(self.addedNodeElements),
                  "  nNodes=", self.nNodes)
        return self.nNodes
    
    def setNumOfNodes(self, num): self.nNodes = num
    def getNumOfAddedNodes(self): return self.numAddedNodes
    def setNumOfAddedNodes(self, num): self.numAddedNodes = num
    def getAddedElements(self): return self.addedNodeElements
    def getUserNode(self, index): return self.nodeIndex[index]
    def getOutputSource(self): return self.outputSource
    def getInputSource(self): return self.inputSource
    
    def appendAddedNodeElement(self, ele, isAddedEle):
        if isAddedEle:
            ele.setIsAddedElement(isAddedEle)
            self.addedNodeElements.append(ele)
            self.nodeIndex.append(self.nNodes)
            self.nNodes += 1
    
    # Called after all elements have been read in by FileReader.
    def finishKMElements(self):
        for ele in self.eList:
            if ele.getEType() in 'km':
                # Save the original L1 & L2 values in the self. k or m element
                lbl1 = ele.getL1()
                iter1 = self.findElementWithLabel(lbl1)
                if iter1.valueIsSet():
                    val1 = iter1.getValue()
                else:
                    val1 = sympy.symbols(iter1.getLabel())
                ele.setOrgL1Value(val1)

                lbl2 = ele.getL2()
                iter2 = self.findElementWithLabel(lbl2)
                if iter2.valueIsSet():
                    val2 = iter2.getValue()
                else:
                    val2 = sympy.symbols(iter2.getLabel())
                ele.setOrgL2Value(val2)
                if Support.gVerbose > 2:
                    print(Support.myName(), "Element", ele.getLabel(), \
                          "  value=", ele.getValue(),
                          "  otherValue=", ele.getOtherValue() )
                    print(Support.myName(), "Ind1 is", lbl1, "value=", val1)
                    print(Support.myName(), "Ind2 is", lbl2, "value=", val2)

                # Saving m here just for the debugging output
                if ele.getEType() == 'k':
                    k = ele.getValue()
                    m = k * val1
                    ele.setOtherValue(m)
                else:   # eType = m, K=M/L1
                    m = ele.getValue()
                    k = m / val1
                    ele.setOtherValue(k)
                l1_new = val1 * (1-k)
                iter1.setValue(l1_new)
                l2_new = val2 * (1-k)
                iter2.setValue(l2_new)
                if Support.gVerbose > 1:
                    print(Support.myName(), 'For element', ele.getLabel(),
                          ', coupling inductors', ele.getL1(), 'and',
                          ele.getL2(), 'together:')
                    print(Support.myName(), 'set k=', k, '  M=', m, '  TR=', sqrt(val1/val2))
                    print(Support.myName(), 'L1 org:', ele.getOrgL1Value(),
                          '  now:', iter1.getValue())
                    print(Support.myName(), 'L2 org:', ele.getOrgL1Value(),
                          '  now:', iter2.getValue())   
                
                
    # True if at least 1 element specifies a value
    def anyValuesDefined(self):
        valuesDefined = False
        for element in self.eList:
            if element.valueIsSet():
                valuesDefined = True
                if Support.gVerbose  > 2:
                    print(Support.myName(), 'For element', element.getLabel(),
                          'valuesDefined=', valuesDefined)
                break
        return valuesDefined
    
    # True if all non-source elements have a value- ie, cefghlmrt
    def allValuesDefined(self):
        allDefined = True
        for element in self.eList:
            if element.getElementType() in element.getEWithValues():
                if not element.valueIsSet():
                    allDefined = False
                    if Support.gVerbose  > 2:
                        print(Support.myName(), 'With element ', element.getLabel(),
                              ' allDefined=', allDefined)
                    break
            if Support.gVerbose  > 2:
                print(Support.myName(), ': Checked element ', element.getLabel(),
                      ' allDefined=', allDefined)
        print("allValuesDefined: =", allDefined)
        return allDefined

    def getHTMLFilename(self): return self.htmlFilename
    
    def createIndexList(self):
        """Generate an array of the node numbers that are used. Zeroth entry is gnd. This
        is where the number of nodes required is determined
        
        1) Go through the eList. Make a list of all of the unique (user) node
            numbers in the input file
        2) Go through the eList again, this time only look for elements that need
            an extra node (or two) added. 
            A) For each one that does,
                a) Add it to the added nodes list
                b) Append nNodes to the node index
                c) Add 1 to nNodes.
                d) Create a voltage element with label 'i'+element label
                e) Set 'isAddedNodeElement=True 
                f) Append it to the added nodes list"""
        self.nNodes = 1
        extraNodes = 0      # Temp var to keep track of # added nodes in the 2nd loop below.
        #self.nodeIndex[0] = 0
        self.nodeIndex.clear()
        self.addedNodeElements.clear()
        self.nodeIndex.append(0)        # Ground
        for element in self.eList:
            self.addNode(element.getNode1())
            self.addNode(element.getNode2())

        newEList = self.eList.copy()
        tmpElement = CElement.CElement('v', 'i(v)', 0, 0, 0, 0, 0)
        # These elements need a node (variable in the matrix) added for the following reasons-
        # e- VCVS. Need a var for current through VS
        # f- CCCS. Need a var for current through CS
        # g- VCCS. Need a var for current through CS
        # h- CCVS. Need a var for current through CS, + another for the current through the VS.
        # t- Transformer. Need a var for the current through the primary windings.
        # v- IVS, need a var for the current through itself, iff it's not only for sensing
        #        current for a CCCS or CCVS. Which only leaves an input voltage source.
        for element in self.eList:
            etype = element.getElementType()
            if (Support.gVerbose > 1):
                print()
                print(Support.myName(), ':    checking element', element.getLabel())
            if (etype in 'efght') or (etype == 'v' and not
                        self.isControlledSourceSensingVS(element) ):
                #
                # Add one node (var)
                element.setSourceNode1(self.nNodes)
                self.appendAddedNodeElement(element, False)
                # From this, it looks like it only gets an iSenseLabel if it's an f, h or t type.
                # If e, g, or v, no iSense is needed. They all have already had an extra element
                # added.
                if etype in 'egv':
                    tmpElement = CElement.CElement('v', 'I'+element.getLabel(), 0, 0, 0, 0)
                else:
                    tmpElement = CElement.CElement('v', 'I'+element.getISenseLabel(), 0, 0, 0, 0)
                tmpElement.setSourceNode1(element.getSourceNode1())
                # Not sure if this line is needed
                #tmpElement.setISenseLabel(element.getLabel())
                self.appendAddedNodeElement(tmpElement, True)
                ##tmpElement.setIsAddedElement(True)
                if (Support.gVerbose > 2):
                    print(Support.myName(), ': Added node ', self.nNodes-1,
                          ' for element ', element.getLabel())
                    print('       label = ', element.getLabel())
                    print('       iSenseLabel = ', element.getISenseLabel())
                    print('       extraNodes=', extraNodes)
                    print('       size(addedNodeElements)=', len(self.addedNodeElements))

                newEList.append(tmpElement)
                extraNodes += 1
            
            if etype == 'h':
                # h- CCVS. Need var for current through the VS.
                element.setSourceNode2(self.nNodes)
                self.appendAddedNodeElement(element, False)
                if Support.gVerbose  > 2:
                    print(Support.myName(), ': Added 2nd extra node ', self.nNodes,
                          ' for element ', element.getLabel())
                #self.nodeIndex.append(self.nNodes)
                #self.nNodes += 1
                hElement = CElement.CElement('v', 'i'+element.getLabel(), 0, 0, 0, 0)
                hElement.setSourceNode2(element.getSourceNode2())
                self.appendAddedNodeElement(hElement, True)
                #hElement.setIsAddedElement(True)
                # Defaults for iSenseLabel & sourceNode1
                #self.addedNodeElements.append(hElement)
                newEList.append(hElement)
                extraNodes += 1
            
            if etype == 'm':
                # A var for the current through the primary
                element.setSourceNode1(self.nNodes)
                self.appendAddedNodeElement(element, False)
                #self.nodeIndex.append(self.nNodes)
                #self.nNodes += 1
                L1_Element = CElement.CElement('l', 'i'+element.getL1(), 0, 0, 0, 0)
                self.appendAddedNodeElement(L1_Element, True)
                #L1_Element.setIsAddedElement(True)
                #self.addedNodeElements.append(L1_Element)
                newEList.append(L1_Element)
                extraNodes += 1

                # A var for the current through the secondary
                element.setSourceNode2(self.nNodes)
                self.appendAddedNodeElement(element, False)
                #self.nodeIndex.append(self.nNodes)
                #self.nNodes += 1
                L2_Element = CElement.CElement('l', 'i'+element.getL2(), 0, 0, 0, 0)
                self.appendAddedNodeElement(L2_Element, True)
                #L2_Element.setIsAddedElement(True)
                #self.addedNodeElements.append(L2_Element)
                newEList.append(L2_Element)
                extraNodes += 1

        self.newEList = newEList
        self.setNumOfAddedNodes(extraNodes)
        if Support.gVerbose  > 0:
            print(Support.myName(), ":")
            print("    Summary ---------------------------------------------")
            print("       extraNodes=", extraNodes, "  len(addedNodeElements)=",
                  len(self.addedNodeElements) )
            print("       nNodes=", self.nNodes, "  len(nodeIndex)=",
                  len(self.nodeIndex) )
            print('    The nodeIndex is')
            print('      Internal    User')
            for i in range(self.nNodes-self.numAddedNodes):
                print('       ', i, '           ', self.nodeIndex[i])
            print('    There are', self.nNodes, 'nodes, including ground.')
            print('             ', self.numAddedNodes, 'nodes were added to account for sources.')
            print('    The added elements are (in user node numbers):')
            for i in range(self.numAddedNodes):
                addedEl = self.getAddedNodeElement(i)
                print('        ', addedEl.getLabel(), addedEl.getNode1(), addedEl.getNode2(), addedEl.getISenseLabel())
            print('***************************************')
            print('    New list is')
            for ele in self.newEList:
                ele.printElement()
            print(Support.myName(), ": End of summary ---------------------")
        return self.nNodes
            
    def addNode(self, number):
        if number != 0:     # Don't add the ground node to the list
            if number not in self.nodeIndex:
                self.nodeIndex.append(number)
                self.nNodes += 1
                return True
        return False
    
    def renumberNodes(self):
        if Support.gVerbose > 1:
            print(Support.myName(), ': eList before renumbering')
            for ele in self.eList:
                print(ele.getLabel(), ele.getNodes())

        renumberedList = self.eList
        for original, renumbered in zip(self.eList, renumberedList):
            if original.hasTwoNodes():
                if Support.gVerbose  > 2:
                    print('CCircuit::renumberNodes: twoNodes reverse lookup for nodes ',
                        original.getNode1(), ' and ', original.getNode2() )
                nd1 = self.reverseLookup(original.getNode1())
                errCode = self.reverseLookupErrorCheck(nd1, Support.myName(), original.getNode1(), 1)
                if errCode: return errCode

                nd2 = self.reverseLookup(original.getNode2())
                errCode = self.reverseLookupErrorCheck(nd2, Support.myName(), original.getNode2(), 1)
                if errCode: return errCode
                renumbered.setNodes12(nd1, nd2)
            
            elif original.hasTwoNodesAndLabel():
                if Support.gVerbose  > 2:
                    print('CCircuit::renumberNodes: twoNodesAndLabel reverse lookup for nodes ',
                        original.getNode1(), ', ', original.getNode2() )
                        #original.getNode3(), ' and ', original.getNode4())
                # Has to be a better way to handle this.
                ond1 = original.getNode1()
                nd1 = self.reverseLookup(ond1)
                errCode = self.reverseLookupErrorCheck(nd1, Support.myName(), ond1, 1)
                if errCode: return errCode
                
                ond2 = original.getNode2()
                nd2 = self.reverseLookup(ond2)
                errCode = self.reverseLookupErrorCheck(nd1, Support.myName(), ond2, 1)
                if errCode: return errCode

                renumbered.setNodes12(nd1, nd2)
            
            elif original.hasFourNodes():
                if Support.gVerbose  > 2:
                    print('CCircuit::renumberNodes: fourNodes reverse lookup for nodes ',
                        original.getNode1(), ', ', original.getNode2(), ', ',
                        original.getNode3(), ' and ', original.getNode4())
                ond1 = original.getNode1()
                nd1 = self.reverseLookup(ond1)
                errCode = self.reverseLookupErrorCheck(nd1, Support.myName(), ond1, 1)
                if errCode: return errCode
                
                ond2 = original.getNode2()
                nd2 = self.reverseLookup(ond2)
                errCode = self.reverseLookupErrorCheck(nd1, Support.myName(), ond2, 1)
                if errCode: return errCode
                
                ond3 = original.getNode3()
                nd3 = self.reverseLookup(ond3)
                errCode = self.reverseLookupErrorCheck(nd1, Support.myName(), ond3, 1)
                if errCode: return errCode
                
                ond4 = original.getNode4()
                nd4 = self.reverseLookup(ond4)
                errCode = self.reverseLookupErrorCheck(nd1, Support.myName(), ond4, 1)
                if errCode: return errCode
                
                renumbered.setNodes1234(nd1, nd2, nd3, nd4)
        
        self.eList = renumberedList
        if Support.gVerbose > 1:
            print(Support.myName(), ': Renumbered eList')
            for ele in self.eList:
                print(ele.getLabel(), ele.getNodes())
        
        # Take care of the solve elements as well
        if Support.gVerbose  > 1:
            print('CCircuit::renumberNodes: Renumbering output source nodes')
        err = self.renumberSourceNodes(self.outputSource)
        if err: return err
        if Support.gVerbose  > 1:
            print(Support.myName(), ': Renumbering input source nodes')
        err = self.renumberSourceNodes(self.inputSource)
        return err
    
    def renumberSourceNodes(self, source):
        if source.getElementType() == 'v':
            if Support.gVerbose  > 2:
                print(Support.myName(),
                      ' node1=', source.getUserNode1(),
                      ' node2=', source.getUserNode2())
            n1 = self.reverseLookup(source.getUserNode1())
            errCode = self.reverseLookupErrorCheck(n1, Support.myName(), source.getUserNode1(), 3)
            if errCode: return errCode
            n2 = self.reverseLookup(source.getUserNode2())
            errCode = self.reverseLookupErrorCheck(n2, Support.myName(), source.getUserNode2(), 4)
            if errCode: return errCode
            if Support.gVerbose  > 2:
                print('                               Renumbering source node ', source.getLabel(),
                      ' to nodes ', n1, ', ', n2)
            source.setNodes12(n1, n2)
        return 0

    def reverseLookupErrorCheck(self, node2Check, methodName, failed_node, errCode):
        if node2Check == -1:
            txt = methodName+': The node '+str(failed_node)+' does not exist in the circuit. Exiting.'
            print(txt)
            Support.myExit(errCode, txt)
            return errCode
        else:
            return 0

    # Return the internal node given the user node. If the user node isn't found, -1 is returned.
    def reverseLookup(self, val):
        if val in self.nodeIndex:
            return self.nodeIndex.index(val)
        else:
            return -1

    def printFHElements(self):
        if len(self.eList) == 0:
            print("No 'F' or 'H' elements found.")
        else:
            for it in self.eList:
                if it.hasTwoNodesAndLabel():
                    n1 = it.getNode1()
                    n2 = it.getNode2()
                    print("{0:s} {1:d} {2:d} {3:s}".format(it.getElementType(), n1, n2, it.getISenseLabel() ))

    # the numbers of nodes has been determined and been renumbered, look for F and H elements and fill
    # in the controlling source node numbers.
    def setControllingSourceNodes(self):
        if Support.gVerbose > 1:
            print(Support.myName(), "Before setControllingSourceNodes:")
            self.printFHElements()
        theControllingElement = CElement.CElement('c', '', 0, 0, 0, 0)
        for it in self.eList:
            if it.hasTwoNodesAndLabel():
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
                if Support.gVerbose  > 1:
                    print('CCircuit::setControllingSourceNodes: Added controlling nodes for element ', it.getLabel())
                if Support.gVerbose  > 2:
                    print('CCircuit::setControllingSourceNodes:    Controlling element is ', it.getISenseLabel())
                    print('                                        Controlling nodes are ', cn1, ' and ', cn2)                
        if Support.gVerbose > 1:
            print(Support.myName(), "After setControllingSourceNodes:")
            self.printFHElements()

    def findElementWithLabel(self, lbl):
        for it in self.eList:
            if it.getLabel() == lbl:
                return it
        print('CCircuit::findElementWithLabel: ***** Error: Label ', lbl, ' was not found.')
        return None
    
    def getNodeElementIndex(self, label):
        i = self.nNodes-1
        print(Support.myName(), " Looking for an element with label ", label)
        for it in self.eList:
            lbl = it.getLabel()
            print('      i=', i, ' this label=', lbl)
            if label == lbl:
                print('Found!!')
                return i
            else:
                i -= 1
        print(Support.myName(), label, ' was not found in the normal element list')
        return None
    
    def getAddedNodeElement(self, index):
        return self.addedNodeElements[index]
    
    def getAddedNodeElementIndex(self, label):
        i = self.getNumOfAddedNodes()
        if Support.gVerbose  > 0:
            print(Support.myName(), ': Searching for iSense label "(I)', label, '", there are ', i, 'added nodes')

        for it in self.addedNodeElements:
            lbl = it.getLabel()
            if lbl == 'I'+label:
                if Support.gVerbose > 2:
                    print(Support.myName(), ': label =', lbl, ', match!')
                return self.nNodes-i
            else:
                if Support.gVerbose > 2:
                    print(Support.myName(), ': label =', lbl, ', not a match')
                i -= 1
        print(Support.myName(), ': ***** Error, label ', label, ' was not found')
        return None
    
    def regurgitate(self, useInternalNodeNumbers=True):
        if Support.gVerbose  > 0:
            if useInternalNodeNumbers:
                print(Support.myName(), ': Dumping eList contents, internal node numbers.')
            else:
                print(Support.myName(), ': Dumping eList contents, user node numbers.')
            print("    frmt eT Lbl  N1   N2   N3   N4   val   src1    src2    iSenseLbl")
            for it in self.eList:
                if useInternalNodeNumbers:
                    it.printElement()
                else:
                    it.printElementU()
            if len(self.getAddedElements()) != 0:
                print("Added elements")
                for it in self.getAddedElements():
                    if useInternalNodeNumbers:
                        it.printElement()
                    else:
                        it.printElementU()
            else:
                print('No added element')
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
            print(Support.myName(), ': End of file dump')
            
    def regurgitateMore(self, internalNodes=True):
        if internalNodes:
            print(Support.myName(), ': Dumping eList contents, internal node numbers.')
        else:
            print(Support.myName(), ': Dumping eList contents, user node numbers.')
        print()
        print("'frmt' column key: xx z")
        print('    xx                        z')
        print('---------------------------------------------------')
        print('    2N    Two nodes.          N    Not an added element')
        print('    4N    Four nodes          Y    Is an added element')
        print('    2L    Two labels')
        print('    NL    Two nodes + label')
        print()
        print(" frmt eT Lbl  N1   N2   N3   N4   val   src1    src2    iSn")
        #        fmt   eType  Label     ND1     ND2     ND3     ND4    val    src  iSense   isAddedEle

        for it in self.getEList():
            it.dumpElement(internalNodes)
        if len(self.getAddedElements()) != 0:
            print('Added elements:')
            for it in self.getAddedElements():
                it.dumpElement(internalNodes)
        else:
            print('No elements have been added')
            
    def calculateVorIEqn(self, iC, sourceElement):
        elType = sourceElement.getElementType()
        if Support.gVerbose  > 0:
            if elType == 'i':
                print(Support.myName(), ': Looking for a current:')
            else:
                print(Support.myName(), ': Looking for a voltage:')
            sourceElement.printElementS()
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
            if Support.gVerbose  > 1:
                print(Support.myName(), ': Calculating V(', pNode, ')-V(', nNode, ')')
                print('                pEqn=', pEqn)
                print('                nEqn=', nEqn)
                print('                eqn=', eqn)
        elif elType == 'i':
            # Requesting the current through a source- must be an IVS, ICS, CCCS (F) or CCVS (H)
            #    IVS: vname    Look in an added row for 
            #    ICS: iname
            #    CCCS: fname
            #    CCVS: hname
            elementLabel = sourceElement.getLabel()
            if CCircuit.elementExists(self.eList, elementLabel):
                if not elementLabel[0] == 'i':
                    pNode = self.getAddedNodeElementIndex(elementLabel)
                    if Support.gVerbose  > 1:
                        print(Support.myName(), ': Looking for element label (I)', elementLabel)
                        print(Support.myName(), ': Using getAddedNodeElementIndex, looking for current in row ', pNode)

                    if pNode is not None and pNode < self.nNodes:
                        eqn = iC[pNode-1]
                        if Support.gVerbose  > 2:
                            print(Support.myName(), ': Looking for current, using node ', pNode)
                            print(Support.myName(), ': eqn=', eqn)
                    else:
                        if Support.gVerbose  > 2:
                            print(Support.myName(), ': pNode=None', pNode, ' numOfNodes=', self.getNumOfNodes(), ' numAddedNodes=', self.getNumOfAddedNodes())
                        cntrldEle = self.getAddedNodeElement(pNode-(self.getNumOfNodes()-self.getNumOfAddedNodes())-1)
                        if cntrldEle.getElementType() == 'f':
                            sym = sympy.symbols(cntrldEle.getLabel())
                            eqn = iC[pNode-1] / sym
                            if Support.gVerbose  > 2:
                                print(Support.myName(), ': Found current, eqn=', eqn)
                            return eqn
                        elif cntrldEle.getElementType() == 'h':
                            eqn = iC[pNode]
                            if Support.gVerbose  > 2:
                                print(Support.myName(), ': Found current in row', pNode+1, '  eqn=', eqn)
                            return eqn
                        else:
                            if Support.gVerbose  > 2:
                                print(Support.myName(), ': Using findElementWithLabel, looking for current in row ', pNode)
                            pNode = self.findElementWithLabel(elementLabel)
                            if pNode is not None and pNode < self.nNodes:
                                eqn = iC[pNode-1]
                                if Support.gVerbose  > 2:
                                    print(Support.myName(), ': Found current in row ', pNode)
                                    print('                            eqn=', eqn)
                            else:
                                print(Support.myName(), ":2 pNode ", pNode, " >= nNodes ", self.nNodes)
                                print("                            Couldn't find element", elementLabel)
                                return Support.myExit(6)
                    
                else:   # Need the current through an ICS. Since this is part of the iColumn, the current
                        # should be part of the equation in the solutions. Just multiply by label.
                    eqn = sympy.symbols(elementLabel)
                    if Support.gVerbose  > 1:
                        print(Support.myName(), ': Need current through an ICS, which is part of the iColumn.')
                        print('                            Just use the ICS name.')
                        print('                            ICS: eqn=', eqn)
            else:
                print(Support.myName(), ': Element with label ', sourceElement.getLabel(), ' not found.')
                return Support.myExit(6)
        else:
            print(Support.myName(), ': Unknown source equation requested- ', elType, '.')
            return Support.myExit(7)
        return eqn

    def isControlledSourceSensingVS(self, el):
        if Support.gVerbose  > 2:
            print(Support.myName(), ': Checking element ', el.getLabel())
        for it in self.eList:
            isSensingIVS = it.getISenseLabel() == el.getLabel()
            if isSensingIVS:
                if Support.gVerbose  > 2:
                    print(Support.myName(), ': Returning True for element ', el.getLabel())
                return True
        
        if Support.gVerbose  > 2:
            print(Support.myName(), ': Returning False for element ', el.getLabel())
        return False

