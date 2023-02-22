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
"""
********************************************************************************
****** 3/24/2020 Added a check to find and save the stimulus for the circuit.
********************************************************************************

*** 2/14/2023
Adapted code to use implicit IVS for current sensing.
Error codes that are now not used: 20, 21, 23, 24
"""
from re import split
from sys import platform
import Support
import CElement as ce
import CSimpList
import CCircuit 
import CReadEquation as CReadEquation
import ntpath
import engineering_notation as eno

class CFileReader(object):
    """Reads and parses a circuit file."""
    
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
        # True if there's at least one element with a value specified.
        self.definesValues = False   
        self.htmlFilename = ''
        self.testAnswer = 0
        self.theCircuit = None
        self.inputSource = ce.CElement('c', 'c123', 0, 0, 0, 0)
        self.outputSource = ce.CElement('c', 'c124', 0, 0, 0, 0)
        self.filePath = filePath
        self.frq = None
        self.simpList = CSimpList.SimpList()
        self.subList = []   
        self.theOrgLines = []
        self.theLines = []
        self.labelDict = {}
        self.has_k_or_m = False
        self.stimulus = None

    def getEList(self): return self.eList
    def getHTMLFilename(self): return self.htmlFilename
    def getCircuitPath(self): return self.filePath
    def getTestAnswer(self): return self.testAnswer
    def getInputSource(self): return self.inputSource
    def getOutputSource(self): return self.outputSource
    def getSimpList(self): return self.simpList
    def getSubList(self): return self.subList
    def getFreq(self): return self.frq
    def valuesDefined(self): return self.definesValues
    def getStimulus(self): return self.stimulus

    def setupHTML_output(self, spl):
        # If no html name is specified, use the file name w/o extension and add
        # the '.html' extension. If a name is specified, remove any extension and
        # add .html.
        if len(spl) > 1:
            root = spl[1]
        else:
            root = ntpath.basename(self.filePath)
        base = root.split('.')[0]
        print('self.filePath=', self.filePath, ' base=', base)
        if platform=='win32':
            self.htmlFilename = base + '.htm'
        else:
            self.htmlFilename = base + '.html'
        if Support.gVerbose > 2:
            print(Support.myName(), 'htmlFilename=', self.htmlFilename)

    def processInputFile(self):
        """Make a dictionary to go from all lowercase labels to the original label versions,
        used only when printing results. Removes all blank and comment lines."""
        theLines = []       # all lowercase
        for line in self.theOrgLines:
            ln = line.strip()
            if ln != '':
                spl = ln.split()
                if spl[0] not in '*;':
                    if Support.gVerbose > 2:
                        print("len(spl)={0:d}  spl[0]={1:s}".format(len(spl), spl[0]))
                    #if len(spl)==0 or spl[0] == []:
                    lbl_org = ln.split()[0]
                    self.labelDict[lbl_org.lower()] = lbl_org
                    theLines.append(ln.lower())
        return theLines

    def readFile(self):
        if Support.gVerbose > 0:
            print('\n\n')
            print('**********************************************************')
            print(Support.myName(), ': Start CFileReader. Reading ', self.filePath)
        try:
            with open(self.filePath) as f:
                self.theOrgLines = f.readlines()
        except IOError:
            print('***** Error, could not find the file, ', self.filePath)
            return Support.myExit(27)
        self.theLines = self.processInputFile()
        return 0

    def readFileAndParse(self, aCircuit):
        self.theCircuit = aCircuit
        err = self.readFile()
        if err:
            return err

        foundSolve = False
        self.has_k_or_m = False
        inx = 0
        while inx < len(self.theLines):
            line = self.theLines[inx]
            if Support.gVerbose > 1:
                print(Support.myName(), ': Parsing line:', line)
            spl = line.split()
            if len(spl) == 0:
                inx += 1
                continue
            # The first letter group in this line, the element type & label, Vin, Cload, solve, etc.
            typ = spl[0]
            if Support.gVerbose > 2:
                print(Support.myName(), ': split line:', spl, ':  type=', typ[0])
            if typ == []:
                inx += 1
                continue
            ###########################################################
            # Comments
            elif typ[0] in ';*':   # Comments
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Found a comment.')
            ###########################################################
            # Answer
            elif typ in ['answer', 'a', 'ans']:
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Found answer, calling readEquationFromOpenFile')
                eqnReader = CReadEquation.CReadEquation(self.theLines)
                inx, self.testAnswer = eqnReader.readEquationFromList(inx)
                continue
            ###########################################################
            # Output
            elif typ in ['output', 'o']:
                self.setupHTML_output(spl)
            ###########################################################
            # Solve
            elif typ in ['solve', 'so']:
                if not foundSolve:
                    foundSolve = True
                    solveLine = line
                    if Support.gVerbose > 1:
                        print(Support.myName(), ': Found solve statement.')
                else:
                    print(Support.myName(),
                          ': Another solve statement found; this one will be ignored:', line)
            ###########################################################
            # Simplify
            # Always put simpList entries in the order [smaller, bigger]
            elif typ in ['si', 'sim', 'simp', 'simplify']:
                rel = CSimpList.Relation(spl[1], spl[2], spl[3])
                self.simpList.appendRelation(rel)
                if Support.gVerbose > 2:
                    print(Support.myName(), ': Added simplify command to simpList:')
                    rel.printRelation()

            ###########################################################
            # Substitute
            # Find spl[1] and replace with spl[2]
            elif typ in ['su', 'sub', 'subs', 'substitute']:
                self.subList.append([spl[1], spl[2]])
                if Support.gVerbose > 2:
                    print(Support.myName(), ': substitute: replace ', spl[1], ' with ', spl[2] )

            ###########################################################
            # Freq
            elif typ in ['freq', 'frequency']:
                self.frq = float(eno.EngNumber(spl[1]))
                if Support.gVerbose > 2:
                    print(Support.myName(), ': Found freq:', self.frq)
            ###########################################################
            # All the other elements
            elif typ[0] in ce.CElement.getETypes():
                tmpElement = self.parseElement(spl)
                if type(tmpElement) is not int:
                    self.getEList().append(tmpElement)
                    if Support.gVerbose > 2:
                        print(Support.myName(), ': Added element ', tmpElement.getLabel(), ' to the eList.')
                        print(Support.myName(), ': ', tmpElement.dumpElement(False))
                else:
                    # This is an error code
                    return tmpElement
            ###########################################################
            # Something unknown
            else:   # Unknown element found
                print(Support.myName(), ': Unknown element found:', line, '. Exiting.')
                Support.myExit(10)
            if Support.gVerbose > 2:
                print()
            inx += 1

        if self.has_k_or_m: 
            code = self.verify2LsForKM()
            # If the return value isn't a 0, it's an error code
            if code: return code
    
        if foundSolve:
            if Support.gVerbose > 2:
                print(Support.myName(), ': Parsing solve statement ', solveLine)
                spl = solveLine.split()
                for it in range(len(spl)):
                    print('         solve[', it, ']: ', spl[it])
            code = self.parseSolveStatement(solveLine)
            if code: return code
        else:
            print(Support.myName(), ": Solve element not found, this is required, otherwise what's the point? Exiting.")
            return Support.myExit(9)

        self.checkForFloatingNodes()

        if Support.gVerbose > 2:
            print(Support.myName(), ': Size(eList)=', len(self.getEList()))
            print(Support.myName(), ': Size(simpList)=', self.simpList.size())
            print(Support.myName(), ': Size(subList)=', len(self.subList))
            print(Support.myName(), ': freq=', self.frq)
            print(Support.myName(), ': HTML filename=', self.htmlFilename)
            print(Support.myName(), ': Filepath=', self.filePath)
            print(Support.myName(), ': Solve elements in internal node numbers')
            print(Support.myName(), ': I/P is', end='')
            self.inputSource.printElementS()
            print(Support.myName(), ': O/P is', end='')
            self.outputSource.printElementS()
        return 0

    # lbl- string
    # p_nd, n_nd- strings
    def initVSource(self, p_nd, n_nd, aSource):
        aSource.setLabel('Vout')
        aSource.setUserNodes12(int(p_nd), int(n_nd) )
        aSource.setElementType('v')

    def initISource(self, lbl, aSource):
        if not self.theCircuit.elementExists(self.getEList(), lbl):
            print(Support.myName(), ': Error- Solve statement, I/I case, used with a source that does not')
            print(Support.myName(), '  exist:', lbl, '. Exiting.')
            return Support.myExit(15)
        aSource.setLabel(lbl)
        aSource.setElementType('i')
        theEle = self.theCircuit.findElementWithLabel(lbl)
        aSource.setUserNodes12(theEle.getNode1(), theEle.getNode2())

    # parse source, if found. Format: solve output input
    # V/V: i i i i    size=5
    # I/V: a i i      size=4
    # V/I: i i a      size=4
    # I/I: a a        size=3
    # The input/output for the solve statements are saved as elements. If a voltage, the nodes are saved and the element
    # type is set to etV. If a current is needed, the label of the element whose current is desired is saved and the
    # element type is set to etI.
    # The label of any voltage element(s) is set to the default "Input V" or "Output V".
    def parseSolveStatement(self, solveLine):
        splt = solveLine.strip().split()
        if Support.gVerbose > 2:
            print(Support.myName(), ': splt=', splt)
        if len(splt) == 5:    # V/V
            self.initVSource(splt[1], splt[2], self.outputSource)
            self.initVSource(splt[3], splt[4], self.inputSource)
            if Support.gVerbose > 1:
                print(Support.myName(), ': Output set to voltage, input set to voltage')
                print(Support.myName(), ': Output= (', self.outputSource.getUserNode1(), ', ',
                                                self.outputSource.getUserNode2(), '), Input= (',
                                                self.inputSource.getUserNode1(), ', ',
                                                self.inputSource.getUserNode2(), ') (user node numbers).')
        
        elif len(splt) == 4:  # I/V or V/I
            # Use the first arg to determine which one, I/V or V/I
            #   I/V:    solve src nd  nd
            #   V/I:    solve nd  nd  src
            try:
                int(splt[3])
            except ValueError:  # Must be V/I
                # Make sure the specified current sensing source exists
                if not self.theCircuit.elementExists(self.getEList(), splt[3]):
                    print(Support.myName(), ': Error- Solve statement, V/I case, used with a source that does not')
                    print(Support.myName(), '  exist:', splt[3], '. Exiting.')
                    return Support.myExit(13)
                self.initVSource(splt[1], splt[2], self.outputSource)
                self.initISource(splt[3], self.inputSource)
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Output set to voltage, input set to current')

            #except ValueError:  # Must be I/V
            else:
                # Make sure the specified current sensing source exists
                if not self.theCircuit.elementExists(self.getEList(), splt[1]):
                    print(Support.myName(), ': Error- Solve statement, I/V case, used with a source that does not')
                    print(Support.myName(), '  exist:', splt[1], '. Exiting.')
                    return Support.myExit(14)
                self.initISource(splt[1], self.outputSource)
                self.initVSource(splt[2], splt[3], self.inputSource)
                if Support.gVerbose > 1:
                    print(Support.myName(), ': Output set to current, input set to voltage')

        elif len(splt) == 3:  # I/I
            self.initISource(splt[1], self.outputSource)
            self.initISource(splt[2], self.inputSource)
            if Support.gVerbose > 1:
                print(Support.myName(), ': Output set to current, input set to current.')
        else:
            print(Support.myName(), ': Error- Solve statement found with incorrect syntax.')
            return Support.myExit(12)
        return 0

    def parseKorM(self, splt):
        # M:      m1 L1 L2 val    size=4
        # M:      m1 L1 L2        size=3
        if len(splt) < 3:
            print(Support.myName(), ': Error- This element needs its name and two inductor names. Exiting.')
            return Support.myExit(32)
        if not (splt[1][0]=='l' and splt[2][0]=='l'):
            print(Support.myName(), splt[1][0], splt[2][0])
            print(Support.myName(), ': Error- A mutual inductor or coupled inductor must be coupled with two inductors (L). Exiting.')
            return Support.myExit(33)
        if len(splt)==4:  # if format is Mxxx L1 L2, use Mxxx as the value
            value = splt[3]
        else:
            value = None
        #                         eType       label    L1       L2
        tempElement = ce.CElement(splt[0][0], splt[0], splt[1], splt[2], value)
        self.has_k_or_m = True
        return tempElement

    def parseCILRV(self, nodeP, nodeN, splt):
        if len(splt)==4:
            value = splt[3]
        else:
            value = None
        tempElement = ce.CElement(splt[0][0], splt[0], nodeP, nodeN, 0, 0, value)
        return tempElement

    def parseEFGHT(self, nodeP, nodeN, splt):
        if len(splt) < 5:
            print(Support.myName(), ': Error- This element requires four nodes to be specified. Exiting.')
            return Support.myExit(18)
        try:
            nodeCP = int(splt[3])
            nodeCN = int(splt[4])
        except ValueError:
            print(Support.myName(), ': Error- nodes must be numeric. Exiting.')
            return Support.myExit(19)
        if len(splt)==6:
            value = splt[5]
        else:
            value = None
        tempElement = ce.CElement(splt[0][0], splt[0], nodeP, nodeN, nodeCP, nodeCN, value)
        return tempElement

#                            split size    connection format
# V/V:    e1 1 2 3 4 [e]    size=5 or 6    4 nodes + <value>
# I/I:    f1 1 2 3 4 [f]    size=5 or 6    4 nodes + <value>
# V/I:    gm 1 2 3 4 [g]    size=5 or 6    4 nodes + <value>
# I/V:    hw 1 2 3 4 [h]    size=5 or 6    4 nodes + <value>
# CILRV:  xa 1 2 [v]        size=3 or 4    2 nodes + <value>
# T:      t1 1 2 3 4        size=5         4 nodes
# M:      m1 L1 L2 [m|k][=]val  size=3,5 or 6  2 L's + <value>
# If m or k aren't given, use k=Mxxx.
    def parseElement(self, splt):
        eType = splt[0][0]
        if Support.gVerbose > 0:
            print(Support.myName(), ': Parsing element type |'+eType+'|')
        # K or M elements, the oddballs.
        if eType in ce.CElement.getEWith2Labels():
            return self.parseKorM(splt)
        # Element is anything except K or M, so splt[1] and splt[2] should be node nums.
        try:
            nodeP = int(splt[1])
            nodeN = int(splt[2])
        except ValueError:
            print(Support.myName(), ': Error- nodes must be numeric. Exiting.')
            return Support.myExit(11)

        if eType in ce.CElement.getEWithTwoNodes():
            return self.parseCILRV(nodeP, nodeN, splt)
        if eType in ce.CElement.getEWith4Nodes():
            return self.parseEFGHT(nodeP, nodeN, splt)
        else:
            print(Support.myName(), ': Found an unknown element: ', splt[0], ' type ', eType, ', skipping this line.')
            return -1

    # Make sure the controlling nodes in the F and H elements exist in the eList, and make sure
    # there's only one stimulus source in the circuit.
    # 1) Make a list of i and v elements.
    # 2)     For each CCVS or CCCS, find its controlling source in the iv list and
    #            mark it as being a current sensor.
    # 3)     Also check that it has 0 or no value set
    # 4) Go through the iv list and make sure that:
    #    1) There's only one source left that hasn't been marked as a current sensor
    #    2) That source must have value = 1
    # def verifyIVSforFandHElements(self):
    #     iv_list = {}
    #     for element in self.getEList():
    #         if element.getEType() in 'iv':
    #             lbl = element.getLabel()
    #             iv_list[lbl] = 0
    #     if Support.gVerbose > 2:
    #         print(Support.myName(), "IV list is:", iv_list)
    #
    #     for element in self.getEList():
    #         if element.getEType() in 'fh':
    #             if not CCircuit.CCircuit.elementExists(self.getEList(), element.getISenseLabel() ):
    #                 print(Support.myName(), ': An "F" or "H" element has referenced a voltage source')
    #                 print(Support.myName(), '  that does not exist in this circuit: Exiting.')
    #                 print(Support.myName(), '  Element:', element.getLabel(), ', source:', element.getISenseLabel())
    #                 return Support.myExit(23)
    #             control_src = element.getISenseLabel()
    #             # Should always work since we just checked to see if that source exists
    #             iv_list[control_src] = 1
    #     indep_count = 0
    #     stimulus = []
    #     for k, v in iv_list.items():
    #         if not v:
    #             stimulus.append(k)
    #             if Support.gVerbose > 2:
    #                 print(Support.myName(), "Stimulus is element", k)
    #         indep_count = indep_count + v
    #
    #     self.stimulus = stimulus[0]
    #     if indep_count != len(iv_list)-1:
    #         if len(stimulus) == 1:
    #             print("This is embarrassing, ", indep_count, "current sensing sources")
    #             print("    were found out of", len(iv_list), ", leaving ", \
    #                   len(iv_list)-indep_count, "sources that seem to be sources for the")
    #             print("    circuit, but only", len(stimulus), "stimulus sources were found")
    #         else:
    #             print("There appears to be more than one independent source acting as a")
    #             print("stimulus for the circuit. Only one is allowed.")
    #         print("List of independent sources that aren't current sensors:")
    #         for src in stimulus:
    #             print(src)
    #         return Support.myExit(24)
    #     return 0

    def verify2LsForKM(self):
        for element in self.getEList():
            exxit = False
            if element.hasTwoLabels():
                if (not self.theCircuit.elementExists(self.getEList(), element.getL1() ) ):
                    print(Support.myName(), ': ', element.getLabel(), ' referenced ', element.getL1(), \
                          ' which is not in this circuit!')
                    exxit = True
                if (not self.theCircuit.elementExists(self.getEList(), element.getL2() ) ):
                    print(Support.myName(), ': ', element.getLabel(), ' referenced ', element.getL2(), \
                          ' which is not in this circuit!')
                    exxit = True
                if exxit:
                    return Support.myExit(35)
        return 0

    def addToDict(self, nd, nodes):
        if nd in nodes:
            nodes[nd] = nodes[nd] + 1
        else:
            nodes[nd] = 1

    def checkForFloatingNodes(self):
        '''Check for floating nodes on any current source, dep or indep. 
        Floating nodes on voltage sources or any other elements seems to be ok.
        Need to check this on transformers and mutual inductors.'''
        nodes = {}
        for ele in self.getEList():
            if not ele.hasTwoLabels():
                self.addToDict(ele.getNode1(), nodes)
                self.addToDict(ele.getNode2(), nodes)

                # Only include CCCS and CCVS here because of the implied IVS
                # that is put between nodes 3 and 4. VCVS and VCCS only senses
                # with nodes 3 & 4.
                if ele.getLabel()[0] in 'fh':
                    self.addToDict(ele.getNode3(), nodes)
                    self.addToDict(ele.getNode4(), nodes)
        
        if Support.gVerbose > 2:
            for k, v in nodes.items():
                print('Node ', k, ' is referenced ', v, ' times')
        
        code = 0
        for ele in self.getEList():
            if ele.getLabel()[0] in 'ifg':
                nd1 = ele.getNode1()
                if nodes[nd1] == 1:
                    code = 26
                    print("Node ", nd1, " on element ", ele.getLabel(), " is not connected")
                    print("to any other nodes. For this circuit to be solvable, it must be")
                    print("connected to at least one other node.")
                nd2 = ele.getNode2()
                if nodes[nd2] == 1:
                    code = 26
                    print("Node ", nd2, " on element ", ele.getLabel(), " is not connected")
                    print("to any other nodes. For this circuit to be solvable, it must be")
                    print("connected to at least one other node.")
        return code


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
    v: ac voltage source. Positive current flows into node 10 (positive terminal).
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
