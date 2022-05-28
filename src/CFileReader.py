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
Created on Nov 26, 2016

@author: Tom Spargo
'''
"""
# From the original C++ program:
ReadFile.h
 *  Equation Solver
 *
 *  Created by Thomas on 6/13/07.
 *  Copyright 2007. All rights reserved.
 *

# End of C++ program snippet
"""

from sys import platform
import Support
import CElement
import CSimpList
from CCircuit import CCircuit
from CReadEquation import CReadEquation
import ntpath
import engineering_notation as eno


class CFileReader(object):
    """Reads and parses a circuit file. Creates a CCircuit object from the circuit file."""
    
    def __init__(self, filePath, computer):    
#         if computer == 'Macbook':   # The new Macbook
#             circuitPath = '/Users/Thomas/Programming/eclipse-workspace/ESGui-Python/Circuit files/'
#         elif computer == 'iMac':
#             circuitPath = '/Users/Thomas/Programming/Programs/Eqn_Solver/Circuit files/'
#         elif computer == 'MacPC':
#             circuitPath = '/Users/Tom/Documents/Windows/Eqn_Solver/Circuit files/'
#         elif computer == 'iMacPC':
#             circuitPath = '/Users/Thomas/Programming/Programs/Circuit files/'
#         else:
#             print(' ***** Huh? ******')
#             Support.myExit(8)
#         self.circuitPath = circuitPath
        
        self.eList = []
        # True if there's at least one element with a value specificed.
        self.definesValues = False   
        self.htmlFilename = ''
        self.testAnswer = 0
        self.inputSource = CElement.CElement('c', 'c123', 0, 0, 0, 0)
        self.outputSource = CElement.CElement('c', 'c124', 0, 0, 0, 0)
        self.filePath = filePath
        self.frq = None
        self.simpList = CSimpList.SimpList()
        self.subList = []

    def readFile(self):
        if Support.gVerbose > 0:
            print(Support.myName(), ': Start CFileReader')
            print(Support.myName(), ':  Reading ', self.filePath)
        
        try:
            f = open(self.filePath, 'r')
        except IOError:
            print('***** Error, could not find the file, ', self.filePath)
            Support.myExit(27)

        foundSolve = False
        # Read the file one line at a time, this allows readEquationFromOpenFile to
        # also read from the file.
        while (1):
            line = f.readline()
            if not line:
                break
            if Support.gVerbose > 1:
                print(Support.myName(), ': Parsing line:', line[:-1])
            spl = line.strip().split()
            if Support.gVerbose > 2:
                print(Support.myName(), ': split line:', spl)
            if spl == []:     # if a blank line
                pass
            ###########################################################
            # Comments
            elif spl[0][0] in ';*':   # Comments
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Found a comment.')
            ###########################################################
            # Answer
            elif spl[0].lower() in ['answer', 'a', 'ans']:
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Found answer, calling readEquationFromOpenFile')
                eqnReader = CReadEquation(line)
                self.testAnswer = eqnReader.readEquationFromOpenFile(f)
            ###########################################################
            # Output
            elif spl[0].lower() in ['output', 'o']:
                # If no html name is specified, use the file name w/o extension and add
                # the '.html' extension. If a name is specified, remove any extension
                # add .html.
                if len(spl) > 1:
                    root = spl[1]
                else:
                    root = ntpath.basename(self.filePath)
                base = root.split('.')[0]
                print('self.filePath', self.filePath, ' base=', base)
                if platform == 'win32':
                    self.htmlFilename = base + '.htm'
                else:
                    self.htmlFilename = base + '.html'
                if Support.gVerbose > 2:
                    print(Support.myName(), 'htmlFilename=', self.htmlFilename)
            ###########################################################
            # Solve
            elif spl[0].lower() in ['solve', 'so']:
                if not foundSolve:
                    foundSolve = True
                    solveLine = line
                    if Support.gVerbose > 1:
                        print(Support.myName(), ': Found solve statement.')
                else:
                    print(Support.myName(), \
                          ': Another solve statement found; this one will be ignored:', line)
            ###########################################################
            # Simplify
            # Always put simpList entries in the order [smaller, bigger]
            elif spl[0].lower() in ['si', 'sim', 'simp', 'simplify']:
                if spl[2] in ['<', '<<']:
                    rel = CSimpList.Relation(spl[1], spl[3])
                    #self.simpList.appendRelation(spl[1], spl[3])
                elif spl[2] in ['>', '>>']:
                    rel = CSimpList.Relation(spl[3], spl[1])
                    #self.simpList.appendRelation(spl[3], spl[1])
                else:
                    print(Support.myName(), \
                          ': Simplify command with unknown operator:', spl[2])
                    Support.myExit(29)
                self.simpList.appendRelation(rel)
                if Support.gVerbose > 2:
                    print(Support.myName(), ': Added simplify command ', rel.printRelation(), ' to simpList.')

            ###########################################################
            # Substitute
            # Find spl[1] and replace with spl[2]
            elif spl[0].lower() in ['su', 'sub', 'subs', 'substitute']:
                self.subList.append([spl[1], spl[2]])
                if Support.gVerbose > 2:
                    print(Support.myName(), ': substitute: replace ', spl[1], ' with ', spl[2] )

            ###########################################################
            # Freq
            elif spl[0].lower() in ['freq', 'frequency']:
                self.frq = float(eno.EngNumber(spl[1]))
                if Support.gVerbose > 2:
                    print(Support.myName(), ': Found freq:', self.frq)
            ###########################################################
            # All the other elements
            elif spl[0][0].lower() in CElement.CElement.getElementTypes():
                tmpElement = self.parseElement(spl)
                self.eList.append(tmpElement)
                if Support.gVerbose > 2:
                    print(Support.myName(), ': Added element ', tmpElement.getLabel(), ' to the eList.')
            ###########################################################
            # Something unknown
            else:   # Unknown element found
                print(Support.myName(), ': Unknown element found:', line, '. Exiting.')
                Support.myExit(10)
            if Support.gVerbose > 2:
                print()
        f.close()
        self.verifyIVSforFandHElements(self.eList)
                    
        if foundSolve:
            if Support.gVerbose > 2:
                print(Support.myName(), ': Parsing solve statement ', solveLine)
                spl = solveLine.strip().split()
                for it in range(len(spl)):
                    print('         solve[', it, ']: ', spl[it])
            self.parseSolveStatement(solveLine)
        else:
            print(Support.myName(), ': Solve element not found, this is required. Exiting.')
            Support.myExit(9)
            
        if Support.gVerbose > 2:
            print(Support.myName(), ': Size(eList)=', len(self.eList))
            print(Support.myName(), ': Size(simpList)=', self.simpList.size())
            print(Support.myName(), ': Size(subList)=', len(self.subList))
            print(Support.myName(), ': freq=', self.frq)
            print(Support.myName(), ': HTML filename=', self.htmlFilename)
            print(Support.myName(), ': Filepath=', self.filePath)  
            print(Support.myName(), ': I/P source=', self.inputSource.printElement())  
            print(Support.myName(), ': O/P source=', self.outputSource.printElement())  
                     
    def getEList(self):
        return self.eList
    
    def getHTMLFilename(self):
        return self.htmlFilename
    
    def getCircuitPath(self):
        return self.filePath
    
    def getTestAnswer(self):
        return self.testAnswer
    
    def getInputSource(self):
        return self.inputSource
    
    def getOutputSource(self):
        return self.outputSource
    
    def getSimpList(self):
        return self.simpList
    
    def getSubList(self):
        return self.subList
    
    def getFreq(self):
        return self.frq
    
    def valuesDefined(self):
        return self.definesValues
    
    # parse source, if found. Format: solve output input
    # V/V: i i i i    size=5
    # I/V: a i i      size=4
    # V/I: i i a      size=4
    # I/I: a a        size=3
    # The input/output for the solve statement are saved as elements. If a voltage, the nodes are saved and the element
    # type is set to etV. If a current is needed, the label of the element whose current is desired is saved and the
    # element type is set to etI.
    # The label of any voltage element(s) is set to the default "Input V" or "Output V".
    def parseSolveStatement(self, solveLine):
        splt = solveLine.strip().split()
        # Identifies which indexes should hold node numbers and therefore should be checked
        #frm = [0, 0, 0, 0, 1, 2, 1]
        #to_ = [0, 0, 0, 0, 3, 4, 5]
        #for ii in range(frm[len(splt)], to_[len(splt)]):
        #    try:
        #        int(splt[ii])
        #    except ValueError:
        #        print Support.myName(), ': Error, nodes must be numeric:', splt.join()
        #        Support.myExit(11)
        if Support.gVerbose > 2:
            print(Support.myName(), ': splt=', splt)
        if len(splt) == 5:    # V/V
            self.outputSource.setLabel('Output V')
            self.outputSource.setUserNodes12(int(splt[1]), int(splt[2]))
            self.outputSource.setElementType('v')
            self.inputSource.setLabel('Input V')
            self.inputSource.setUserNodes12(int(splt[3]), int(splt[4]))
            self.inputSource.setElementType('v')
            if Support.gVerbose > 1:
                print(Support.myName(), ': Output set to voltage, input set to voltage')
                print(Support.myName(), ': Output= (', self.outputSource.getUserNode1(), ', ', \
                                                self.outputSource.getUserNode2(), '), Input= (', \
                                                self.inputSource.getUserNode1(), ', ', \
                                                self.inputSource.getUserNode2(), ') (user node numbers).')
        
        elif len(splt) == 4:  # I/V or V/I
            # Use the first arg to determine which one, I/V or V/I
            try:
                int(splt[1])    # If no error, it's V/I
                # Make sure the specified current sensing source exists
                if not CCircuit.elementExists(self.eList, splt[3]):
                    print(Support.myName(), ': Error- Solve statement, V/I case, used with a source that does not')
                    print(Support.myName(), '  exist:', splt[3], '. Exiting.')
                    Support.myExit(13)
                self.outputSource.setLabel('Output V')
                self.outputSource.setUserNodes12(int(splt[1]), int(splt[2]) )
                self.outputSource.setElementType('v')
                self.inputSource.setLabel(splt[3])
                self.inputSource.setElementType('i')
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Output set to voltage, input set to current')

            except ValueError:  # Must be I/V
                # Make sure the specified current sensing source exists
                if not CCircuit.elementExists(self.eList, splt[1]):
                    print(Support.myName(), ': Error- Solve statement, I/V case, used with a source that does not')
                    print(Support.myName(), '  exist:', splt[1], '. Exiting.')
                    Support.myExit(14)
                self.outputSource.setLabel(splt[1])
                self.outputSource.setElementType('i')
                self.inputSource.setLabel('Input V')
                self.inputSource.setUserNodes12(int(splt[2]), int(splt[3]) )
                self.inputSource.setElementType('v')
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Output set to current, input set to voltage')

        elif len(splt) == 3:  # I/I
            if not CCircuit.elementExists(self.eList, splt[1]):
                print(Support.myName(), ': Error- Solve statement, I/I case, used with a source that does not')
                print(Support.myName(), '  exist:', splt[1], '. Exiting.')
                Support.myExit(15)
            if not CCircuit.elementExists(self.eList, splt[2]):
                print(Support.myName(), ': Error- Solve statement, I/I case, used with a source that does not')
                print(Support.myName(), '  exist:', splt[2], '. Exiting.')
                Support.myExit(16)
            self.outputSource.setLabel(splt[1])
            self.outputSource.setElementType('i')
            self.inputSource.setLabel(splt[2])
            self.inputSource.setElementType('i')
            if Support.gVerbose > 1:
                print(Support.myName(), ': Output set to current, input set to current.')
        
        else:
            print(Support.myName(), ': Error- Solve statement found with incorrect syntax.')
            Support.myExit(12)

    # V/V:    e1 1 2 3 4 [e]    size=5 or 6
    # V/I:    gm 1 2 3 4 [g]    size=5 or 6
    # I/V:    hw 1 2 vs  [h]    size=4 or 5
    # I/I:    f1 1 2 vs  [f]    size=4 or 5
    # CILRV:  xa 1 2 [v]        size=3 or 4
    def parseElement(self, splt):
        eType = splt[0][0].lower()
        if Support.gVerbose > 2:
            print(Support.myName(), ': Parsing element type ', eType)
        if eType in 'cilrv':
            # Get the element label and two connecting nodes
            if len(splt) < 3:
                print(Support.myName(), ': Error- This element requires two nodes to be specified.')
                Support.myExit(17)
            else:
                try:
                    nodeP = int(splt[1])
                    nodeN = int(splt[2])
                    if len(splt) == 4:
                        if eType not in 'iv':
                            value = splt[3]
                        else:
                            print('Ignoring value for element ', splt[0])
                            value = None
                    else:
                        value = None
                    tempElement = CElement.CElement(eType, splt[0], nodeP, nodeN, 0, 0, value)
                    
                except ValueError:
                    print(Support.myName(), ': Error- nodes must be numeric. Exiting.')
                    Support.myExit(17)
        elif eType in 'eg':     # VCVS or VCCS
            if len(splt) < 5:
                print(Support.myName(), ': Error- This element requires four nodes to be specified. Exiting.')
                Support.myExit(18)
            else:
                try:
                    nodeP = int(splt[1])
                    nodeN = int(splt[2])
                    nodeCP = int(splt[3])
                    nodeCN = int(splt[4])
                    if len(splt) == 6:
                        value = splt[5]
                    else:
                        value = None
                    tempElement = CElement.CElement(eType, splt[0], nodeP, nodeN, nodeCP, nodeCN, value)
                except ValueError:
                    print(Support.myName(), ': Error- nodes must be numeric. Exiting.')
                    Support.myExit(19)
        elif eType in 'fh':     # CCCS or CCVS
            if len(splt) < 4:
                print(Support.myName(), ': Error- This element requires two nodes and a voltage source name. Exiting.')
                Support.myExit(20)
            elif not splt[3][0].lower() == 'v':
                print(Support.myName(), ': Error- The current sensing element must be a voltage source. Exiting.')
                Support.myExit(21)
            else:
                try:
                    nodeP = int(splt[1])
                    nodeN = int(splt[2])
                    if len(splt) == 5:
                        value = splt[4]
                    else:
                        value = None
                    tempElement = CElement.CElement(eType, splt[0], nodeP, nodeN, 0, 0, value)
                    tempElement.setISenseLabel(splt[3])
                except ValueError:
                    print(Support.myName(), ': Nodes must be numeric. Exiting.')
                    Support.myExit(22)
        else:
            print(Support.myName(), ': Found an unknown element: ', splt[0], ', skipping this line.')
        return tempElement

    # Make sure the IVS's in the F and H elements exist in the eList
    def verifyIVSforFandHElements(self, eList):
        for element in eList:
            if element.getElementType == 'f' or element.getElementType() == 'h':
                if not CCircuit.elementExists(eList, element.getLabel() ):
                    print(Support.myName(), ': An "F" or "H" element has referenced a voltage source')
                    print(Support.myName(), '  that does not exist: Exiting.')
                    print(Support.myName(), '  Element:', element.getLabel(), ', source:', element.getISenseLabel())
                    Support.myExit(23)

"""
  ReadFile.h
 *  Equation Solver
 *
 *  Created by Thomas on 6/13/07.
 *  Copyright 2007. All rights reserved.
 *
 *********************************************************************************
    Reads a SPICE type input text file. Nodes can only be integers. Element types
 can be upper or lower case, but are restricted to:
    r: resistor
        r22 2 1
    c: capacitor
        c11 55 2
    l: inductor
        l54 23 0
    v: ac voltage source. Positive current flows into node 
        vin 10 0
    i: ac current source. Positive current flows into node 1 and out of node 10.
        Arrow points to node 10.
        iin 1 10
    e: voltage controlled voltage source
        esrc 1 0 5 6
        Adds a VCVS between nodes 1 and 0, controlled by the voltage between nodes 5 and 6.
    f: current controlled current source. Positive current flows into node 5 and out of node 4
        Arrow points to node 4.
        f1 5 4  vs
        Adds a CCCS between nodes 5 and 4, controlled by the current through the IVS 'vs'.
    g: voltage controlled current source. Positive current flows into node 2 and out of node 10
        Arrow points to node 10.
        g1 2 10 4 5
        Adds a VCCS between nodes 0 and 10, controlled by the voltage between nodes 4 and 5.
    h: current controlled voltage source
        h2 4 3 Vsense
        Adds a CCVS between nodes 4 and 3, controlled by the current through the IVS 'Vsense'.
    so)lve: specifies what to solve for. Only one solve statement is allowed per input file. The output is
        specified first, then the input. Voltages must be specified with both the +tive and -tive nodes.
        solve vin iin      Solve for current gain, i(vin)/i(iin)
        solve vin 10 0     Solve for transadmittance, i(vin)/v(10,0)
        solve 10 2 iin     Solve for transresistance, v(10,2)/i(iin)
        solve 10 2 10 0    Solve for voltage gain, v(10,2)/v(10,0)
    o)utput: Outputs the results into an html file for easier reading. Only one output statement
       is allowed per input file.
        ouput results.html
        ouput Zin.htm
    ; or *: specifies a comment line, can be used anywhere in a line
    a)answer:  The answer to the solve statement is in the following three lines (making a CRational). This is part of the unit
        testing and isn't meant to be part of the normal functionality.
"""
'''
     Added 4/28/2019
     su)b: Substitude one expression for another. Such as Re*gm = Beta, so:
         sub Re*gm Beta
         Anyplace that Re*gm is found, it is removed and Beta is put in. This works
         even if there are other variables in between, such as gm*C1*L1*Re.
'''
