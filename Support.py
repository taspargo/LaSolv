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

import wx
import traceback

# 0 to 4?
gVerbose = 0

def myName():
    return traceback.extract_stack(None, 2)[0][2]

# 1    Node not found in reverselookup           CCircuit, reverseLookup
# 2    Current for a controlling src not found   CCircuit, calculateVorIEqn
# 3    Node in o/p source spec doesn't exist.    CCircuit, renumberSourceNodes
# 4    Node in i/p source spec doesn't exist.    CCircuit, renumberSourceNodes
# 5    Added element with 'label' not found      CCircuit, getAddedNodeElementIndex
# 6    Source with name 'label' not found        CCircuit, calculateVorIEqn
# 7    Source element type not v or i            CCircuit, calculateVorIEqn
# 8    Computer type not found                   CFileReader, init
# 9    Solve element not found                   CFileReader, init
# 10   Unknown element found                     CFileReader, init; CLinearEq, fillAMatrix
# 11   None-numeric node name                    CFileReader, parseSolveStatement
# 12   Incorrect solve statement syntax          CFileReader, parseSolveStatement
# 13   Solve statement with unknown source, V/I  CFileReader, parseSolveStatement
# 14   Solve statement with unknown source, I/V  CFileReader, parseSolveStatement
# 15   Solve statement, unknown 1st source, I/I  CFileReader, parseSolveStatement
# 16   Solve statement, unknown 2nd source, I/I  CFileReader, parseSolveStatement
# 17   Two node element without enough nodes     CFileReader, parseElement
# 18   2-node element, non-numeric nodes         CFileReader, parseElement
# 19   4-node element, non-numeric nodes         CFileReader, parseElement
# 20   F or H element, not enough nodes          CFileReader, parseElement
# 21   F or H element, c-sense isn't an IVS      CFileReader, parseElement
# 22   F or H element, non-numeric nodes         CFileReader, parseElement
# 23   F or H element uses a non-existent source CFileReader, verifyIVSforFandHElements
# 24   More than one stimulus source found       CFileReader, verifyIVSforFandHElements
# 25   Reorder equations failed                  CLinearEquations, solveEquations
# 26   Floating node on current source           CFileReader, checkForFloatingNodes
# 27   Could not find file/path                  CFileReader, init
# 28   Permissions error when opening file       eqnSolver, createHTMLFile
# 29   Unknown relational operator in simplify   CFileReader
# 30   Denominator is zero                       eqnSolver, eqnSolve
# 31   Numerator is zero                         eqnSolver, eqnSolve
# 32   Mutual inductor 'm' or 'k' not used.      CFileReader, parseElement
# 33   Mutual inductor, non-L coupling           CFileReader, parseElement
# 34   M element, k or m supplied but no value   CFileReader, parseElement
# 35   M element, coupled ind not in ckt         CFileReader, parseElement
# 36   Eqn has no freq dependence, trivial plot  eqnSolver, eqnPlot
# 37   Eqn is unstable, can't plot it.           eqnSolver, eqnPlot

err_list = [ \
"Zero",
"Node not found in reverse lookup",
"Controlling source current couldn't be calculated",           
"Node in output source doesn't exist.",             
"Node in input source doesn't exist.",  
"Added element with 'label' not found",   
"Source not found" ,     
"Source element type not v or i",
"Computer type not found",
"Solve element not found",
"Unknown element found",
"None-numeric node name",
"Incorrect solve statement syntax",
"Solve statement with unknown source, V/I",
"Solve statement with unknown source, I/V",
"Solve statement, unknown 1st source, I/I",
"Solve statement, unknown 2nd source, I/I",
"Two node element without enough nodes",
"2-node element, non-numeric nodes",
"4-node element, non-numeric nodes",
"F or H element, not enough nodes",
"F or H element, c-sense isn't an IVS",
"F or H element, non-numeric nodes",
"F or H element uses a non-existent source",
"More than one independent source being used as a stimulus",
"Reorder equations failed",
"Floating node on a current source",
"Could not find file/path",
"Permissions error when opening file",
"Unknown relational operator in simplify statement",
"Denominator is zero",
"Numerator is zero",
"Mutual inductor found with value specification not using 'k' or 'm'",
"Mutual inductor found with non-inductors specified for coupling elements",
"Mutual inductor found with 'k' or 'm' supplied but no value or name",
"Mutual inductor found referencing a non-existent coupling element",
"Plot is flat, no frequency dependence.",
"This circuit is unstable, can't plot the equation"
]

def myExit(code, errMssg=''):
    if code <= len(err_list):
        print('*'*(len(err_list[code])+11))
        print("Error #{0:2}: {1:}".format(code, err_list[code]))
            
        print('*'*(len(err_list[code])+11))
    else:
        print('?'*50)
        print('An unknown error occurred: code', code)
        print('?'*50)
        
    mssg = "Error #{0:2}: {1:}".format(code, err_list[code])
    if errMssg != '':
        mssg = mssg + '\n' + errMssg
    wx.MessageBox(mssg, 'Error', wx.OK | wx.ICON_ERROR)
    input("")
    return code
    #sys.exit(code)
